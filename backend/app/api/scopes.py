from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..schemas import Scope
from ..services.scope_service import ScopeService

router = APIRouter(prefix="/scopes", tags=["scopes"])


@router.get("")
def list_scopes(db: Session = Depends(get_db)):
    return ScopeService().list_scopes(db)


@router.post("")
def upsert_scope(scope: Scope, db: Session = Depends(get_db)):
    return ScopeService().upsert_scope(db, scope)


@router.get("/{scope_id}")
def get_scope(scope_id: str, db: Session = Depends(get_db)):
    try:
        return ScopeService().get_scope(db, scope_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="Scope not found")
