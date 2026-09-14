"""
Image analysis service for crop disease diagnosis.

Supports:
- Image validation (type, size, quality)
- Disease classification (when model available)
- Integration with field context and RAG
"""
from typing import Optional, List, Dict, Any
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
import uuid
import base64
import io

from fastapi import UploadFile, File, HTTPException
from pydantic import BaseModel


# Allowed image types
ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp"}
MAX_FILE_SIZE_MB = 10
MAX_DIMENSION = 4096

# Disease classes for future model integration
DISEASE_CLASSES = [
    "healthy",
    "bacterial_blight",
    "brown_spot",
    "leaf_blight",
    "leaf_blast",
    "bacterial_leaf_streak",
    "brown_spot_rice",
    "tungro",
    "bacterial_leaf_blight",
    "brown_spot",
    "leaf_blight",
    "leaf_blast",
    "bacterial_leaf_streak",
    "brown_spot_rice",
    "tungro",
    "powdery_mildew",
    "downy_mildew",
    "rust",
    "early_blight",
    "late_blight",
    "septoria_leaf_spot",
    "bacterial_spot",
    "anthracnose",
    "fusarium_wilt",
    "verticillium_wilt",
    "root_rot",
    "nutrient_deficiency_n",
    "nutrient_deficiency_p",
    "nutrient_deficiency_k",
    "nutrient_deficiency_ca",
    "nutrient_deficiency_mg",
    "nutrient_deficiency_fe",
    "nutrient_deficiency_zn",
    "nutrient_deficiency_b",
]

@dataclass
class DiseasePrediction:
    disease: str
    confidence: float
    crop: Optional[str] = None
    alternative_predictions: List[Dict[str, float]] = None

    def __post_init__(self):
        if self.alternative_predictions is None:
            self.alternative_predictions = []


@dataclass
class ImageAnalysisResult:
    """Result of image analysis."""
    predictions: List[Dict[str, Any]]
    image_quality: str  # good, poor, insufficient
    crop_detected: Optional[str] = None
    confidence: float = 0.0
    processing_time_ms: int = 0
    model_version: str = "pending"
    warnings: List[str] = None

    def __post_init__(self):
        if self.warnings is None:
            self.warnings = []


def validate_image_file(file: UploadFile) -> tuple[bool, str]:
    """Validate uploaded image file."""
    # Check content type
    if file.content_type not in ALLOWED_IMAGE_TYPES:
        return False, f"Unsupported file type: {file.content_type}. Allowed: {', '.join(ALLOWED_IMAGE_TYPES)}"
    
    # Check file size (will be checked after reading)
    return True, ""


async def read_image_file(file: UploadFile) -> tuple[bytes, str]:
    """Read and validate image file."""
    content = await file.read()
    
    if len(content) > MAX_FILE_SIZE_MB * 1024 * 1024:
        raise HTTPException(413, f"File too large. Max size: {MAX_FILE_SIZE_MB}MB")
    
    if len(content) == 0:
        raise HTTPException(400, "Empty file")
    
    return content, file.filename


def validate_image_quality(image_bytes: bytes) -> tuple[str, List[str]]:
    """
    Basic image quality validation.
    Returns (quality_rating, warnings).
    """
    try:
        from PIL import Image
        import io
        
        img = Image.open(io.BytesIO(image_bytes))
        width, height = img.size
        
        warnings = []
        
        # Check dimensions
        if width < 224 or height < 224:
            warnings.append(f"Image resolution ({width}x{height}) below minimum 224x224")
            quality = "poor"
        elif width > MAX_DIMENSION or height > MAX_DIMENSION:
            warnings.append(f"Image resolution ({width}x{height}) exceeds maximum {MAX_DIMENSION}x{MAX_DIMENSION}")
            quality = "poor"
        else:
            quality = "good"
        
        # Check if image is blurry (simple check)
        # Convert to grayscale and check variance of Laplacian
        try:
            import cv2
            import numpy as np
            gray = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2GRAY)
            laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
            if laplacian_var < 100:
                warnings.append("Image may be blurry")
                quality = "poor"
        except:
            pass  # OpenCV not available, skip blur check
        
        return quality, warnings
        
    except Exception as e:
        return "unknown", [f"Quality check failed: {str(e)}"]


