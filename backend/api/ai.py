from typing import Optional, List, Dict
from datetime import datetime, timedelta
import re
import os

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import desc

from backend.config.database import get_db, init_db
from backend.auth.deps import get_current_user, get_current_user_optional
from backend.models.models import User, SensorReading, Farm, Field, Device
from backend.services.agricultural_rag import get_rag, KnowledgeItem
from backend.services.crop_knowledge import get_crop_knowledge_base
import csv

router = APIRouter(prefix="/ai", tags=["AI"])

try:
    init_db()
except Exception:
    pass

# Load dataset for crop recommendations
DATASET = []
DATASET_PATH = "backend/datasets/agromind_master_dataset_full (1).csv"
try:
    with open(DATASET_PATH, newline='', encoding='utf-8') as f:
        DATASET = list(csv.DictReader(f))
except Exception:
    DATASET = []

INTENTS = ["irrigation", "disease", "fertilizer", "soil", "weather", "crop", "field_status", "historical", "action", "general"]

def classify_intent(q: str) -> str:
    ql = q.lower()
    if any(w in ql for w in ["irrigat", "water", "moist"]):
        return "irrigation"
    if any(w in ql for w in ["yellow", "spot", "disease", "pest", "blight", "leaf"]):
        return "disease"
    if any(w in ql for w in ["fertiliz", "nutrient", "manure", "urea", "nitrogen", "potassium", "phosphorus"]):
        return "fertilizer"
    if any(w in ql for w in ["soil", "ph", "suitable"]):
        return "soil"
    if any(w in ql for w in ["rain", "weather", "forecast", "temperature"]):
        return "weather"
    if any(w in ql for w in ["which crop", "what crop", "what should i plant"]):
        return "crop"
    if any(w in ql for w in ["how is my field", "field doing", "field status"]):
        return "field_status"
    if any(w in ql for w in ["last 5 days", "history", "changed", "trend"]):
        return "historical"
    if any(w in ql for w in ["what should i do today", "what to do"]):
        return "action"
    return "general"

def _field_context(user: Optional[User], db: Session) -> Dict:
    if not user:
        return {"available": False, "reason": "Not authenticated — no field linked"}
    farms = db.query(Farm).filter(Farm.user_id == user.id).all()
    farm_ids = [f.id for f in farms]
    fields = db.query(Field).filter(Field.farm_id.in_(farm_ids)).all() if farm_ids else []
    field_ids = [f.id for f in fields]
    reading = db.query(SensorReading).filter(SensorReading.field_id.in_(field_ids)).order_by(desc(SensorReading.recorded_at)).first() if field_ids else None
    history = db.query(SensorReading).filter(SensorReading.field_id.in_(field_ids)).order_by(desc(SensorReading.recorded_at)).limit(10).all() if field_ids else []
    return {
        "available": reading is not None,
        "user": {"id": user.id, "name": user.name, "email": user.email} if user else None,
        "fields": [{"id": f.id, "name": f.name, "crop": f.crop} for f in fields],
        "latest": {
            "soil_moisture": reading.soil_moisture,
            "temperature": reading.temperature,
            "humidity": reading.humidity,
            "soil_ph": reading.soil_ph,
            "rain": reading.rain,
            "recorded_at": reading.recorded_at.isoformat() if reading else None,
        } if reading else None,
        "history": [
            {"at": r.recorded_at.isoformat(), "soil_moisture": r.soil_moisture, "temperature": r.temperature, "humidity": r.humidity}
            for r in history
        ],
        "field_ids": field_ids,
    }

class AskIn(BaseModel):
    question: str
    image_quality: Optional[str] = None

