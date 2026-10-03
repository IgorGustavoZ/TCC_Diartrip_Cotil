import hashlib
import hmac
import logging
import os
import secrets
import smtplib
import ssl
from datetime import datetime, timedelta, timezone
from email.message import EmailMessage

from fastapi import HTTPException

from database import get_db
from utils.security import verificar_senha

logger = logging.getLogger("diartrip.email_verification")

_CODIGO_TTL = timedelta(minutes=15)
_MAX_TENTATIVAS = 5

_TEXTO_CADASTRO = (
    "Seu codigo de verificacao do Diartrip e {codigo}. "
    "Ele expira em 15 minutos. Se voce nao criou uma conta, ignore este email."
)
_TEXTO_TROCA_EMAIL = (
    "Seu codigo para confirmar o novo email da sua conta Diartrip e {codigo}. "
    "Ele expira em 15 minutos. Se voce nao pediu essa alteracao, ignore este email."
)


class EmailDeliveryError(Exception):
    pass


def normalizar_email(email: str) -> str:
    """Email canônico (sem espaços, minúsculo). O MySQL compara emails sem
    diferenciar maiúsculas, então tudo que usa o email como chave (rate
    limit, gravação no banco) precisa usar esta forma — senão "A@x.com" e
    "a@x.com" viram contadores de rate limit diferentes para a mesma conta."""
    return email.strip().lower()


def _agora() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _hash_codigo(codigo: str) -> str:
    segredo = os.getenv("SECRET_KEY")
    if not segredo:
        raise EmailDeliveryError("SECRET_KEY deve estar configurado")
    return hmac.new(segredo.encode(), codigo.encode("ascii"), hashlib.sha256).hexdigest()


def gerar_codigo_verificacao() -> tuple[str, str, datetime]:
    codigo = f"{secrets.randbelow(1_000_000):06d}"
    codigo_hash = _hash_codigo(codigo)
    expira = _agora() + _CODIGO_TTL
    return codigo, codigo_hash, expira


def enviar_codigo_verificacao(email: str, codigo: str, troca_email: bool = False) -> None:
    host = os.getenv("SMTP_HOST")
    remetente = os.getenv("SMTP_FROM") or os.getenv("SMTP_USERNAME")
    if not host or not remetente:
        raise EmailDeliveryError("SMTP_HOST e SMTP_FROM devem estar configurados")

    try:
        porta = int(os.getenv("SMTP_PORT", "587"))
        usar_ssl = os.getenv("SMTP_USE_SSL", "false").lower() == "true"
        usuario = os.getenv("SMTP_USERNAME")
        senha = os.getenv("SMTP_PASSWORD")
        if bool(usuario) != bool(senha):
            raise EmailDeliveryError("SMTP_USERNAME e SMTP_PASSWORD devem ser configurados juntos")

        mensagem = EmailMessage()
        mensagem["Subject"] = (
            "Confirme seu novo email - Diartrip" if troca_email else "Confirme seu email - Diartrip"
        )
        mensagem["From"] = remetente
        mensagem["To"] = email
        texto = _TEXTO_TROCA_EMAIL if troca_email else _TEXTO_CADASTRO
        mensagem.set_content(texto.format(codigo=codigo))

        contexto = ssl.create_default_context()
        cliente_cls = smtplib.SMTP_SSL if usar_ssl else smtplib.SMTP
        with cliente_cls(
            host,
            porta,
            timeout=10,
            **({"context": contexto} if usar_ssl else {}),
        ) as cliente:
            if not usar_ssl:
                cliente.starttls(context=contexto)
            if usuario and senha:
                cliente.login(usuario, senha)
            cliente.send_message(mensagem)
    except EmailDeliveryError:
        raise
    except (OSError, smtplib.SMTPException, ValueError) as exc:
        raise EmailDeliveryError("Falha ao enviar email de verificacao") from exc


def _conferir_codigo(cursor, usuario: dict, codigo: str, extra_valido: bool = True) -> str:
    """Confere o código de `usuario` (linha travada com FOR UPDATE) e já
    grava no banco o efeito das falhas (tentativa a mais / código expirado).
    `extra_valido` permite exigir outra prova junto com o código (ex.: a
    senha); se for False, conta como tentativa errada sem dizer o motivo.
    Retorna "ok", "invalid", "expired" ou "locked"."""
    tentativas = usuario["tentativas_verificacao"]
    expira = usuario["codigo_verificacao_expira"]
    if tentativas >= _MAX_TENTATIVAS:
        return "locked"
    if not expira or expira < _agora():
        cursor.execute(
            "UPDATE usuarios SET codigo_verificacao_hash=NULL, "
            "codigo_verificacao_expira=NULL WHERE id_usuario=%s",
            (usuario["id_usuario"],),
        )
        return "expired"
    codigo_ok = secrets.compare_digest(
        _hash_codigo(codigo), usuario["codigo_verificacao_hash"] or ""
    )
    if codigo_ok and extra_valido:
        return "ok"
    tentativas += 1
    cursor.execute(
        "UPDATE usuarios SET tentativas_verificacao=%s WHERE id_usuario=%s",
        (tentativas, usuario["id_usuario"]),
    )
    return "locked" if tentativas >= _MAX_TENTATIVAS else "invalid"


