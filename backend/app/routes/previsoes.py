from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.ml.previsao import prever_consumo
from app.models import Usuario
from app.services.auth_service import get_current_user
from app.services.previsao_service import train_models

router = APIRouter(prefix="/api/previsoes", tags=["previsões"])


@router.get("")
def list_forecasts(dias: int = Query(default=30, ge=7, le=90), db: Session = Depends(get_db), _user: Usuario = Depends(get_current_user)) -> list[dict]:
    return prever_consumo(db, horizonte_dias=dias)


@router.post("/treinar")
def train(db: Session = Depends(get_db), _user: Usuario = Depends(get_current_user)) -> dict:
    return train_models(db)
