"""
FILE: database/supabase_client.py

Supabase client for backend — saves chat history and user profiles.
Uses the 3 tables already created: chat_messages, chat_sessions, user_profiles.
"""

import logging
from core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

_client = None

def get_supabase():
    """Get Supabase client — returns None if not configured."""
    global _client
    if _client is not None:
        return _client

    try:
        from supabase import create_client
        url = settings.SUPABASE_URL
        key = settings.SUPABASE_KEY
        if not url or not key or "placeholder" in url:
            return None
        _client = create_client(url, key)
        return _client
    except Exception as e:
        logger.debug(f"Supabase client init failed: {e}")
        return None


def save_session(session_id: str, user_id: str | None, title: str) -> bool:
    """Create or update a chat session record."""
    try:
        sb = get_supabase()
        if not sb or not user_id:
            return False
        sb.table("chat_sessions").upsert({
            "id":      session_id,
            "user_id": user_id,
            "title":   title[:100],
        }).execute()
        return True
    except Exception as e:
        logger.debug(f"save_session failed: {e}")
        return False


def save_message(session_id: str, role: str, content: str, metadata: dict = None) -> bool:
    """Save a single chat message."""
    try:
        sb = get_supabase()
        if not sb:
            return False
        sb.table("chat_messages").insert({
            "session_id": session_id,
            "role":       role,
            "content":    content,
            "metadata":   metadata or {},
        }).execute()
        return True
    except Exception as e:
        logger.debug(f"save_message failed: {e}")
        return False


def get_user_sessions(user_id: str) -> list:
    """Get all chat sessions for a user."""
    try:
        sb = get_supabase()
        if not sb:
            return []
        result = sb.table("chat_sessions") \
            .select("id, title, created_at") \
            .eq("user_id", user_id) \
            .order("created_at", desc=True) \
            .limit(20) \
            .execute()
        return result.data or []
    except Exception as e:
        logger.debug(f"get_user_sessions failed: {e}")
        return []


def get_session_messages(session_id: str) -> list:
    """Get all messages for a session."""
    try:
        sb = get_supabase()
        if not sb:
            return []
        result = sb.table("chat_messages") \
            .select("role, content, created_at") \
            .eq("session_id", session_id) \
            .order("created_at") \
            .execute()
        return result.data or []
    except Exception as e:
        logger.debug(f"get_session_messages failed: {e}")
        return []


def save_user_profile(user_id: str, profile: dict) -> bool:
    """Save or update user health profile."""
    try:
        sb = get_supabase()
        if not sb:
            return False
        sb.table("user_profiles").upsert({
            "id":                   user_id,
            "age":                  profile.get("age"),
            "sex":                  profile.get("sex"),
            "known_conditions":     profile.get("known_conditions", []),
            "current_medications":  profile.get("current_medications", []),
            "allergies":            profile.get("allergies", []),
            "user_mode":            profile.get("user_mode", "general"),
        }).execute()
        return True
    except Exception as e:
        logger.debug(f"save_user_profile failed: {e}")
        return False