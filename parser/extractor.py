import fitz
from docx import Document
import os


def extract_pdf(file_path: str) -> str:
    """
    Đọc toàn bộ text từ file PDF.
    """

    document = fitz.open(file_path)

    text = ""

    for page in document:
        text += page.get_text()

    document.close()

    return text.strip()


def extract_docx(file_path: str) -> str:
    """
    Đọc toàn bộ text từ file DOCX.
    """

    doc = Document(file_path)

    paragraphs = []

    for paragraph in doc.paragraphs:
        paragraphs.append(paragraph.text)

    return "\n".join(paragraphs).strip()


def extract_text(file_path: str) -> str:
    """
    Tự động chọn hàm đọc theo định dạng file.
    """

    extension = os.path.splitext(file_path)[1].lower()

    if extension == ".pdf":
        return extract_pdf(file_path)

    elif extension == ".docx":
        return extract_docx(file_path)

    else:
        raise Exception("Unsupported file type")
    
    