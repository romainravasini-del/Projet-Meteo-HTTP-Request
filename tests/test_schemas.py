"""Tests unitaires pour les schémas Pydantic (CurrentWeather et WeatherResponseModel)."""

import pytest
from pydantic import ValidationError

from schemas.weather import CurrentWeather, WeatherResponseModel


def test_current_weather_valid():
    """Vérifie la création valide de CurrentWeather."""
    data = {
        "time": "2026-11-04T12:00",
        "temperature": 15.5,
        "windspeed": 18.2,
        "winddirection": 180,
        "weathercode": 2,
        "is_day": 1,
    }
    model = CurrentWeather(**data)
    assert model.time == "2026-11-04T12:00"
    assert model.temperature == 15.5
    assert model.windspeed == 18.2
    assert model.winddirection == 180
    assert model.weathercode == 2
    assert model.is_day == 1


@pytest.mark.parametrize("temperature", [-101.0, 101.0])
def test_current_weather_temperature_out_of_bounds(temperature):
    """Vérifie que les températures hors limites (-100 à 100) lèvent une ValidationError."""
    with pytest.raises(ValidationError):
        CurrentWeather(
            time="2026-11-04T12:00",
            temperature=temperature,
            windspeed=10.0,
            winddirection=90,
            weathercode=1,
            is_day=1,
        )


def test_current_weather_negative_windspeed():
    """Vérifie qu'une vitesse de vent négative lève une ValidationError."""
    with pytest.raises(ValidationError):
        CurrentWeather(
            time="2026-11-04T12:00",
            temperature=10.0,
            windspeed=-1.0,
            winddirection=90,
            weathercode=1,
            is_day=1,
        )


@pytest.mark.parametrize("direction", [-1, 361])
def test_current_weather_winddirection_out_of_bounds(direction):
    """Vérifie que la direction du vent doit être comprise entre 0 et 360."""
    with pytest.raises(ValidationError):
        CurrentWeather(
            time="2026-11-04T12:00",
            temperature=10.0,
            windspeed=10.0,
            winddirection=direction,
            weathercode=1,
            is_day=1,
        )


@pytest.mark.parametrize("is_day", [-1, 2])
def test_current_weather_is_day_invalid(is_day):
    """Vérifie que is_day doit être 0 ou 1."""
    with pytest.raises(ValidationError):
        CurrentWeather(
            time="2026-11-04T12:00",
            temperature=10.0,
            windspeed=10.0,
            winddirection=90,
            weathercode=1,
            is_day=is_day,
        )


def test_current_weather_missing_fields():
    """Vérifie qu'un champ manquant lève une ValidationError."""
    with pytest.raises(ValidationError):
        CurrentWeather(
            time="2026-11-04T12:00",
            temperature=10.0,
            # windspeed manquant
            winddirection=90,
            weathercode=1,
            is_day=1,
        )


def test_weather_response_model_valid_minimal():
    """Vérifie la validation d'une réponse météo complète sans champs optionnels."""
    payload = {
        "latitude": 48.8566,
        "longitude": 2.3522,
        "generationtime_ms": 0.05,
        "timezone": "Europe/Paris",
        "elevation": 35.0,
        "current_weather": {
            "time": "2026-11-04T12:00",
            "temperature": 14.2,
            "windspeed": 15.0,
            "winddirection": 220,
            "weathercode": 3,
            "is_day": 1,
        },
    }
    model = WeatherResponseModel.model_validate(payload)
    assert model.latitude == 48.8566
    assert model.longitude == 2.3522
    assert model.generationtime_ms == 0.05
    assert model.timezone == "Europe/Paris"
    assert model.elevation == 35.0
    assert model.current_weather.temperature == 14.2
    assert model.hourly is None
    assert model.daily is None


def test_weather_response_model_with_hourly_daily():
    """Vérifie la validation avec des champs hourly et daily fournis."""
    payload = {
        "latitude": 48.8566,
        "longitude": 2.3522,
        "generationtime_ms": 0.05,
        "timezone": "Europe/Paris",
        "elevation": 35.0,
        "current_weather": {
            "time": "2026-11-04T12:00",
            "temperature": 14.2,
            "windspeed": 15.0,
            "winddirection": 220,
            "weathercode": 3,
            "is_day": 1,
        },
        "hourly": {"time": ["2026-11-04T12:00"], "temperature_2m": [14.2]},
        "daily": {"time": ["2026-11-04"], "temperature_2m_max": [16.0]},
    }
    model = WeatherResponseModel.model_validate(payload)
    assert model.hourly is not None
    assert model.daily is not None
    assert model.hourly["temperature_2m"] == [14.2]


@pytest.mark.parametrize("lat", [-90.1, 90.1])
def test_weather_response_model_invalid_latitude(lat):
    """Vérifie qu'une latitude hors bornes [-90, 90] lève une ValidationError."""
    payload = {
        "latitude": lat,
        "longitude": 2.3522,
        "generationtime_ms": 0.05,
        "timezone": "Europe/Paris",
        "elevation": 35.0,
        "current_weather": {
            "time": "2026-11-04T12:00",
            "temperature": 14.2,
            "windspeed": 15.0,
            "winddirection": 220,
            "weathercode": 3,
            "is_day": 1,
        },
    }
    with pytest.raises(ValidationError):
        WeatherResponseModel.model_validate(payload)


@pytest.mark.parametrize("lon", [-180.1, 180.1])
def test_weather_response_model_invalid_longitude(lon):
    """Vérifie qu'une longitude hors bornes [-180, 180] lève une ValidationError."""
    payload = {
        "latitude": 48.8566,
        "longitude": lon,
        "generationtime_ms": 0.05,
        "timezone": "Europe/Paris",
        "elevation": 35.0,
        "current_weather": {
            "time": "2026-11-04T12:00",
            "temperature": 14.2,
            "windspeed": 15.0,
            "winddirection": 220,
            "weathercode": 3,
            "is_day": 1,
        },
    }
    with pytest.raises(ValidationError):
        WeatherResponseModel.model_validate(payload)

