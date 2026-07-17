from fastapi import APIRouter, UploadFile, File
import os
from backend.services.pdf_service import convert_pdf_to_images
from backend.services.ocr_services import extract_text_from_images

router = APIRouter(
    prefix="/soil",
    tags=["Soil Analysis"]
)

UPLOAD_FOLDER = "backend/uploads/pdfs"

os.makedirs(UPLOAD_FOLDER, exist_ok=True)


@router.post("/upload")
async def upload_soil_report(file: UploadFile = File(...)):
    file_path = os.path.join(UPLOAD_FOLDER, file.filename)

    with open(file_path, "wb") as buffer:
        buffer.write(await file.read())

    image_paths = convert_pdf_to_images(
        pdf_path=file_path,
        output_folder="backend/uploads/images"
    )
    ocr_text = extract_text_from_images(image_paths)

    return {
        "message": "Soil report uploaded successfully.",
        "filename": file.filename,
        "pages_converted": len(image_paths),
        "generated_images": image_paths,
        "extracted_text": ocr_text
    }