"""Tests for chunking and the HTTP/RAG flow.

IMPORTANT: these tests replace the embedding model and Claude with small fakes, so they
run offline. They prove the pipeline wiring (upload, chunks, Chroma, citations, deletion,
isolation, error handling). They do NOT prove answer quality from the real models.
"""
import hashlib
import math
import re
import uuid

import pymupdf
import pytest
from fastapi.testclient import TestClient

from app.services import embeddings, llm, vector_store
from app.services.chunking import split_text


def fake_embed(texts):
    """Deterministic bag-of-words vectors (shared words => similar vectors)."""
    out = []
    for t in texts:
        v = [0.0] * 256
        for w in re.findall(r"\w+", t.lower()):
            v[int(hashlib.md5(w.encode()).hexdigest(), 16) % 256] += 1.0
        norm = math.sqrt(sum(x * x for x in v)) or 1.0
        out.append([x / norm for x in v])
    return out


def make_pdf(pages: list[str]) -> bytes:
    doc = pymupdf.open()
    for text in pages:
        page = doc.new_page()
        page.insert_textbox(pymupdf.Rect(50, 50, 550, 780), text, fontsize=11)
    data = doc.tobytes()
    doc.close()
    return data


@pytest.fixture()
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("CHROMA_DIR", str(tmp_path / "chroma"))
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    monkeypatch.setenv("MAX_DISTANCE", "0.9")
    monkeypatch.setattr(vector_store, "_client", None)
    monkeypatch.setattr(embeddings, "embed_texts", fake_embed)
    monkeypatch.setattr(
        llm, "generate_answer", lambda q, sources: "Entropy measures disorder [1]."
    )
    from app.main import app

    return TestClient(app)


def headers(session=None):
    return {"X-Session-ID": session or str(uuid.uuid4())}


# ---------- chunking ----------
def test_chunks_overlap_and_cover_text():
    text = " ".join(f"Sentence number {i} talks about thermodynamics." for i in range(80))
    chunks = split_text(text, chunk_size=300, overlap=60)
    assert len(chunks) > 3
    assert all(len(c) <= 300 for c in chunks)
    for a, b in zip(chunks, chunks[1:]):
        assert b[:25] in a  # the start of the next chunk appears at the end of the previous
    assert chunks[0].startswith("Sentence number 0")
    assert chunks[-1].endswith("thermodynamics.")


def test_chunking_empty_and_short():
    assert split_text("   \n ") == []
    assert split_text("Short note.", 1000, 200) == ["Short note."]


# ---------- API ----------
def test_health_reports_missing_key(client, monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY")
    assert client.get("/api/health").json()["anthropic_configured"] is False


def test_session_header_required(client):
    assert client.get("/api/documents").status_code == 400


def test_upload_rejects_bad_files(client):
    h = headers()
    r = client.post("/api/documents", files={"file": ("a.txt", b"hello", "text/plain")}, headers=h)
    assert r.status_code == 415
    r = client.post("/api/documents", files={"file": ("fake.pdf", b"not a pdf", "application/pdf")}, headers=h)
    assert r.status_code == 415
    r = client.post("/api/documents", files={"file": ("broken.pdf", b"%PDF-1.4 garbage", "application/pdf")}, headers=h)
    assert r.status_code == 422


def test_upload_too_large(client, monkeypatch):
    monkeypatch.setenv("MAX_UPLOAD_MB", "1")
    big = b"%PDF-" + b"0" * (1024 * 1024 + 10)
    r = client.post("/api/documents", files={"file": ("big.pdf", big, "application/pdf")}, headers=headers())
    assert r.status_code == 413


def test_empty_pdf_is_rejected(client):
    r = client.post("/api/documents", files={"file": ("empty.pdf", make_pdf([""]), "application/pdf")}, headers=headers())
    assert r.status_code == 422
    assert "No selectable text" in r.json()["detail"]


def test_full_flow_upload_ask_cite_delete(client):
    h = headers()
    pdf = make_pdf(
        ["Introduction to the course and its grading policy.",
         "Entropy is a measure of disorder in a thermodynamic system. Entropy always increases."]
    )
    r = client.post("/api/documents", files={"file": ("Thermo-L4.pdf", pdf, "application/pdf")}, headers=h)
    assert r.status_code == 201, r.text
    doc = r.json()
    assert doc["pages"] == 2 and doc["chunks"] >= 2

    assert [d["filename"] for d in client.get("/api/documents", headers=h).json()["documents"]] == ["Thermo-L4.pdf"]

    r = client.post("/api/chat", json={"question": "What is entropy?"}, headers=h)
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["grounded"] is True
    assert body["sources"][0]["filename"] == "Thermo-L4.pdf"
    assert body["sources"][0]["page"] == 2  # page number kept through the pipeline

    assert client.delete(f"/api/documents/{doc['doc_id']}", headers=h).status_code == 200
    assert client.get("/api/documents", headers=h).json()["documents"] == []
    assert client.delete(f"/api/documents/{doc['doc_id']}", headers=h).status_code == 404


def test_users_are_isolated(client):
    a, b = headers(), headers()
    pdf = make_pdf(["Entropy is a measure of disorder."])
    client.post("/api/documents", files={"file": ("a.pdf", pdf, "application/pdf")}, headers=a)
    assert client.get("/api/documents", headers=b).json()["documents"] == []
    r = client.post("/api/chat", json={"question": "entropy?"}, headers=b)
    assert r.status_code == 400  # B has no documents


def test_unrelated_question_says_not_enough_info(client, monkeypatch):
    monkeypatch.setenv("MAX_DISTANCE", "0.5")
    h = headers()
    client.post("/api/documents", files={"file": ("a.pdf", make_pdf(["Entropy is a measure of disorder."]), "application/pdf")}, headers=h)
    called = []
    monkeypatch.setattr(llm, "generate_answer", lambda q, s: called.append(1) or "x")
    body = client.post("/api/chat", json={"question": "zebra pizza volcano"}, headers=h).json()
    assert body["grounded"] is False and body["sources"] == []
    assert not called  # Claude is not even called when nothing relevant is found


def test_model_can_refuse_with_insufficient_context(client, monkeypatch):
    h = headers()
    client.post("/api/documents", files={"file": ("a.pdf", make_pdf(["Entropy is a measure of disorder."]), "application/pdf")}, headers=h)
    monkeypatch.setattr(llm, "generate_answer", lambda q, s: llm.INSUFFICIENT)
    body = client.post("/api/chat", json={"question": "entropy disorder?"}, headers=h).json()
    assert body["grounded"] is False and body["sources"] == []


def test_chat_without_api_key_returns_503(client, monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY")
    r = client.post("/api/chat", json={"question": "hi"}, headers=headers())
    assert r.status_code == 503
    assert "ANTHROPIC_API_KEY" in r.json()["detail"]


def test_claude_failure_becomes_502(client, monkeypatch):
    h = headers()
    client.post("/api/documents", files={"file": ("a.pdf", make_pdf(["Entropy is a measure of disorder."]), "application/pdf")}, headers=h)

    def boom(q, s):
        raise llm.LLMError("Claude is rate-limited right now.")

    monkeypatch.setattr(llm, "generate_answer", boom)
    r = client.post("/api/chat", json={"question": "entropy disorder?"}, headers=h)
    assert r.status_code == 502
