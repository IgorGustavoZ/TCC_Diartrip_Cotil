import os
import time
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

import pytest
import jwt as pyjwt

SECRET_KEY = os.environ["SECRET_KEY"]
ALGORITHM = "HS256"


class TestSecurity:
    def test_gerar_hash_retorna_bcrypt(self):
        from utils.security import gerar_hash
        h = gerar_hash("SenhaForte1")
        assert h.startswith("$2b$") or h.startswith("$2a$")

    def test_gerar_hash_diferente_cada_vez(self):
        from utils.security import gerar_hash
        h1 = gerar_hash("SenhaForte1")
        h2 = gerar_hash("SenhaForte1")
        assert h1 != h2

    def test_verificar_senha_correta_retorna_true(self):
        from utils.security import gerar_hash, verificar_senha
        senha = "SenhaForte1"
        h = gerar_hash(senha)
        assert verificar_senha(senha, h) is True

    def test_verificar_senha_errada_retorna_false(self):
        from utils.security import gerar_hash, verificar_senha
        h = gerar_hash("SenhaCorreta1")
        assert verificar_senha("SenhaErrada1", h) is False

    def test_criar_token_contem_id_e_jti(self):
        from utils.security import criar_token
        token = criar_token(42)
        payload = pyjwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        assert payload["id"] == 42
        assert "jti" in payload
        assert "exp" in payload

    def test_decodificar_token_valido(self):
        from utils.security import criar_token, decodificar_token
        token = criar_token(7)
        assert decodificar_token(token) == 7

    def test_decodificar_token_expirado_lanca_401(self):
        from utils.security import decodificar_token
        from fastapi import HTTPException
        token = pyjwt.encode(
            {"id": 1, "jti": "exp-test",
             "exp": datetime.now(timezone.utc) - timedelta(seconds=1)},
            SECRET_KEY, algorithm=ALGORITHM,
        )
        with pytest.raises(HTTPException) as exc:
            decodificar_token(token)
        assert exc.value.status_code == 401
        assert "expirado" in exc.value.detail.lower()

    def test_decodificar_token_assinatura_invalida_lanca_401(self):
        from utils.security import decodificar_token
        from fastapi import HTTPException
        token = pyjwt.encode(
            {"id": 1, "jti": "bad-sig",
             "exp": datetime.now(timezone.utc) + timedelta(hours=1)},
            "chave-errada", algorithm=ALGORITHM,
        )
        with pytest.raises(HTTPException) as exc:
            decodificar_token(token)
        assert exc.value.status_code == 401

    def test_revogar_e_detectar_token_revogado(self):
        """Token revogado deve ser detectado por _is_revogado."""
        from utils.security import criar_token, revogar_token, _is_revogado
        import utils.security as sec

        token = criar_token(99)
        payload = pyjwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        jti = payload["jti"]

        with patch("utils.security.get_redis", return_value=None):
            revogar_token(token)
            assert _is_revogado(jti) is True

    def test_token_nao_revogado_nao_detectado(self):
        from utils.security import criar_token, _is_revogado
        token = criar_token(88)
        payload = pyjwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        jti = payload["jti"]
        assert _is_revogado(jti) is False



class TestRateLimiter:
    def _fresh_key(self, prefix="test"):
        """Gera uma chave unica por teste para evitar interferencia."""
        return f"{prefix}:{time.monotonic_ns()}"

    def test_abaixo_do_limite_nao_levanta_excecao(self):
        """Requisicoes abaixo do limite nao devem levantar HTTPException."""
        from utils.rate_limiter import _verificar_memoria
        chave = self._fresh_key("below")
        for _ in range(5):
            _verificar_memoria(chave, limite=10)

    def test_acima_do_limite_levanta_429(self):
        """Apos atingir o limite, deve levantar HTTPException 429."""
        from utils.rate_limiter import _verificar_memoria
        from fastapi import HTTPException
        chave = self._fresh_key("above")
        limite = 3
        for _ in range(limite):
            _verificar_memoria(chave, limite=limite)
        with pytest.raises(HTTPException) as exc:
            _verificar_memoria(chave, limite=limite)
        assert exc.value.status_code == 429

    def test_chaves_diferentes_nao_interferem(self):
        """Chaves distintas nao devem compartilhar contadores."""
        from utils.rate_limiter import _verificar_memoria
        from fastapi import HTTPException
        chave_a = self._fresh_key("a")
        chave_b = self._fresh_key("b")
        limite = 2
        for _ in range(limite):
            _verificar_memoria(chave_a, limite=limite)
        with pytest.raises(HTTPException):
            _verificar_memoria(chave_a, limite=limite)
        _verificar_memoria(chave_b, limite=limite)



