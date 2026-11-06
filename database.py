"""Module de gestion de la base de données avec l'ORM SQLModel."""

from typing import Any, Dict, List, Optional

from sqlalchemy import event, func
from sqlalchemy.engine import Engine
from sqlalchemy.exc import IntegrityError
from sqlmodel import Field, Relationship, Session, SQLModel, create_engine, select

DEFAULT_DB_PATH = "meteo.db"


@event.listens_for(Engine, "connect")
def _set_sqlite_pragma(dbapi_connection, connection_record):
    """Active systématiquement les clés étrangères sur chaque connexion SQLite."""
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys = ON;")
    cursor.close()


# =====================================================================
# Modèles ORM SQLModel (Tables Relationnelles)
# =====================================================================

class Ville(SQLModel, table=True):
    """Modèle ORM représentant la table 'villes'."""

    __tablename__ = "villes"

    id: Optional[int] = Field(default=None, primary_key=True)
    nom: str = Field(unique=True, index=True, description="Nom unique de la ville")
    latitude: float = Field(description="Latitude géographique")
    longitude: float = Field(description="Longitude géographique")

    releves: List["Releve"] = Relationship(back_populates="ville")


class Releve(SQLModel, table=True):
    """Modèle ORM représentant la table 'releves'."""

    __tablename__ = "releves"

    id: Optional[int] = Field(default=None, primary_key=True)
    ville_id: int = Field(foreign_key="villes.id", index=True, description="Identifiant de la ville associée")
    temperature: float = Field(description="Température relevée (°C)")
    vitesse_vent: float = Field(description="Vitesse du vent relevée (km/h)")
    date_heure: str = Field(index=True, description="Horodatage ISO 8601 du relevé")

    ville: Optional[Ville] = Relationship(back_populates="releves")


# =====================================================================
# Moteur (Engine) & Sessions ORM
# =====================================================================

def get_engine(db_path: str = DEFAULT_DB_PATH) -> Engine:
    """Crée un moteur SQLAlchemy/SQLModel pour le chemin SQLite indiqué."""
    url = "sqlite:///:memory:" if db_path == ":memory:" else f"sqlite:///{db_path}"
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

    if ville_existante:
        ville_existante.latitude = float(latitude)
        ville_existante.longitude = float(longitude)
        session.add(ville_existante)
        session.commit()
        session.refresh(ville_existante)
        return int(ville_existante.id)

    nouvelle_ville = Ville(
        nom=nom_clean,
        latitude=float(latitude),
        longitude=float(longitude),
    )
    session.add(nouvelle_ville)
    session.commit()
    session.refresh(nouvelle_ville)
    return int(nouvelle_ville.id)


def get_villes(session: Session) -> List[Dict[str, Any]]:
    """Retourne la liste de toutes les villes enregistrées triées par nom."""
    statement = select(Ville).order_by(Ville.nom.asc())
    villes = session.exec(statement).all()
    return [v.model_dump() for v in villes]


def get_ville_by_id(session: Session, ville_id: int) -> Optional[Dict[str, Any]]:
    """Récupère une ville par sa clé primaire via session.get()."""
    ville = session.get(Ville, ville_id)
    return ville.model_dump() if ville else None


def get_ville_by_nom(session: Session, nom: str) -> Optional[Dict[str, Any]]:
    """Récupère une ville par son nom (insensible à la casse)."""
    statement = select(Ville).where(func.lower(Ville.nom) == nom.strip().lower())
    ville = session.exec(statement).first()
    return ville.model_dump() if ville else None


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
        return int(nouveau_releve.id)
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
        .order_by(Releve.date_heure.desc(), Releve.id.desc())
        .limit(limit)
    )
    releves = session.exec(statement).all()
    return [r.model_dump() for r in releves]


def get_dernier_releve(session: Session, ville_id: int) -> Optional[Dict[str, Any]]:
    """Récupère le relevé le plus récent pour une ville."""
    releves = get_releves_by_ville(session, ville_id, limit=1)
    return releves[0] if releves else None


def get_statistiques_ville(session: Session, ville_id: int) -> Optional[Dict[str, Any]]:
    """Calcule des statistiques agrégées pour une ville avec les fonctions d'agrégation ORM."""
    statement = select(
        func.count(Releve.id),
        func.round(func.avg(Releve.temperature), 2),
        func.min(Releve.temperature),
        func.max(Releve.temperature),
        func.round(func.avg(Releve.vitesse_vent), 2),
        func.max(Releve.vitesse_vent),
    ).where(Releve.ville_id == ville_id)

    row = session.exec(statement).first()
    if not row or row[0] == 0:
        return None

    return {
        "total_releves": row[0],
        "temperature_moyenne": float(row[1]) if row[1] is not None else None,
        "temperature_min": float(row[2]) if row[2] is not None else None,
        "temperature_max": float(row[3]) if row[3] is not None else None,
        "vent_moyen": float(row[4]) if row[4] is not None else None,
        "vent_max": float(row[5]) if row[5] is not None else None,
    }


def get_statistiques_globales(session: Session) -> Dict[str, Any]:
    """Retourne des statistiques globales sur l'ensemble de la base via l'ORM."""
    total_villes = session.exec(select(func.count(Ville.id))).one()

    agg_stmt = select(
        func.count(Releve.id),
        func.round(func.avg(Releve.temperature), 2),
        func.min(Releve.temperature),
        func.max(Releve.temperature),
        func.round(func.avg(Releve.vitesse_vent), 2),
        func.max(Releve.vitesse_vent),
    )
    row = session.exec(agg_stmt).one()
    total_releves = row[0]

    stats: Dict[str, Any] = {
        "total_villes": total_villes,
        "total_releves": total_releves,
        "temperature_moyenne": float(row[1]) if row[1] is not None else None,
        "temperature_min": float(row[2]) if row[2] is not None else None,
        "temperature_max": float(row[3]) if row[3] is not None else None,
        "vent_moyen": float(row[4]) if row[4] is not None else None,
        "vent_max": float(row[5]) if row[5] is not None else None,
        "releve_plus_chaud": None,
        "releve_plus_froid": None,
        "releve_plus_venteux": None,
    }

    if total_releves > 0:
        # Relevé le plus chaud (jointure ORM Releve <-> Ville)
        chaud_stmt = (
            select(Ville.nom, Releve.temperature, Releve.date_heure)
            .join(Ville, Releve.ville_id == Ville.id)
            .order_by(Releve.temperature.desc())
            .limit(1)
        )
        chaud = session.exec(chaud_stmt).first()
        if chaud:
            stats["releve_plus_chaud"] = {
                "ville": chaud[0],
                "temperature": chaud[1],
                "date_heure": chaud[2],
            }

        # Relevé le plus froid
        froid_stmt = (
            select(Ville.nom, Releve.temperature, Releve.date_heure)
            .join(Ville, Releve.ville_id == Ville.id)
            .order_by(Releve.temperature.asc())
            .limit(1)
        )
        froid = session.exec(froid_stmt).first()
        if froid:
            stats["releve_plus_froid"] = {
                "ville": froid[0],
                "temperature": froid[1],
                "date_heure": froid[2],
            }

        # Relevé le plus venteux
        vent_stmt = (
            select(Ville.nom, Releve.vitesse_vent, Releve.date_heure)
            .join(Ville, Releve.ville_id == Ville.id)
            .order_by(Releve.vitesse_vent.desc())
            .limit(1)
        )
        vent = session.exec(vent_stmt).first()
        if vent:
            stats["releve_plus_venteux"] = {
                "ville": vent[0],
                "vitesse_vent": vent[1],
                "date_heure": vent[2],
            }

    return stats
