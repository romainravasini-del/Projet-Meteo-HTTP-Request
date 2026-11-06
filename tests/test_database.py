"""Tests unitaires pour le module de base de données ORM SQLModel (database.py)."""

import pytest
from sqlalchemy import inspect
from sqlalchemy.exc import IntegrityError

from observatoire.database import (
    Releve,
    Ville,
    get_dernier_releve,
    get_releves_by_ville,
    get_statistiques_globales,
    get_statistiques_ville,
    get_ville_by_id,
    get_ville_by_nom,
    get_villes,
    init_db,
    insert_releve,
    insert_ville,
)


@pytest.fixture
def memory_db():
    """Fixture créant une Session SQLModel connectée à une base SQLite en mémoire."""
    session = init_db(":memory:")
    yield session
    session.close()


def test_init_db_creates_tables(memory_db):
    """Vérifie que les tables villes et releves sont créées par SQLModel."""
    inspector = inspect(memory_db.get_bind())
    tables = set(inspector.get_table_names())
    assert "villes" in tables
    assert "releves" in tables


def test_sqlmodel_relationships(memory_db):
    """Vérifie les relations ORM bidirectionnelles entre Ville et Releve."""
    ville = Ville(nom="Bordeaux", latitude=44.8378, longitude=-0.5792)
    memory_db.add(ville)
    memory_db.commit()
    memory_db.refresh(ville)

    releve = Releve(
        ville_id=ville.id,
        temperature=17.5,
        vitesse_vent=12.0,
        date_heure="2026-11-06T10:00",
    )
    memory_db.add(releve)
    memory_db.commit()
    memory_db.refresh(releve)
    memory_db.refresh(ville)

    assert len(ville.releves) == 1
    assert ville.releves[0].temperature == 17.5
    assert releve.ville.nom == "Bordeaux"


def test_insert_and_get_ville(memory_db):
    """Vérifie l'insertion et la récupération d'une ville."""
    ville_id = insert_ville(memory_db, "Paris", 48.8566, 2.3522)
    assert ville_id > 0

    ville = get_ville_by_id(memory_db, ville_id)
    assert ville is not None
    assert ville["nom"] == "Paris"
    assert ville["latitude"] == 48.8566
    assert ville["longitude"] == 2.3522

    ville_par_nom = get_ville_by_nom(memory_db, "paris")
    assert ville_par_nom is not None
    assert ville_par_nom["id"] == ville_id


def test_insert_ville_idempotence(memory_db):
    """Vérifie que réinsérer une ville existante met à jour ses coordonnées sans créer de doublon."""
    id1 = insert_ville(memory_db, "Lyon", 45.0, 4.0)
    id2 = insert_ville(memory_db, "Lyon", 45.7640, 4.8357)
    assert id1 == id2

    villes = get_villes(memory_db)
    assert len(villes) == 1
    assert villes[0]["latitude"] == 45.7640


def test_insert_releve_and_foreign_key(memory_db):
    """Vérifie l'insertion d'un relevé et le respect des clés étrangères."""
    ville_id = insert_ville(memory_db, "Marseille", 43.2965, 5.3698)

    releve_id = insert_releve(
        memory_db,
        ville_id=ville_id,
        temperature=18.5,
        vitesse_vent=22.0,
        date_heure="2026-11-04T12:00",
    )
    assert releve_id > 0

    # Tenter d'insérer un relevé avec un ville_id inexistant doit lever une IntegrityError
    with pytest.raises(IntegrityError):
        insert_releve(
            memory_db,
            ville_id=9999,
            temperature=10.0,
            vitesse_vent=5.0,
            date_heure="2026-11-04T12:00",
        )


def test_get_releves_and_dernier_releve(memory_db):
    """Vérifie la récupération chronologique des relevés et du dernier relevé."""
    ville_id = insert_ville(memory_db, "Toulouse", 43.6047, 1.4442)

    insert_releve(memory_db, ville_id, 12.0, 10.0, "2026-11-04T10:00")
    insert_releve(memory_db, ville_id, 16.0, 15.0, "2026-11-04T14:00")
    insert_releve(memory_db, ville_id, 14.0, 12.0, "2026-11-04T12:00")

    releves = get_releves_by_ville(memory_db, ville_id, limit=2)
    assert len(releves) == 2
    assert releves[0]["date_heure"] == "2026-11-04T14:00"

    dernier = get_dernier_releve(memory_db, ville_id)
    assert dernier is not None
    assert dernier["temperature"] == 16.0
    assert dernier["date_heure"] == "2026-11-04T14:00"


def test_get_statistiques_ville(memory_db):
    """Vérifie le calcul des statistiques pour une ville."""
    ville_id = insert_ville(memory_db, "Nice", 43.7102, 7.2620)

    # Sans relevé
    assert get_statistiques_ville(memory_db, ville_id) is None

    # Avec plusieurs relevés
    insert_releve(memory_db, ville_id, 10.0, 15.0, "2026-11-04T08:00")
    insert_releve(memory_db, ville_id, 20.0, 25.0, "2026-11-04T12:00")

    stats = get_statistiques_ville(memory_db, ville_id)
    assert stats is not None
    assert stats["total_releves"] == 2
    assert stats["temperature_moyenne"] == 15.0
    assert stats["temperature_min"] == 10.0
    assert stats["temperature_max"] == 20.0
    assert stats["vent_moyen"] == 20.0
    assert stats["vent_max"] == 25.0


def test_get_statistiques_globales(memory_db):
    """Vérifie le calcul des statistiques globales sur plusieurs villes."""
    v1 = insert_ville(memory_db, "Brest", 48.3904, -4.4861)
    v2 = insert_ville(memory_db, "Strasbourg", 48.5734, 7.7521)

    insert_releve(memory_db, v1, 8.0, 40.0, "2026-11-04T10:00")  # Plus froid et plus venteux
    insert_releve(memory_db, v2, 16.0, 10.0, "2026-11-04T10:00")  # Plus chaud

    stats = get_statistiques_globales(memory_db)
    assert stats["total_villes"] == 2
    assert stats["total_releves"] == 2
    assert stats["temperature_min"] == 8.0
    assert stats["temperature_max"] == 16.0
    assert stats["releve_plus_chaud"]["ville"] == "Strasbourg"
    assert stats["releve_plus_froid"]["ville"] == "Brest"
    assert stats["releve_plus_venteux"]["ville"] == "Brest"