def _erro_codigo(resultado: str) -> HTTPException:
    if resultado == "expired":
        return HTTPException(status_code=400, detail="Codigo expirado. Solicite um novo codigo.")
    if resultado == "locked":
        return HTTPException(status_code=429, detail="Limite de tentativas atingido. Solicite um novo codigo.")
    return HTTPException(status_code=400, detail="Codigo invalido")


def verificar_codigo(email: str, codigo: str, senha: str) -> dict:
    """Ativa a conta pendente. Exige o código E a senha do cadastro: assim,
    mesmo que alguém tenha cadastrado o email de outra pessoa, o dono da
    caixa de entrada não ativa sem querer uma conta com a senha do atacante
    (e o atacante não ativa sem o código)."""
    email = normalizar_email(email)
    resultado = "invalid"
    usuario_id = None
    with get_db() as conexao:
        cursor = conexao.cursor(dictionary=True)
        try:
            cursor.execute(
                """SELECT id_usuario, senha_hash, email_verificado, codigo_verificacao_hash,
                          codigo_verificacao_expira, tentativas_verificacao
                   FROM usuarios WHERE email=%s FOR UPDATE""",
                (email,),
            )
            usuario = cursor.fetchone()
            # Conta inexistente ou já verificada: mesma resposta de código
            # inválido, para a rota (sem login) não revelar quais emails existem.
            if usuario and not usuario["email_verificado"]:
                senha_ok = verificar_senha(senha, usuario["senha_hash"])
                resultado = _conferir_codigo(cursor, usuario, codigo, extra_valido=senha_ok)
                if resultado == "ok":
                    cursor.execute(
                        """UPDATE usuarios SET email_verificado=1,
                                  codigo_verificacao_hash=NULL,
                                  codigo_verificacao_expira=NULL,
                                  tentativas_verificacao=0
                           WHERE id_usuario=%s""",
                        (usuario["id_usuario"],),
                    )
                    usuario_id = usuario["id_usuario"]
        finally:
            cursor.close()

    if resultado == "ok":
        return {"mensagem": "Email verificado com sucesso", "usuario_id": usuario_id}
    raise _erro_codigo(resultado)


def reenviar_codigo(email: str) -> None:
    email = normalizar_email(email)
    codigo = None
    with get_db() as conexao:
        cursor = conexao.cursor(dictionary=True)
        try:
            cursor.execute(
                "SELECT id_usuario, email_verificado FROM usuarios WHERE email=%s FOR UPDATE",
                (email,),
            )
            usuario = cursor.fetchone()
            if not usuario or usuario["email_verificado"]:
                return

            codigo, codigo_hash, expira = gerar_codigo_verificacao()
            cursor.execute(
                """UPDATE usuarios SET codigo_verificacao_hash=%s,
                          codigo_verificacao_expira=%s, tentativas_verificacao=0
                   WHERE id_usuario=%s""",
                (codigo_hash, expira, usuario["id_usuario"]),
            )
        finally:
            cursor.close()

    # Envia depois do commit: o SMTP pode levar segundos e não deve segurar
    # a conexão do pool nem o lock da linha.
    enviar_codigo_verificacao(email, codigo)


def solicitar_troca_email(cursor, usuario_id: int, novo_email: str) -> str:
    """Grava `novo_email` como pendente e devolve o código a ser enviado para
    ele. O email da conta só muda em `confirmar_troca_email`. Roda dentro da
    transação de quem chama (usuario_service.atualizar)."""
    cursor.execute(
        "SELECT 1 FROM usuarios WHERE email=%s AND id_usuario<>%s",
        (novo_email, usuario_id),
    )
    if cursor.fetchone():
        raise HTTPException(status_code=409, detail="Este e-mail já está em uso por outro usuário")
    codigo, codigo_hash, expira = gerar_codigo_verificacao()
    cursor.execute(
        """UPDATE usuarios SET email_pendente=%s, codigo_verificacao_hash=%s,
                  codigo_verificacao_expira=%s, tentativas_verificacao=0
           WHERE id_usuario=%s""",
        (novo_email, codigo_hash, expira, usuario_id),
    )
    return codigo


def confirmar_troca_email(usuario_id: int, codigo: str) -> dict:
    resultado = "invalid"
    with get_db() as conexao:
        cursor = conexao.cursor(dictionary=True)
        try:
            cursor.execute(
                """SELECT id_usuario, email_pendente, codigo_verificacao_hash,
                          codigo_verificacao_expira, tentativas_verificacao
                   FROM usuarios WHERE id_usuario=%s FOR UPDATE""",
                (usuario_id,),
            )
            usuario = cursor.fetchone()
            if not usuario or not usuario["email_pendente"]:
                raise HTTPException(status_code=400, detail="Nenhuma troca de email pendente")
            resultado = _conferir_codigo(cursor, usuario, codigo)
            if resultado == "ok":
                try:
                    cursor.execute(
                        """UPDATE usuarios SET email=email_pendente, email_pendente=NULL,
                                  codigo_verificacao_hash=NULL,
                                  codigo_verificacao_expira=NULL,
                                  tentativas_verificacao=0
                           WHERE id_usuario=%s""",
                        (usuario_id,),
                    )
                except Exception as err:
                    if getattr(err, "errno", None) == 1062:
                        raise HTTPException(
                            status_code=409, detail="Este e-mail já está em uso por outro usuário"
                        )
                    raise
        finally:
            cursor.close()

    if resultado == "ok":
        return {"mensagem": "Email atualizado com sucesso"}
    raise _erro_codigo(resultado)
