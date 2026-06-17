from fastapi import APIRouter, Depends
from schemas import DashboardCompleto, DashboardGeral, DashboardPessoal, DashboardAdmin
from utils.auth import get_usuario_logado
from services import dashboard_service

router = APIRouter(prefix="/grupos/{id_grupo}/dashboard", tags=["Dashboard"])


@router.get("", response_model=DashboardCompleto)
def dashboard_completo(id_grupo: int, usuario_id: int = Depends(get_usuario_logado)):
    """Retorna geral + pessoal + admin (se admin) em uma única chamada."""
    return dashboard_service.completo(id_grupo, usuario_id)


@router.get("/geral", response_model=DashboardGeral)
def dashboard_geral(id_grupo: int, usuario_id: int = Depends(get_usuario_logado)):
    return dashboard_service.geral(id_grupo, usuario_id)


@router.get("/pessoal", response_model=DashboardPessoal)
def dashboard_individual(id_grupo: int, usuario_id: int = Depends(get_usuario_logado)):
    return dashboard_service.pessoal(id_grupo, usuario_id)


@router.get("/admin", response_model=DashboardAdmin)
def dashboard_admin(id_grupo: int, usuario_id: int = Depends(get_usuario_logado)):
    return dashboard_service.admin(id_grupo, usuario_id)
