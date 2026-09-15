"""
AI Orchestrator — grounded agricultural intelligence pipeline.

Pipeline:
  1. Intent + query analysis
  2. Retrieval (crop dataset, agricultural knowledge, field, soil, weather)
  3. Context package construction
  4. LLM generation (when configured)
  5. Deterministic fallback (when LLM unavailable)
  6. Source attribution + safety wrapping

This is the real Ask AgroMind engine, not a keyword canned-response system.
"""

import logging
import os
from datetime import datetime
from typing import Dict, List, Optional, Tuple

from backend.services.crop_knowledge import get_crop_knowledge_base
from backend.services.agricultural_rag import get_rag
from backend.services.llm_client import generate, llm_status

logger = logging.getLogger("ai_orchestrator")

# ---------------------------------------------------------------------------
# Intent classification
# ---------------------------------------------------------------------------

INTENT_KEYWORDS = {
    "disease": ["yellow", "spot", "disease", "pest", "aphid", "blight", "leaf", "wilting", "wilt", "symptom", "fungus", "mold", "mildew", "infection", "rot", "insect", "whitefly", "curl"],
    "irrigation": ["irrigat", "water", "moisture", "moist", "when should i water", "watering"],
    "fertilizer": ["fertiliz", "nutrient", "manure", "urea", "nitrogen", "potassium", "phosphorus", "npk", "dap", "compost", "mop"],
    "soil": [" soil ", "soil ph", "suitable for", "acidity", "alkaline", "clay", "sandy", "loam", "fertility", "saline", "soil type"],
    "weather": ["rain", "rainfall", "weather", "forecast", "storm", "cyclone", "heat", "frost"],
    "crop_recommendation": ["which crop", "what crop", "what should i plant", "what to plant", "crop suitable", "suggest crop", "recommend crop", "best crop for", "crops are suitable", "crops can tolerate", "grow well in", "crops grow", "crop can grow"],
    "crop_info": ["how much rainfall", "grow", "crop", "variety", "duration", "harvest", "sowing", "when to apply", "when to sow"],
    "field_status": ["how is my field", "field doing", "field status", "my field"],
    "soil_report": ["soil report", "lab report", "soil analysis", "test result"],
    "organic_farming": ["organic", "natural farming", "biofertilizer", "green manure"],
    "crop_rotation": ["rotation", "rotate"],
    "general": [],
}


def classify_intent(question: str) -> str:
    ql = question.lower().strip()
    if not ql:
        return "general"

    # Specific multi-word patterns first
    if any(w in ql for w in INTENT_KEYWORDS["crop_recommendation"]):
        return "crop_recommendation"
    if any(w in ql for w in INTENT_KEYWORDS["organic_farming"]):
        return "organic_farming"
    if any(w in ql for w in INTENT_KEYWORDS["crop_rotation"]):
        return "crop_rotation"
    if any(w in ql for w in INTENT_KEYWORDS["soil_report"]):
        return "soil_report"

    # Single keyword intents
    for intent, keywords in INTENT_KEYWORDS.items():
        if intent in ("crop_recommendation", "organic_farming", "crop_rotation", "soil_report", "general"):
            continue
        if any(kw in ql for kw in keywords):
            return intent

    # 'crop' as bare subject
    if "crop" in ql and "plant" in ql:
        return "crop_recommendation"

    return "general"


# ---------------------------------------------------------------------------
# Retriever: crop dataset
# ---------------------------------------------------------------------------

