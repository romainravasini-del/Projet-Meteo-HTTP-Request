import os
from dotenv import load_dotenv

# Chargement de la configuration
load_dotenv()

LATITUDE = float(os.getenv("DEFAULT_LATITUDE", 48.8566))
LONGITUDE = float(os.getenv("DEFAULT_LONGITUDE", 2.3522))
TIMEOUT = int(os.getenv("OPEN_METEO_TIMEOUT", 10))
TIMEZONE = os.getenv("DEFAULT_TIMEZONE", "auto")
DB_PATH = os.getenv("SQLITE_DB_PATH", "data/meteo.db")