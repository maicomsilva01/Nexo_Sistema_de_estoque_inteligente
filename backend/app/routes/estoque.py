from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from app.database.connection import get_db
from app.models import Movimentacao, Produto, Usuario
from app.services.auth_service import get_current_user
from app.services.estoque_service import build_alerts, estimated_inventory_value, products_with_balances, serialize_product
from app.services.previsao_service import daily_consumption

router = APIRouter(prefix="/api/estoque", tags=["estoque"])


def _serialize_move(move: Movimentacao) -> dict:
    signed = move.quantidade if move.tipo in {"entrada", "ajuste"} else -move.quantidade
    return {"id": move.id, "produto_id": move.produto_id, "produto_nome": move.produto.nome if move.produto else "—", "sku": move.produto.sku if move.produto else "—", "tipo": move.tipo, "quantidade": abs(move.quantidade), "quantidade_assinada": signed, "motivo": move.motivo, "usuario_nome": move.usuario_nome, "criado_em": move.criado_em.isoformat() if move.criado_em else "", "origem": move.origem}


@router.get("")
def stock_list(db: Session = Depends(get_db), _user: Usuario = Depends(get_current_user)) -> list[dict]:
    return [serialize_product(product, balance) for product, balance in products_with_balances(db)]


@router.get("/alertas")
def stock_alerts(db: Session = Depends(get_db), _user: Usuario = Depends(get_current_user)) -> list[dict]:
    return build_alerts(products_with_balances(db))


@router.get("/resumo")
def dashboard_summary(db: Session = Depends(get_db), _user: Usuario = Depends(get_current_user)) -> dict:
    rows = products_with_balances(db)
    product_ids = [product.id for product, _ in rows]
    now = datetime.now(UTC).replace(tzinfo=None)
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    in_count = db.query(func.coalesce(func.sum(Movimentacao.quantidade), 0)).filter(Movimentacao.tipo == "entrada", Movimentacao.criado_em >= month_start).scalar() or 0
    out_count = db.query(func.coalesce(func.sum(Movimentacao.quantidade), 0)).filter(Movimentacao.tipo == "saida", Movimentacao.criado_em >= month_start).scalar() or 0
    recent = db.query(Movimentacao).options(joinedload(Movimentacao.produto)).order_by(Movimentacao.criado_em.desc(), Movimentacao.id.desc()).limit(8).all()
    alerts = build_alerts(rows)
    value = estimated_inventory_value(rows)
    return {
        "total_skus": len(rows),
        "unidades": sum(balance for _, balance in rows),
        "itens_criticos": len(alerts),
        "valor_estimado": float(value) if isinstance(value, Decimal) else None,
        "entradas_mes": int(in_count), "saidas_mes": int(out_count),
        "serie_consumo": daily_consumption(db),
        "alertas": alerts[:8],
        "movimentacoes_recentes": [_serialize_move(move) for move in recent],
        "demonstracao": bool(rows) and all(product.demonstracao for product, _ in rows),
    }
