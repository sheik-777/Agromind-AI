"""
Crop API — REST endpoints for browsing, searching, and filtering the crop dataset.

Provides:
- GET /crops — paginated crop list with search, filters, sorting
- GET /crops/stats — dataset statistics
- GET /crops/{crop_name} — detailed crop information
- GET /crops/{crop_name}/compatibility — compatibility with user's field
"""

from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Query, HTTPException, Depends
from pydantic import BaseModel

from backend.services.crop_knowledge import get_crop_knowledge_base, CropRequirement
from backend.auth.deps import get_current_user_optional
from backend.config.database import get_db
from sqlalchemy.orm import Session
from backend.models.models import User, SensorReading, Farm, Field

router = APIRouter(prefix="/crops", tags=["Crops"])

SEASONS = [
    "kharif", "rabi", "zaid", "summer", "winter", "year_round", "perennial",
    "long_term", "annual"
]

SOIL_TYPES = [
    "loamy", "sandy", "clay", "silt", "peat", "chalk", "saline",
    "black", "red", "alluvial", "laterite", "desert", "mountain"
]


class CropListItem(BaseModel):
    id: str
    name: str
    soil_type: str
    season: str
    ph_min: float
    ph_max: float
    temp_min: float
    temp_max: float
    humidity_min: float
    humidity_max: float
    rain_min: float
    rain_max: float
    nitrogen_min: float
    nitrogen_max: float
    phosphorus_min: float
    phosphorus_max: float
    potassium_min: float
    potassium_max: float
    moisture_min: float
    moisture_max: float


class CropListResponse(BaseModel):
    crops: List[CropListItem]
    total: int
    page: int
    limit: int
    total_pages: int


class CropStatsResponse(BaseModel):
    total_records: int
    unique_crops: int
    soil_types: List[Dict[str, Any]]
    seasons: List[Dict[str, Any]]
    columns: List[str]


class CropDetailResponse(BaseModel):
    id: str
    name: str
    soil_type: str
    season: str
    nitrogen: Dict[str, float]
    phosphorus: Dict[str, float]
    potassium: Dict[str, float]
    ph: Dict[str, float]
    temperature: Dict[str, float]
    humidity: Dict[str, float]
    rainfall: Dict[str, float]
    moisture: Dict[str, float]


class CropCompatibilityResponse(BaseModel):
    crop_name: str
    compatibility_score: float
    matched: List[str]
    constraints: List[str]
    scores: Dict[str, Optional[float]]
    field_used: bool


def _crop_to_list_item(crop: CropRequirement, idx: int) -> CropListItem:
    return CropListItem(
        id=f"crop_{idx}",
        name=crop.crop,
        soil_type=crop.soil_type,
        season=crop.season,
        ph_min=crop.ph_min,
        ph_max=crop.ph_max,
        temp_min=crop.temp_min,
        temp_max=crop.temp_max,
        humidity_min=crop.humidity_min,
        humidity_max=crop.humidity_max,
        rain_min=crop.rain_min,
        rain_max=crop.rain_max,
        nitrogen_min=crop.nitrogen_min,
        nitrogen_max=crop.nitrogen_max,
        phosphorus_min=crop.phosphorus_min,
        phosphorus_max=crop.phosphorus_max,
        potassium_min=crop.potassium_min,
        potassium_max=crop.potassium_max,
        moisture_min=crop.moisture_min,
        moisture_max=crop.moisture_max,
    )


