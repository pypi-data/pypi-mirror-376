import pypdfium2 as pdfium

def extract_text_from_pdf(pdf_path: str) -> str:
    """
    Extracts all text from a PDF file and returns it as a single string.

    Args:
        pdf_path: The path to the PDF file.

    Returns:
        A string containing all the text extracted from the PDF.
    """
    pdf = pdfium.PdfDocument(pdf_path)
    text = ""
    for page_index in range(len(pdf)):
        page = pdf.get_page(page_index)
        text += page.get_text_bounded()
        text += "\n"  # Add a newline between pages for clarity
    return text