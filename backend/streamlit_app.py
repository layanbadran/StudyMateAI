"""StudyMate AI: the all-Python version (one program, no Node.js needed).

Run it from the backend folder:  streamlit run streamlit_app.py
It reuses the same RAG pipeline in app/services/.
"""
import re
import uuid

import streamlit as st

from app.config import settings
from app.services import rag, vector_store
from app.services.embeddings import EmbeddingError
from app.services.llm import LLMError, LLMNotConfigured
from app.services.pdf_service import PDFError
from app.services.uploads import UploadRejected, ingest_upload

st.set_page_config(page_title="StudyMate AI", page_icon="📚", layout="wide")

# ---------- look: orange and yellow ----------
st.markdown(
    """
<style>
  .stApp { background: #FFFDF7; color: #2A1A0A; }
  [data-testid="stSidebar"] { background: #FFF1B8; border-right: 2px solid #2A1A0A; }
  .hero { background: #FFD23F; border: 2px solid #2A1A0A; border-radius: 16px;
          padding: 22px 26px; margin-bottom: 18px; box-shadow: 6px 6px 0 #2A1A0A; }
  .hero h1 { margin: 0; font-size: 2.1rem; color: #2A1A0A; }
  .hero p { margin: 6px 0 0; font-size: 1.05rem; color: #2A1A0A; }
  .stButton > button[kind="primary"], .stFormSubmitButton > button {
      background: #FF7A00; color: #2A1A0A; border: 2px solid #2A1A0A; font-weight: 600; }
  .stButton > button[kind="primary"]:hover { background: #FFD23F; color: #2A1A0A; }
  [data-testid="stChatMessage"] { background: #FFFFFF; border: 2px solid #2A1A0A33; border-radius: 14px; }
  /* Each paragraph picks its own direction, so Arabic text reads right-to-left */
  [data-testid="stChatMessage"] p { unicode-bidi: plaintext; text-align: start; }
</style>
<div class="hero">
  <h1>StudyMate AI</h1>
  <p>Ask questions about your own lecture notes. Answers come only from your PDFs, with the page they were found on.</p>
</div>
""",
    unsafe_allow_html=True,
)

# ---------- each browser gets a private space (its ID lives in the page address) ----------
UUID_RE = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$")
sid = str(st.query_params.get("sid", "")).lower()
if not UUID_RE.match(sid):
    sid = str(uuid.uuid4())
    st.query_params["sid"] = sid

st.session_state.setdefault("messages", [])
st.session_state.setdefault("uploader_key", 0)
st.session_state.setdefault("flash", [])


def friendly(exc: Exception) -> str:
    if isinstance(exc, (UploadRejected, PDFError, EmbeddingError, LLMError, LLMNotConfigured)):
        return str(exc)
    return f"Unexpected error: {type(exc).__name__}: {exc}"


# ---------- sidebar: upload + document list ----------
with st.sidebar:
    st.subheader("Your documents")

    for kind, text in st.session_state.flash:
        (st.success if kind == "ok" else st.error)(text)
    st.session_state.flash = []

    files = st.file_uploader(
        "Choose PDF files",
        type=["pdf"],
        accept_multiple_files=True,
        key=f"uploader_{st.session_state.uploader_key}",
        help=f"PDF only, up to {settings.max_upload_mb} MB each. Scanned images are not supported.",
    )
    if st.button("Add to my notes", type="primary", disabled=not files):
        flash = []
        for f in files:
            try:
                with st.spinner(
                    f"Reading and indexing {f.name}. The first upload can take a few minutes "
                    "while the search model downloads."
                ):
                    result = ingest_upload(sid, f.name, f.getvalue())
                flash.append(("ok", f"{f.name}: added ({result['pages']} pages, {result['chunks']} passages)."))
            except Exception as exc:  # show the real reason instead of a blank crash
                flash.append(("err", f"{f.name}: {friendly(exc)}"))
        st.session_state.flash = flash
        st.session_state.uploader_key += 1  # clears the file picker
        st.rerun()

    try:
        docs = vector_store.list_documents(sid)
    except Exception as exc:
        docs = []
        st.error(f"Could not load your documents. {friendly(exc)}")

    if not docs:
        st.caption("No documents yet. Upload a PDF to start asking questions.")
    for d in docs:
        with st.container(border=True):
            st.markdown(f"**{d['filename']}**")
            st.caption(f"{d['pages']} pages · {d['chunks']} passages")
            if st.button("Remove", key=f"rm_{d['doc_id']}"):
                vector_store.delete_document(sid, d["doc_id"])
                st.rerun()

    st.caption("Your PDF file itself is not saved. Only its text is kept, so it can be searched.")

# ---------- chat ----------
if not settings.llm_ready:
    st.warning(
        "Answers are turned off. Open backend/.env and set LLM_PROVIDER=ollama (free), "
        "or add an ANTHROPIC_API_KEY. Then restart this app. You can still upload documents."
    )


def render(m: dict) -> None:
    with st.chat_message("user" if m["role"] == "user" else "assistant"):
        if m["role"] == "error":
            st.error(m["text"])
            return
        if m["role"] == "assistant" and not m.get("grounded"):
            st.warning("Not found in your documents")
        st.markdown(m["text"])
        for s in m.get("sources", []):
            with st.expander(f"[{s['id']}] {s['filename']}, page {s['page']}"):
                st.write(s["excerpt"])


if not st.session_state.messages:
    st.markdown("#### What do you want to understand?" if docs else "#### Start by adding a PDF")
    st.caption(
        "Try: “Summarize the main ideas in my notes” or “What are the key definitions?”"
        if docs
        else "Upload lecture notes in the sidebar, then ask questions here."
    )

for m in st.session_state.messages:
    render(m)

disabled = (not docs) or (not settings.llm_ready)
question = st.chat_input(
    "Upload a PDF to start asking questions" if not docs else "Ask a question about your notes",
    disabled=disabled,
    max_chars=2000,
)

if question:
    user_msg = {"role": "user", "text": question}
    st.session_state.messages.append(user_msg)
    render(user_msg)
    with st.chat_message("assistant"):
        with st.spinner("Searching your notes and writing an answer…"):
            try:
                res = rag.answer_question(sid, question)
                reply = {
                    "role": "assistant",
                    "text": res["answer"],
                    "sources": res["sources"],
                    "grounded": res["grounded"],
                }
            except Exception as exc:
                reply = {"role": "error", "text": f"Couldn't get an answer. {friendly(exc)}"}
    st.session_state.messages.append(reply)
    st.rerun()