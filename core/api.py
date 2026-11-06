from fastapi import FastAPI
from api.v1.router import api_router

app = FastAPI(
    title="Observatoire Météo API",
    description="API REST de consultation météorologique propulsée par FastAPI et SQLModel",
    version="1.0.0",
)

app.include_router(api_router)