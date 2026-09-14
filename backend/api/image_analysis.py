"""
Image analysis API endpoints for crop disease diagnosis.
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, File, UploadFile, Form
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.config.database import get_db
from backend.auth.deps import get_current_user
from backend.models.models import User
from backend.services.image_analysis import (
    analyze_plant_image, save_uploaded_image, validate_image_file,
    AnalyzeImageRequest, AnalyzeImageResponse
)

router = APIRouter(prefix="/ai", tags=["AI"])


class AnalyzeImageIn(BaseModel):
    crop_hint: Optional[str] = None
    field_id: Optional[str] = None


@router.post("/analyze-image", response_model=dict)
async def analyze_image(
    file: UploadFile = File(...),
    crop_hint: Optional[str] = Form(None),
    field_id: Optional[str] = Form(None),
    current_user = Depends(get_current_user),
    db = Depends(get_db)
):
    """
    Upload and analyze a plant image for disease diagnosis.
    
    Accepts JPEG, PNG, WebP up to 10MB.
    Returns disease predictions with confidence and treatment recommendations.
    """
    # Validate file
    valid, error = validate_image_file(file)
    if not valid:
        raise HTTPException(400, error)
    
    # Read file
    content = await file.read()
    if len(content) == 0:
        raise HTTPException(400, "Empty file")
    
    if len(content) > 10 * 1024 * 1024:
        raise HTTPException(413, "File too large. Max 10MB.")
    
    # Get field context if provided
    field_context = None
    if field_id:
        from backend.models.models import Field
        field = db.query(Field).filter(Field.id == field_id).first()
        if field:
            field_context = {
                "crop": field.crop,
                "field_id": field.id
            }
    
    # Analyze image
    result = await analyze_plant_image(
        image_bytes=content,
        field_context=None,  # TODO: pass field context
        crop_hint=crop_hint
    )
    
    return {
        "predictions": result.predictions,
        "image_quality": result.image_quality,
        "crop_detected": result.crop_detected,
        "confidence": result.confidence,
        "processing_time_ms": result.processing_time_ms,
        "model_version": result.model_version,
        "warnings": result.warnings
    }


@router.post("/analyze-image-multipart")
async def analyze_image_multipart(
    file: UploadFile = File(...),
    crop_hint: Optional[str] = Form(None),
    field_id: Optional[str] = Form(None),
    current_user = Depends(get_current_user),
    db = Depends(get_db)
):
    """Alternative endpoint using multipart form data."""
    return await analyze_image(file, crop_hint, field_id, current_user, db)


# Health check for AI service
@router.get("/health")
async def ai_health():
    return {
        "status": "ok",
        "vision_model": "pending",
        "rag": "active",
        "llm": "configured" if os.environ.get("OPENAI_API_KEY") else "not_configured"
    }