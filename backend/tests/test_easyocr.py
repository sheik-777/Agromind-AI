from pathlib import Path
import easyocr

reader = easyocr.Reader(['en'])

image_path = Path(__file__).parent.parent / "uploads" / "images" / "page_1.png"

result = reader.readtext(str(image_path), detail=0)

print("\nExtracted Text:")
print("-" * 40)

for line in result:
    print(line)