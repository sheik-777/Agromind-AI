from paddleocr import PaddleOCR
import os

print("Creating model...")

ocr = PaddleOCR(
    lang="en",
    enable_mkldnn=False
)

print("Model created.")

image = "backend/uploads/images/page_1.png"

print("Image exists:", os.path.exists(image))

print("Calling predict...")

result = ocr.predict(image)

print("Prediction completed!")

print(result)