from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.models import Produto, Usuario
from app.schemas.produto import ProdutoCreate, ProdutoUpdate
from app.services.auth_service import get_current_user
from app.services.estoque_service import products_with_balances, serialize_product

router = APIRouter(prefix="/api/produtos", tags=["produtos"])


@router.get("")
def list_products(q: str = Query(default="", max_length=100), db: Session = Depends(get_db), _user: Usuario = Depends(get_current_user)) -> list[dict]:
    query = db.query(Produto).filter(Produto.ativo.is_(True))
    if q.strip():
        term = f"%{q.strip()}%"
        query = query.filter((Produto.nome.ilike(term)) | (Produto.sku.ilike(term)) | (Produto.categoria.ilike(term)))
    products = query.order_by(Produto.nome.asc()).all()
    balances = {p.id: balance for p, balance in products_with_balances(db)}
    return [serialize_product(p, balances.get(p.id, p.estoque_inicial)) for p in products]


@router.post("", status_code=201)
def create_product(payload: ProdutoCreate, db: Session = Depends(get_db), user: Usuario = Depends(get_current_user)) -> dict:
    product = Produto(**payload.model_dump(), demonstracao=False)
    db.add(product)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="SKU ou UID RFID já está cadastrado.") from None
    db.refresh(product)
    return serialize_product(product, product.estoque_inicial)


@router.patch("/{product_id}")
def update_product(product_id: int, payload: ProdutoUpdate, db: Session = Depends(get_db), _user: Usuario = Depends(get_current_user)) -> dict:
    product = db.get(Produto, product_id)
    if product is None:
        raise HTTPException(status_code=404, detail="Produto não encontrado.")
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(product, key, value)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="UID RFID já está associado a outro produto.") from None
    db.refresh(product)
    balances = {p.id: balance for p, balance in products_with_balances(db, active_only=False)}
    return serialize_product(product, balances.get(product.id, product.estoque_inicial))
