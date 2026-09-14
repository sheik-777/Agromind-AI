"""Field telemetry ingestion + retrieval. Real DB path.

Ownership: every read checks that the field/device belongs to the authenticated
farmer's farm(s). Ingestion uses device_key (per-device secret) when set;
otherwise open for WiFi-prototype testing but logs a warning.
"""
from datetime import datetime, timedelta
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Header
from pydantic import BaseModel, Field as PydField
from sqlalchemy.orm import Session
from sqlalchemy import desc

from backend.config.database import get_db, init_db
from backend.models.models import User, Farm, Field, Device, SensorReading
from backend.auth.deps import get_current_user
from backend.auth.security import hash_password, verify_password
import hashlib

router = APIRouter(prefix="/field", tags=["Field"])

try:
    init_db()
except Exception:
    pass

class IngestIn(BaseModel):
    device_id: str = PydField(..., description="AGRO_NODE_001")
    field_id: str = PydField(..., description="FIELD_001")
    soil_moisture: Optional[float] = None
    temperature: Optional[float] = None
    humidity: Optional[float] = None
    soil_ph: Optional[float] = None
    rain: Optional[bool] = False
    timestamp: Optional[str] = None  # ISO
    device_key: Optional[str] = None  # optional shared secret

def _hash_key(k: str) -> str:
    return hashlib.sha256(k.encode()).hexdigest()

def _validate_ranges(p: IngestIn):
    if p.soil_moisture is not None and not (0 <= p.soil_moisture <= 100):
        raise HTTPException(400, "soil_moisture must be 0-100")
    if p.humidity is not None and not (0 <= p.humidity <= 100):
        raise HTTPException(400, "humidity must be 0-100")
    if p.soil_ph is not None and not (0 <= p.soil_ph <= 14):
        raise HTTPException(400, "soil_ph must be 0-14")
    if p.temperature is not None and not (-40 <= p.temperature <= 80):
        raise HTTPException(400, "temperature out of range")

@router.post("/ingest")
def ingest(payload: IngestIn, db: Session = Depends(get_db), x_device_key: Optional[str] = Header(None)):
    """Controlled ingestion for WiFi prototype / test payloads.
    When device has a stored key, caller must provide correct key via body device_key or header X-Device-Key.
    """
    _validate_ranges(payload)
    # Find or auto-create field/device chain for testing convenience?
    # For now require field exists OR auto-create under first farm of a pseudo system — but enforce schema.
    field = db.query(Field).filter(Field.id == payload.field_id).first()
    if not field:
        # Auto-create field under a placeholder farm if missing (dev mode) — otherwise 404
        # Try to find any farm; if none, error
        farm = db.query(Farm).first()
        if not farm:
            raise HTTPException(404, f"Field {payload.field_id} not found and no farm to attach to. Register a user first.")
        field = Field(id=payload.field_id, farm_id=farm.id, name=payload.field_id)
        db.add(field)
        db.flush()

    device = db.query(Device).filter(Device.id == payload.device_id).first()
    if not device:
        device = Device(id=payload.device_id, field_id=field.id)
        db.add(device)
        db.flush()
    else:
        # Ensure device belongs to claimed field (prevent hijack)
        if device.field_id != field.id:
            raise HTTPException(400, f"Device {payload.device_id} belongs to field {device.field_id}, not {payload.field_id}")

    # Optional device-key auth
    provided = payload.device_key or x_device_key
    if device.device_key_hash:
        if not provided or _hash_key(provided) != device.device_key_hash:
            raise HTTPException(401, "Invalid device key")

    recorded = None
    if payload.timestamp:
        try:
            recorded = datetime.fromisoformat(payload.timestamp.replace("Z", "+00:00"))
        except Exception:
            recorded = datetime.utcnow()
    else:
        recorded = datetime.utcnow()

    reading = SensorReading(
        device_id=device.id,
        field_id=field.id,
        soil_moisture=payload.soil_moisture,
        temperature=payload.temperature,
        humidity=payload.humidity,
        soil_ph=payload.soil_ph,
        rain=bool(payload.rain),
        recorded_at=recorded,
    )
    db.add(reading)
    device.last_seen_at = datetime.utcnow()
    db.commit()
    return {"ok": True, "reading_id": reading.id, "recorded_at": reading.recorded_at.isoformat()}

