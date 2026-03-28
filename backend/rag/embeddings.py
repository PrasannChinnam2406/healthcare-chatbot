"""
Embeddings — loads MiniLM-L6-v2 locally (no GPU needed, ~90MB).
Used for both the medical knowledge base and uploaded PDFs.
"""

import logging
from sentence_transformers import SentenceTransformer
from functools import lru_cache

logger = logging.getLogger(__name__)

EMBEDDING_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"


@lru_cache(maxsize=1)
def get_embedding_model() -> SentenceTransformer:
    """
    Loads the embedding model once and caches it.
    First call downloads the model (~90MB) — subsequent calls are instant.
    """
    logger.info(f"Loading embedding model: {EMBEDDING_MODEL_NAME}")
    model = SentenceTransformer(EMBEDDING_MODEL_NAME)
    logger.info("Embedding model loaded successfully.")
    return model


def embed_texts(texts: list[str]) -> list[list[float]]:
    """
    Embed a list of text strings.
    Returns list of float vectors (384 dimensions for MiniLM).
    """
    model = get_embedding_model()
    embeddings = model.encode(texts, convert_to_numpy=True, show_progress_bar=False)
    return embeddings.tolist()


def embed_query(query: str) -> list[float]:
    """
    Embed a single query string for similarity search.
    """
    model = get_embedding_model()
    embedding = model.encode([query], convert_to_numpy=True, show_progress_bar=False)
    return embedding[0].tolist()