from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload

from app.database.connection import get_db
from app.models import Movimentacao, Produto, Usuario
from app.schemas.movimentacao import LeituraRfid, MovimentacaoCreate
from app.services.auth_service import get_current_user
from app.services.estoque_service import current_balance, signed_quantity
from app.services.rfid_service import resolve_product

router = APIRouter(prefix="/api/movimentacoes", tags=["movimentações"])


def _serialize(move: Movimentacao) -> dict:
    signed = signed_quantity(move.tipo, move.quantidade)
    return {
        "id": move.id, "produto_id": move.produto_id,
        "produto_nome": move.produto.nome if move.produto else "Produto removido",
        "sku": move.produto.sku if move.produto else "—",
        "tipo": move.tipo, "quantidade": abs(move.quantidade), "quantidade_assinada": signed,
        "motivo": move.motivo, "usuario_nome": move.usuario_nome,
        "criado_em": move.criado_em.isoformat() if move.criado_em else "",
        "origem": move.origem,
    }


def _record(db: Session, product: Produto, tipo: str, quantity: int, reason: str, user: Usuario, origin: str) -> Movimentacao:
    signed = signed_quantity(tipo, quantity)
    if current_balance(db, product) + signed < 0:
        raise HTTPException(status_code=409, detail="A movimentação deixaria o saldo negativo. Ajuste a quantidade ou faça um inventário físico.")
    move = Movimentacao(
        produto_id=product.id, tipo=tipo, quantidade=quantity, motivo=reason[:240],
        usuario_open_id=user.open_id, usuario_nome=user.nome, origem=origin,
    )
    db.add(move)
    db.commit()
    db.refresh(move)
    return move


@router.get("")
def list_movements(limit: int = Query(default=100, ge=1, le=300), db: Session = Depends(get_db), _user: Usuario = Depends(get_current_user)) -> list[dict]:
    moves = db.query(Movimentacao).options(joinedload(Movimentacao.produto)).order_by(Movimentacao.criado_em.desc(), Movimentacao.id.desc()).limit(limit).all()
    return [_serialize(move) for move in moves]


@router.post("", status_code=201)
def create_movement(payload: MovimentacaoCreate, db: Session = Depends(get_db), user: Usuario = Depends(get_current_user)) -> dict:
    product = db.query(Produto).filter(Produto.id == payload.produto_id, Produto.ativo.is_(True)).with_for_update().first()
    if product is None:
        raise HTTPException(status_code=404, detail="Produto ativo não encontrado.")
    reason = payload.motivo or ("Ajuste de inventário" if payload.tipo == "ajuste" else "Movimentação manual")
    try:
        move = _record(db, product, payload.tipo, payload.quantidade, reason, user, "manual")
    except Exception:
        db.rollback()
        raise
    return _serialize(db.query(Movimentacao).options(joinedload(Movimentacao.produto)).filter(Movimentacao.id == move.id).one())


@router.post("/scan", status_code=201)
def scan_rfid(payload: LeituraRfid, db: Session = Depends(get_db), user: Usuario = Depends(get_current_user)) -> dict:
    product = resolve_product(db, payload.uid)
    if product is None:
        raise HTTPException(status_code=404, detail="UID não associada a um produto ativo. Cadastre a tag no catálogo primeiro.")
    try:
        move = _record(db, product, payload.tipo, payload.quantidade, f"Leitura RFID · {payload.uid}", user, "rfid")
    except Exception:
        db.rollback()
        raise
    return _serialize(db.query(Movimentacao).options(joinedload(Movimentacao.produto)).filter(Movimentacao.id == move.id).one())
