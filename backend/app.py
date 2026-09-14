from fastapi import FastAPI
from backend.api.soil import router as soil_router

from backend.config.settings import (
    PROJECT_NAME,
    VERSION,
    DESCRIPTION,
)

from backend.api.auth import router as auth_router
from backend.api.field import router as field_router
from backend.api.ai import router as ai_router
from backend.api.weather import router as weather_router
from backend.api.irrigation import router as irrigation_router
from backend.api.image_analysis import router as image_analysis_router
from backend.config.database import init_db

app = FastAPI(
    title=PROJECT_NAME,
    version=VERSION,
    description=DESCRIPTION,
)

@app.on_event("startup")
def on_startup():
    try:
        init_db()
    except Exception:
        pass

app.include_router(auth_router)
app.include_router(soil_router)
app.include_router(field_router)
app.include_router(ai_router)
app.include_router(weather_router)
app.include_router(irrigation_router)
app.include_router(image_analysis_router)

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