@router.get("/stats", response_model=CropStatsResponse)
def get_crop_stats():
    kb = get_crop_knowledge_base()

    unique_crops = set(c.crop.lower() for c in kb.crops)
    soil_counts: Dict[str, int] = {}
    season_counts: Dict[str, int] = {}

    for crop in kb.crops:
        st = crop.soil_type.strip().lower() if crop.soil_type else "unknown"
        soil_counts[st] = soil_counts.get(st, 0) + 1
        s = crop.season.strip().lower() if crop.season else "unknown"
        season_counts[s] = season_counts.get(s, 0) + 1

    soil_types = sorted(
        [{"name": k, "count": v} for k, v in soil_counts.items()],
        key=lambda x: -x["count"]
    )
    seasons = sorted(
        [{"name": k, "count": v} for k, v in season_counts.items()],
        key=lambda x: -x["count"]
    )

    columns = [
        "crop", "soil_type", "nitrogen_min", "nitrogen_max", "phosphorus_min",
        "phosphorus_max", "potassium_min", "potassium_max", "ph_min", "ph_max",
        "temp_min", "temp_max", "humidity_min", "humidity_max", "rain_min",
        "rain_max", "moisture_min", "moisture_max", "season"
    ]

    return CropStatsResponse(
        total_records=len(kb.crops),
        unique_crops=len(unique_crops),
        soil_types=soil_types,
        seasons=seasons,
        columns=columns,
    )