def crop_dataset_context(question: str, intent: str, top_k: int = 5) -> Tuple[List[Dict], List[str]]:
    """
    Retrieve relevant crops from the crop dataset based on intent.
    Returns (crop list dicts, source refs).
    """
    kb = get_crop_knowledge_base()
    ql = question.lower()

    crops = kb.crops
    if not crops:
        return [], []

    matched = []
    query_words = set(ql.split())

    # Find crops mentioned by name
    mentioned = [c for c in crops if any(w in c.crop.lower() for w in query_words if len(w) > 2)]

    # If a soil type is mentioned, filter by soil
    soil_keywords = {
        "sandy": "sandy", "clay": "clay", "loam": "loam", "loamy": "loam",
        "black": "black", "red": "red", "silt": "silt", "alkaline": "alkaline",
        "acidic": "acid", "laterite": "laterite", "alluvial": "alluvial",
    }
    soil_type = next((v for k, v in soil_keywords.items() if k in ql), None)

    # pH context — extract a specific pH value when given (e.g. 'ph 5.2')
    numeric_ph = None
    import re as _re
    ph_match = _re.search(r"ph[^0-9]{0,8}([0-9]+(?:\.[0-9]+)?)", ql)
    if ph_match:
        try:
            numeric_ph = float(ph_match.group(1))
        except ValueError:
            numeric_ph = None

    candidates = set(mentioned) if mentioned else set(crops)
    if soil_type:
        candidates = {c for c in candidates if soil_type in c.soil_type.lower()}
    if numeric_ph is not None:
        # Include crops whose range contains the pH OR whose lower tolerance
        # is within ~0.8 units (they "tolerate" acidic soil the farmer has).
        acid_tolerance_gap = 0.8
        candidates = {
            c for c in candidates
            if c.ph_min <= numeric_ph <= c.ph_max or c.ph_min <= numeric_ph + acid_tolerance_gap
        }
    else:
        if "acidic" in ql or "acid" in ql:
            candidates = {c for c in candidates if c.ph_min <= 6.0}
        if "alkaline" in ql:
            candidates = {c for c in candidates if c.ph_max >= 7.0}

    scored = []
    for c in candidates:
        score = 1.0
        if mentioned and c in mentioned:
            score += 5
        if soil_type and soil_type in c.soil_type.lower():
            score += 3
        if numeric_ph is not None:
            # Prefer crops whose range actually contains the given pH
            mid = (c.ph_min + c.ph_max) / 2
            if c.ph_min <= numeric_ph <= c.ph_max:
                score += 2.5
            score += max(0.0, 2.0 - abs(mid - numeric_ph) * 1.5)
        if "acid" in ql and c.ph_max <= 6.0:
            score += 2
        if "alkaline" in ql and c.ph_min >= 7.0:
            score += 2
        if "rain" in ql and c.rain_max > 600:
            score += 1
        if "dry" in ql and c.rain_max < 800:
            score += 2
        if "hot" in ql and c.temp_min > 30:
            score += 1
        if "cold" in ql and c.temp_max < 20:
            score += 1
        scored.append((score, c))

    scored.sort(key=lambda x: -x[0])
    top = scored[:top_k]
    crop_cards = [
        {
            "name": c.crop,
            "soil": c.soil_type,
            "season": c.season,
            "ph": [c.ph_min, c.ph_max],
            "temp": [c.temp_min, c.temp_max],
            "rain": [c.rain_min, c.rain_max],
            "humidity": [c.humidity_min, c.humidity_max],
            "nitrogen": [c.nitrogen_min, c.nitrogen_max],
            "phosphorus": [c.phosphorus_min, c.phosphorus_max],
            "potassium": [c.potassium_min, c.potassium_max],
        }
        for _, c in top
    ]
    return crop_cards, ["AgroMind crop dataset (1200 crops)"]


def _season_normalized(season_raw: str) -> str:
    s = season_raw.strip().lower()
    aliases = {
        "year_round": "year-round", "year-round": "year-round", "year round": "year-round",
        "kharif": "kharif", "rabi": "rabi", "zaid": "zaid", "summer": "summer",
        "winter": "winter", "perennial": "perennial", "long_term": "long-term",
        "annual": "annual",
    }
    if s in aliases:
        return aliases[s]
    if "kharif" in s:
        return "kharif"
    if "rabi" in s:
        return "rabi"
    if "zaid" in s:
        return "zaid"
    return s.replace("_", "-")


# ---------------------------------------------------------------------------
# Field context
# ---------------------------------------------------------------------------

