"""Tests unitaires pour le pipeline d'ingestion (pipeline.py)."""

from unittest.mock import MagicMock

import pytest

from observatoire.database import (
    get_dernier_releve,
    get_villes,
    init_db,
    insert_ville,
)
from observatoire.pipeline import (
    VILLES_PAR_DEFAUT,
    collecter_et_stocker_pour_ville,
    executer_pipeline,
    initialiser_villes_par_defaut,
)
from observatoire.schemas.weather import CurrentWeather, WeatherResponseModel


@pytest.fixture
def memory_db():
    """Base de données en mémoire pour les tests de pipeline."""
    conn = init_db(":memory:")
    yield conn
    conn.close()


@pytest.fixture
def mock_weather_response():
    """Modèle WeatherResponseModel simulé."""
    return WeatherResponseModel(
        latitude=48.8566,
        longitude=2.3522,
        generationtime_ms=0.05,
        timezone="Europe/Paris",
        elevation=40.0,
        current_weather=CurrentWeather(
            time="2026-11-04T12:00",
            temperature=14.0,
            windspeed=18.0,
            winddirection=180,
            weathercode=2,
            is_day=1,
        ),
    )


def test_initialiser_villes_par_defaut(memory_db):
    """Vérifie que les villes par défaut sont correctement insérées."""
    initialiser_villes_par_defaut(memory_db)
    villes = get_villes(memory_db)
    assert len(villes) == len(VILLES_PAR_DEFAUT)

    noms = {v["nom"] for v in villes}
    assert "Paris" in noms
    assert "Marseille" in noms
    assert "Lyon" in noms


def test_collecter_et_stocker_pour_ville(memory_db, mock_weather_response):
    """Vérifie le cycle complet API -> Validation -> Insertion SQLite pour une ville."""
    ville_id = insert_ville(memory_db, "Paris", 48.8566, 2.3522)
    ville = {"id": ville_id, "nom": "Paris", "latitude": 48.8566, "longitude": 2.3522}

    mock_client = MagicMock()
    mock_client.get_weather.return_value = mock_weather_response

    resultat = collecter_et_stocker_pour_ville(memory_db, ville, mock_client)

    assert resultat["ville"] == "Paris"
    assert resultat["temperature"] == 14.0
    assert resultat["vitesse_vent"] == 18.0

    # Vérification dans la base SQLite
    releve = get_dernier_releve(memory_db, ville_id)
    assert releve is not None
    assert releve["temperature"] == 14.0
    assert releve["vitesse_vent"] == 18.0
    assert releve["date_heure"] == "2026-11-04T12:00"


def test_executer_pipeline_success(tmp_path, mock_weather_response):
    """Vérifie l'exécution du pipeline sur un ensemble de villes avec mock."""
    db_file = str(tmp_path / "test_meteo.db")

    mock_client = MagicMock()
    mock_client.get_weather.return_value = mock_weather_response

    resultats = executer_pipeline(db_path=db_file, client=mock_client)

    assert len(resultats) == len(VILLES_PAR_DEFAUT)
    assert mock_client.get_weather.call_count == len(VILLES_PAR_DEFAUT)


def test_executer_pipeline_handles_individual_errors(tmp_path, mock_weather_response):
    """Vérifie que l'échec de collecte sur une ville ne stoppe pas le reste du pipeline."""
    db_file = str(tmp_path / "test_meteo.db")

    mock_client = MagicMock()
    # Fait échouer la première ville puis réussit pour les autres
    mock_client.get_weather.side_effect = [
        Exception("Timeout"),
        *[mock_weather_response] * (len(VILLES_PAR_DEFAUT) - 1),
    ]

    resultats = executer_pipeline(db_path=db_file, client=mock_client)
    assert len(resultats) == len(VILLES_PAR_DEFAUT) - 1

