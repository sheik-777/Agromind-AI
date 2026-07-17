from fastapi import FastAPI
from backend.api.soil import router as soil_router

from backend.config.settings import (
    PROJECT_NAME,
    VERSION,
    DESCRIPTION,
)

from backend.api.auth import router as auth_router

app = FastAPI(
    title=PROJECT_NAME,
    version=VERSION,
    description=DESCRIPTION,
)

app.include_router(auth_router)
app.include_router(soil_router)

@app.get("/")
def home():
    return {
        "message": "Welcome to AgroMind 🌱",
        "status": "Backend Running"
    }


@app.get("/health")
def health():
    return {
        "status": "Healthy"
    }