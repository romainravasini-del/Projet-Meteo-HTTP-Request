"""Script principal pour tester la récupération et la validation météo."""

from client import OpenMeteoClient
from requests.exceptions import RequestException
from pydantic import ValidationError


def main():
    # Coordonnées de Paris
    paris_lat = 48.8566
    paris_lon = 2.3522

    print("📡 Récupération des données météo pour Paris...")

    with OpenMeteoClient(timeout=10) as client:
        try:
            weather_data = client.get_weather(
                latitude=paris_lat,
                longitude=paris_lon,
                current_weather=True,
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
