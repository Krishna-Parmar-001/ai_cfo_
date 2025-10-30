# utils/ocr_utils.py
from pdf2image import convert_from_bytes
import pytesseract
import asyncio

async def ocr_pdf_to_text(pdf_bytes: bytes) -> str:
    """
    Convert PDF bytes to images and run pytesseract on each page.
    Runs blocking operations in threads via asyncio.to_thread
    """
    # convert to images (blocking) in thread
    images = await asyncio.to_thread(convert_from_bytes, pdf_bytes)
    texts = []
    for img in images:
        # run OCR in thread per page
        page_text = await asyncio.to_thread(pytesseract.image_to_string, img)
        texts.append(page_text)
    return "\n".join(texts)
