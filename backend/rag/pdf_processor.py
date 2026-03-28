"""
PDF Processor — handles uploaded PDFs end to end:
  1. Parse PDF text using PyMuPDF (handles scanned + digital PDFs)
  2. Split into chunks using RecursiveCharacterTextSplitter
  3. Embed and store in session-specific ChromaDB collection
  4. Return chunk list for session storage

Chunk settings (optimised for medical documents):
  chunk_size    = 512 tokens  (~400 words)
  chunk_overlap = 100 tokens  (preserves context across chunks)
  splitter      = paragraph → sentence → word (never cuts mid-sentence)
"""

import logging
import uuid
import io
import fitz                          # PyMuPDF
from langchain.text_splitter import RecursiveCharacterTextSplitter
from rag.vector_store import add_pdf_to_session, clear_session_pdf, get_pdf_chunk_count

logger = logging.getLogger(__name__)

# ── Splitter config ───────────────────────────────────────────────────────────

PDF_SPLITTER = RecursiveCharacterTextSplitter(
    chunk_size=512,
    chunk_overlap=100,
    separators=["\n\n", "\n", ". ", "? ", "! ", " ", ""],
    length_function=len,
)

# ── PDF text extraction ───────────────────────────────────────────────────────

def extract_text_from_pdf(file_bytes: bytes) -> str:
    """
    Extract all text from a PDF file given as bytes.
    Handles both digital PDFs and basic text extraction from scanned docs.
    """
    text_parts = []
    try:
        doc = fitz.open(stream=file_bytes, filetype="pdf")
        for page_num, page in enumerate(doc, start=1):
            page_text = page.get_text("text")
            if page_text.strip():
                text_parts.append(f"[Page {page_num}]\n{page_text.strip()}")
        doc.close()
    except Exception as e:
        logger.error(f"PDF extraction error: {e}")
        raise ValueError(f"Could not read PDF: {e}")

    full_text = "\n\n".join(text_parts)

    if not full_text.strip():
        raise ValueError(
            "No text could be extracted from this PDF. "
            "It may be a scanned image-only PDF. "
            "Please upload a PDF with selectable text."
        )

    return full_text


def extract_text_from_docx(file_bytes: bytes) -> str:
    """Extract text from a .docx Word document."""
    import docx
    import io
    doc = docx.Document(io.BytesIO(file_bytes))
    paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
    return "\n\n".join(paragraphs)


# ── Chunking ──────────────────────────────────────────────────────────────────

def chunk_text(text: str, filename: str) -> tuple[list[str], list[dict], list[str]]:
    """
    Split text into chunks.
    Returns (texts, metadatas, ids) ready for ChromaDB upsert.
    """
    raw_chunks = PDF_SPLITTER.split_text(text)

    texts = []
    metadatas = []
    ids = []

    for i, chunk in enumerate(raw_chunks):
        if not chunk.strip():
            continue
        texts.append(chunk.strip())
        metadatas.append({
            "source": filename,
            "chunk_index": i,
            "type": "uploaded_document",
        })
        ids.append(f"{filename}_{i}_{uuid.uuid4().hex[:8]}")

    return texts, metadatas, ids


# ── Main processor ────────────────────────────────────────────────────────────

def process_uploaded_file(
    session_id: str,
    file_bytes: bytes,
    filename: str,
) -> dict:
    """
    Full pipeline: file bytes → extract → chunk → embed → store.

    Returns:
    {
        "success": bool,
        "filename": str,
        "chunk_count": int,
        "page_count": int,
        "preview": str,       # first 300 chars of extracted text
        "error": str          # only if success=False
    }
    """
    filename_lower = filename.lower()

    try:
        # 1. Extract text
        if filename_lower.endswith(".pdf"):
            raw_text = extract_text_from_pdf(file_bytes)
            page_count = raw_text.count("[Page ")
        elif filename_lower.endswith(".docx") or filename_lower.endswith(".doc"):
            raw_text = extract_text_from_docx(file_bytes)
            page_count = 1
        elif filename_lower.endswith(".txt"):
            raw_text = file_bytes.decode("utf-8", errors="ignore")
            page_count = 1
        else:
            return {
                "success": False,
                "filename": filename,
                "chunk_count": 0,
                "page_count": 0,
                "preview": "",
                "error": f"Unsupported file type. Please upload PDF, DOCX, or TXT files."
            }

        # 2. Clear any existing PDF for this session
        clear_session_pdf(session_id)

        # 3. Chunk the text
        texts, metadatas, ids = chunk_text(raw_text, filename)

        if not texts:
            return {
                "success": False,
                "filename": filename,
                "chunk_count": 0,
                "page_count": page_count,
                "preview": "",
                "error": "Document appears to be empty or has no readable content."
            }

        # 4. Embed and store in ChromaDB
        add_pdf_to_session(session_id, texts, metadatas, ids)

        chunk_count = get_pdf_chunk_count(session_id)
        preview = raw_text[:300].replace("\n", " ").strip()

        logger.info(
            f"Session {session_id}: processed '{filename}' "
            f"→ {chunk_count} chunks, {page_count} pages"
        )

        return {
            "success": True,
            "filename": filename,
            "chunk_count": chunk_count,
            "page_count": page_count,
            "preview": preview,
            "error": ""
        }

    except ValueError as e:
        return {
            "success": False,
            "filename": filename,
            "chunk_count": 0,
            "page_count": 0,
            "preview": "",
            "error": str(e)
        }
    except Exception as e:
        logger.error(f"Unexpected error processing {filename}: {e}")
        return {
            "success": False,
            "filename": filename,
            "chunk_count": 0,
            "page_count": 0,
            "preview": "",
            "error": "An unexpected error occurred while processing the file."
        }