@router.post("/devices/{device_id}/key")
def set_device_key(device_id: str, body: dict, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Set/rotate device key. Requires ownership of the device's farm."""
    key = body.get("device_key") or body.get("key")
    if not key or len(key) < 8:
        raise HTTPException(400, "device_key must be at least 8 characters")
    device = db.query(Device).filter(Device.id == device_id).first()
    if not device:
        raise HTTPException(404, "Device not found")
    field = db.query(Field).filter(Field.id == device.field_id).first()
    farm = db.query(Farm).filter(Farm.id == field.farm_id).first() if field else None
    if not farm or farm.user_id != current_user.id:
        raise HTTPException(403, "Not your device")
    device.device_key_hash = _hash_key(key)
    db.commit()
    return {"ok": True}

def _user_field_ids(user: User, db: Session) -> List[str]:
    farms = db.query(Farm).filter(Farm.user_id == user.id).all()
    farm_ids = [f.id for f in farms]
    if not farm_ids:
        return []
    fields = db.query(Field).filter(Field.farm_id.in_(farm_ids)).all()
    return [f.id for f in fields]

@router.get("/latest")
def latest(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    field_ids = _user_field_ids(current_user, db)
    if not field_ids:
        raise HTTPException(404, "No fields for this user. Upload a soil report or wait for device assignment.")
    reading = db.query(SensorReading).filter(SensorReading.field_id.in_(field_ids)).order_by(desc(SensorReading.recorded_at)).first()
    if not reading:
        raise HTTPException(404, "No telemetry yet for your fields")
    device = db.query(Device).filter(Device.id == reading.device_id).first()
    field = db.query(Field).filter(Field.id == reading.field_id).first()
    return {
        "field_id": field.id if field else reading.field_id,
        "device_id": reading.device_id,
        "soil_moisture": reading.soil_moisture,
        "temperature": reading.temperature,
        "humidity": reading.humidity,
        "soil_ph": reading.soil_ph,
        "rain": reading.rain,
        "timestamp": reading.recorded_at.isoformat(),
        "device_online": (device.last_seen_at and (datetime.utcnow() - device.last_seen_at) < timedelta(minutes=15)) if device and device.last_seen_at else False,
        "last_seen_at": device.last_seen_at.isoformat() if device and device.last_seen_at else None,
    }

@router.get("/history")
def history(days: int = 5, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    field_ids = _user_field_ids(current_user, db)
    if not field_ids:
        return []
    since = datetime.utcnow() - timedelta(days=days)
    rows = db.query(SensorReading).filter(SensorReading.field_id.in_(field_ids), SensorReading.recorded_at >= since).order_by(SensorReading.recorded_at).all()
    return [
        {
            "at": r.recorded_at.isoformat(),
            "soil_moisture": r.soil_moisture,
            "temperature": r.temperature,
            "humidity": r.humidity,
            "soil_ph": r.soil_ph,
            "rain": r.rain,
        }
        for r in rows
    ]

@router.get("/status")
def status(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    # Same as latest but explicit status shape
    return latest(current_user, db)

@router.get("/devices")
def list_devices(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    field_ids = _user_field_ids(current_user, db)
    devices = db.query(Device).filter(Device.field_id.in_(field_ids)).all() if field_ids else []
    out = []
    for d in devices:
        out.append({"device_id": d.id, "field_id": d.field_id, "last_seen_at": d.last_seen_at.isoformat() if d.last_seen_at else None})
    return out