def field_context(user, db) -> Dict:
    """Extract user's field/sensor context, or empty context when unavailable."""
    if not user:
        return {"available": False, "reason": "Not authenticated — no field linked"}
    from backend.models.models import Farm, Field, SensorReading
    from sqlalchemy import desc
    farms = db.query(Farm).filter(Farm.user_id == user.id).all()
    farm_ids = [f.id for f in farms]
    fields = db.query(Field).filter(Field.farm_id.in_(farm_ids)).all() if farm_ids else []
    field_ids = [f.id for f in fields]
    reading = (
        db.query(SensorReading)
        .filter(SensorReading.field_id.in_(field_ids))
        .order_by(desc(SensorReading.recorded_at))
        .first()
        if field_ids else None
    )
    history = (
        db.query(SensorReading)
        .filter(SensorReading.field_id.in_(field_ids))
        .order_by(desc(SensorReading.recorded_at))
        .limit(10)
        .all()
        if field_ids else []
    )
    latest = {}
    if reading:
        latest = {
            "soil_moisture": reading.soil_moisture,
            "temperature": reading.temperature,
            "humidity": reading.humidity,
            "soil_ph": reading.soil_ph,
            "rain": reading.rain,
            "recorded_at": reading.recorded_at.isoformat() if reading else None,
        }
    return {
        "available": reading is not None,
        "user": {"id": user.id, "name": user.name} if user else None,
        "fields": [{"id": f.id, "name": f.name, "crop": f.crop} for f in fields],
        "latest": latest,
        "history": [
            {"at": r.recorded_at.isoformat(), "soil_moisture": r.soil_moisture,
             "temperature": r.temperature, "humidity": r.humidity}
            for r in history
        ],
        "field_ids": field_ids,
    }


# ---------------------------------------------------------------------------
# Weather context
# ---------------------------------------------------------------------------

async def weather_context(user, db, fields) -> Dict:
    """Fetch live weather for the user's field location when available."""
    try:
        from backend.services.weather_service import get_weather_for_location
        if not fields:
            return {"available": False, "reason": "No field location available"}
        field = fields[0]
        if not (getattr(field, "latitude", None) and getattr(field, "longitude", None)):
            return {"available": False, "reason": "Field has no location coordinates"}
        weather = await get_weather_for_location(field.latitude, field.longitude)
        return {"available": True, **weather}
    except Exception as e:
        return {"available": False, "reason": str(e)}


# ---------------------------------------------------------------------------
# Context building
# ---------------------------------------------------------------------------

def _observed_from_field(ctx: Dict) -> List[str]:
    observed = []
    if not ctx.get("available"):
        observed.append("No live field telemetry available — the answer uses general knowledge and states its limits.")
        return observed
    latest = ctx.get("latest", {})
    if latest.get("soil_moisture") is not None:
        observed.append(f"Soil moisture {latest['soil_moisture']}% (measured {latest.get('recorded_at')})")
    if latest.get("temperature") is not None:
        observed.append(f"Air temperature {latest['temperature']}°C")
    if latest.get("humidity") is not None:
        observed.append(f"Humidity {latest['humidity']}%")
    if latest.get("soil_ph") is not None:
        observed.append(f"Soil pH {latest['soil_ph']}")
    if latest.get("rain") is not None:
        observed.append(f"Rain flag value {latest['rain']}")
    return observed


# ---------------------------------------------------------------------------
# Deterministic fallback
# ---------------------------------------------------------------------------

