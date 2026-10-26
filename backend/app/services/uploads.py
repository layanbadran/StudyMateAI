"""Checks an uploaded file and runs it through the pipeline (used by the Streamlit app)."""
from pathlib import Path

from app.config import settings
from app.services import rag


class UploadRejected(Exception):
    """The file is not acceptable. The message is safe to show to the user."""


def ingest_upload(session_id: str, filename: str, data: bytes) -> dict:
    name = Path(filename or "").name
    if not name.lower().endswith(".pdf"):
        raise UploadRejected("Only PDF files are supported.")
    if len(data) > settings.max_upload_bytes:
        raise UploadRejected(f"This file is larger than the {settings.max_upload_mb} MB limit.")
    if not data.startswith(b"%PDF-"):  # check the real content, not just the name
        raise UploadRejected("This file is not a valid PDF.")
    return rag.ingest_pdf(session_id, name, data)