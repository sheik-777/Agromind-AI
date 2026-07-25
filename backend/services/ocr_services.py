import easyocr

# Initialize EasyOCR Reader once when the application starts
# Using CPU because CUDA is not available on your system.
reader = easyocr.Reader(['en'])

def extract_text_from_images(image_paths):
    """
    Extract text from a list of image paths using EasyOCR.

    Parameters:
        image_paths (list): List of image file paths.

    Returns:
        list: A list where each element contains the extracted text
              from one image/page.
    """

    print("Entered extract_text_from_images()", flush=True)

    extracted_pages = []

    for image_path in image_paths:

        print(f"Processing image: {image_path}", flush=True)

        try:
            # detail=0 returns only the recognized text
            result = reader.readtext(image_path, detail=0)

            print("OCR returned successfully", flush=True)

            page_text = "\n".join(result)

            extracted_pages.append(page_text)

        except Exception as e:
            print(f"OCR Error: {e}", flush=True)
            extracted_pages.append("")

    print("Leaving extract_text_from_images()", flush=True)

    return extracted_pages