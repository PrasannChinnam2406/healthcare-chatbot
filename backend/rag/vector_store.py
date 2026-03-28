"""
Vector Store — ChromaDB with two collections:

  1. medical_kb      : permanent medical knowledge base (diseases, drugs, guidelines)
  2. session_{id}    : temporary per-session PDF store (cleared when session ends)

Uses MiniLM-L6-v2 embeddings throughout.
"""

import logging
import os
import chromadb
from chromadb.config import Settings as ChromaSettings
from rag.embeddings import embed_texts, embed_query

logger = logging.getLogger(__name__)

# ── ChromaDB client (persisted to disk) ──────────────────────────────────────

CHROMA_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "chroma_db")

_client = None

def get_chroma_client() -> chromadb.PersistentClient:
    global _client
    if _client is None:
        os.makedirs(CHROMA_PATH, exist_ok=True)
        _client = chromadb.PersistentClient(
            path=CHROMA_PATH,
            settings=ChromaSettings(anonymized_telemetry=False)
        )
        logger.info(f"ChromaDB client initialised at {CHROMA_PATH}")
    return _client


# ── Medical Knowledge Base collection ────────────────────────────────────────

KB_COLLECTION_NAME = "medical_kb"

def get_kb_collection():
    """Get or create the permanent medical knowledge base collection."""
    client = get_chroma_client()
    collection = client.get_or_create_collection(
        name=KB_COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"}
    )
    return collection


def add_to_kb(texts: list[str], metadatas: list[dict], ids: list[str]) -> None:
    """Add documents to the medical knowledge base."""
    if not texts:
        return
    collection = get_kb_collection()
    embeddings = embed_texts(texts)
    collection.upsert(
        documents=texts,
        embeddings=embeddings,
        metadatas=metadatas,
        ids=ids
    )
    logger.info(f"Added {len(texts)} documents to medical KB.")


def search_kb(query: str, n_results: int = 5) -> list[dict]:
    """
    Search the medical knowledge base.
    Returns list of { text, metadata, distance } dicts.
    """
    collection = get_kb_collection()

    # if collection is empty return nothing
    if collection.count() == 0:
        logger.warning("Medical KB is empty — run knowledge_base_loader.py first.")
        return []

    query_embedding = embed_query(query)
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=min(n_results, collection.count()),
        include=["documents", "metadatas", "distances"]
    )

    output = []
    for doc, meta, dist in zip(
        results["documents"][0],
        results["metadatas"][0],
        results["distances"][0]
    ):
        output.append({
            "text": doc,
            "metadata": meta,
            "distance": round(dist, 4),
            "relevance": round(1 - dist, 4)   # cosine: lower distance = more relevant
        })

    return output


def get_kb_count() -> int:
    return get_kb_collection().count()


# ── Session PDF collection ────────────────────────────────────────────────────

def _session_collection_name(session_id: str) -> str:
    # ChromaDB collection names must be alphanumeric + underscore/hyphen
    safe = session_id.replace("-", "_").replace(" ", "_")[:50]
    return f"session_{safe}"


def add_pdf_to_session(
    session_id: str,
    texts: list[str],
    metadatas: list[dict],
    ids: list[str]
) -> None:
    """Store PDF chunks in a session-specific collection."""
    client = get_chroma_client()
    col_name = _session_collection_name(session_id)
    collection = client.get_or_create_collection(
        name=col_name,
        metadata={"hnsw:space": "cosine"}
    )
    embeddings = embed_texts(texts)
    collection.upsert(
        documents=texts,
        embeddings=embeddings,
        metadatas=metadatas,
        ids=ids
    )
    logger.info(f"Session {session_id}: stored {len(texts)} PDF chunks.")


def search_pdf(session_id: str, query: str, n_results: int = 4) -> list[dict]:
    """Search the PDF chunks for a session."""
    client = get_chroma_client()
    col_name = _session_collection_name(session_id)

    try:
        collection = client.get_collection(name=col_name)
    except Exception:
        return []   # no PDF uploaded for this session

    if collection.count() == 0:
        return []

    query_embedding = embed_query(query)
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=min(n_results, collection.count()),
        include=["documents", "metadatas", "distances"]
    )

    output = []
    for doc, meta, dist in zip(
        results["documents"][0],
        results["metadatas"][0],
        results["distances"][0]
    ):
        output.append({
            "text": doc,
            "metadata": meta,
            "distance": round(dist, 4),
            "relevance": round(1 - dist, 4)
        })

    return output


def clear_session_pdf(session_id: str) -> None:
    """Delete the session PDF collection from ChromaDB."""
    client = get_chroma_client()
    col_name = _session_collection_name(session_id)
    try:
        client.delete_collection(name=col_name)
        logger.info(f"Session {session_id}: PDF collection cleared.")
    except Exception:
        pass   # collection didn't exist, that's fine


def get_pdf_chunk_count(session_id: str) -> int:
    client = get_chroma_client()
    col_name = _session_collection_name(session_id)
    try:
        return client.get_collection(name=col_name).count()
    except Exception:
        return 0


# ── Combined search (PDF first, then KB) ─────────────────────────────────────

def search_all(
    session_id: str,
    query: str,
    pdf_results: int = 4,
    kb_results: int = 3
) -> dict:
    """
    Search both PDF (if uploaded) and KB.
    Returns { pdf_chunks: [...], kb_chunks: [...], context_string: str }
    """
    pdf_chunks = search_pdf(session_id, query, n_results=pdf_results)
    kb_chunks = search_kb(query, n_results=kb_results)

    # build a single context string for the LLM
    context_parts = []

    if pdf_chunks:
        context_parts.append("=== From your uploaded document ===")
        for chunk in pdf_chunks:
            context_parts.append(chunk["text"])

    if kb_chunks:
        context_parts.append("=== From medical knowledge base ===")
        for chunk in kb_chunks:
            source = chunk["metadata"].get("source", "Medical KB")
            context_parts.append(f"[{source}] {chunk['text']}")

    context_string = "\n\n".join(context_parts)

    return {
        "pdf_chunks": pdf_chunks,
        "kb_chunks": kb_chunks,
        "context_string": context_string,
        "has_pdf": len(pdf_chunks) > 0,
        "has_kb": len(kb_chunks) > 0,
    }