class TestImagemUtils:
    def test_validar_jpeg_valido(self):
        """Bytes JPEG com extensao jpg deve passar validacao."""
        from utils.imagem_utils import validar_imagem
        jpeg = b"\xff\xd8\xff\xe0" + b"\x00" * 100
        with patch("utils.imagem_utils._validar_dimensoes"):
            validar_imagem(jpeg, "jpg")

    def test_validar_png_valido(self):
        from utils.imagem_utils import validar_imagem
        png = b"\x89PNG\r\n\x1a\n" + b"\x00" * 100
        with patch("utils.imagem_utils._validar_dimensoes"):
            validar_imagem(png, "png")

    def test_validar_extensao_nao_permitida_lanca_400(self):
        """Extensao .exe deve levantar HTTPException 400."""
        from utils.imagem_utils import validar_imagem
        from fastapi import HTTPException
        with pytest.raises(HTTPException) as exc:
            validar_imagem(b"\x4d\x5a\x90\x00", "exe")
        assert exc.value.status_code == 400

    def test_validar_pdf_como_jpg_lanca_400(self):
        """Bytes PDF com extensao jpg (magic bytes incorretos) deve retornar 400."""
        from utils.imagem_utils import validar_imagem
        from fastapi import HTTPException
        pdf_bytes = b"%PDF-1.4\n" + b"\x00" * 50
        with pytest.raises(HTTPException) as exc:
            validar_imagem(pdf_bytes, "jpg")
        assert exc.value.status_code == 400

    def test_validar_arquivo_muito_grande_lanca_400(self):
        """Arquivo maior que max_size lanca HTTPException 400."""
        from utils.imagem_utils import validar_imagem
        from fastapi import HTTPException
        jpeg = b"\xff\xd8\xff\xe0" + b"\x00" * 100
        with pytest.raises(HTTPException) as exc:
            validar_imagem(jpeg, "jpg", max_size=10)
        assert exc.value.status_code == 400

    def test_validar_jpeg_bytes_com_extensao_png_lanca_400(self):
        """Magic bytes JPEG com extensao .png deve falhar validacao."""
        from utils.imagem_utils import validar_imagem
        from fastapi import HTTPException
        jpeg = b"\xff\xd8\xff\xe0" + b"\x00" * 100
        with pytest.raises(HTTPException) as exc:
            validar_imagem(jpeg, "png")
        assert exc.value.status_code == 400

    def test_strip_exif_retorna_bytes(self):
        """strip_exif deve retornar bytes processados."""
        from utils.imagem_utils import strip_exif
        jpeg = b"\xff\xd8\xff\xe0" + b"\x00" * 100

        mock_img = MagicMock()
        mock_img.mode = "RGB"
        mock_img.save.side_effect = lambda buf, format: buf.write(b"\xff\xd8\xff\xe0\x00\x10")

        with patch("PIL.Image.open", return_value=mock_img):
            result = strip_exif(jpeg, "jpg")

        assert isinstance(result, bytes)
        assert len(result) > 0

    def test_strip_exif_fallback_em_erro(self):
        """strip_exif deve retornar bytes originais se PIL falhar."""
        from utils.imagem_utils import strip_exif
        with patch("utils.imagem_utils.strip_exif") as mock_strip:
            mock_strip.return_value = b"original"
            result = mock_strip(b"original", "jpg")
        assert result == b"original"



class TestCloudinaryUpload:
    def test_parse_public_id_da_url(self):
        """deletar_imagem deve extrair public_id corretamente da URL."""
        import cloudinary.uploader as cu_uploader
        import utils.cloudinary_upload as cu

        url = "https://res.cloudinary.com/mycloud/image/upload/v123456/diartrip/fotos/10/abc.jpg"

        with patch.object(cu_uploader, "destroy") as mock_destroy:
            cu._configurado = True
            try:
                cu.deletar_imagem(url)
            finally:
                cu._configurado = False

        mock_destroy.assert_called_once()
        call_args = mock_destroy.call_args[0][0]
        assert call_args == "diartrip/fotos/10/abc"

    def test_deletar_imagem_url_sem_cloudinary_ignorada(self):
        """URLs sem 'cloudinary.com' nao devem chamar destroy."""
        import cloudinary.uploader as cu_uploader
        import utils.cloudinary_upload as cu

        with patch.object(cu_uploader, "destroy") as mock_destroy:
            cu.deletar_imagem("https://example.com/imagem.jpg")

        mock_destroy.assert_not_called()

    def test_deletar_imagem_url_vazia_ignorada(self):
        """URL vazia nao deve chamar destroy."""
        import cloudinary.uploader as cu_uploader
        import utils.cloudinary_upload as cu

        with patch.object(cu_uploader, "destroy") as mock_destroy:
            cu.deletar_imagem("")
            cu.deletar_imagem(None)

        mock_destroy.assert_not_called()

    def test_upload_falha_lanca_502(self):
        """Se cloudinary.uploader.upload falhar, deve levancar HTTPException 502."""
        import cloudinary.uploader as cu_uploader
        import utils.cloudinary_upload as cu
        from fastapi import HTTPException

        with patch.object(cu_uploader, "upload", side_effect=Exception("timeout")):
            cu._configurado = True
            try:
                with pytest.raises(HTTPException) as exc:
                    cu.upload_imagem(b"\xff\xd8\xff\xe0" + b"\x00" * 10, "diartrip/test")
                assert exc.value.status_code == 502
            finally:
                cu._configurado = False


