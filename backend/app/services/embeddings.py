"""Step 3: turn text into vectors ("embeddings") with sentence-transformers.

Texts with similar meaning get vectors that point in similar directions, which is what
lets us search by meaning instead of exact keywords. The model is loaded once, the first
time it is needed (the first run downloads it).
"""
from app.config import settings

_model = None


class EmbeddingError(Exception):
    pass


def _get_model():
    global _model
    if _model is None:
        from sentence_transformers import SentenceTransformer

        _model = SentenceTransformer(settings.embedding_model)
    return _model


def embed_texts(texts: list[str]) -> list[list[float]]:
    try:
        vectors = _get_model().encode(
            texts, normalize_embeddings=True, batch_size=32, show_progress_bar=False
        )
    except Exception as exc:
        raise EmbeddingError(
            "The embedding model could not be loaded or run. Check your internet connection "
            "on first start (the model is downloaded once) and the EMBEDDING_MODEL setting."
        ) from exc
    return vectors.tolist()
