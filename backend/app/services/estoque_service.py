from __future__ import annotations

from decimal import Decimal

from sqlalchemy import case, func
from sqlalchemy.orm import Session

from app.models import Movimentacao, Produto


def signed_quantity(tipo: str, quantidade: int) -> int:
    if tipo == "entrada":
        return quantidade
    if tipo == "saida":
        return -quantidade
    return quantidade


def current_balance(db: Session, product: Produto) -> int:
    delta = db.query(func.coalesce(func.sum(case(
        (Movimentacao.tipo == "entrada", Movimentacao.quantidade),
        (Movimentacao.tipo == "saida", -Movimentacao.quantidade),
        else_=Movimentacao.quantidade,
    )), 0)).filter(Movimentacao.produto_id == product.id).scalar()
    return int(product.estoque_inicial + (delta or 0))


def products_with_balances(db: Session, active_only: bool = True) -> list[tuple[Produto, int]]:
    delta = case(
        (Movimentacao.tipo == "entrada", Movimentacao.quantidade),
        (Movimentacao.tipo == "saida", -Movimentacao.quantidade),
        else_=Movimentacao.quantidade,
    )
    query = db.query(Produto, func.coalesce(func.sum(delta), 0).label("variacao")).outerjoin(
        Movimentacao, Movimentacao.produto_id == Produto.id
    )
    if active_only:
        query = query.filter(Produto.ativo.is_(True))
    rows = query.group_by(Produto.id).order_by(Produto.nome.asc()).all()
    return [(product, int(product.estoque_inicial + (variation or 0))) for product, variation in rows]


def serialize_product(product: Produto, balance: int | None = None) -> dict:
    return {
        "id": product.id,
        "sku": product.sku,
        "nome": product.nome,
        "categoria": product.categoria,
        "unidade": product.unidade,
        "custo": float(product.custo) if product.custo is not None else None,
        "estoque_minimo": product.estoque_minimo,
        "estoque_inicial": product.estoque_inicial,
        "saldo": current_balance_for_serialization(product, balance),
        "rfid_uid": product.rfid_uid,
        "ativo": product.ativo,
        "demonstracao": product.demonstracao,
        "atualizado_em": product.atualizado_em.isoformat() if product.atualizado_em else "",
    }


def current_balance_for_serialization(product: Produto, balance: int | None) -> int:
    return int(balance if balance is not None else product.estoque_inicial)


def build_alerts(rows: list[tuple[Produto, int]]) -> list[dict]:
    alerts = []
    for product, balance in rows:
        if balance <= product.estoque_minimo:
            alerts.append({
                "produto_id": product.id,
                "sku": product.sku,
                "nome": product.nome,
                "saldo": balance,
                "estoque_minimo": product.estoque_minimo,
                "quantidade_repor": max(product.estoque_minimo * 2 - balance, 0),
                "severidade": "ruptura" if balance <= 0 else "baixo",
            })
    alerts.sort(key=lambda alert: (0 if alert["severidade"] == "ruptura" else 1, alert["saldo"] - alert["estoque_minimo"], alert["nome"]))
    return alerts


def estimated_inventory_value(rows: list[tuple[Produto, int]]) -> Decimal | None:
    known = [(product, balance) for product, balance in rows if product.custo is not None]
    if not known:
        return None
    return sum((product.custo or Decimal("0")) * balance for product, balance in known)
