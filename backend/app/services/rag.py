"""The whole RAG pipeline in two functions: ingest_pdf() and answer_question()."""
import re
import uuid

from app.config import settings
from app.services import embeddings, llm, vector_store
from app.services.chunking import chunk_pages
from app.services.pdf_service import extract_pages

NOT_ENOUGH_INFO = (
    "I couldn't find enough information about this in your uploaded documents, "
    "so I won't guess. Try rephrasing the question or upload the notes that cover it."
)


def ingest_pdf(session_id: str, filename: str, data: bytes) -> dict:
    extracted = extract_pages(data)  # PDF -> text per page
    chunks = chunk_pages(extracted.pages, settings.chunk_size, settings.chunk_overlap)
    vectors = embeddings.embed_texts([c.text for c in chunks])  # text -> vectors
    doc_id = uuid.uuid4().hex
    vector_store.add_document(  # vectors + text + filename/page -> ChromaDB
        session_id, doc_id, filename, extracted.total_pages, chunks, vectors
    )
    return {
        "doc_id": doc_id,
        "filename": filename,
        "pages": extracted.total_pages,
        "chunks": len(chunks),
    }


def answer_question(session_id: str, question: str) -> dict:
    query_vector = embeddings.embed_texts([question])[0]  # question -> vector
    hits = vector_store.search(session_id, query_vector, settings.top_k)  # similarity search
    hits = [h for h in hits if h["distance"] <= settings.max_distance]  # drop weak matches

    if not hits:
        return {"answer": NOT_ENOUGH_INFO, "sources": [], "grounded": False}

    sources = [
        {
            "id": i,
            "filename": h["filename"],
            "page": h["page"],
            "text": h["text"],
            "score": round(1 - h["distance"], 3),
        }
        for i, h in enumerate(hits, start=1)
    ]

    answer = llm.generate_answer(question, sources)  # context augmentation + Claude

    if not answer or answer.startswith(llm.INSUFFICIENT):
        return {"answer": NOT_ENOUGH_INFO, "sources": [], "grounded": False}

    # Show only the sources Claude actually cited (fall back to all retrieved ones).
    cited = {int(n) for n in re.findall(r"\[(\d+)\]", answer)}
    shown = [s for s in sources if s["id"] in cited] or sources

    return {
        "answer": answer,
        "sources": [
            {
                "id": s["id"],
                "filename": s["filename"],
                "page": s["page"],
                "excerpt": s["text"][:500],
                "score": s["score"],
            }
            for s in shown
        ],
        "grounded": True,
    }
