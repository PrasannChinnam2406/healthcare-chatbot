"""
Session Manager — stores per-user session state in memory.

Each session holds:
  - chat_history     : list of {role, content} dicts
  - pdf_vectorstore  : ChromaDB collection for uploaded PDF (or None)
  - pdf_filename     : name of the uploaded file
  - user_profile     : age, sex, conditions, medications
  - user_mode        : general | patient | medical
  - iomt_data        : latest vitals from IoMT device (or None)
"""

from datetime import datetime, timedelta
import threading

# ── In-memory session store ───────────────────────────────────────────────────
# Key: session_id (str)
# Value: dict with all session fields
_sessions: dict = {}
_lock = threading.Lock()

SESSION_TTL_HOURS = 12   # sessions expire after 12 hours of inactivity


# ── Internal helpers ──────────────────────────────────────────────────────────

def _now() -> datetime:
    return datetime.utcnow()

def _make_session(session_id: str) -> dict:
    return {
        "session_id": session_id,
        "chat_history": [],
        "pdf_vectorstore": None,
        "pdf_filename": None,
        "pdf_chunks": [],          # raw text chunks for context building
        "user_profile": {
            "age": None,
            "sex": None,
            "known_conditions": [],
            "current_medications": [],
            "allergies": [],
        },
        "user_mode": "general",
        "iomt_data": None,
        "created_at": _now(),
        "last_active": _now(),
    }


# ── Public API ────────────────────────────────────────────────────────────────

def get_session(session_id: str) -> dict:
    """Get existing session or create a new one."""
    with _lock:
        if session_id not in _sessions:
            _sessions[session_id] = _make_session(session_id)
        session = _sessions[session_id]
        session["last_active"] = _now()
        return session


def update_session(session_id: str, **kwargs) -> None:
    """Update any fields in a session."""
    with _lock:
        if session_id not in _sessions:
            _sessions[session_id] = _make_session(session_id)
        session = _sessions[session_id]
        for key, value in kwargs.items():
            if key in session:
                session[key] = value
        session["last_active"] = _now()


def add_message(session_id: str, role: str, content: str) -> None:
    """Append a message to the session chat history."""
    with _lock:
        session = _sessions.get(session_id)
        if not session:
            _sessions[session_id] = _make_session(session_id)
            session = _sessions[session_id]
        session["chat_history"].append({
            "role": role,
            "content": content,
        })
        session["last_active"] = _now()
        # keep history to last 50 messages to avoid memory bloat
        if len(session["chat_history"]) > 50:
            session["chat_history"] = session["chat_history"][-50:]


def get_chat_history(session_id: str) -> list:
    """Return chat history for a session."""
    session = get_session(session_id)
    return session.get("chat_history", [])


def set_pdf(session_id: str, vectorstore, filename: str, chunks: list) -> None:
    """Store the PDF vectorstore and metadata for a session."""
    update_session(
        session_id,
        pdf_vectorstore=vectorstore,
        pdf_filename=filename,
        pdf_chunks=chunks,
    )


def clear_pdf(session_id: str) -> None:
    """Remove PDF from session."""
    update_session(
        session_id,
        pdf_vectorstore=None,
        pdf_filename=None,
        pdf_chunks=[],
    )


def set_iomt_data(session_id: str, vitals: dict) -> None:
    """Store latest IoMT vitals reading for a session."""
    update_session(session_id, iomt_data=vitals)


def set_user_mode(session_id: str, mode: str) -> None:
    """Set user mode: general | patient | medical"""
    valid = {"general", "patient", "medical"}
    if mode not in valid:
        mode = "general"
    update_session(session_id, user_mode=mode)


def set_user_profile(session_id: str, profile: dict) -> None:
    """Update user health profile fields."""
    with _lock:
        session = get_session(session_id)
        current = session.get("user_profile", {})
        current.update(profile)
        session["user_profile"] = current


def delete_session(session_id: str) -> None:
    """Delete a session completely."""
    with _lock:
        _sessions.pop(session_id, None)


def cleanup_expired_sessions() -> int:
    """Remove sessions inactive for more than SESSION_TTL_HOURS. Returns count removed."""
    cutoff = _now() - timedelta(hours=SESSION_TTL_HOURS)
    with _lock:
        expired = [
            sid for sid, s in _sessions.items()
            if s["last_active"] < cutoff
        ]
        for sid in expired:
            del _sessions[sid]
    return len(expired)


def get_session_summary(session_id: str) -> dict:
    """Return a lightweight summary of a session (for debugging / API response)."""
    session = get_session(session_id)
    return {
        "session_id": session_id,
        "user_mode": session["user_mode"],
        "pdf_active": session["pdf_filename"] is not None,
        "pdf_filename": session["pdf_filename"],
        "message_count": len(session["chat_history"]),
        "iomt_connected": session["iomt_data"] is not None,
        "user_profile": session["user_profile"],
    }