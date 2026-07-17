import os
import fitz  # PyMuPDF


def convert_pdf_to_images(pdf_path: str, output_folder: str):
    """
    Convert every page of a PDF into PNG images.

    Args:
        pdf_path: Path to the uploaded PDF.
        output_folder: Folder where images will be saved.

    Returns:
        A list containing the paths of all generated images.
    """

    # Create the output folder if it doesn't exist
    os.makedirs(output_folder, exist_ok=True)

    # Open the PDF
    pdf_document = fitz.open(pdf_path)

    image_paths = []

    # Convert each page
    for page_number in range(len(pdf_document)):
        page = pdf_document.load_page(page_number)

        pix = page.get_pixmap(dpi=300)

        image_path = os.path.join(
            output_folder,
            f"page_{page_number + 1}.png"
        )

        pix.save(image_path)

        image_paths.append(image_path)

    pdf_document.close()

    return image_paths