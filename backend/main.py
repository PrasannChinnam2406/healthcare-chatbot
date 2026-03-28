"""
FILE: backend/main.py

HealthBot FastAPI Application — Main Entry Point

Routes:
  POST /chat              — send message, get AI response
  POST /chat/stream       — streaming response (token by token)
  POST /upload-pdf        — upload health document
  DELETE /pdf             — remove uploaded document
  GET  /session           — get session info
  POST /session/profile   — update user health profile
  POST /session/mode      — change user mode
  GET  /vitals            — get latest IoMT vitals
  POST /vitals            — push new IoMT vitals reading
  GET  /history           — get chat history
  DELETE /history         — clear chat history
  GET  /health            — server health check
"""

import logging
import uuid
import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI, UploadFile, File, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from typing import Optional

from core.config import get_settings
from core.session_manager import (
    get_session, update_session, set_pdf, clear_pdf,
    set_user_mode, set_user_profile, set_iomt_data,
    get_session_summary, get_chat_history, cleanup_expired_sessions
)
from agents.orchestrator import process_message
from rag.pdf_processor import process_uploaded_file
from rag.vector_store import clear_session_pdf
from core.llm_client import call_llm_stream

logging.basicConfig(
    level   = logging.INFO,
    format  = "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
)
logger   = logging.getLogger(__name__)
settings = get_settings()


# ── Startup / Shutdown ────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("HealthBot API starting up...")
    logger.info(f"Environment: {settings.APP_ENV}")
    logger.info(f"Primary model: {settings.GROQ_PRIMARY_MODEL}")
    logger.info(f"OpenFDA: {'enabled' if settings.openfda_enabled else 'disabled'}")
    logger.info(f"WHO ICD-11: {'enabled' if settings.who_icd_enabled else 'disabled'}")
    logger.info(f"IoMT: {'enabled' if settings.iomt_enabled else 'disabled (add keys later)'}")
    yield
    logger.info("HealthBot API shutting down.")
    cleanup_expired_sessions()


# ── App setup ─────────────────────────────────────────────────────────────────

app = FastAPI(
    title       = "HealthBot API",
    description = "AI-powered healthcare chatbot with IoMT integration",
    version     = "1.0.0",
    lifespan    = lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins     = settings.get_allowed_origins(),
    allow_credentials = True,
    allow_methods     = ["*"],
    allow_headers     = ["*"],
)


# ── Request / Response models ─────────────────────────────────────────────────

class ChatRequest(BaseModel):
    session_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    message:    str = Field(..., min_length=1, max_length=5000)
    user_mode:  str = Field(default="general")
    iomt_data:  Optional[dict] = None

class ProfileUpdate(BaseModel):
    age:                Optional[int]       = None
    sex:                Optional[str]       = None
    known_conditions:   Optional[list[str]] = None
    current_medications:Optional[list[str]] = None
    allergies:          Optional[list[str]] = None

class ModeUpdate(BaseModel):
    session_id: str
    user_mode:  str   # general | patient | medical

class VitalsUpdate(BaseModel):
    session_id:   str
    heart_rate:   Optional[float] = None
    spo2:         Optional[float] = None
    temperature:  Optional[float] = None
    systolic_bp:  Optional[float] = None
    diastolic_bp: Optional[float] = None
    glucose:      Optional[float] = None


# ── Helper ────────────────────────────────────────────────────────────────────

def _get_or_create_session(session_id: str | None) -> str:
    if not session_id:
        session_id = str(uuid.uuid4())
    get_session(session_id)   # creates if not exists
    return session_id


# ── Routes ────────────────────────────────────────────────────────────────────

@app.get("/health")
async def health_check():
    """Server health check — used by deployment platforms."""
    return {
        "status":       "healthy",
        "service":      "HealthBot API",
        "version":      "1.0.0",
        "environment":  settings.APP_ENV,
    }


@app.post("/chat")
async def chat(req: ChatRequest):
    """
    Main chat endpoint.
    Runs the full 6-agent pipeline and returns the complete response.
    """
    try:
        session_id = _get_or_create_session(req.session_id)

        # Update user mode if provided
        if req.user_mode:
            set_user_mode(session_id, req.user_mode)

        result = await process_message(
            session_id = session_id,
            message    = req.message,
            user_mode  = req.user_mode or "general",
            iomt_data  = req.iomt_data,
        )

        return {
            "session_id":          session_id,
            "response":            result["response"],
            "is_emergency":        result["is_emergency"],
            "severity":            result["severity"],
            "has_prescription":    result["has_prescription"],
            "vitals_risk":         result["vitals_risk"],
            "vitals_alerts":       result["vitals_alerts"],
            "suggested_questions": result["suggested_questions"],
            "sources":             result["sources"],
            "model_used":          result["model_used"],
            "agents_used":         result["agents_used"],
        }

    except Exception as e:
        logger.error(f"Chat error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")


