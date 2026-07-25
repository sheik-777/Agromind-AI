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
    print("===== STEP 1: Upload endpoint reached =====", flush=True)

    file_path = os.path.join(UPLOAD_FOLDER, file.filename)

    print(f"Saving file to: {file_path}", flush=True)

    with open(file_path, "wb") as buffer:
        buffer.write(await file.read())

    print("===== STEP 2: PDF saved successfully =====", flush=True)

    image_paths = convert_pdf_to_images(
        pdf_path=file_path,
        output_folder="backend/uploads/images"
    )

    print("===== STEP 3: PDF converted to images =====", flush=True)
    print(image_paths, flush=True)

    # ===================== STEP 4 =====================
    print("===== STEP 4: Starting OCR =====", flush=True)

    extracted_text = extract_text_from_images(image_paths)

    print("===== STEP 5: OCR completed successfully =====", flush=True)

    # ===================== STEP 6 =====================
    print("===== STEP 6: Starting parser =====", flush=True)

    parsed_report = []

    for i, page in enumerate(extracted_text):

        print("=" * 60)
        print(f"PAGE {i + 1}")
        print("=" * 60)
        print("Type:", type(page))
        print("=" * 80)
        print(f"RAW OCR TEXT - PAGE {i + 1}")
        print("=" * 80)
        print(page)
        print("=" * 80)

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

    print("===== STEP 7: All pages parsed successfully =====", flush=True)

    print("===== STEP 8: Returning response =====", flush=True)

    return {
        "success": True,
        "message": "Soil report uploaded successfully.",
        "filename": file.filename,
        "pages_converted": len(image_paths),
        "generated_images": image_paths,
        "parsed_report": parsed_report
    }