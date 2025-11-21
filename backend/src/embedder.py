from functools import lru_cache
from typing import Iterable, List

import numpy as np
from sentence_transformers import SentenceTransformer


@lru_cache(maxsize=1)
def _get_model() -> SentenceTransformer:
    """Load the sentence-transformers model once and cache it."""

    # Recommended lightweight model for semantic search
    return SentenceTransformer("all-MiniLM-L6-v2")


def _l2_normalize(vectors: np.ndarray) -> np.ndarray:
    """L2-normalize embedding matrix row-wise."""

    if vectors.size == 0:
        return vectors
    norms = np.linalg.norm(vectors, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    return (vectors / norms).astype("float32")


def embed_documents(texts: Iterable[str], batch_size: int = 32) -> np.ndarray:
    """Embed a collection of documents.

    Returns an array of shape (n_docs, dim) with L2-normalized embeddings.
    """

    texts_list: List[str] = list(texts)
    if not texts_list:
        return np.zeros((0, 0), dtype="float32")

    model = _get_model()
    embeddings = model.encode(
        texts_list,
        batch_size=batch_size,
        show_progress_bar=True,
        convert_to_numpy=True,
        normalize_embeddings=False,
    )
    return _l2_normalize(np.asarray(embeddings, dtype="float32"))


def embed_query(text: str) -> np.ndarray:
    """Embed a single query string; returns array of shape (1, dim)."""

    if not text.strip():
        raise ValueError("Query text is empty")
    return embed_documents([text])


