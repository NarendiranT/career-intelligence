from __future__ import annotations

from pathlib import Path

from pypdf import PdfReader


def extract_text(path: str | Path) -> str:
    file_path = Path(path)
    if not file_path.exists():
        raise FileNotFoundError(f"Document not found: {file_path}")
    suffix = file_path.suffix.lower()
    if suffix == ".txt":
        return file_path.read_text(encoding="utf-8", errors="replace")
    if suffix == ".pdf":
        reader = PdfReader(str(file_path))
        pages = [page.extract_text() or "" for page in reader.pages]
        return "\n".join(pages).strip()
    if suffix == ".docx":
        from docx import Document as DocxDocument

        doc = DocxDocument(str(file_path))
        return "\n".join(p.text for p in doc.paragraphs).strip()
    if suffix == ".doc":
        raise ValueError("Legacy .doc files are not supported; convert to .docx or PDF")
    return file_path.read_text(encoding="utf-8", errors="replace")
