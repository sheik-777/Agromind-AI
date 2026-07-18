from fastapi import APIRouter, UploadFile, File
import os

from backend.services.pdf_service import convert_pdf_to_images
from backend.services.ocr_services import extract_text_from_images
from backend.services.parser_service import parse_soil_report

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

    parsed_report = []

    for i, page in enumerate(ocr_text):
        print("=" * 60)
        print(f"PAGE {i + 1}")
        print("=" * 60)
        print("Type:", type(page))
        print("First 300 characters:")
        print(str(page)[:300])

        try:
            result = parse_soil_report(page)
            print("✅ Parser completed successfully.")
            parsed_report.append(result)

        except Exception as e:
            import traceback
            traceback.print_exc()

            return {
                "success": False,
                "error": str(e)
            }

    return {
        "success": True,
        "message": "Soil report uploaded successfully.",
        "filename": file.filename,
        "pages_converted": len(image_paths),
        "generated_images": image_paths,
        "extracted_text": ocr_text,
        "parsed_report": parsed_report
    }