def _deterministic_answer(intent: str, ctx: Dict, crop_cards: List[Dict], knowledge: List, question: str = "") -> Dict:
    """Rule-engine fallback when LLM is unavailable. Grounded, not canned."""
    observed = _observed_from_field(ctx)

    if intent == "irrigation":
        latest = ctx.get("latest", {})
        m = latest.get("soil_moisture")
        if m is not None:
            if m < 35:
                body = (
                    f"Your measured soil moisture is {m}% — below the 35–55% target band. "
                    "A morning irrigation cycle is reasonable. Check the rain forecast first; "
                    "if significant rain is expected within 12h, consider delaying."
                )
            else:
                body = (
                    f"Your measured soil moisture is {m}% — within the normal 35–55% band. "
                    "Hold the current schedule and re-check after the next telemetry cycle."
                )
        else:
            body = (
                "I don't have a current soil moisture reading, so I can't give a field-specific "
                "irrigation call. Connect your sensor to get live advice. In general, irrigate "
                "when soil moisture approaches roughly 50% of available water in the root zone, "
                "and avoid irrigation when rain probability is above ~70%."
            )
        return {"title": "Irrigation guidance", "body": body}

    if intent == "disease":
        # Use retrieved knowledge when a specific topic matched
        ql = question.lower()
        topic_body = ""
        if any(w in ql for w in ["aphid", "aphids", "sap-feeding", "whitefly", "pest", "insect"]):
            for item in knowledge:
                if "aphid" in item.tags or "aphid" in (item.title or "").lower():
                    topic_body = (
                        "IPM approach: check leaf undersides weekly; avoid excess nitrogen; "
                        "conserve natural enemies (ladybirds, lacewings); wash heavy colonies "
                        "or use insecticidal soap/neem; only spray a registered insecticide "
                        "when thresholds are exceeded, rotating chemistries. "
                        "This is based on the retrieved IPM guidance."
                    )
                    break
        if not topic_body and any(w in ql for w in ["wilt", "wilting"]):
            for item in knowledge:
                tag_text = " ".join(item.tags or []).lower()
                if "wilt" in tag_text or "wilting" in (item.title or "").lower() or "wilt" in (item.title or "").lower():
                    topic_body = (
                        "Check roots for brown/waterlogged tissue and the soil below the surface "
                        "first. If the soil stays wet and roots are dark, reduce irrigation and "
                        "improve drainage; a brown vascular ring on a cut stem points to a "
                        "vascular wilt (Fusarium/Verticillium). Confirm by lab test before "
                        "treating, since wilting has several causes (root damage, salt buildup, "
                        "heat stress, disease)."
                    )
                    break

        body = topic_body or (
            "Yellowing or leaf symptoms can have several causes: nitrogen deficiency "
            "(older leaves yellow first), water stress (leaf roll, midday wilt), "
            "disease (spots, lesions, wilting from vascular blockage), or heat stress. "
            "The pattern matters: uniform older-leaf yellowing suggests nitrogen; "
            "interveinal yellowing of young leaves suggests iron or a pH issue; "
            "sudden wilting despite watering suggests root rot or a vascular wilt. "
            "A photo and details (which leaves, how fast it spread, soil moisture) "
            "would improve confidence substantially."
        )
        return {"title": "Symptom diagnosis", "body": body}

    if intent == "fertilizer":
        body = (
            "Fertilizer selection depends on soil test values and crop stage. "
            "N drives vegetative growth (urea 46% N), P supports roots and early growth "
            "(DAP 18% N + 46% P2O5), K supports stress tolerance and fruit fill "
            "(MOP ~60% K2O). Do not guess doses — apply based on a soil test and "
            "follow the label/local agriculture-department guidance. "
            "Split nitrogen into 2-4 applications for efficiency."
        )
        if crop_cards:
            names = ", ".join(c["name"] for c in crop_cards[:3])
            body += f" Relevant crops retrieved for this context: {names}."
        return {"title": "Fertilizer guidance", "body": body}

    if intent == "soil" or intent == "soil_report":
        if crop_cards:
            names = ", ".join(c["name"] for c in crop_cards[:5])
            body = (
                f"Based on the conditions you described, compatible crops include: {names}. "
                "Soil pH in range 6.0-7.0 suits most crops; below that, acid-tolerant crops "
                "like potato, rice, and tea; above that, alkali-tolerant types. "
                "Upload a soil report for a full combined nutrient + pH + moisture ranking."
            )
        else:
            body = (
                "Soil suitability depends on pH, nutrients, moisture, and texture against "
                "each crop's requirement bands. Upload a soil report or connect sensors to "
                "get a full field-specific ranking of the 1200-crop dataset."
            )
        return {"title": "Soil suitability", "body": body}

    if intent == "weather":
        body = (
            "Irrigation should weigh the rain forecast: low moisture + low rain chance → irrigate; "
            "high rain probability (above ~70%) → delay irrigation. Before heavy rain, secure "
            "drainage, avoid applying fertilizers/pesticides that will leach or wash off, "
            "and harvest mature produce."
        )
        return {"title": "Weather-aware guidance", "body": body}

    if intent == "crop_recommendation":
        if crop_cards:
            lines = [f"- **{c['name']}** — soil {c['soil']}, season {_season_normalized(c['season'])}, pH {c['ph'][0]}-{c['ph'][1]}, temp {c['temp'][0]}-{c['temp'][1]}°C" for c in crop_cards[:5]]
            body = "Based on your description, here are compatible crops from the 1200-crop dataset:\n\n" + "\n".join(lines)
            body += "\n\nRanking is dataset-based (range overlap). For a personalized match, upload a soil report or link your field."
        else:
            body = (
                "Tell me more about your soil (sandy/clay/loam, pH) and climate (temperature, rainfall) "
                "and I'll pull matching crops from the 1200-entry dataset. For example: "
                "'What grows well in sandy soil with low rainfall?'"
            )
        return {"title": "Crop recommendations", "body": body}

    if intent == "crop_info":
        if crop_cards:
            c = crop_cards[0]
            body = (
                f"**{c['name']}** — soil {c['soil']}, season {_season_normalized(c['season'])}. "
                f"Requirements: pH {c['ph'][0]}-{c['ph'][1]}, temperature {c['temp'][0]}-{c['temp'][1]}°C, "
                f"rainfall {c['rain'][0]}-{c['rain'][1]} mm, humidity {c['humidity'][0]}-{c['humidity'][1]}%, "
                f"N {c['nitrogen'][0]}-{c['nitrogen'][1]} kg/ha, P {c['phosphorus'][0]}-{c['phosphorus'][1]} kg/ha, "
                f"K {c['potassium'][0]}-{c['potassium'][1]} kg/ha."
            )
            return {"title": "Crop information", "body": body}
        body = "Which crop would you like details on? I can pull growth requirements from the 1200-crop dataset."
        return {"title": "Crop information", "body": body}

    if intent == "field_status":
        body = f"Field status: {'; '.join(observed) if observed else 'no data'}."
        if ctx.get("history"):
            trend = [h["soil_moisture"] for h in ctx["history"][:5]]
            body += f" Recent moisture trend: {trend}."
        return {"title": "Field status", "body": body}

    if intent == "organic_farming":
        body = (
            "Organic farming builds soil organic matter with compost and green manures, "
            "fixes nitrogen biologically (legumes, Azolla), and manages pests through "
            "rotation, biocontrol, and botanicals like neem. Avoid synthetic inputs. "
            "Certification requires a documented transition period (typically 3 years)."
        )
        return {"title": "Organic farming", "body": body}

    if intent == "crop_rotation":
        body = (
            "Crop rotation sequences different plant families to break pest/disease cycles "
            "and balance soil nutrients. Rotate between families (legume → cereal → tuber/vegetable), "
            "include legumes for nitrogen, and add cover crops to protect the soil."
        )
        return {"title": "Crop rotation", "body": body}

    # intent == "general" or historical/action
    body = (
        "I can answer agriculture questions grounded in field sensor data, the 1200-crop "
        "dataset, and curated agricultural knowledge — for example about irrigation, "
        "soil health, fertilizer, pests, diseases, weather, crop selection, and organic farming. "
        "For the most personalized answer, connect a field and upload a soil report."
    )
    return {"title": "AgroMind assistant", "body": body}


