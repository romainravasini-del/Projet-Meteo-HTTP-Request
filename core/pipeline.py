"""Pipeline d'ingestion et de persistance météo : API -> Pydantic -> SQLite."""
from services.ville_service import (
    VILLES_PAR_DEFAUT,
    initialiser_villes_par_defaut,
    collecter_et_stocker_pour_ville,
    executer_pipeline,
)