@app.post("/chat/stream")
async def chat_stream(req: ChatRequest):
    """
    Streaming chat endpoint — returns tokens one by one like ChatGPT.
    Frontend receives Server-Sent Events (SSE).
    """
    session_id = _get_or_create_session(req.session_id)

    if req.user_mode:
        set_user_mode(session_id, req.user_mode)

    async def generate():
        try:
            # First run safety check
            from agents.safety_guard import run_safety_guard
            session    = get_session(session_id)
            iomt_data  = session.get("iomt_data") or req.iomt_data
            safety     = run_safety_guard(req.message, iomt_data)

            if safety["should_stop"]:
                yield f"data: {safety['emergency_response']}\n\n"
                yield "data: [DONE]\n\n"
                return

            # Get RAG context
            from rag.vector_store import search_all
            rag_result  = search_all(session_id, req.message)
            rag_context = rag_result["context_string"]

            # Stream LLM response
            chat_history = session.get("chat_history", [])
            user_mode    = req.user_mode or session.get("user_mode", "general")

            for token in call_llm_stream(
                prompt       = req.message,
                user_mode    = user_mode,
                context      = rag_context,
                chat_history = chat_history,
            ):
                # Skip the model metadata token at the end
                if token.startswith("\n\n<!-- model_used:"):
                    continue
                yield f"data: {token}\n\n"

            yield "data: [DONE]\n\n"

        except Exception as e:
            logger.error(f"Stream error: {e}")
            yield f"data: Sorry, I encountered an error. Please try again.\n\n"
            yield "data: [DONE]\n\n"

    return StreamingResponse(
        generate(),
        media_type = "text/event-stream",
        headers    = {
            "Cache-Control":               "no-cache",
            "X-Accel-Buffering":           "no",
            "Access-Control-Allow-Origin": "*",
        }
    )


@app.post("/upload-pdf")
async def upload_pdf(
    session_id: str,
    file:       UploadFile = File(...),
):
    """Upload a health document (PDF, DOCX, TXT) for the session."""
    try:
        # Validate file type
        allowed = {".pdf", ".docx", ".doc", ".txt"}
        ext     = "." + file.filename.lower().split(".")[-1]
        if ext not in allowed:
            raise HTTPException(
                status_code = 400,
                detail      = f"File type {ext} not supported. Upload PDF, DOCX or TXT."
            )

        # Validate file size (max 10MB)
        contents = await file.read()
        if len(contents) > 10 * 1024 * 1024:
            raise HTTPException(
                status_code = 400,
                detail      = "File too large. Maximum size is 10MB."
            )

        session_id = _get_or_create_session(session_id)

        result = process_uploaded_file(
            session_id = session_id,
            file_bytes = contents,
            filename   = file.filename,
        )

        if not result["success"]:
            raise HTTPException(status_code=422, detail=result["error"])

        # Store PDF info in session
        set_pdf(session_id, None, file.filename, [])

        return {
            "session_id":  session_id,
            "success":     True,
            "filename":    result["filename"],
            "chunk_count": result["chunk_count"],
            "page_count":  result["page_count"],
            "preview":     result["preview"],
            "message":     f"Document '{file.filename}' uploaded successfully. You can now ask questions about it.",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"PDF upload error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


@app.delete("/pdf")
async def delete_pdf(session_id: str):
    """Remove the uploaded document from the session."""
    try:
        clear_session_pdf(session_id)
        clear_pdf(session_id)
        return {"success": True, "message": "Document removed from session."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/session")
async def get_session_info(session_id: str):
    """Get current session summary."""
    try:
        summary = get_session_summary(session_id)
        return summary
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/session/profile")
async def update_profile(session_id: str, profile: ProfileUpdate):
    """Update user health profile for personalised responses."""
    try:
        session_id = _get_or_create_session(session_id)
        set_user_profile(session_id, profile.model_dump(exclude_none=True))
        return {"success": True, "message": "Profile updated."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/session/mode")
async def update_mode(req: ModeUpdate):
    """Switch user mode: general | patient | medical"""
    valid_modes = {"general", "patient", "medical"}
    if req.user_mode not in valid_modes:
        raise HTTPException(
            status_code = 400,
            detail      = f"Invalid mode. Choose: {', '.join(valid_modes)}"
        )
    set_user_mode(req.session_id, req.user_mode)
    return {"success": True, "user_mode": req.user_mode}


@app.get("/vitals")
async def get_vitals(session_id: str):
    """Get latest IoMT vitals for the session."""
    session   = get_session(session_id)
    iomt_data = session.get("iomt_data")
    if not iomt_data:
        return {"vitals": None, "message": "No vitals data available for this session."}
    return {"vitals": iomt_data}


@app.post("/vitals")
async def push_vitals(req: VitalsUpdate):
    """
    Push new IoMT vitals reading.
    Called by your IoMT device app when new readings are available.
    """
    try:
        session_id = _get_or_create_session(req.session_id)
        vitals = req.model_dump(exclude={"session_id"}, exclude_none=True)

        if not vitals:
            raise HTTPException(status_code=400, detail="No vitals data provided.")

        set_iomt_data(session_id, vitals)

        # Check for critical values immediately
        from services.emergency_service import check_vitals_emergency
        risk = check_vitals_emergency(vitals)

        return {
            "success":    True,
            "vitals":     vitals,
            "risk_level": risk["risk_level"],
            "alerts":     risk["alerts"],
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/history")
async def get_history(session_id: str, limit: int = 20):
    """Get chat history for a session."""
    try:
        history = get_chat_history(session_id)
        return {
            "session_id": session_id,
            "messages":   history[-limit:],
            "total":      len(history),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/history")
async def clear_history(session_id: str):
    """Clear chat history for a session."""
    try:
        update_session(session_id, chat_history=[])
        return {"success": True, "message": "Chat history cleared."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── Run ───────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host     = "0.0.0.0",
        port     = 8000,
        reload   = True,      # auto-restart on code changes during development
        log_level= "info",
    )