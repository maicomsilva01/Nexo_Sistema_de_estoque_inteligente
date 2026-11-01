"""Interface de inferência: método, estimativa e confiança são produzidos pelo serviço de domínio."""

from sqlalchemy.orm import Session

from app.services.previsao_service import forecasts


def prever_consumo(db: Session, horizonte_dias: int = 30) -> list[dict]:
    return forecasts(db, horizon_days=horizonte_dias)
