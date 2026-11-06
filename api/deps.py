from typing import Generator
from sqlmodel import Session
from core.database import engine

def get_db() -> Generator[Session, None, None]:
    """Dépendance FastAPI fournissant une session de base de données isolée par requête."""
    with Session(engine) as session:
        yield session
