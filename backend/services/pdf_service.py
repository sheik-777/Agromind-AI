import logging
import os

import fitz  # PyMuPDF

logger = logging.getLogger("pdf_service")

TARGET_DPI = 200


def convert_pdf_to_images(pdf_path: str, output_folder: str) -> list[str]:
    """Convert every page of a PDF into PNG images at 200 DPI.

    200 DPI is sufficient for document OCR while keeping memory usage
    manageable (~5.5 MB per A4 page vs ~13 MB at 300 DPI).

    Args:
        pdf_path: Path to the uploaded PDF.
        output_folder: Folder where images will be saved.

    Returns:
        A list containing the paths of all generated images.
    """
    os.makedirs(output_folder, exist_ok=True)

    image_paths: list[str] = []

    with fitz.open(pdf_path) as pdf_document:
        for page_number in range(len(pdf_document)):
            page = pdf_document.load_page(page_number)

            pix = page.get_pixmap(dpi=TARGET_DPI)

            image_path = os.path.join(output_folder, f"page_{page_number + 1}.png")
            pix.save(image_path)
            image_paths.append(image_path)

    logger.info("Converted %d pages to images at %d DPI", len(image_paths), TARGET_DPI)

    return image_paths
