"""Tests unitaires pour le client HTTP OpenMeteoClient."""

from unittest.mock import MagicMock, patch

import pytest
import requests
from pydantic import ValidationError
from requests.exceptions import ConnectionError, HTTPError, RequestException, Timeout

from core.client import OpenMeteoClient
from core.schemas.weather import WeatherResponseModel


@pytest.fixture
def valid_weather_payload():
    """Données de test simulant une réponse JSON valide d'Open-Meteo."""
    return {
        "latitude": 48.8566,
        "longitude": 2.3522,
        "generationtime_ms": 0.045,
        "timezone": "Europe/Paris",
        "elevation": 42.0,
        "current_weather": {
            "time": "2026-11-04T10:00",
            "temperature": 12.5,
            "windspeed": 10.2,
            "winddirection": 200,
            "weathercode": 2,
            "is_day": 1,
        },
    }


def test_client_init_valid():
    """Vérifie l'initialisation du client avec un timeout valide."""
    client = OpenMeteoClient(timeout=5)
    assert client.timeout == 5
    assert isinstance(client.session, requests.Session)
    client.close()


@pytest.mark.parametrize("invalid_timeout", [0, -1, -10])
def test_client_init_invalid_timeout(invalid_timeout):
    """Vérifie qu'un timeout <= 0 lève une ValueError."""
    with pytest.raises(ValueError, match="Le timeout doit être strictement positif"):
        OpenMeteoClient(timeout=invalid_timeout)


@pytest.mark.parametrize("lat,lon", [
    (95.0, 2.0),
    (-95.0, 2.0),
    (48.0, 185.0),
    (48.0, -185.0),
])
def test_get_weather_invalid_coordinates(lat, lon):
    """Vérifie que des coordonnées hors bornes lèvent une ValueError avant tout appel réseau."""
    client = OpenMeteoClient()
    with pytest.raises(ValueError):
        client.get_weather(latitude=lat, longitude=lon)
    client.close()


def test_get_weather_success(valid_weather_payload):
    """Vérifie qu'un appel avec réponse 200 retourne un WeatherResponseModel validé."""
    client = OpenMeteoClient(timeout=10)

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = valid_weather_payload
    mock_response.raise_for_status.return_value = None

    with patch.object(client.session, "get", return_value=mock_response) as mock_get:
        result = client.get_weather(
            latitude=48.8566,
            longitude=2.3522,
            current_weather=True,
            timezone="auto",
        )

        mock_get.assert_called_once_with(
            "https://api.open-meteo.com/v1/forecast",
            params={
                "latitude": 48.8566,
                "longitude": 2.3522,
                "current_weather": "true",
                "timezone": "auto",
            },
            timeout=10,
        )

        assert isinstance(result, WeatherResponseModel)
        assert result.latitude == 48.8566
        assert result.current_weather.temperature == 12.5

    client.close()


def test_get_weather_timeout():
    """Vérifie que l'exception Timeout est correctement propagée."""
    client = OpenMeteoClient(timeout=5)

    with patch.object(client.session, "get", side_effect=Timeout("Délai expiré")):
        with pytest.raises(Timeout):
            client.get_weather(latitude=48.8566, longitude=2.3522)

    client.close()


def test_get_weather_connection_error():
    """Vérifie que l'exception ConnectionError est correctement propagée."""
    client = OpenMeteoClient()

    with patch.object(client.session, "get", side_effect=ConnectionError("Réseau indisponible")):
        with pytest.raises(ConnectionError):
            client.get_weather(latitude=48.8566, longitude=2.3522)

    client.close()


def test_get_weather_http_error():
    """Vérifie que les erreurs HTTP (4xx / 5xx) sont correctement propagées."""
    client = OpenMeteoClient()

    mock_response = MagicMock()
    mock_response.raise_for_status.side_effect = HTTPError("404 Not Found")

    with patch.object(client.session, "get", return_value=mock_response):
        with pytest.raises(HTTPError):
            client.get_weather(latitude=48.8566, longitude=2.3522)

    client.close()


def test_get_weather_unexpected_request_exception():
    """Vérifie que les autres erreurs réseau génériques sont propagées."""
    client = OpenMeteoClient()

    with patch.object(client.session, "get", side_effect=RequestException("Erreur inattendue")):
        with pytest.raises(RequestException):
            client.get_weather(latitude=48.8566, longitude=2.3522)

    client.close()


def test_get_weather_validation_error():
    """Vérifie qu'un payload malformé renvoyé par l'API lève une ValidationError."""
    client = OpenMeteoClient()

    mock_response = MagicMock()
    mock_response.raise_for_status.return_value = None
    mock_response.json.return_value = {"invalid": "payload"}

    with patch.object(client.session, "get", return_value=mock_response):
        with pytest.raises(ValidationError):
            client.get_weather(latitude=48.8566, longitude=2.3522)

    client.close()


def test_client_context_manager():
    """Vérifie que le context manager ferme automatiquement la session à la sortie."""
    client = OpenMeteoClient()
    mock_close = MagicMock()
    client.session.close = mock_close

    with client:
        pass

    mock_close.assert_called_once()
