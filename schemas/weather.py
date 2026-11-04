# Schémas Pydantic pour les données météo Open-Meteo
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class CurrentWeather(BaseModel):
    time: str = Field(..., examples=["2026-11-02T14:00"], description="Horodatage du relevé météo")
    temperature: float = Field(..., ge=-100.0, le=100.0, examples=[13.5], description="Température instantanée (°C)")
    windspeed: float = Field(..., ge=0.0, examples=[12.4], description="Vitesse du vent (km/h)")
    winddirection: int = Field(..., ge=0, le=360, examples=[210], description="Direction du vent en degrés (0° à 360°)")
    weathercode: int = Field(..., ge=0, examples=[3], description="Code condition météo WMO (ex: 0=Ciel dégagé, 3=Couvert)")
    is_day: int = Field(..., ge=0, le=1, examples=[1], description="Indicateur diurne/nocturne (1 = jour, 0 = nuit)")


class WeatherResponseModel(BaseModel):
    latitude: float = Field(..., ge=-90.0, le=90.0, examples=[48.8566], description="Latitude géographique du lieu")
    longitude: float = Field(..., ge=-180.0, le=180.0, examples=[2.3522], description="Longitude géographique du lieu")
    generationtime_ms: float = Field(..., ge=0.0, examples=[0.045], description="Temps de génération côté serveur (ms)")
    timezone: str = Field(..., examples=["Europe/Paris"], description="Fuseau horaire appliqué")
    elevation: float = Field(..., examples=[42.0], description="Altitude du lieu en mètres")
    current_weather: CurrentWeather = Field(..., description="Données météo instantanées")
    hourly: Optional[Dict[str, Any]] = Field(default=None, description="Données météo horaires")
    daily: Optional[Dict[str, Any]] = Field(default=None, description="Données météo journalières")
