from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from observatoire.database import (
    Releve,
    Session,
    engine,
    get_dernier_releve,
    get_releves_by_ville,
    get_statistiques_globales,
    get_ville_by_nom,
)


class MeteoEtStats(BaseModel):
    ville: str
    releve: Releve
    stats: dict


app = FastAPI(
    title="Observatoire Météo API",
    description="API REST de consultation météorologique propulsée par FastAPI et SQLModel",
    version="1.0.0",
)


@app.get("/")
def index():
    with Session(engine) as session:
        return get_statistiques_globales(session)


@app.get("/export")
def export():
    with Session(engine) as session:
        return get_statistiques_globales(session)


@app.get("/meteo/{ville}", response_model=MeteoEtStats)
def get_meteo(ville: str):
    with Session(engine) as session:
        ville_info = get_ville_by_nom(session, ville)
        if not ville_info:
            raise HTTPException(status_code=404, detail="Ville non trouvée")
        stats = get_statistiques_globales(session)
        releve = get_dernier_releve(session, ville_info["id"])
        return {"ville": ville_info["nom"], "releve": releve, "stats": stats}


@app.get("/meteo/{ville}/historique")
def get_historique(ville: str, limit: int = 50):
    with Session(engine) as session:
        ville_info = get_ville_by_nom(session, ville)
        if not ville_info:
            raise HTTPException(status_code=404, detail="Ville non trouvée")
        releves = get_releves_by_ville(session, ville_info["id"], limit=limit)
        return {"ville": ville_info["nom"], "releves": releves}
