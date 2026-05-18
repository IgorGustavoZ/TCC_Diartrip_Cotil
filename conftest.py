import pytest
from database import get_db

_TEST_EMAILS = [
    "teste_pytest@diartrip.com",
    "gastos_pytest@diartrip.com",
    "estranho_pytest@diartrip.com",
    "estranho2_pytest@diartrip.com",
    "estranho3_pytest@diartrip.com",
]


def _limpar_dados_teste():
    with get_db() as db:
        cursor = db.cursor()
        placeholders = ",".join(["%s"] * len(_TEST_EMAILS))
        emails = tuple(_TEST_EMAILS)

        cursor.execute(
            f"DELETE g FROM gastos g JOIN usuarios u ON g.id_usuario = u.id_usuario"
            f" WHERE u.email IN ({placeholders})",
            emails,
        )
        cursor.execute(
            f"DELETE g FROM gastos g JOIN grupos_viagem gv ON g.id_grupo = gv.id_grupo"
            f" JOIN usuarios u ON gv.criado_por = u.id_usuario WHERE u.email IN ({placeholders})",
            emails,
        )

        cursor.execute(
            f"DELETE gm FROM grupo_membros gm JOIN grupos_viagem gv ON gm.id_grupo = gv.id_grupo"
            f" JOIN usuarios u ON gv.criado_por = u.id_usuario WHERE u.email IN ({placeholders})",
            emails,
        )

        cursor.execute(
            f"DELETE gm FROM grupo_membros gm JOIN usuarios u ON gm.id_usuario = u.id_usuario"
            f" WHERE u.email IN ({placeholders})",
            emails,
        )

        cursor.execute(
            f"DELETE gv FROM grupos_viagem gv JOIN usuarios u ON gv.criado_por = u.id_usuario"
            f" WHERE u.email IN ({placeholders})",
            emails,
        )

        cursor.execute(
            f"DELETE FROM usuarios WHERE email IN ({placeholders})",
            emails,
        )
        cursor.close()


@pytest.fixture(autouse=True, scope="session")
def limpar_banco_antes_dos_testes():
    _limpar_dados_teste()
    yield
    _limpar_dados_teste()
