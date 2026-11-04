"""Pipeline d'ingestion et de persistance météo : API -> Pydantic -> SQLite."""

import logging
from typing import Any, Dict, List, Optional

from client import OpenMeteoClient
from database import (
    DEFAULT_DB_PATH,
    get_connection,
    get_statistiques_globales,
    get_statistiques_ville,
    get_villes,
    init_db,
    insert_releve,
    insert_ville,
)

logger = logging.getLogger(__name__)

# Liste de villes françaises de référence
VILLES_PAR_DEFAUT = [
    {"nom": "Paris", "latitude": 48.8566, "longitude": 2.3522},
    {"nom": "Marseille", "latitude": 43.2965, "longitude": 5.3698},
    {"nom": "Lyon", "latitude": 45.7640, "longitude": 4.8357},
    {"nom": "Toulouse", "latitude": 43.6047, "longitude": 1.4442},
    {"nom": "Nice", "latitude": 43.7102, "longitude": 7.2620},
    {"nom": "Nantes", "latitude": 47.2184, "longitude": -1.5536},
    {"nom": "Strasbourg", "latitude": 48.5734, "longitude": 7.7521},
    {"nom": "Bordeaux", "latitude": 44.8378, "longitude": -0.5792},
    {"nom": "Lille", "latitude": 50.6292, "longitude": 3.0573},
    {"nom": "Brest", "latitude": 48.3904, "longitude": -4.4861},
]


def initialiser_villes_par_defaut(conn) -> None:
    """Enregistre les villes de référence dans la base si elles ne sont pas déjà présentes."""
    for ville in VILLES_PAR_DEFAUT:
        insert_ville(conn, nom=ville["nom"], latitude=ville["latitude"], longitude=ville["longitude"])


def collecter_et_stocker_pour_ville(
    conn,
    ville: Dict[str, Any],
    client: OpenMeteoClient,
) -> Dict[str, Any]:
    """Interroge l'API Open-Meteo pour une ville, valide la donnée avec Pydantic et l'insère dans SQLite.

    Étapes :
    1. Interroge l'API via requests.
    2. Valide la réponse avec Pydantic (CurrentWeather / WeatherResponseModel).
    3. Insère proprement ces données validées dans SQLite (INSERT).
    """
    nom = ville["nom"]
    lat = ville["latitude"]
    lon = ville["longitude"]
    ville_id = ville["id"]

    # 1. Requête réseau & 2. Validation Pydantic automatique par le client
    weather_data = client.get_weather(latitude=lat, longitude=lon, current_weather=True)
    current = weather_data.current_weather

    # 3. Insertion propre dans SQLite
    releve_id = insert_releve(
        conn=conn,
        ville_id=ville_id,
        temperature=current.temperature,
        vitesse_vent=current.windspeed,
        date_heure=current.time,
    )

    return {
        "releve_id": releve_id,
        "ville": nom,
        "temperature": current.temperature,
        "vitesse_vent": current.windspeed,
        "date_heure": current.time,
    }


def executer_pipeline(
    db_path: str = DEFAULT_DB_PATH,
    client: Optional[OpenMeteoClient] = None,
) -> List[Dict[str, Any]]:
    """Exécute le pipeline complet pour l'ensemble des villes de la base de données."""
    conn = init_db(db_path)
    initialiser_villes_par_defaut(conn)
    villes = get_villes(conn)

    releves_inseres = []
    own_client = client is None

    if own_client:
        client = OpenMeteoClient(timeout=10)

    try:
        for ville in villes:
            try:
                result = collecter_et_stocker_pour_ville(conn, ville, client)
                releves_inseres.append(result)
            except Exception as e:
                logger.error("Erreur lors de la collecte pour %s : %s", ville["nom"], e)
    finally:
        if own_client:
            client.close()

    return releves_inseres


if __name__ == "__main__":
    import json

    print("🚀 Démarrage du pipeline de collecte et stockage SQLite...")
    conn = init_db(DEFAULT_DB_PATH)
    initialiser_villes_par_defaut(conn)

    with OpenMeteoClient(timeout=10) as client:
        resultats = executer_pipeline(DEFAULT_DB_PATH, client=client)

    print(f"\n✅ {len(resultats)} relevés validés et enregistrés dans '{DEFAULT_DB_PATH}'.")
    print("-" * 70)
    for r in resultats:
        print(f"📍 {r['ville']:<12} | {r['temperature']:>5.1f} °C | Vent : {r['vitesse_vent']:>4.1f} km/h | Date : {r['date_heure']}")

    print("\n📊 Statistiques globales de la base de données :")
    print("-" * 70)
    stats = get_statistiques_globales(conn)
    print(f"Total relevés stockés   : {stats['total_releves']}")
    print(f"Température moyenne     : {stats['temperature_moyenne']} °C")
    print(f"Température min / max   : {stats['temperature_min']} °C / {stats['temperature_max']} °C")
    print(f"Vent moyen / max        : {stats['vent_moyen']} km/h / {stats['vent_max']} km/h")
    if stats["releve_plus_chaud"]:
        print(f"🔥 Plus chaud           : {stats['releve_plus_chaud']['ville']} ({stats['releve_plus_chaud']['temperature']} °C)")
    if stats["releve_plus_froid"]:
        print(f"❄️  Plus froid           : {stats['releve_plus_froid']['ville']} ({stats['releve_plus_froid']['temperature']} °C)")
    if stats["releve_plus_venteux"]:
        print(f"💨 Plus venteux         : {stats['releve_plus_venteux']['ville']} ({stats['releve_plus_venteux']['vitesse_vent']} km/h)")

