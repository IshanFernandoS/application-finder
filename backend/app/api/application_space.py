from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..database import get_db
from ..services.application_space_service import ApplicationSpaceService
from .utils import raise_http

router = APIRouter(prefix="/application-space", tags=["application-space"])


@router.post("/build")
def build_application_space(scope_id: str = "electromagnetic_functional_materials", db: Session = Depends(get_db)):
    try:
        return ApplicationSpaceService().build(db, scope_id)
    except Exception as exc:
        raise_http(exc)


@router.get("")
def get_application_space(scope_id: str = "electromagnetic_functional_materials", db: Session = Depends(get_db)):
    try:
        return ApplicationSpaceService().get_space(db, scope_id)
    except Exception as exc:
        raise_http(exc)


@router.get("/clusters")
def clusters(scope_id: str = "electromagnetic_functional_materials", db: Session = Depends(get_db)):
    return ApplicationSpaceService().list_clusters(db, scope_id)


@router.get("/nodes/{node_id}")
def node(node_id: str, db: Session = Depends(get_db)):
    try:
        return ApplicationSpaceService().get_node(db, node_id)
    except Exception as exc:
        raise_http(exc)
