from backend.services.ocr_services import extract_text_from_images

images = [
    "backend/uploads/images/page_1.png",
    "backend/uploads/images/page_2.png"
]

print("Before OCR")

result = extract_text_from_images(images)

print("OCR Finished")
print(result)