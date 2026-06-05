"""
conftest.py — Fixtures compartilhadas para toda a suite de testes.
"""
import os
import sys
import time
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
import pytest
from unittest.mock import MagicMock, patch

# --------------------------------------------------------------------------- #
# Configurar variaveis de ambiente ANTES de qualquer import do projeto
# --------------------------------------------------------------------------- #
os.environ.setdefault("SECRET_KEY", "test-secret-key-diartrip-2026-pytest")
os.environ.setdefault("ALGORITHM", "HS256")
os.environ.setdefault("DB_HOST", "localhost")
os.environ.setdefault("DB_USER", "root")
os.environ.setdefault("DB_PASSWORD", "")
os.environ.setdefault("DB_NAME", "diartrip_test")
os.environ.setdefault("OPENROUTER_API_KEY", "test-openrouter-key")
os.environ.setdefault("CLOUDINARY_CLOUD_NAME", "test-cloud")
os.environ.setdefault("CLOUDINARY_API_KEY", "test-api-key")
os.environ.setdefault("CLOUDINARY_API_SECRET", "test-api-secret")
os.environ["REDIS_URL"] = ""  # forca fallback em memoria

# --------------------------------------------------------------------------- #
# Mock do mysql.connector ANTES de importar database.py
# --------------------------------------------------------------------------- #
_mysql_mock = MagicMock()
_mysql_connector_mock = MagicMock()

class MockError(Exception):
    def __init__(self, *args, **kwargs):
        super().__init__(*args)
        self.errno = kwargs.get('errno', 0)
        self.msg = kwargs.get('msg', '')

_mysql_connector_mock.Error = MockError
_mysql_connector_mock.IntegrityError = MockError
_mysql_connector_mock.DatabaseError = MockError
_mysql_connector_mock.ProgrammingError = MockError
_mysql_connector_mock.OperationalError = MockError
_mysql_connector_mock.InterfaceError = MockError
_mysql_connector_mock.InternalError = MockError
_mysql_connector_mock.NotSupportedError = MockError
_mysql_connector_mock.DataError = MockError

_mock_pool = MagicMock()
_mock_connection = MagicMock()

def _default_cursor(*args, **kwargs):
    # Retorna um mock que se comporta como um dicionário para evitar KeyError em rotas
    c = MagicMock()
    # Configura fetchone para retornar um dicionário real com chaves comuns e TIPOS CORRETOS
    c.fetchone.return_value = {
        "id_usuario": 1, 
        "usuario_id": 1, # as used in some responses
        "id_grupo": 1, 
        "id_post": 1, 
        "id_gasto": 1, 
        "id_foto": 1, 
        "id_roteiro": 1,
        "cargo": "admin", 
        "senha_hash": "$2b$04$ducseYqWmvWtI/uSEsMtq.ZPQzr5p2YIAe335YKoG3xIe0F8bT5jK", # hash for "Teste1234"
        "nome": "Mock User", 
        "email": "mock@test.com", 
        "nome_grupo": "Mock Group",
        "codigo_convite": "MOCK123",
        "total_consumido": 0.0,
        "orcamento_restante": 1000.0,
        "percentual_consumido": 0,
        "distribuicao_categorias": [],
        "total_pago_por_mim": 0.0,
        "minha_divida_atual": 0.0,
        "ultimos_gastos_pessoais": [],
        "estatisticas": MagicMock(membros_ativos=1, total_fotos_subidas=0, itens_no_roteiro=0),
        "ranking_contribuicao_financeira": []
    }
    c.fetchall.return_value = []
    c.rowcount = 1
    c.lastrowid = 1
    return c

_mock_connection.cursor.side_effect = _default_cursor
_mock_pool.get_connection.return_value = _mock_connection
_mysql_connector_mock.pooling.MySQLConnectionPool = MagicMock(return_value=_mock_pool)

sys.modules["mysql"] = _mysql_mock
sys.modules["mysql.connector"] = _mysql_connector_mock
sys.modules["mysql.connector.pooling"] = _mysql_connector_mock.pooling

# --------------------------------------------------------------------------- #
# Global get_db mock support - OVERRIDE REAL database.get_db
# --------------------------------------------------------------------------- #
_override_db_conn = [None]

