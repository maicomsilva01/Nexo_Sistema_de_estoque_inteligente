from __future__ import annotations

from datetime import UTC, datetime, timedelta

from sqlalchemy import DateTime, Integer, String, func, select
from sqlalchemy.orm import Mapped, Session, mapped_column

from app.database.connection import Base, engine
from app.database.migrations.v0001_initial import description as initial_description
from app.database.migrations.v0001_initial import upgrade as initial_upgrade
from app.database.migrations.v0002_contas_individuais import description as accounts_description
from app.database.migrations.v0002_contas_individuais import upgrade as accounts_upgrade
from app.database.migrations.v0003_username_login import description as username_description
from app.database.migrations.v0003_username_login import upgrade as username_upgrade
from app.database.migrations.v0004_username_not_null import description as username_required_description
from app.database.migrations.v0004_username_not_null import upgrade as username_required_upgrade
from app.models import Movimentacao, Produto, Usuario  # noqa: F401 — registra metadados


class VersaoSchema(Base):
    __tablename__ = "schema_migrations"

    versao: Mapped[int] = mapped_column(Integer, primary_key=True)
    descricao: Mapped[str] = mapped_column(String(160), nullable=False)
    aplicada_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


def _seed_demo(db: Session) -> None:
    if db.scalar(select(Produto.id).limit(1)) is not None:
        return
    products = [
        Produto(sku="CAB-USB-C", nome="Cabo USB-C 1,5 m", categoria="Acessórios", unidade="un", custo=24.90, estoque_minimo=8, estoque_inicial=32, rfid_uid="A1B2C3D4", demonstracao=True),
        Produto(sku="MOU-ERG-01", nome="Mouse ergonômico", categoria="Periféricos", unidade="un", custo=89.90, estoque_minimo=5, estoque_inicial=28, rfid_uid="B4C5D6E7", demonstracao=True),
        Produto(sku="TEC-SLM-02", nome="Teclado slim ABNT2", categoria="Periféricos", unidade="un", custo=119.00, estoque_minimo=5, estoque_inicial=24, rfid_uid="C8D9E0F1", demonstracao=True),
        Produto(sku="SUP-ALU-04", nome="Suporte de notebook alumínio", categoria="Acessórios", unidade="un", custo=74.50, estoque_minimo=6, estoque_inicial=6, rfid_uid="D2E3F4A5", demonstracao=True),
        Produto(sku="HUB-USBC-07", nome="Hub USB-C 7 portas", categoria="Conectividade", unidade="un", custo=149.90, estoque_minimo=4, estoque_inicial=4, rfid_uid="E6F7A8B9", demonstracao=True),
        Produto(sku="KIT-LIMP-03", nome="Kit de limpeza eletrônica", categoria="Manutenção", unidade="un", custo=36.00, estoque_minimo=3, estoque_inicial=0, rfid_uid="F0A1B2C3", demonstracao=True),
    ]
    db.add_all(products)
    db.flush()
    today = datetime.now(UTC).replace(tzinfo=None)
    demo_moves: list[Movimentacao] = []
    for day in range(30):
        for index, product in enumerate(products):
            if index < 3 and (day + index * 2) % (4 + index) == 0:
                amount = 1 if day % 3 else 2
            elif index == 3 and day in {5, 13, 22}:
                amount = 1
            elif index == 4 and day in {9, 20, 27}:
                amount = 1
            else:
                continue
            demo_moves.append(Movimentacao(
                produto_id=product.id, tipo="saida", quantidade=amount,
                motivo="Consumo da carga demonstrativa", usuario_nome="Carga demonstrativa",
                origem="demonstracao", criado_em=today - timedelta(days=29 - day, hours=(day * 3) % 12),
            ))
    db.add_all(demo_moves)


def initialize_database() -> None:
    """Apply pending additive migrations once; never reset existing product data."""
    VersaoSchema.__table__.create(bind=engine, checkfirst=True)  # type: ignore[attr-defined]
    with engine.begin() as connection:
        current = connection.execute(select(VersaoSchema.versao).where(VersaoSchema.versao == 1)).scalar_one_or_none()
        if current is None:
            initial_upgrade(connection)
            with Session(bind=connection) as db:
                _seed_demo(db)
                db.flush()
            connection.execute(VersaoSchema.__table__.insert().values(versao=1, descricao=initial_description))  # type: ignore[attr-defined]

        current_accounts = connection.execute(select(VersaoSchema.versao).where(VersaoSchema.versao == 2)).scalar_one_or_none()
        if current_accounts is None:
            accounts_upgrade(connection)
            connection.execute(VersaoSchema.__table__.insert().values(versao=2, descricao=accounts_description))  # type: ignore[attr-defined]

        current_username = connection.execute(select(VersaoSchema.versao).where(VersaoSchema.versao == 3)).scalar_one_or_none()
        if current_username is None:
            username_upgrade(connection)
            connection.execute(VersaoSchema.__table__.insert().values(versao=3, descricao=username_description))  # type: ignore[attr-defined]

        current_username_required = connection.execute(select(VersaoSchema.versao).where(VersaoSchema.versao == 4)).scalar_one_or_none()
        if current_username_required is None:
            username_required_upgrade(connection)
            connection.execute(VersaoSchema.__table__.insert().values(versao=4, descricao=username_required_description))  # type: ignore[attr-defined]


__all__ = ["initialize_database"]