async def analyze_plant_image(
    image_bytes: bytes,
    field_context: Optional[Dict] = None,
    crop_hint: Optional[str] = None
) -> ImageAnalysisResult:
    """
    Analyze plant image for disease diagnosis.
    
    Currently uses deterministic rules + RAG. When vision model is available,
    will replace with actual ML inference.
    """
    start_time = datetime.utcnow()
    
    # Validate image quality
    quality, warnings = validate_image_quality(image_bytes)
    
    if quality == "poor":
        return ImageAnalysisResult(
            predictions=[],
            image_quality="poor",
            confidence=0.0,
            processing_time_ms=int((datetime.utcnow() - start_time).total_seconds() * 1000),
            warnings=["Image quality insufficient for reliable diagnosis"] + warnings,
            model_version="pending"
        )
    
    # TODO: Replace with actual vision model inference
    # For now, return structured mock response based on deterministic logic
    
    # Simulate disease detection based on simple heuristics
    # In production, this would call a vision model (e.g., PlantVillage model)
    
    predictions = []
    
    # Mock prediction logic - in production, replace with actual model inference
    # For now, return placeholder predictions with clear "not real" indicators
    predictions = [
        {
            "disease": "Model not deployed",
            "confidence": 0.0,
            "status": "vision_model_pending",
            "message": "Computer vision model not yet deployed. Upload infrastructure ready; model integration pending.",
            "alternatives": []
        }
    ]
    
    # If crop hint provided, add crop-specific note
    if crop_hint:
        crop_note = f"Crop hint provided: {crop_hint}. "
        predictions[0]["message"] += f" Crop context: {crop_hint}."
    
    # Add field context note if available
    if field_context:
        context_parts = []
        if field_context.get("crop"):
            context_parts.append(f"Crop: {field_context['crop']}")
        if field_context.get("soil_moisture") is not None:
            context_parts.append(f"Soil moisture: {field_context['soil_moisture']}%")
        if context_parts:
            for p in predictions:
                p["field_context"] = "; ".join(context_parts)
    
    processing_time = int((datetime.utcnow() - start_time).total_seconds() * 1000)
    
    return ImageAnalysisResult(
        predictions=predictions,
        image_quality="good",
        crop_detected=None,
        confidence=0.0,
        processing_time_ms=processing_time,
        model_version="pending",
        warnings=warnings + [
            "Computer vision model not yet deployed - this is a placeholder response",
            "Image quality check passed" if "good" in str(quality).lower() else "Image quality may affect results"
        ]
    )


async def save_uploaded_image(file_bytes: bytes, filename: str, user_id: str) -> str:
    """Save uploaded image to storage and return path."""
    # Create directory structure: uploads/images/{user_id}/{date}/
    from datetime import datetime
    date_str = datetime.utcnow().strftime("%Y/%m/%d")
    upload_dir = Path("backend/uploads/images") / str(user_id) / date_str
    upload_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate unique filename
    ext = Path(filename).suffix.lower()
    if not ext:
        ext = ".jpg"
    unique_name = f"{uuid.uuid4().hex}{ext}"
    file_path = upload_dir / unique_name
    
    # Save file
    with open(file_path, "wb") as f:
        f.write(file_content)
    
    return str(file_path.relative_to(Path("backend")))


# FastAPI endpoint models
class AnalyzeImageRequest(BaseModel):
    crop_hint: Optional[str] = None
    field_id: Optional[str] = None

class AnalyzeImageResponse(BaseModel):
    predictions: List[Dict[str, Any]]
    image_quality: str
    crop_detected: Optional[str] = None
    confidence: float
    processing_time_ms: int
    model_version: str
    warnings: List[str]