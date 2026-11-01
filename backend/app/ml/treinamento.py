"""Treina tendências de consumo usando o histórico persistido e grava modelo.pkl."""

from app.database.connection import SessionLocal
from app.services.previsao_service import train_models


def main() -> None:
    with SessionLocal() as db:
        result = train_models(db)
    print(f"Treinamento concluído: {result['modelos']} produto(s) com histórico.")
    print(f"Artefato: {result['caminho']}")


if __name__ == "__main__":
    main()
