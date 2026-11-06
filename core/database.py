"""Module de gestion de la base de données avec l'ORM SQLModel."""

import os
from typing import Any, Optional
from sqlalchemy import event
from sqlalchemy.engine import Engine
from sqlmodel import Session, SQLModel, create_engine
from core.config import DB_PATH as DEFAULT_DB_PATH
from repositories.ville_repository import (
    insert_ville,
    get_villes,
    get_ville_by_id,
    get_ville_by_nom,
    insert_releve,
    get_releves_by_ville,
    get_dernier_releve,
    get_statistiques_ville,
    get_statistiques_globales,
)

@event.listens_for(Engine, "connect")
def _set_sqlite_pragma(dbapi_connection: Any, connection_record: Any) -> None:
    """Active systématiquement les clés étrangères sur chaque connexion SQLite."""
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys = ON;")
    cursor.close()



# =====================================================================
# Moteur (Engine) & Sessions ORM
# =====================================================================

def get_engine(db_path: str = DEFAULT_DB_PATH) -> Engine:
    """Crée un moteur SQLAlchemy/SQLModel pour le chemin SQLite indiqué."""
    if db_path == ":memory:":
        url = "sqlite:///:memory:"
    else:
        # Crée le dossier parent (ex: data/) s'il n'existe pas encore
        dossier = os.path.dirname(db_path)
        if dossier:
            os.makedirs(dossier, exist_ok=True)
        url = f"sqlite:///{db_path}"
    return create_engine(url, connect_args={"check_same_thread": False})


# Moteur par défaut pointant sur meteo.db
engine = get_engine(DEFAULT_DB_PATH)


def init_db(db_path: str = DEFAULT_DB_PATH) -> Session:
    """Initialise les tables SQLModel et retourne une Session ORM ouverte."""
    current_engine = engine if db_path == DEFAULT_DB_PATH else get_engine(db_path)
    SQLModel.metadata.create_all(current_engine)
    return Session(current_engine)


def get_session(custom_engine: Optional[Engine] = None) -> Session:
    """Ouvre et retourne une nouvelle session ORM SQLModel."""
    target_engine = custom_engine or engine
    SQLModel.metadata.create_all(target_engine)
    return Session(target_engine)


# Alias pour compatibilité
get_connection = get_session

