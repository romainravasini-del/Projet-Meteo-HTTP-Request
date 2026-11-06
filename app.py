from fastapi import FastAPI, HTTPException
from database import (
    get_connection,
    get_statistiques_globales,
    get_ville_by_nom,
    get_dernier_releve,
    get_releves_by_ville,
)
from pydantic import BaseModel

class ReleveModel(BaseModel):
    id: int
    vitesse_vent: float
    date_heure: str
    temperature: float

class MeteoEtStats(BaseModel):
    ville: str
    releve: ReleveModel
    stats: dict  


app = FastAPI()

@app.get("/")
def index():
    conn = get_connection()
    stats = get_statistiques_globales(conn)
    conn.close()
    return stats

@app.get("/export")
def export():
    conn = get_connection()
    stats = get_statistiques_globales(conn)
    conn.close()
    return stats

@app.get("/meteo/{ville}", response_model=MeteoEtStats)
def get_meteo(ville: str):
    conn = get_connection()
    ville_info = get_ville_by_nom(conn, ville)
    if not ville_info:
        conn.close()
        raise HTTPException(status_code=404, detail="Ville non trouvée")
    stats = get_statistiques_globales(conn)
    releve = get_dernier_releve(conn, ville_info["id"])
    conn.close()
    return {"ville": ville_info["nom"], "releve": releve, "stats": stats}

@app.get("/meteo/{ville}/historique")
def get_historique(ville: str, limit: int = 50):
    conn = get_connection()
    ville_info = get_ville_by_nom(conn, ville)
    if not ville_info:
        conn.close()
        raise HTTPException(status_code=404, detail="Ville non trouvée")
    releves = get_releves_by_ville(conn, ville_info["id"], limit=limit)
    conn.close()
    return {"ville": ville_info["nom"], "releves": releves}
