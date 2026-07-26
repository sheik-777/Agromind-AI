import gc
import logging
import os
import tempfile

os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")

import easyocr
import numpy as np
from PIL import Image, ImageOps

logger = logging.getLogger("ocr_services")

_reader = None

MAX_OCR_WIDTH = 1500


def _get_reader() -> easyocr.Reader:
    """Lazy-initialize EasyOCR reader on first use."""
    global _reader
    if _reader is None:
        logger.info("Initializing EasyOCR reader (CPU mode)...")
        _reader = easyocr.Reader(["en"], gpu=False)
        logger.info("EasyOCR reader initialized.")
    return _reader


def _preprocess_image(image_path: str) -> str:
    """Apply minimal preprocessing to improve OCR accuracy.

    Converts to grayscale and applies simple thresholding. Avoids
    creating multiple intermediate copies to keep memory usage low.

    Args:
        image_path: Path to the original image.

    Returns:
        Path to the preprocessed temporary image.
    """
    img = Image.open(image_path)

    try:
        if img.width > MAX_OCR_WIDTH:
            ratio = MAX_OCR_WIDTH / img.width
            img = img.resize((MAX_OCR_WIDTH, int(img.height * ratio)), Image.LANCZOS)

        img = ImageOps.grayscale(img)

        img = ImageOps.autocontrast(img, cutoff=1)

        # Save to temp file
        tmp = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
        tmp.close()
        img.save(tmp.name)
    finally:
        img.close()

    return tmp.name


def extract_text_from_images(image_paths: list[str]) -> list[str]:
    """Extract text from a list of image paths using EasyOCR.

    Args:
        image_paths: List of image file paths.

    Returns:
        A list where each element contains the extracted text from one page.
    """
    reader = _get_reader()

    extracted_pages: list[str] = []

    for image_path in image_paths:
        logger.info("Processing image: %s", image_path)

        preprocessed_path = None
        try:
            preprocessed_path = _preprocess_image(image_path)

            result = reader.readtext(
                preprocessed_path,
                detail=0,
                paragraph=True,
            )

            page_text = "\n".join(result)
            extracted_pages.append(page_text)
            logger.info("OCR returned %d characters", len(page_text))

        except Exception as e:
            logger.exception("OCR failed for %s", image_path)
            extracted_pages.append("")

        finally:
            if preprocessed_path and os.path.exists(preprocessed_path):
                try:
                    os.remove(preprocessed_path)
                except OSError:
                    pass
            gc.collect()

    return extracted_pages