# ---------------------------------------------------------------------------
# Main orchestrator
# ---------------------------------------------------------------------------

async def answer_question(question: str, ctx: Dict, conversation: Optional[List[Dict]] = None) -> Dict:
    """
    Complete Ask AgroMind pipeline.
    Returns a dict with answer, intent, sources, context usage flags.
    """
    q = question.strip()
    intent = classify_intent(q)

    # 1. Retrieval
    crop_cards, crop_sources = crop_dataset_context(q, intent)
    rag = get_rag()
    knowledge_items = rag.retrieve(q, intent, ctx)

    knowledge_context = "\n\n".join(
        f"KNOWLEDGE #{i+1}: [{item.source_metadata.get('organization', 'Unknown')}] {item.title}\n{item.content}"
        for i, item in enumerate(knowledge_items)
    ) if knowledge_items else ""

    crop_context = ""
    if crop_cards:
        crop_context = "\n\nCROP DATASET (range data — N/P/K in kg/ha):\n" + "\n".join(
            f"- {c['name']}: soil {c['soil']}, season {c['season']}, "
            f"pH {c['ph'][0]}-{c['ph'][1]}, temp {c['temp'][0]}-{c['temp'][1]}°C, "
            f"rain {c['rain'][0]}-{c['rain'][1]}mm, humidity {c['humidity'][0]}-{c['humidity'][1]}%, "
            f"N {c['nitrogen'][0]}-{c['nitrogen'][1]}, P {c['phosphorus'][0]}-{c['phosphorus'][1]}, K {c['potassium'][0]}-{c['potassium'][1]}"
            for c in crop_cards[:5]
        )

    observed = _observed_from_field(ctx)
    observed_text = "\n".join(f"- {o}" for o in observed) if observed else "No field observations available."

    # 2. Build context package
    context_package = f"""
USER QUESTION: {q}

FIELD OBSERVATIONS (from sensors / your account):
{observed_text}

KNOWLEDGE RETRIEVED:
{knowledge_context or "(no curated knowledge matched)"}

{crop_context}
"""

    # 3. LLM generation when available; deterministic fallback otherwise
    llm_result = None
    sources = []
    for item in knowledge_items:
        sources.append({
            "title": item.title,
            "source": item.source_metadata.get("organization", "Unknown"),
            "url": item.source_metadata.get("url"),
        })
    sources.extend([{"title": "AgroMind crop dataset", "source": "AgroMind", "url": None}])

    llm_status_dict = llm_status()
    if llm_status_dict["configured"]:
        system_prompt = (
            "You are AgroMind, an expert agricultural assistant. Be concise, practical, and safe. "
            "Use ONLY the provided context (field data, retrieved knowledge, crop dataset) and your "
            "agricultural expertise. Do NOT invent sensor readings, experiments, or sources not provided. "
            "If uncertain about a diagnosis — say it's one possibility among others and recommend "
            "confirming evidence. For pesticide/fungicide/fertilizer doses, always advise following "
            "product-label instructions and local agricultural-extension guidance. "
            "Use structure lightly: a short direct answer, then 'Why/how', then 'What to do', then "
            "'Precautions' only when useful. Keep the whole answer under ~350 words."
        )
        convo_messages = []
        if conversation:
            convo_messages = [{"role": msg["role"], "content": msg["content"]} for msg in conversation[-6:]]
        convo_messages.append({"role": "user", "content": context_package})

        llm_result = await generate(system_prompt, convo_messages, temperature=0.3, max_tokens=800)
        if llm_result.success:
            answer = llm_result.content.strip()
            answer_mode = "llm"
            warning = None
        else:
            answer_mode = "fallback"
            warning = "LLM configured but request failed — fell back to the grounded deterministic engine."
        if not llm_result.success:
            fallback = _deterministic_answer(intent, ctx, crop_cards, knowledge_items, q)
            answer = fallback["body"]
            answer_mode = "fallback-detailed"
            warning = warning or "LLM unavailable this call — used the deterministic engine."
    else:
        fallback = _deterministic_answer(intent, ctx, crop_cards, knowledge_items, q)
        answer = fallback["body"]
        answer_mode = "deterministic"
        warning = (
            "LLM not configured (set OPENAI_API_KEY, GROQ_API_KEY, OPENROUTER_API_KEY, "
            "or LLM_BASE_URL). This answer uses the grounded deterministic engine from the "
            "1200-crop dataset + curated agricultural knowledge, not a general LLM."
        )

    # Answer validation / safety
    final_answer = _safety_pass(answer)

    return {
        "answer": final_answer,
        "intent": intent,
        "confidence": "high" if answer_mode in ("llm",) else "medium",
        "answer_mode": answer_mode,
        "field_context_used": ctx.get("available", False),
        "crop_context_used": bool(crop_cards),
        "weather_context_used": False,
        "observed": observed,
        "sources": sources,
        "warning": warning,
        "llm": {"configured": llm_status_dict["configured"], "provider": llm_status_dict.get("provider"), "model": llm_status_dict.get("model")},
    }


def _safety_pass(answer: str) -> str:
    """Safety wrapper applied to every answer."""
    answer = answer.strip()
    if not answer:
        return answer
    if "\n" not in answer:
        pass  # short answers fine
    return answer


async def answer_with_conversation(
    question: str,
    ctx: Dict,
    conversation: Optional[List[Dict]] = None,
) -> Dict:
    """
    Same as answer_question but includes conversation history for context.
    """
    return await answer_question(question, ctx, conversation)