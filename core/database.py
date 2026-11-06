"""Module de gestion de la base de données avec l'ORM SQLModel."""

import os
from typing import Any, Dict, List, Optional
from sqlalchemy import event, func
from sqlalchemy.engine import Engine
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, SQLModel, col, create_engine, select
from core.config import DB_PATH as DEFAULT_DB_PATH
from models.ville import Ville, Releve

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


# =====================================================================
# Opérations CRUD & Requêtes ORM
# =====================================================================

def insert_ville(session: Session, nom: str, latitude: float, longitude: float) -> int:
    """Insère une nouvelle ville ou met à jour ses coordonnées via l'ORM SQLModel."""
    nom_clean = nom.strip()
    statement = select(Ville).where(Ville.nom == nom_clean)
    ville_existante = session.exec(statement).first()

    if ville_existante is not None:
        ville_existante.latitude = float(latitude)
        ville_existante.longitude = float(longitude)
        session.add(ville_existante)
        session.commit()
        session.refresh(ville_existante)
        assert ville_existante.id is not None
        return ville_existante.id

    nouvelle_ville = Ville(
        nom=nom_clean,
        latitude=float(latitude),
        longitude=float(longitude),
    )
    session.add(nouvelle_ville)
    session.commit()
    session.refresh(nouvelle_ville)
    assert nouvelle_ville.id is not None
    return nouvelle_ville.id


def get_villes(session: Session) -> List[Dict[str, Any]]:
    """Retourne la liste de toutes les villes enregistrées triées par nom."""
    statement = select(Ville).order_by(col(Ville.nom).asc())
    villes = session.exec(statement).all()
    return [v.model_dump() for v in villes]


def get_ville_by_id(session: Session, ville_id: int) -> Optional[Dict[str, Any]]:
    """Récupère une ville par sa clé primaire via session.get()."""
    ville = session.get(Ville, ville_id)
    return ville.model_dump() if ville is not None else None


def get_ville_by_nom(session: Session, nom: str) -> Optional[Dict[str, Any]]:
    """Récupère une ville par son nom (insensible à la casse)."""
    statement = select(Ville).where(func.lower(col(Ville.nom)) == nom.strip().lower())
    ville = session.exec(statement).first()
    return ville.model_dump() if ville is not None else None


def insert_releve(
    session: Session,
    ville_id: int,
    temperature: float,
    vitesse_vent: float,
    date_heure: str,
) -> int:
    """Insère un relevé météorologique associé à une ville via l'ORM."""
    nouveau_releve = Releve(
        ville_id=ville_id,
        temperature=float(temperature),
        vitesse_vent=float(vitesse_vent),
        date_heure=date_heure,
    )
    try:
        session.add(nouveau_releve)
        session.commit()
        session.refresh(nouveau_releve)
        assert nouveau_releve.id is not None
        return nouveau_releve.id
    except IntegrityError:
        session.rollback()
        raise


def get_releves_by_ville(
    session: Session,
    ville_id: int,
    limit: int = 50,
) -> List[Dict[str, Any]]:
    """Récupère les relevés récents d'une ville par ordre chronologique décroissant."""
    statement = (
        select(Releve)
        .where(Releve.ville_id == ville_id)
        .order_by(col(Releve.date_heure).desc(), col(Releve.id).desc())
        .limit(limit)
    )
    releves = session.exec(statement).all()
    return [r.model_dump() for r in releves]


def get_dernier_releve(session: Session, ville_id: int) -> Optional[Dict[str, Any]]:
    """Récupère le relevé le plus récent pour une ville."""
    releves = get_releves_by_ville(session, ville_id, limit=1)
    return releves[0] if releves else None


def get_statistiques_ville(session: Session, ville_id: int) -> Optional[Dict[str, Any]]:
    """Calcule des statistiques agrégées pour une ville via l'ORM."""
    releves = session.exec(select(Releve).where(Releve.ville_id == ville_id)).all()
    if not releves:
        return None

    temperatures = [r.temperature for r in releves]
    vents = [r.vitesse_vent for r in releves]
    total = len(releves)

    return {
        "total_releves": total,
        "temperature_moyenne": round(sum(temperatures) / total, 2),
        "temperature_min": min(temperatures),
        "temperature_max": max(temperatures),
        "vent_moyen": round(sum(vents) / total, 2),
        "vent_max": max(vents),
    }


def get_statistiques_globales(session: Session) -> Dict[str, Any]:
    """Retourne des statistiques globales sur l'ensemble de la base via l'ORM."""
    villes = session.exec(select(Ville)).all()
    releves = session.exec(select(Releve)).all()

    total_villes = len(villes)
    total_releves = len(releves)

    stats: Dict[str, Any] = {
        "total_villes": total_villes,
        "total_releves": total_releves,
        "temperature_moyenne": None,
        "temperature_min": None,
        "temperature_max": None,
        "vent_moyen": None,
        "vent_max": None,
        "releve_plus_chaud": None,
        "releve_plus_froid": None,
        "releve_plus_venteux": None,
    }

    if total_releves > 0:
        temperatures = [r.temperature for r in releves]
        vents = [r.vitesse_vent for r in releves]

        stats["temperature_moyenne"] = round(sum(temperatures) / total_releves, 2)
        stats["temperature_min"] = min(temperatures)
        stats["temperature_max"] = max(temperatures)
        stats["vent_moyen"] = round(sum(vents) / total_releves, 2)
        stats["vent_max"] = max(vents)

        villes_par_id = {v.id: v.nom for v in villes}

        plus_chaud = max(releves, key=lambda r: r.temperature)
        stats["releve_plus_chaud"] = {
            "ville": villes_par_id.get(plus_chaud.ville_id, ""),
            "temperature": plus_chaud.temperature,
            "date_heure": plus_chaud.date_heure,
        }

        plus_froid = min(releves, key=lambda r: r.temperature)
        stats["releve_plus_froid"] = {
            "ville": villes_par_id.get(plus_froid.ville_id, ""),
            "temperature": plus_froid.temperature,
            "date_heure": plus_froid.date_heure,
        }

        plus_venteux = max(releves, key=lambda r: r.vitesse_vent)
        stats["releve_plus_venteux"] = {
            "ville": villes_par_id.get(plus_venteux.ville_id, ""),
            "vitesse_vent": plus_venteux.vitesse_vent,
            "date_heure": plus_venteux.date_heure,
        }

    return stats
