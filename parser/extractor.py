import os
import fitz
import pdfplumber
from docx import Document
from docx.document import Document as DocxDocument
from docx.table import Table
from docx.text.paragraph import Paragraph

from docx.oxml.text.paragraph import CT_P
from docx.oxml.table import CT_Tbl
import re

BAD_CHARS = {
    "Ä", "Å", "Ç", "Ñ", "¿", "£", "¡",
    "°", "±", "Þ", "Æ", "¤"
}


def text_quality(text: str) -> int:
    """
    Chấm điểm chất lượng text.
    100 = rất tốt
    0 = rất tệ
    """

    if not text:
        return 0

    score = 100

    bad = sum(text.count(c) for c in BAD_CHARS)

    score -= bad * 5

    letters = sum(c.isalpha() for c in text)

    if letters < 100:
        score -= 40

    return max(score, 0)


# ---------------- PDF ---------------- #

def extract_pdf_blocks(file_path: str) -> str:
    """
    Đọc PDF bằng PyMuPDF.
    Hỗ trợ CV 2 cột.
    """

    doc = fitz.open(file_path)

    pages_text = []

    for page in doc:

        blocks = page.get_text("blocks")

        page_width = page.rect.width

        mid = page_width / 2

        left = []
        right = []

        for block in blocks:

            text = block[4].strip()

            if not text:
                continue

            center_x = (block[0] + block[2]) / 2

            if center_x < mid:
                left.append(block)

            else:
                right.append(block)

        left.sort(key=lambda b: b[1])

        right.sort(key=lambda b: b[1])

        page_text = []

        page_text.extend(
            block[4].strip()
            for block in left
        )

        page_text.extend(
            block[4].strip()
            for block in right
        )

        pages_text.append(
            "\n\n".join(page_text)
        )

    doc.close()

    return "\n\n".join(pages_text).strip()


def extract_pdf_pdfplumber(file_path: str) -> str:

    texts = []

    with pdfplumber.open(file_path) as pdf:

        for page in pdf.pages:

            txt = page.extract_text()

            if txt:
                texts.append(txt)

    return "\n".join(texts).strip()


def extract_pdf(file_path: str) -> str:
    """
    Tự động chọn kết quả đọc PDF tốt nhất.
    """

    pymupdf_text = extract_pdf_blocks(file_path)

    score1 = text_quality(pymupdf_text)

    if score1 >= 85:
        print(f"[PDF] PyMuPDF selected (score={score1})")
        return pymupdf_text

    print(
        f"[PDF] PyMuPDF score={score1}. Trying pdfplumber..."
    )

    plumber_text = extract_pdf_pdfplumber(file_path)

    score2 = text_quality(plumber_text)

    if score2 > score1:
        print(f"[PDF] pdfplumber selected (score={score2})")
        return plumber_text

    print(f"[PDF] PyMuPDF kept (score={score1})")

    return pymupdf_text


# ---------------- DOCX ---------------- #

def iter_block_items(parent):
    """
    Duyệt toàn bộ document theo đúng thứ tự xuất hiện.
    Bao gồm Paragraph và Table.
    """

    if isinstance(parent, DocxDocument):
        parent_elm = parent.element.body
    else:
        parent_elm = parent._element

    for child in parent_elm.iterchildren():

        if isinstance(child, CT_P):
            yield Paragraph(child, parent)

        elif isinstance(child, CT_Tbl):
            yield Table(child, parent)

def extract_table(table: Table) -> str:

    rows = []

    for row in table.rows:

        cols = []

        for cell in row.cells:

            text = cell.text.strip()

            if text:
                cols.append(text)

        if cols:
            rows.append(" | ".join(cols))

    return "\n".join(rows)

def clean_text(text: str):

    text = text.replace("\xa0", " ")

    text = re.sub(r"[ \t]+", " ", text)

    text = re.sub(r"\n{3,}", "\n\n", text)

    return text.strip()

def extract_docx(file_path: str) -> str:

    doc = Document(file_path)

    blocks = []

    for block in iter_block_items(doc):

        if isinstance(block, Paragraph):

            text = block.text.strip()

            if text:

                blocks.append(text)

        elif isinstance(block, Table):

            text = extract_table(block)

            if text:

                blocks.append(text)

    return clean_text("\n\n".join(blocks))

# ---------------- AUTO ---------------- #

def extract_text(file_path: str) -> str:

    extension = os.path.splitext(file_path)[1].lower()

    if extension == ".pdf":
        return extract_pdf(file_path)

    elif extension == ".docx":
        return extract_docx(file_path)

    raise Exception("Unsupported file type")
