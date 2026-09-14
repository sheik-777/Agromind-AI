"""
Irrigation API endpoints.
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.config.database import get_db
from backend.auth.deps import get_current_user
from backend.models.models import User
from backend.services.irrigation_engine import get_irrigation_engine, IrrigationDecisionResult

router = APIRouter(prefix="/irrigation", tags=["Irrigation"])


class IrrigationDecisionResponse(BaseModel):
    decision: str
    confidence: float
    reason: str
    important_factors: list[str]
    next_evaluation: str
    recommended_duration_minutes: Optional[int] = None
    recommended_volume_mm: Optional[float] = None
    risk_factors: list[str]
    expected_outcome: str


@router.get("/decision/{field_id}")
async def get_irrigation_decision(
    field_id: str,
    current_user = Depends(get_current_user),
    db = Depends(get_db)
):
    """Get irrigation decision for a field."""
    from backend.models.models import Field, Farm
    
    field = db.query(Field).filter(Field.id == field_id).first()
    if not field:
        raise HTTPException(404, "Field not found")
    
    farm = db.query(Farm).filter(Farm.id == field.farm_id).first()
    if not farm or farm.user_id != current_user.id:
        raise HTTPException(403, "Access denied to this field")
    
    engine = get_irrigation_engine(db)
    decision = await engine.make_decision(field_id, db)
    
    return IrrigationDecisionResponse(
        decision=decision.decision.value,
        confidence=decision.confidence,
        reason=decision.reason,
        important_factors=decision.important_factors,
        next_evaluation=decision.next_evaluation.isoformat(),
        recommended_duration_minutes=decision.recommended_duration_minutes,
        recommended_volume_mm=decision.recommended_volume_mm,
        risk_factors=decision.risk_factors,
        expected_outcome=decision.expected_outcome
    )


@router.get("/status/{field_id}")
async def get_irrigation_status(
    field_id: str,
    current_user = Depends(get_current_user),
    db = Depends(get_db)
):
    """Get current irrigation status and recent history."""
    from backend.models.models import Field, Farm, IrrigationEvent
    from sqlalchemy import desc
    
    field = db.query(Field).filter(Field.id == field_id).first()
    if not field:
        raise HTTPException(404, "Field not found")
    
    farm = db.query(Farm).filter(Farm.id == field.farm_id).first()
    if not farm or farm.user_id != current_user.id:
        raise HTTPException(403, "Access denied to this field")
    
    # Get recent irrigation events
    events = db.query(IrrigationEvent).filter(
        IrrigationEvent.field_id == field_id
    ).order_by(desc(IrrigationEvent.started_at)).limit(10).all()
    
    # Get current field status
    from backend.models.models import SensorReading
    from sqlalchemy import desc
    latest = db.query(SensorReading).filter(
        SensorReading.field_id == field_id
    ).order_by(desc(SensorReading.recorded_at)).first()
    
    soil_moisture = latest.soil_moisture if latest else None
    
    return {
        "field_id": field_id,
        "current_soil_moisture": soil_moisture,
        "last_updated": latest.recorded_at.isoformat() if latest else None,
        "recent_events": [
            {
                "id": e.id,
                "started_at": e.started_at.isoformat(),
                "ended_at": e.ended_at.isoformat() if e.ended_at else None,
                "duration_minutes": e.duration_minutes,
                "volume_mm": e.volume_mm,
                "trigger": e.trigger,
                "status": e.status
            }
            for e in events
        ]
    }


@router.post("/decision/{field_id}/acknowledge")
async def acknowledge_irrigation_decision(
    field_id: str,
    action: str,  # "accept", "defer", "manual"
    current_user = Depends(get_current_user),
    db = Depends(get_db)
):
    """Farmer acknowledges or overrides irrigation decision."""
    from backend.models.models import Field, Farm
    
    field = db.query(Field).filter(Field.id == field_id).first()
    if not field:
        raise HTTPException(404, "Field not found")
    
    farm = db.query(Farm).filter(Farm.id == field.farm_id).first()
    if not farm or farm.user_id != current_user.id:
        raise HTTPException(403, "Access denied")
    
    if action == "accept":
        # Trigger actual irrigation if hardware supports it
        # For now, just log the decision
        return {"message": "Irrigation decision accepted. Implementation pending hardware integration."}
    elif action == "defer":
        return {"message": "Irrigation deferred. Will re-evaluate at next scheduled check."}
    elif action == "manual":
        return {"message": "Manual irrigation mode selected. Farmer will handle."}
    else:
        raise HTTPException(400, "Invalid action. Use: accept, defer, or manual")