@contextmanager
def global_get_db_mock():
    # Se database.get_db foi alterado (ex: por um patch), usamos a versão alterada.
    # Isso resolve o problema de módulos que já importaram get_db antes do patch.
    import database
    if database.get_db is not global_get_db_mock:
        with database.get_db() as conn:
            yield conn
        return

    if _override_db_conn[0]:
        yield _override_db_conn[0]
    else:
        # Fallback para o pool mockado
        conn = database._pool.get_connection()
        try:
            yield conn
        finally:
            pass

import database
database._pool = _mock_pool
database.get_db = global_get_db_mock

# Patch cloudinary antes de importar
_cloudinary_mock = MagicMock()
_cloudinary_uploader_mock = MagicMock()
sys.modules["cloudinary"] = _cloudinary_mock
sys.modules["cloudinary.uploader"] = _cloudinary_uploader_mock

# Garantir que redis_client usa fallback
import utils.redis_client as _redis_mod
_redis_mod._tentou = True
_redis_mod._client = None

from fastapi.testclient import TestClient
from main import app

# Token CSRF fixo usado nos testes autenticados.
_TEST_CSRF = "test-csrf-token-pytest-2026"

_METODOS_MUTANTES = {"POST", "PUT", "PATCH", "DELETE"}


class CsrfTestClient(TestClient):
    """TestClient que injeta X-CSRF-Token automaticamente em requisições mutantes,
    lendo o valor do cookie csrf_token já presente no jar do cliente."""

    def request(self, method, url, **kwargs):
        if method.upper() in _METODOS_MUTANTES:
            csrf = self.cookies.get("csrf_token")
            if csrf:
                headers = dict(kwargs.get("headers") or {})
                headers.setdefault("X-CSRF-Token", csrf)
                kwargs["headers"] = headers
        return super().request(method, url, **kwargs)


# --------------------------------------------------------------------------- #
# Helpers para criar cursor mock configuravel
# --------------------------------------------------------------------------- #

def make_cursor(rows=None, lastrowid=1, rowcount=1):
    """Cria um cursor MagicMock com fetchone/fetchall configuravel."""
    cursor = MagicMock()
    cursor.lastrowid = lastrowid
    cursor.rowcount = rowcount
    if rows is None:
        rows = []
    _rows = list(rows)
    _idx = [0]

    def _fetchone():
        if _idx[0] < len(_rows):
            val = _rows[_idx[0]]
            _idx[0] += 1
            return val
        return None

    cursor.fetchone.side_effect = _fetchone
    cursor.fetchall.return_value = list(_rows)
    return cursor


def make_connection(cursor=None):
    """Cria uma conexao MagicMock."""
    conn = MagicMock()
    if cursor is not None:
        conn.cursor.return_value = cursor
    conn.commit = MagicMock()
    conn.rollback = MagicMock()
    conn.close = MagicMock()
    return conn


def fake_get_db(conn):
    """Factory que retorna um context manager imitando get_db com conn mockado."""
    @contextmanager
    def _inner():
        old = _override_db_conn[0]
        _override_db_conn[0] = conn
        try:
            yield conn
        except Exception:
            raise
        finally:
            _override_db_conn[0] = old
    return _inner


# --------------------------------------------------------------------------- #
# Tokens JWT de sessao
# --------------------------------------------------------------------------- #

@pytest.fixture(scope="session")
def token_usuario():
    """Gera JWT valido para usuario_id=1."""
    import jwt as pyjwt
    payload = {
        "id": 1,
        "jti": "test-jti-usuario",
        "exp": datetime.now(timezone.utc) + timedelta(hours=2),
    }
    return pyjwt.encode(payload, os.environ["SECRET_KEY"], algorithm="HS256")


@pytest.fixture(scope="session")
def token_admin():
    """Gera JWT valido para usuario_id=99 (admin)."""
    import jwt as pyjwt
    payload = {
        "id": 99,
        "jti": "test-jti-admin",
        "exp": datetime.now(timezone.utc) + timedelta(hours=2),
    }
    return pyjwt.encode(payload, os.environ["SECRET_KEY"], algorithm="HS256")


# --------------------------------------------------------------------------- #
# Fixture: client HTTP anonimo (sem cookie)
# --------------------------------------------------------------------------- #

@pytest.fixture
def client():
    """TestClient FastAPI sem autenticacao — um novo por teste para isolamento."""
    from main import app
    with CsrfTestClient(app, raise_server_exceptions=False) as c:
        yield c


# --------------------------------------------------------------------------- #
# Fixtures: client com cookie de autenticacao
# --------------------------------------------------------------------------- #

