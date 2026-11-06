"""Script principal pour tester la récupération, la validation Pydantic et la persistance SQLite."""

from pydantic import ValidationError
from requests.exceptions import RequestException
from core.client import OpenMeteoClient
from core.database import (
    get_statistiques_ville,
    init_db,
    insert_releve,
    insert_ville,
)
from core.pipeline import initialiser_villes_par_defaut
from core.config import (LATITUDE, LONGITUDE, TIMEOUT, TIMEZONE, DB_PATH)   

def main():

    print("🗄️ Initialisation de la base SQLite...")
    conn = init_db(DB_PATH)
    initialiser_villes_par_defaut(conn)

    ville_nom = "Paris"
    ville_id = insert_ville(conn, ville_nom, LATITUDE, LONGITUDE)

    print(f"📡 Récupération des données météo pour {ville_nom} (Lat: {LATITUDE}°, Lon: {LONGITUDE}°)...")

    with OpenMeteoClient(timeout=TIMEOUT) as client:
        try:
            # 1. Récupération & 2. Validation Pydantic
            weather_data = client.get_weather(
                latitude=LATITUDE,
                longitude=LONGITUDE,
                current_weather=True,
                timezone=TIMEZONE,
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
