from pydantic import BaseModel
from models.ville import Releve

class MeteoEtStats(BaseModel):
    ville: str
    releve: Releve
    stats: dict