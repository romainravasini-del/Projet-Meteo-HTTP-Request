"""Script principal pour tester la récupération et la validation météo."""

import os

from dotenv import load_dotenv
from pydantic import ValidationError
from requests.exceptions import RequestException

from client import OpenMeteoClient

# Chargement des variables d'environnement depuis le fichier .env si présent
load_dotenv()


def main():
    # Coordonnées configurables via variables d'environnement (par défaut : Paris)
    lat = float(os.getenv("DEFAULT_LATITUDE", 48.8566))
    lon = float(os.getenv("DEFAULT_LONGITUDE", 2.3522))
    timeout = int(os.getenv("OPEN_METEO_TIMEOUT", 10))
    timezone = os.getenv("DEFAULT_TIMEZONE", "auto")

    print(f"📡 Récupération des données météo (Lat: {lat}°, Lon: {lon}°)...")

    with OpenMeteoClient(timeout=timeout) as client:
        try:
            weather_data = client.get_weather(
                latitude=lat,
                longitude=lon,
                current_weather=True,
                timezone=timezone,
            )

            print("\n Données récupérées et validées avec succès avec Pydantic !")
            print("-" * 70)
            print(f" Lieu : Latitude {weather_data.latitude}° | Longitude {weather_data.longitude}°")
            print(f" Fuseau horaire : {weather_data.timezone}")
            print(f" Altitude : {weather_data.elevation} m")
            print(f" Temps de réponse serveur : {weather_data.generationtime_ms} ms")
            print("-" * 70)
            print(f" Température actuelle   : {weather_data.current_weather.temperature} °C")
            print(f" Vitesse du vent        : {weather_data.current_weather.windspeed} km/h")
            print(f" Direction du vent      : {weather_data.current_weather.winddirection}°")
            print(f" Indicateur Jour        : {'Jour' if weather_data.current_weather.is_day == 1 else 'Nuit'}")
            print(f" Code météo WMO         : {weather_data.current_weather.weathercode}")
            print("-" * 70)

        except RequestException as e:
            print(f"❌ Erreur réseau lors de la requête : {e}")
        except ValidationError as e:
            print(f"❌ Erreur de validation Pydantic : {e}")


if __name__ == "__main__":
    main()