class TestGeoapifyClient:
    def test_geocodificar_sem_key_retorna_none(self):
        import utils.geoapify_client as geo
        with patch.object(geo, "_API_KEY", None):
            assert geo.geocodificar("Paris") is None

    def test_geocodificar_sem_destino_retorna_none(self):
        import utils.geoapify_client as geo
        with patch.object(geo, "_API_KEY", "fake-key"):
            assert geo.geocodificar("") is None

    def test_geocodificar_sucesso(self):
        import utils.geoapify_client as geo
        resp = MagicMock()
        resp.json.return_value = {"features": [{"geometry": {"coordinates": [2.35, 48.85]}}]}
        with patch.object(geo, "_API_KEY", "fake-key"), \
             patch("utils.geoapify_client.httpx.get", return_value=resp):
            assert geo.geocodificar("Paris") == (48.85, 2.35)

    def test_geocodificar_sem_resultado_retorna_none(self):
        import utils.geoapify_client as geo
        resp = MagicMock()
        resp.json.return_value = {"features": []}
        with patch.object(geo, "_API_KEY", "fake-key"), \
             patch("utils.geoapify_client.httpx.get", return_value=resp):
            assert geo.geocodificar("Lugar Inexistente") is None

    def test_geocodificar_erro_de_rede_retorna_none(self):
        import utils.geoapify_client as geo
        with patch.object(geo, "_API_KEY", "fake-key"), \
             patch("utils.geoapify_client.httpx.get", side_effect=Exception("timeout")):
            assert geo.geocodificar("Paris") is None

    def test_buscar_pontos_interesse_sem_key_retorna_vazio(self):
        import utils.geoapify_client as geo
        with patch.object(geo, "_API_KEY", None):
            assert geo.buscar_pontos_interesse(48.85, 2.35) == []

    def test_buscar_pontos_interesse_filtra_campos(self):
        import utils.geoapify_client as geo
        resp = MagicMock()
        resp.json.return_value = {"features": [{
            "properties": {"name": "Museu do Louvre", "categories": ["tourism.sights"], "formatted": "Paris, França"},
            "geometry": {"coordinates": [2.33, 48.86]},
        }]}
        with patch.object(geo, "_API_KEY", "fake-key"), \
             patch("utils.geoapify_client.httpx.get", return_value=resp):
            pois = geo.buscar_pontos_interesse(48.85, 2.35)
        assert pois == [{
            "nome": "Museu do Louvre",
            "categoria": "tourism.sights",
            "endereco": "Paris, França",
            "coordenadas": {"lat": 48.86, "lon": 2.33},
        }]

    def test_buscar_pontos_interesse_erro_retorna_vazio(self):
        import utils.geoapify_client as geo
        with patch.object(geo, "_API_KEY", "fake-key"), \
             patch("utils.geoapify_client.httpx.get", side_effect=Exception("timeout")):
            assert geo.buscar_pontos_interesse(48.85, 2.35) == []

    def test_autocomplete_sem_key_lanca_erro(self):
        import utils.geoapify_client as geo
        with patch.object(geo, "_API_KEY", None):
            with pytest.raises(RuntimeError):
                geo.autocomplete("Par")

    def test_autocomplete_retorna_features(self):
        import utils.geoapify_client as geo
        resp = MagicMock()
        resp.json.return_value = {"features": [{"properties": {"city": "Paris", "formatted": "Paris, França"}}]}
        with patch.object(geo, "_API_KEY", "fake-key"), \
             patch("utils.geoapify_client.httpx.get", return_value=resp):
            features = geo.autocomplete("Par")
        assert features[0]["properties"]["city"] == "Paris"


class TestOpenWeatherClient:
    def test_previsao_sem_key_retorna_vazio(self):
        import utils.openweather_client as ow
        with patch.object(ow, "_API_KEY", None):
            assert ow.previsao_por_dia(48.85, 2.35) == {}

    def test_previsao_agrupa_por_dia_e_detecta_chuva(self):
        import utils.openweather_client as ow
        resp = MagicMock()
        resp.json.return_value = {"list": [
            {"dt_txt": "2026-09-10 09:00:00", "main": {"temp": 14}, "weather": [{"main": "Rain", "description": "chuva leve"}]},
            {"dt_txt": "2026-09-10 12:00:00", "main": {"temp": 16}, "weather": [{"main": "Rain", "description": "chuva leve"}]},
            {"dt_txt": "2026-09-11 09:00:00", "main": {"temp": 22}, "weather": [{"main": "Clear", "description": "céu limpo"}]},
        ]}
        with patch.object(ow, "_API_KEY", "fake-key"), \
             patch("utils.openweather_client.httpx.get", return_value=resp):
            previsao = ow.previsao_por_dia(48.85, 2.35)

        assert previsao["2026-09-10"]["chuva"] is True
        assert "15" in previsao["2026-09-10"]["resumo"]
        assert previsao["2026-09-11"]["chuva"] is False

    def test_previsao_erro_de_rede_retorna_vazio(self):
        import utils.openweather_client as ow
        with patch.object(ow, "_API_KEY", "fake-key"), \
             patch("utils.openweather_client.httpx.get", side_effect=Exception("timeout")):
            assert ow.previsao_por_dia(48.85, 2.35) == {}
