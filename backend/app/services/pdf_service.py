"""Step 1 of the pipeline: get text out of a PDF, page by page (PyMuPDF)."""
from dataclasses import dataclass

import pymupdf  # PyMuPDF


class PDFError(Exception):
    """Raised with a user-friendly message when a PDF can't be used."""


@dataclass
class PageText:
    page: int  # 1-based, matches what the student sees in their PDF viewer
    text: str


@dataclass
class ExtractedPDF:
    total_pages: int
    pages: list[PageText]  # only pages that contain text


def extract_pages(data: bytes) -> ExtractedPDF:
    try:
        doc = pymupdf.open(stream=data, filetype="pdf")
    except Exception as exc:
        raise PDFError(
            "This file could not be opened as a PDF. It may be damaged."
        ) from exc

    with doc:
        if doc.needs_pass:
            raise PDFError(
                "This PDF is password-protected. Remove the password and upload it again."
            )
        pages: list[PageText] = []
        for number, page in enumerate(doc, start=1):
            text = page.get_text("text").strip()
            if text:
                pages.append(PageText(page=number, text=text))
        total = doc.page_count

    if not pages:
        raise PDFError(
            "No selectable text was found in this PDF. It may be a scan or a set of images. "
            "StudyMate AI can't read scanned pages yet (no OCR)."
        )
    return ExtractedPDF(total_pages=total, pages=pages)
