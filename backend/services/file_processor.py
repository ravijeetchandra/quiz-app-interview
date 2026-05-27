import asyncio
import os
import tempfile
from typing import Optional
import fitz
import docx


ALLOWED_EXTENSIONS = {".pdf", ".doc", ".docx", ".txt"}


def validate_file_extension(filename: str) -> bool:
    ext = os.path.splitext(filename)[1].lower()
    return ext in ALLOWED_EXTENSIONS


def extract_text_from_pdf(file_path: str) -> str:
    text = ""
    doc = fitz.open(file_path)
    for page in doc:
        text += page.get_text()
    doc.close()

    if not text.strip():
        try:
            from pypdf import PdfReader
            reader = PdfReader(file_path)
            text = "\n".join(page.extract_text() or "" for page in reader.pages)
        except Exception:
            pass

    return text


def extract_text_from_docx(file_path: str) -> str:
    doc = docx.Document(file_path)
    return "\n".join([p.text for p in doc.paragraphs])


def extract_text_from_txt(file_path: str) -> str:
    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        return f.read()


async def process_upload(file_content: bytes, filename: str) -> str:
    ext = os.path.splitext(filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise ValueError(f"Unsupported file type: {ext}")

    def _process():
        with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp:
            tmp.write(file_content)
            tmp_path = tmp.name

        try:
            if ext == ".pdf":
                return extract_text_from_pdf(tmp_path)
            elif ext in (".doc", ".docx"):
                return extract_text_from_docx(tmp_path)
            else:
                return extract_text_from_txt(tmp_path)
        finally:
            os.unlink(tmp_path)

    return await asyncio.to_thread(_process)


def get_document_preview(text: str, max_chars: int = 2000) -> str:
    return text[:max_chars]