@pytest.fixture
def auth_cookies(token_usuario):
    return {"access_token": token_usuario}


@pytest.fixture
def admin_cookies(token_admin):
    return {"access_token": token_admin}


@pytest.fixture
def client_usuario(token_usuario):
    with CsrfTestClient(app, raise_server_exceptions=False) as c:
        c.cookies.set("access_token", token_usuario)
        c.cookies.set("csrf_token", _TEST_CSRF)
        yield c


@pytest.fixture
def client_admin(token_admin):
    with CsrfTestClient(app, raise_server_exceptions=False) as c:
        c.cookies.set("access_token", token_admin)
        c.cookies.set("csrf_token", _TEST_CSRF)
        yield c


# --------------------------------------------------------------------------- #
# Factories para dados fake
# --------------------------------------------------------------------------- #

def fake_usuario(id_usuario=1, nome="Teste User", email="teste@example.com"):
    return {
        "id_usuario": id_usuario,
        "nome": nome,
        "email": email,
        "bio": "Bio de teste",
        "foto_perfil": None,
        "data_criacao": "2026-01-01T00:00:00",
    }


def fake_grupo(id_grupo=10):
    return {
        "id_grupo": id_grupo,
        "nome_grupo": "Grupo Teste",
        "destino_principal": "Paris",
        "data_inicio": "2026-06-01",
        "data_fim": "2026-06-15",
        "orcamento": 5000.0,
        "tipo_viagem": "lazer",
        "preferencias": "praias, museus",
        "codigo_convite": "ABC123",
        "criador_id": 1,
        "criador": "Teste User",
    }


def fake_gasto(id_gasto=1, id_grupo=10, id_usuario=1, valor=100.0):
    return {
        "id_gasto": id_gasto,
        "id_grupo": id_grupo,
        "id_usuario": id_usuario,
        "valor": valor,
        "categoria": "alimentacao",
        "descricao": "Jantar",
        "data_gasto": "2026-06-01",
        "nome": "Teste User",
    }


def fake_foto(id_foto=1, id_grupo=10, id_usuario=1):
    return {
        "id_foto": id_foto,
        "id_grupo": id_grupo,
        "id_usuario": id_usuario,
        "caminho_arquivo": "https://res.cloudinary.com/test/image/upload/v123/diartrip/fotos/10/abc.jpg",
        "template_usado": None,
        "data_upload": "2026-06-01T10:00:00",
        "nome": "Teste User",
    }


def fake_post(id_post=1, id_usuario=1):
    return {
        "id_post": id_post,
        "id_usuario": id_usuario,
        "conteudo": "Post de teste",
        "imagem": None,
        "data_criacao": "2026-06-01T10:00:00",
        "nome": "Teste User",
        "foto_perfil": None,
    }


def fake_roteiro(id_roteiro=1, id_grupo=10):
    return {
        "id_roteiro": id_roteiro,
        "id_grupo": id_grupo,
        "titulo": "Dia 1 em Paris",
        "descricao": "Visitar Torre Eiffel",
        "data_criacao": "2026-06-01T10:00:00",
    }


# --------------------------------------------------------------------------- #
# Fixture: bypass rate limiter (autouse — ativo em todos os testes)
# --------------------------------------------------------------------------- #

@pytest.fixture(autouse=True)
def clean_security_state():
    from utils.security import _revogados
    with patch("utils.rate_limiter.verificar_rate_limit", return_value=None):
        _revogados.clear()
        yield


@pytest.fixture(autouse=True)
def bypass_rate_limiter():
    with patch("utils.rate_limiter.verificar_rate_limit", return_value=None):
        yield


# --------------------------------------------------------------------------- #
# Bytes de imagem minimos validos para testes
# --------------------------------------------------------------------------- #

JPEG_MAGIC = b"\xff\xd8\xff\xe0" + b"\x00" * 100
PNG_MAGIC = b"\x89PNG\r\n\x1a\n" + b"\x00" * 100
WEBP_MAGIC = b"RIFF\x00\x00\x00\x00WEBP" + b"\x00" * 100
PDF_BYTES = b"%PDF-1.4\n1 0 obj\n<< >>\nendobj\n"
JPEG_AS_PNG = JPEG_MAGIC  # magic bytes JPEG mas extensao .png
AS_PNG = JPEG_MAGIC  # magic bytes JPEG mas extensao .png
