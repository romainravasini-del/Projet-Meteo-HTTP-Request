from typing import List, Optional
from sqlmodel import Field, Relationship, SQLModel


# =====================================================================
# Modèles ORM SQLModel (Tables Relationnelles)
# =====================================================================

class Ville(SQLModel, table=True):
    """Modèle ORM représentant la table 'villes'."""

    __tablename__ = "villes"

    id: Optional[int] = Field(default=None, primary_key=True)
    nom: str = Field(unique=True, index=True, description="Nom unique de la ville")
    latitude: float = Field(description="Latitude géographique")
    longitude: float = Field(description="Longitude géographique")

    releves: List["Releve"] = Relationship(back_populates="ville")


class Releve(SQLModel, table=True):
    """Modèle ORM représentant la table 'releves'."""

    __tablename__ = "releves"

    id: Optional[int] = Field(default=None, primary_key=True)
    ville_id: int = Field(foreign_key="villes.id", index=True, description="Identifiant de la ville associée")
    temperature: float = Field(description="Température relevée (°C)")
    vitesse_vent: float = Field(description="Vitesse du vent relevée (km/h)")
    date_heure: str = Field(index=True, description="Horodatage ISO 8601 du relevé")

    ville: Optional[Ville] = Relationship(back_populates="releves")
