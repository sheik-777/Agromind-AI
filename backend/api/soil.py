import logging
import os
import shutil
import tempfile
import traceback
import uuid

from fastapi import APIRouter, UploadFile, File

from backend.services.pdf_service import convert_pdf_to_images
from backend.services.ocr_services import extract_text_from_images
from backend.services.parser_service import parse_soil_report
from backend.services.recommendation_services import recommend_crops

logger = logging.getLogger("soil_api")

router = APIRouter(
    prefix="/soil",
    tags=["Soil Analysis"],
)

UPLOAD_FOLDER = "backend/uploads/pdfs"
DATASET_PATH = "backend/datasets/agromind_master_dataset_full (1).csv"
MAX_FILE_SIZE_MB = 20
MAX_PAGES = 50

os.makedirs(UPLOAD_FOLDER, exist_ok=True)


def _sanitize_filename(filename: str) -> str:
    """Strip directory components and limit length to prevent path traversal."""
    name = os.path.basename(filename or "upload.pdf")
    name = name.replace("\x00", "")
    base, ext = os.path.splitext(name)
    if ext.lower() != ".pdf":
        ext = ".pdf"
    return f"{base[:80]}{ext}"


@router.post("/upload")
def upload_soil_report(file: UploadFile = File(...)):
    request_id = uuid.uuid4().hex[:12]
    logger.info("[%s] Upload endpoint reached: %s", request_id, file.filename)

    safe_name = _sanitize_filename(file.filename)
    file_path = os.path.join(UPLOAD_FOLDER, f"{request_id}_{safe_name}")

    contents = file.file.read()
    with open(file_path, "wb") as buffer:
        buffer.write(contents)

    file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
    if file_size_mb > MAX_FILE_SIZE_MB:
        os.remove(file_path)
        return {"success": False, "error": f"File exceeds {MAX_FILE_SIZE_MB}MB limit."}

    logger.info("[%s] PDF saved: %s (%.1f MB)", request_id, file_path, file_size_mb)

    image_dir = os.path.join(tempfile.gettempdir(), f"agromind_ocr_{request_id}")

    try:
        image_paths = convert_pdf_to_images(pdf_path=file_path, output_folder=image_dir)

        if not image_paths:
            return {"success": False, "error": "PDF produced no pages."}

        if len(image_paths) > MAX_PAGES:
            return {"success": False, "error": f"PDF has {len(image_paths)} pages, max is {MAX_PAGES}."}

        logger.info("[%s] PDF converted to %d images", request_id, len(image_paths))

        extracted_text = extract_text_from_images(image_paths)

        logger.info("[%s] OCR completed", request_id)

        parsed_report = []

        for i, page in enumerate(extracted_text):
            logger.debug("[%s] PAGE %d OCR length: %d", request_id, i + 1, len(page))

            try:
                result = parse_soil_report(page)

                recommendations = recommend_crops(result, DATASET_PATH)
                result["crop_recommendations"] = recommendations

                parsed_report.append(result)

            except Exception as e:
                logger.warning("[%s] Page %d failed: %s", request_id, i + 1, e)
                parsed_report.append({
                    "metadata": {},
                    "laboratory_analysis": {"samples": [], "unknown_parameters": []},
                    "interpretation": [],
                    "recommendations": {"lime_to_apply": "", "fertilizer_to_apply": "", "cultural_and_management_tips": "", "references_and_resources": ""},
                    "warnings": [f"Page processing failed: {e}"],
                    "crop_recommendations": [],
                })

        if not parsed_report:
            return {"success": False, "error": "No pages could be processed."}

        logger.info("[%s] All pages processed successfully", request_id)

        return {
            "success": True,
            "message": "Soil report uploaded successfully.",
            "filename": file.filename,
            "pages_converted": len(image_paths),
            "parsed_report": parsed_report,
        }

    finally:
        # Clean up generated images
        if os.path.exists(image_dir):
            shutil.rmtree(image_dir, ignore_errors=True)
        # Clean up uploaded PDF
        if os.path.exists(file_path):
            os.remove(file_path)
