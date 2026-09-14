"""
Weather API endpoints using Open-Meteo.
Provides current weather, forecast, and agricultural impact analysis.
"""
from typing import Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.config.database import get_db
from backend.auth.deps import get_current_user
from backend.models.models import User, Farm, Field
from backend.services.weather_service import get_weather_for_field, agricultural_impact

router = APIRouter(prefix="/weather", tags=["Weather"])


class WeatherResponse(BaseModel):
    current: Dict
    hourly: Dict
    daily: Dict
    agricultural_impact: Dict
    fetched_at: str


@router.get("/current")
async def get_current_weather(
    latitude: float = Query(..., ge=-90, le=90),
    longitude: float = Query(..., ge=-180, le=180),
    soil_moisture: Optional[float] = Query(None, ge=0, le=100),
    current_user = Depends(get_current_user),
    db = Depends(get_db)
):
    """Get current weather and forecast for specific coordinates."""
    # Verify user has access to this location (optional - could link to fields)
    weather = await get_weather_for_field(latitude, longitude, soil_moisture)
    if not weather:
        raise HTTPException(503, "Weather service unavailable")
    return weather


@router.get("/current/field/{field_id}")
async def get_weather_for_field_endpoint(
    field_id: str,
    current_user = Depends(get_current_user),
    db = Depends(get_db)
):
    """Get weather for a specific field (requires ownership)."""
    from backend.models.models import Field, Farm
    field = db.query(Field).filter(Field.id == field_id).first()
    if not field:
        raise HTTPException(404, "Field not found")
    
    farm = db.query(Farm).filter(Farm.id == field.farm_id).first()
    if not farm or farm.user_id != current_user.id:
        raise HTTPException(403, "Access denied to this field")
    
    # Get field coordinates (would need to add lat/lon to Field model)
    # For now, use a default or stored coordinates
    latitude = getattr(field, 'latitude', 20.5937)  # Default to India center
    longitude = getattr(field, 'longitude', 78.9629)
    
    # Get latest soil moisture from field's latest reading
    from backend.models.models import SensorReading
    from sqlalchemy import desc
    from backend.config.database import get_db as get_db_session
    
    db_session = next(get_db())
    try:
        latest = db_session.query(SensorReading).filter(
            SensorReading.field_id == field_id
        ).order_by(SensorReading.recorded_at.desc()).first()
        soil_moisture = latest.soil_moisture if latest else None
    finally:
        db_session.close()
    
    weather = await get_weather_for_field(latitude, longitude, soil_moisture)
    if not weather:
        raise HTTPException(503, "Weather service unavailable")
    return weather


@router.get("/forecast/{latitude}/{longitude}")
async def get_forecast(
    latitude: float,
    longitude: float,
    days: int = Query(7, ge=1, le=14),
    current_user = Depends(get_current_user)
):
    """Get multi-day forecast for coordinates."""
    from backend.services.weather_service import fetch_current_weather
    
    weather = await fetch_current_weather(latitude, longitude)
    if not weather:
        raise HTTPException(503, "Weather service unavailable")
    
    # Filter to requested days
    daily = weather.get("daily", {})
    if daily and "time" in daily:
        # Truncate to requested days
        n = min(days, len(daily.get("time", [])))
        for key in daily:
            if isinstance(daily[key], list):
                daily[key] = daily[key][:n]
    
    return {
        "daily": daily,
        "latitude": latitude,
        "longitude": longitude,
        "days": days,
    }


@router.get("/agricultural-impact/{latitude}/{longitude}")
async def get_agricultural_impact(
    latitude: float,
    longitude: float,
    soil_moisture: Optional[float] = Query(None, ge=0, le=100),
    current_user = Depends(get_current_user)
):
    """Get agricultural impact assessment for weather conditions."""
    impact = await agricultural_impact(
        await fetch_current_weather(latitude, longitude), 
        soil_moisture
    )
    return impact


@router.get("/field/{field_id}/impact")
async def get_field_weather_impact(
    field_id: str,
    current_user = Depends(get_current_user),
    db = Depends(get_db)
):
    """Get weather impact assessment for a specific field."""
    from backend.models.models import Field, Farm, SensorReading
    from sqlalchemy import desc
    
    field = db.query(Field).filter(Field.id == field_id).first()
    if not field:
        raise HTTPException(404, "Field not found")
    
    farm = db.query(Farm).filter(Farm.id == field.farm_id).first()
    if not farm or farm.user_id != current_user.id:
        raise HTTPException(403, "Access denied to this field")
    
    # Get latest soil moisture
    latest = db.query(SensorReading).filter(
        SensorReading.field_id == field_id
    ).order_by(desc(SensorReading.recorded_at)).first()
    
    soil_moisture = latest.soil_moisture if latest else None
    
    # Use field coordinates (add lat/lon to Field model in future)
    latitude = getattr(field, 'latitude', 20.5937)
    longitude = getattr(field, 'longitude', 78.9629)
    
    weather = await get_weather_for_field(latitude, longitude, soil_moisture)
    if not weather:
        raise HTTPException(503, "Weather service unavailable")
    return weather