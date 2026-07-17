from backend.services.ocr_services import extract_text_from_images

image_paths = [
    "backend/uploads/images/page_1.png"
]

result = extract_text_from_images(image_paths)

print("\n========== OCR RESULT ==========\n")

for page in result:
    print(page)