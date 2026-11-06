from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session

from api.deps import get_db
from api.v1.schemas.ville import MeteoEtStats
from repositories.ville_repository import (
    get_dernier_releve,
    get_releves_by_ville,
    get_statistiques_globales,
    get_ville_by_nom,
)

router = APIRouter()

@router.get("/")
def index(session: Session = Depends(get_db)):
    return get_statistiques_globales(session)

@router.get("/export")
def export(session: Session = Depends(get_db)):
    return get_statistiques_globales(session)

@router.get("/meteo/{ville}", response_model=MeteoEtStats)
def get_meteo(ville: str, session: Session = Depends(get_db)):
    ville_info = get_ville_by_nom(session, ville)
    if not ville_info:
        raise HTTPException(status_code=404, detail="Ville non trouvée")
    stats = get_statistiques_globales(session)
    releve = get_dernier_releve(session, ville_info["id"])
    return {"ville": ville_info["nom"], "releve": releve, "stats": stats}

@router.get("/meteo/{ville}/historique")
def get_historique(ville: str, limit: int = 50, session: Session = Depends(get_db)):
    ville_info = get_ville_by_nom(session, ville)
    if not ville_info:
        raise HTTPException(status_code=404, detail="Ville non trouvée")
    releves = get_releves_by_ville(session, ville_info["id"], limit=limit)
    return {"ville": ville_info["nom"], "releves": releves}