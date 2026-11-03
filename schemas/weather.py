# Schémas Pydantic pour les données météo Open-Meteo
from pydantic import BaseModel, Field
from typing import Dict , Any

class CurrentWeather(BaseModel):
    time: str  = Field(..., example="2026-11-02T14:00", description="Horodatage du relevé météo")
    temperature: float = Field(..., example="13.5", description="Température instantanée (°C)")
    windspeed: float = Field(..., example="12.4", description="Vitesse du vent (km/h)")
    winddirection: int = Field(..., example="210", description="Direction du vent en degrés (0° à 360°)")
    weathercode: int = Field(..., example="3", description="Code condition météo WMO (ex: 0=Ciel dégagé, 3=Couvert)")
    is_day: int = Field(..., example="1", description="Indicateur diurne/nocturne (1 = jour, 0 = nuit)")

class WeatherResponseModel(BaseModel):
    latitude: float = Field(..., example="48.8566", description="Latitude géographique du lieu")
    longitude: float = Field(..., example="2.3522", description="Longitude géographique du lieu")
    generationtime_ms: float = Field(..., example="0.045", description="Temps de génération côté serveur (ms)")
    timezone: str = Field(..., example="Europe/Paris", description="Fuseau horaire appliqué")
    elevation: float = Field(..., example="42.0", description="Altitude du lieu en mètres")
    current_weather: CurrentWeather = Field(..., example="CurrentWeather(...)", description="Données météo instantanées")
    hourly: Dict[str, Any] = Field(..., example="Hourly(...)", description="Données météo horaires")
    daily: Dict[str, Any] = Field(..., example="Daily(...)", description="Données météo journalières")