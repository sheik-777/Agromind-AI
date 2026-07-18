from paddleocr import PaddleOCR

# Load the OCR model once when the backend starts
ocr = PaddleOCR(
    lang="en",
    enable_mkldnn=False
)

def extract_text_from_images(image_paths):
    """
    Reads text from one or more images.

    Parameters:
        image_paths (list): List of image file paths.

    Returns:
        list: Extracted text for each page.
    """

    extracted_pages = []

    for image_path in image_paths:

        result = ocr.predict(image_path)
        
        print(result)

        page_text = ""

        for block in result:

            if "rec_texts" in block:

                page_text += "\n".join(block["rec_texts"])

        extracted_pages.append(page_text)

    return extracted_pages