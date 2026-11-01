from __future__ import annotations

import pickle
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from typing import Any

from sqlalchemy.orm import Session

from app.models import Movimentacao
from app.services.estoque_service import products_with_balances

MODEL_PATH = Path(__file__).resolve().parents[1] / "ml" / "modelo.pkl"
WINDOW_DAYS = 30


def _daily_series(db: Session, product_id: int, today: date) -> list[dict[str, str | int]]:
    start = today - timedelta(days=WINDOW_DAYS - 1)
    daily = {start + timedelta(days=i): 0 for i in range(WINDOW_DAYS)}
    rows = db.query(Movimentacao).filter(
        Movimentacao.produto_id == product_id,
        Movimentacao.tipo == "saida",
        Movimentacao.criado_em >= datetime.combine(start, datetime.min.time()),
    ).all()
    for movement in rows:
        day = movement.criado_em.date()
        if day in daily:
            daily[day] += movement.quantidade
    return [{"dia": day.isoformat(), "quantidade": count} for day, count in daily.items()]


def _linear_fit(values: list[float]) -> tuple[float, float]:
    count = len(values)
    if count < 2:
        return (values[0] if values else 0.0, 0.0)
    xs = list(range(count))
    mean_x = sum(xs) / count
    mean_y = sum(values) / count
    denominator = sum((x - mean_x) ** 2 for x in xs)
    slope = sum((x - mean_x) * (y - mean_y) for x, y in zip(xs, values)) / denominator if denominator else 0.0
    return mean_y - slope * mean_x, slope


def train_models(db: Session) -> dict[str, Any]:
    today = datetime.now(UTC).date()
    trained_products: dict[str, dict[str, Any]] = {}
    count = 0
    for product, _balance in products_with_balances(db):
        series = _daily_series(db, product.id, today)
        values = [float(row["quantidade"]) for row in series]
        intercept, slope = _linear_fit(values)
        observed = sum(1 for value in values if value > 0)
        trained_products[str(product.id)] = {
            "intercept": intercept, "slope": slope, "media_diaria": sum(values) / WINDOW_DAYS,
            "dias_com_consumo": observed, "total_30_dias": sum(values), "sku": product.sku,
        }
        count += int(observed > 0)
    model: dict[str, Any] = {"generated_at": datetime.now(UTC).isoformat(), "window_days": WINDOW_DAYS, "products": trained_products}
    MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    with MODEL_PATH.open("wb") as output:
        pickle.dump(model, output, protocol=pickle.HIGHEST_PROTOCOL)
    return {"modelos": count, "caminho": "backend/app/ml/modelo.pkl"}


def _load_models() -> dict[str, Any]:
    if not MODEL_PATH.exists():
        return {"products": {}}
    try:
        with MODEL_PATH.open("rb") as source:
            result = pickle.load(source)  # arquivo é produzido somente pelo treinamento interno
        return result if isinstance(result, dict) else {"products": {}}
    except (OSError, EOFError, pickle.PickleError):
        return {"products": {}}


def forecasts(db: Session, horizon_days: int = 30) -> list[dict[str, Any]]:
    today = datetime.now(UTC).date()
    loaded = _load_models().get("products", {})
    models = loaded if isinstance(loaded, dict) else {}
    results: list[dict[str, Any]] = []
    for product, balance in products_with_balances(db):
        series = _daily_series(db, product.id, today)
        values = [float(row["quantidade"]) for row in series]
        total = sum(values)
        active_days = sum(1 for value in values if value > 0)
        stored = models.get(str(product.id), {})
        model = stored if isinstance(stored, dict) else {}
        _, computed_slope = _linear_fit(values)
        model_matches_history = bool(model) and float(model.get("total_30_dias", -1)) == total
        if active_days >= 5:
            # Na ausência de artefato atual, a mesma tendência é calculada sob demanda com a série real.
            slope = float(model.get("slope", computed_slope)) if model_matches_history else computed_slope
            baseline = total / WINDOW_DAYS
            projected_daily = max(0.0, (baseline * 0.65) + (max(0.0, baseline + slope * min(horizon_days / 2, 15)) * 0.35))
            method = "tendência treinada + média" if model_matches_history else "tendência calculada na consulta + média"
            confidence = "adequada"
        elif active_days > 0:
            projected_daily = total / WINDOW_DAYS
            method, confidence = "média móvel · pouca amostra", "limitada"
        else:
            projected_daily = 0.0
            method, confidence = "sem histórico suficiente", "sem_historico"
        horizon_estimate = round(projected_daily * horizon_days, 1)
        rupture_days = max(0, int(balance / projected_daily)) if projected_daily > 0 else None
        if confidence == "sem_historico":
            recommendation = "Registrar consumo para habilitar uma estimativa útil."
        elif rupture_days is not None and rupture_days <= horizon_days:
            recommendation = f"Avaliar reposição: cobertura estimada de {rupture_days} dias."
        else:
            recommendation = "Cobertura sem risco imediato pela estimativa atual."
        results.append({
            "produto_id": product.id, "sku": product.sku, "nome": product.nome,
            "saldo_atual": balance, "consumo_30_dias": int(total),
            "consumo_diario_estimado": round(projected_daily, 3),
            "previsao_horizonte": horizon_estimate, "horizonte_dias": horizon_days,
            "dias_ate_ruptura": rupture_days, "metodo": method, "confianca": confidence,
            "serie": series, "recomendacao": recommendation,
        })
    return results


def daily_consumption(db: Session) -> list[dict[str, str | int]]:
    today = datetime.now(UTC).date()
    start = today - timedelta(days=WINDOW_DAYS - 1)
    daily = {start + timedelta(days=i): 0 for i in range(WINDOW_DAYS)}
    rows = db.query(Movimentacao).filter(
        Movimentacao.tipo == "saida",
        Movimentacao.criado_em >= datetime.combine(start, datetime.min.time()),
    ).all()
    for movement in rows:
        day = movement.criado_em.date()
        if day in daily:
            daily[day] += movement.quantidade
    return [{"dia": day.isoformat(), "quantidade": count} for day, count in daily.items()]
