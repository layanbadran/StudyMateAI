"""FastAPI entry point: the HTTP endpoints the React app talks to."""
import re
from pathlib import Path

from fastapi import Depends, FastAPI, File, Header, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from app.config import settings
from app.services import rag, vector_store
from app.services.embeddings import EmbeddingError
from app.services.llm import LLMError, LLMNotConfigured
from app.services.pdf_service import PDFError

app = FastAPI(title="StudyMate AI")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin],
    allow_methods=["*"],
    allow_headers=["*"],
)

UUID_RE = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$", re.IGNORECASE
)


def get_session_id(x_session_id: str = Header(default="")) -> str:
    """Each browser sends a random ID. It decides which private collection is used.

    NOTE: this isolates users from each other, but it is not a login system.
    Anyone who knows an ID could use it, so keep this MVP for personal / local use.
    """
    if not UUID_RE.match(x_session_id):
        raise HTTPException(status_code=400, detail="Missing or invalid session ID.")
    return x_session_id.lower()


class ChatRequest(BaseModel):
    question: str = Field(min_length=1, max_length=2000)


@app.get("/api/health")
def health():
    return {
        "status": "ok",
        "anthropic_configured": bool(settings.anthropic_api_key),
        "max_upload_mb": settings.max_upload_mb,
    }


@app.get("/api/documents")
def list_documents(session_id: str = Depends(get_session_id)):
    return {"documents": vector_store.list_documents(session_id)}


@app.post("/api/documents", status_code=201)
def upload_document(
    file: UploadFile = File(...), session_id: str = Depends(get_session_id)
):
    filename = Path(file.filename or "").name
    if not filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=415, detail="Only PDF files are supported.")

    data = file.file.read(settings.max_upload_bytes + 1)
    if len(data) > settings.max_upload_bytes:
        raise HTTPException(
            status_code=413,
            detail=f"This file is larger than the {settings.max_upload_mb} MB limit.",
        )
    if not data.startswith(b"%PDF-"):  # check the real content, not just the name
        raise HTTPException(status_code=415, detail="This file is not a valid PDF.")

    try:
        return rag.ingest_pdf(session_id, filename, data)
    except PDFError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    except EmbeddingError as exc:
        raise HTTPException(status_code=503, detail=str(exc))


@app.delete("/api/documents/{doc_id}")
def delete_document(doc_id: str, session_id: str = Depends(get_session_id)):
    if not vector_store.delete_document(session_id, doc_id):
        raise HTTPException(status_code=404, detail="Document not found.")
    return {"deleted": doc_id}


@app.post("/api/chat")
def chat(body: ChatRequest, session_id: str = Depends(get_session_id)):
    # Fail early and honestly if the key is missing.
    if not settings.anthropic_api_key:
        raise HTTPException(
            status_code=503,
            detail="The server has no ANTHROPIC_API_KEY. Add it to backend/.env and restart the backend.",
        )
    question = body.question.strip()
    if not question:
        raise HTTPException(status_code=400, detail="Please type a question.")
    if not vector_store.list_documents(session_id):
        raise HTTPException(
            status_code=400, detail="Upload at least one PDF before asking questions."
        )

    try:
        return rag.answer_question(session_id, question)
    except LLMNotConfigured as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    except LLMError as exc:
        raise HTTPException(status_code=502, detail=str(exc))
    except EmbeddingError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