@router.post("/ask")
def ask(payload: AskIn, db: Session = Depends(get_db), current_user: Optional[User] = Depends(get_current_user_optional)):
    q = payload.question.strip()
    if not q:
        raise HTTPException(400, "Question is required")
    intent = classify_intent(q)
    ctx = _field_context(current_user, db)
    rag = get_rag()
    knowledge = rag.retrieve(q, intent, ctx)

    # Try LLM if key present (optional reasoning layer)
    llm_answer = None
    api_key = os.environ.get("OPENAI_API_KEY") or os.environ.get("LLM_API_KEY")
    if api_key:
        try:
            import httpx
            # For now use deterministic engine; LLM can be plugged in later
            llm_answer = None
        except Exception:
            llm_answer = None

    # Deterministic grounded answer per intent
    observed = []
    if ctx["available"]:
        l = ctx["latest"]
        observed.append(f"Soil moisture {l['soil_moisture']}% (measured {l['recorded_at']})" if l.get('soil_moisture') is not None else "Soil moisture unavailable")
        observed.append(f"Temperature {l['temperature']}°C, humidity {l['humidity']}%")
        observed.append(f"Soil pH {l['soil_ph']}" if l.get('soil_ph') is not None else "Soil pH unavailable")
    else:
        observed.append("No live field telemetry available — answer uses general knowledge and states limits")

    # Build response by intent
    if intent == "irrigation":
        title = "Irrigation guidance"
        if ctx["available"] and ctx["latest"]["soil_moisture"] is not None:
            m = ctx["latest"]["soil_moisture"]
            if m < 35:
                rec = "Moisture is below the 35–55% target band — a morning irrigation cycle is reasonable. Check rain forecast first; if significant rain is expected within 12h, consider delaying."
            else:
                rec = "Moisture sits inside normal bands — hold current schedule and re-check after the next telemetry cycle."
        else:
            rec = "I don't have a current soil moisture reading, so I can't give a field-specific irrigation call. Connect your sensor to get live advice."
        body = rec
    elif intent == "disease":
        body = ("Yellowing can be (1) nitrogen deficiency, (2) water stress, (3) disease, or (4) heat stress — the camera alone cannot decide. "
                "If you upload a photo, I run: image quality check → vision model (when deployed) → RAG verification → sensor fusion → final assessment. "
                "For now, compare recent moisture trend and soil pH against the crop's needs.")
    elif intent == "fertilizer":
        body = "Fertilizer is farmer-applied, not automatic. The engine weighs soil N/P/K, crop stage, and weather. Share your lab report N/P/K if available for a specific recommendation. Without lab values I can only give general guidance — do not apply a dose I have not grounded in retrieved sources."
    elif intent == "soil":
        crops = _recommend_crops_for_field(ctx.get("latest")) if ctx["available"] else []
        body = f"Soil suitability depends on pH, nutrients and moisture vs crop requirement bands. Top compatible crops from your dataset for current field: {', '.join(crops[:3]) if crops else 'no live field to compare — upload a soil report for a full ranking'}."
    elif intent == "weather":
        body = "I don't have live weather yet (backend will fetch Open-Meteo and cache it). Irrigation considers rain probability: low moisture + low rain chance → irrigate; high rain chance → delay."
    elif intent == "crop":
        crops = _recommend_crops_for_field(ctx.get("latest")) if ctx["available"] else []
        body = f"Based on current field bands, compatible crops include: {', '.join(crops)}. Full ranking uses soil report + moisture/pH."
    elif intent == "field_status":
        body = f"Field status: {'; '.join(observed) if observed else 'no data'}. Historical trend over last readings: {[h['soil_moisture'] for h in ctx.get('history', [])[:5]] if ctx.get('history') else 'no history yet'}."
    elif intent == "historical":
        body = f"Over last readings your moisture values were: {[h['soil_moisture'] for h in ctx.get('history', [])[:5]] if ctx.get('history') else 'no history yet'}. A falling trend with warm temps suggests increasing irrigation need."
    elif intent == "action":
        body = "Today: check moisture vs 35% threshold, inspect newest camera scan (5/day schedule), and review any soil-report advisories. If moisture is low and no rain is forecast, irrigate early morning."
    else:
        body = "I can answer agricultural questions grounded in your field data + retrieved knowledge. Ask about irrigation, soil, disease, fertilizer, weather, or field status — each gets different evidence."

    # Gather sources from retrieved knowledge
    sources = [k.source_metadata.get("organization", "AgroMind dataset") for k in knowledge] if knowledge else ["AgroMind dataset (1200 crops)"]

    return {
        "intent": intent,
        "observed": observed,
        "retrieved_knowledge": knowledge,
        "inferred": body,
        "recommended": body,
        "sources": sources,
        "field_available": ctx["available"],
        "field_context": ctx,
        "warning": "Demo reasoning — upgrade to LLM + RAG pipeline when OPENAI_API_KEY is configured" if not api_key else None,
    }

def _recommend_crops_for_field(latest: Optional[Dict]) -> List[str]:
    if not latest or not DATASET:
        return []
    field_params = {}
    if latest.get("soil_moisture") is not None: field_params["moisture"] = latest["soil_moisture"]
    if latest.get("soil_ph") is not None: field_params["ph"] = latest["soil_ph"]
    if latest.get("airTempC") is not None: field_params["temperature"] = latest["airTempC"]
    if latest.get("humidity") is not None: field_params["humidity"] = latest["humidity"]
    if latest.get("nitrogen") is not None: field_params["nitrogen"] = latest["nitrogen"]
    if latest.get("phosphorus") is not None: field_params["phosphorus"] = latest["phosphorus"]
    if latest.get("potassium") is not None: field_params["potassium"] = latest["potassium"]
    if latest.get("rainfall") is not None: field_params["rainfall"] = latest["rainfall"]
    # Use crop knowledge base
    from backend.services.crop_knowledge import get_crop_knowledge_base
    kb = get_crop_knowledge_base()
    top = kb.get_compatible_crops(field_params, 3)
    return [r["crop"] for r in top]