@router.get("", response_model=CropListResponse)
def list_crops(
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(24, ge=1, le=100, description="Items per page"),
    search: Optional[str] = Query(None, description="Search crop name"),
    soil_type: Optional[str] = Query(None, description="Filter by soil type"),
    season: Optional[str] = Query(None, description="Filter by season"),
    ph_min: Optional[float] = Query(None, description="Filter by minimum pH"),
    ph_max: Optional[float] = Query(None, description="Filter by maximum pH"),
    temp_min: Optional[float] = Query(None, description="Filter by minimum temperature"),
    temp_max: Optional[float] = Query(None, description="Filter by maximum temperature"),
    sort: Optional[str] = Query("name", description="Sort field: name, soil_type, season, ph, temp"),
    order: Optional[str] = Query("asc", description="Sort order: asc or desc"),
):
    kb = get_crop_knowledge_base()

    filtered = list(kb.crops)

    if search:
        search_lower = search.lower().strip()
        filtered = [c for c in filtered if search_lower in c.crop.lower()]

    if soil_type:
        soil_lower = soil_type.lower().strip()
        filtered = [c for c in filtered if soil_lower in c.soil_type.lower()]

    if season:
        season_lower = season.lower().strip()
        filtered = [c for c in filtered if season_lower in c.season.lower()]

    if ph_min is not None:
        filtered = [c for c in filtered if c.ph_max >= ph_min]

    if ph_max is not None:
        filtered = [c for c in filtered if c.ph_min <= ph_max]

    if temp_min is not None:
        filtered = [c for c in filtered if c.temp_max >= temp_min]

    if temp_max is not None:
        filtered = [c for c in filtered if c.temp_min <= temp_max]

    sort_key_map = {
        "name": lambda c: c.crop.lower(),
        "soil_type": lambda c: c.soil_type.lower(),
        "season": lambda c: c.season.lower(),
        "ph": lambda c: (c.ph_min + c.ph_max) / 2,
        "temp": lambda c: (c.temp_min + c.temp_max) / 2,
        "nitrogen": lambda c: (c.nitrogen_min + c.nitrogen_max) / 2,
    }

    if sort in sort_key_map:
        filtered.sort(key=sort_key_map[sort], reverse=(order == "desc"))

    total = len(filtered)
    total_pages = max(1, (total + limit - 1) // limit)
    start = (page - 1) * limit
    end = start + limit
    page_items = filtered[start:end]

    crops = [_crop_to_list_item(c, start + i) for i, c in enumerate(page_items)]

    return CropListResponse(
        crops=crops,
        total=total,
        page=page,
        limit=limit,
        total_pages=total_pages,
    )


@router.get("/{crop_name}", response_model=CropDetailResponse)
def get_crop_detail(crop_name: str):
    kb = get_crop_knowledge_base()
    crop = kb.get_crop_detail(crop_name)

    if not crop:
        # Lenient partial-name match (e.g. 'rice' -> 'Paddy (Rice)'; prefer exact-start)
        crop_lower = crop_name.lower().strip()
        exact_start = [c for c in kb.crops if c.crop.lower().startswith(crop_lower)]
        contains_word = [c for c in kb.crops if crop_lower in c.crop.lower() and c not in exact_start]
        candidates = exact_start or contains_word
        if candidates:
            # Prefer name that most closely matches the query
            def _name_relevance(c):
                name = c.crop.lower()
                if name.startswith(crop_lower):
                    return (0, len(name))
                return (1, len(name))
            candidates.sort(key=_name_relevance)
            crop = candidates[0]

    if not crop:
        raise HTTPException(status_code=404, detail=f"Crop '{crop_name}' not found")

    return CropDetailResponse(
        id=crop.crop.lower().replace(" ", "_"),
        name=crop.crop,
        soil_type=crop.soil_type,
        season=crop.season,
        nitrogen={"min": crop.nitrogen_min, "max": crop.nitrogen_max},
        phosphorus={"min": crop.phosphorus_min, "max": crop.phosphorus_max},
        potassium={"min": crop.potassium_min, "max": crop.potassium_max},
        ph={"min": crop.ph_min, "max": crop.ph_max},
        temperature={"min": crop.temp_min, "max": crop.temp_max},
        humidity={"min": crop.humidity_min, "max": crop.humidity_max},
        rainfall={"min": crop.rain_min, "max": crop.rain_max},
        moisture={"min": crop.moisture_min, "max": crop.moisture_max},
    )


@router.get("/{crop_name}/compatibility", response_model=CropCompatibilityResponse)
def get_crop_compatibility(
    crop_name: str,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    kb = get_crop_knowledge_base()
    crop = kb.get_crop_detail(crop_name)

    if not crop:
        crop_lower = crop_name.lower().strip()
        exact_start = [c for c in kb.crops if c.crop.lower().startswith(crop_lower)]
        contains_word = [c for c in kb.crops if crop_lower in c.crop.lower() and c not in exact_start]
        candidates = exact_start or contains_word
        if candidates:
            def _name_relevance(c):
                name = c.crop.lower()
                if name.startswith(crop_lower):
                    return (0, len(name))
                return (1, len(name))
            candidates.sort(key=_name_relevance)
            crop = candidates[0]

    if not crop:
        raise HTTPException(status_code=404, detail=f"Crop '{crop_name}' not found")

    field_params: Dict[str, Optional[float]] = {}
    field_used = False

    if current_user:
        farms = db.query(Farm).filter(Farm.user_id == current_user.id).all()
        farm_ids = [f.id for f in farms]
        fields = db.query(Field).filter(Field.farm_id.in_(farm_ids)).all() if farm_ids else []
        field_ids = [f.id for f in fields]

        if field_ids:
            reading = (
                db.query(SensorReading)
                .filter(SensorReading.field_id.in_(field_ids))
                .order_by(SensorReading.recorded_at.desc())
                .first()
            )
            if reading:
                field_used = True
                if reading.soil_moisture is not None:
                    field_params["moisture"] = reading.soil_moisture
                if reading.soil_ph is not None:
                    field_params["ph"] = reading.soil_ph
                if reading.temperature is not None:
                    field_params["temperature"] = reading.temperature
                if reading.humidity is not None:
                    field_params["humidity"] = reading.humidity

    results = kb.score_crop(field_params)
    match = next((r for r in results if r["crop"].lower() == crop.crop.lower()), None)

    if match:
        return CropCompatibilityResponse(
            crop_name=crop.crop,
            compatibility_score=match["compatibility"],
            matched=match["matched"],
            constraints=match["constraints"],
            scores=match["scores"],
            field_used=field_used,
        )

    return CropCompatibilityResponse(
        crop_name=crop_name,
        compatibility_score=0.0,
        matched=[],
        constraints=["No field data available for comparison"],
        scores={},
        field_used=False,
    )
