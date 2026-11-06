"""Client HTTP pour interroger l'API Open-Meteo avec validation Pydantic."""

import logging

import requests
from pydantic import ValidationError
from requests.exceptions import ConnectionError, HTTPError, RequestException, Timeout

from observatoire.schemas.weather import WeatherResponseModel

logger = logging.getLogger(__name__)


class OpenMeteoClient:
    """Client HTTP pour interagir de façon robuste avec l'API Open-Meteo."""

    BASE_URL = "https://api.open-meteo.com/v1/forecast"

    def __init__(self, timeout: int = 10):
        if timeout <= 0:
            raise ValueError("Le timeout doit être strictement positif.")
        self.timeout = timeout
        self.session = requests.Session()

    def get_weather(
        self,
        latitude: float,
        longitude: float,
        current_weather: bool = True,
        timezone: str = "auto",
    ) -> WeatherResponseModel:
        """Récupère les prévisions météo pour des coordonnées données et valide la réponse.

        Args:
            latitude: Latitude du lieu.
            longitude: Longitude du lieu.
            current_weather: Si True, inclut le relevé météo instantané.
            timezone: Fuseau horaire (ex: "auto" ou "Europe/Paris").

        Returns:
            Une instance validée de WeatherResponseModel.

        Raises:
            RequestException: En cas d'erreur de communication réseau ou HTTP.
            ValidationError: Si le format reçu ne correspond pas au schéma Pydantic attendu.
        """
        latitude = float(latitude)
        longitude = float(longitude)

        if not -90.0 <= latitude <= 90.0:
            raise ValueError("La latitude doit être comprise entre -90 et 90 degrés.")
        if not -180.0 <= longitude <= 180.0:
            raise ValueError("La longitude doit être comprise entre -180 et 180 degrés.")

        params = {
            "latitude": latitude,
            "longitude": longitude,
            "current_weather": str(bool(current_weather)).lower(),
            "timezone": timezone,
        }

        try:
            response = self.session.get(
                self.BASE_URL,
                params=params,
                timeout=self.timeout,
            )
            response.raise_for_status()

            raw_data = response.json()
            validated_weather = WeatherResponseModel.model_validate(raw_data)
            return validated_weather

        except Timeout as err:
            logger.error("Le délai d'attente (timeout) a expiré lors de l'appel à Open-Meteo.")
            raise err
        except ConnectionError as err:
            logger.error("Erreur de connexion réseau impossible à établir avec Open-Meteo.")
            raise err
        except HTTPError as err:
            logger.error("Erreur HTTP reçue du serveur Open-Meteo : %s", err)
            raise err
        except RequestException as err:
            logger.error("Erreur inattendue lors de la requête : %s", err)
            raise err
        except ValidationError as err:
            logger.error("Les données retournées par l'API ne respectent pas le schéma attendu : %s", err)
            raise err

    def close(self):
        """Ferme la session HTTP sous-jacente."""
        self.session.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
