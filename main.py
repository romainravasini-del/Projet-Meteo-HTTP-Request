"""Script principal pour tester la récupération, la validation Pydantic et la persistance SQLite."""

import os
from dotenv import load_dotenv
from pydantic import ValidationError
from requests.exceptions import RequestException
from client import OpenMeteoClient
from database import (
    DEFAULT_DB_PATH,
    get_statistiques_ville,
    init_db,
    insert_releve,
    insert_ville,
)
from pipeline import initialiser_villes_par_defaut

# Chargement de la configuration
load_dotenv()


def main():
    lat = float(os.getenv("DEFAULT_LATITUDE", 48.8566))
    lon = float(os.getenv("DEFAULT_LONGITUDE", 2.3522))
    timeout = int(os.getenv("OPEN_METEO_TIMEOUT", 10))
    timezone = os.getenv("DEFAULT_TIMEZONE", "auto")
    db_path = os.getenv("SQLITE_DB_PATH", DEFAULT_DB_PATH)

    print("🗄️ Initialisation de la base SQLite...")
    conn = init_db(db_path)
    initialiser_villes_par_defaut(conn)

    ville_nom = "Paris"
    ville_id = insert_ville(conn, ville_nom, lat, lon)

    print(f"📡 Récupération des données météo pour {ville_nom} (Lat: {lat}°, Lon: {lon}°)...")

    with OpenMeteoClient(timeout=timeout) as client:
        try:
            # 1. Récupération & 2. Validation Pydantic
            weather_data = client.get_weather(
                latitude=lat,
                longitude=lon,
                current_weather=True,
                timezone=timezone,
            )

            current = weather_data.current_weather

            print("\n Données récupérées et validées avec succès avec Pydantic !")
            print("-" * 70)
            print(f" Ville                  : {ville_nom}")
            print(f" Coordonnées            : Latitude {weather_data.latitude}° | Longitude {weather_data.longitude}°")
            print(f" Fuseau horaire         : {weather_data.timezone}")
            print(f" Altitude               : {weather_data.elevation} m")
            print(f" Temps de réponse       : {weather_data.generationtime_ms:.3f} ms")
            print("-" * 70)
            print(f" Température actuelle   : {current.temperature} °C")
            print(f" Vitesse du vent        : {current.windspeed} km/h")
            print(f" Direction du vent      : {current.winddirection}°")
            print(f" Indicateur Jour        : {'Jour' if current.is_day == 1 else 'Nuit'}")
            print(f" Code météo WMO         : {current.weathercode}")
            print("-" * 70)

            # 3. Insertion SQLite via SQLModel
            releve_id = insert_releve(
                session=conn,
                ville_id=ville_id,
                temperature=current.temperature,
                vitesse_vent=current.windspeed,
                date_heure=current.time,
            )
            print(f"💾 Relevé enregistré dans SQLite (table 'releves', ID: {releve_id}).")

            # 4. Requête de lecture et statistiques
            stats = get_statistiques_ville(conn, ville_id)
            if stats:
                print("\n📊 Statistiques de la ville dans SQLite :")
                print(f" - Nombre total de relevés : {stats['total_releves']}")
                print(f" - Température moyenne     : {stats['temperature_moyenne']} °C")
                print(f" - Température min / max   : {stats['temperature_min']} °C / {stats['temperature_max']} °C")
                print(f" - Vent moyen / max        : {stats['vent_moyen']} km/h / {stats['vent_max']} km/h")
            print("-" * 70)

        except RequestException as e:
            print(f"❌ Erreur réseau lors de la requête : {e}")
        except ValidationError as e:
            print(f"❌ Erreur de validation Pydantic : {e}")


if __name__ == "__main__":
    main()
