from __future__ import annotations

from sqlalchemy.orm import Session

from app.models import Produto


def normalize_uid(uid: str) -> str:
    return "".join(character for character in uid.strip().upper() if character not in {" ", ":", "-"})


def resolve_product(db: Session, uid: str) -> Produto | None:
    normalized = normalize_uid(uid)
    if not normalized:
        return None
    return db.query(Produto).filter(Produto.rfid_uid == normalized, Produto.ativo.is_(True)).first()


def integration_status() -> dict[str, str]:
    """The current implementation is a simulator; hardware transport is intentionally isolated."""
    return {"modo": "simulacao", "leitor": "ESP32 + RC522 (Wokwi)", "acao": "uid_para_produto"}
