"""Step 4: store and search vectors in ChromaDB.

Isolation: every browser session gets its OWN Chroma collection, so one user's search can
never touch another user's chunks. Each chunk keeps its filename and page as metadata.
"""
import re
from datetime import datetime, timezone

import chromadb
from chromadb.config import Settings as ChromaSettings

from app.config import settings
from app.services.chunking import Chunk

_client = None


def _get_client():
    global _client
    if _client is None:
        _client = chromadb.PersistentClient(
            path=settings.chroma_dir,
            settings=ChromaSettings(anonymized_telemetry=False),
        )
    return _client


def _collection(session_id: str):
    safe = re.sub(r"[^a-zA-Z0-9]", "", session_id)
    return _get_client().get_or_create_collection(
        name=f"user_{safe}",
        metadata={"hnsw:space": "cosine"},  # cosine distance: 0 = same meaning
    )


def add_document(
    session_id: str,
    doc_id: str,
    filename: str,
    total_pages: int,
    chunks: list[Chunk],
    embeddings: list[list[float]],
) -> None:
    uploaded_at = datetime.now(timezone.utc).isoformat()
    _collection(session_id).add(
        ids=[f"{doc_id}-{c.index}" for c in chunks],
        embeddings=embeddings,
        documents=[c.text for c in chunks],
        metadatas=[
            {
                "doc_id": doc_id,
                "filename": filename,
                "page": c.page,
                "total_pages": total_pages,
                "uploaded_at": uploaded_at,
            }
            for c in chunks
        ],
    )


def list_documents(session_id: str) -> list[dict]:
    data = _collection(session_id).get(include=["metadatas"])
    docs: dict[str, dict] = {}
    for meta in data["metadatas"] or []:
        entry = docs.setdefault(
            meta["doc_id"],
            {
                "doc_id": meta["doc_id"],
                "filename": meta["filename"],
                "pages": meta["total_pages"],
                "chunks": 0,
                "uploaded_at": meta["uploaded_at"],
            },
        )
        entry["chunks"] += 1
    return sorted(docs.values(), key=lambda d: d["uploaded_at"], reverse=True)


def delete_document(session_id: str, doc_id: str) -> bool:
    col = _collection(session_id)
    found = col.get(where={"doc_id": doc_id}, limit=1, include=[])
    if not found["ids"]:
        return False
    col.delete(where={"doc_id": doc_id})
    return True


def search(session_id: str, query_embedding: list[float], k: int) -> list[dict]:
    col = _collection(session_id)
    total = col.count()
    if total == 0:
        return []
    result = col.query(
        query_embeddings=[query_embedding],
        n_results=min(k, total),
        include=["documents", "metadatas", "distances"],
    )
    hits = []
    for text, meta, dist in zip(
        result["documents"][0], result["metadatas"][0], result["distances"][0]
    ):
        hits.append(
            {
                "text": text,
                "filename": meta["filename"],
                "page": meta["page"],
                "distance": float(dist),
            }
        )
    return hits
