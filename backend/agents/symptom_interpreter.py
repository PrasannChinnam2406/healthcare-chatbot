"""
FILE: agents/symptom_interpreter.py  — FIXED VERSION

Key fix: Use a much simpler, more reliable prompt that always returns valid JSON.
The previous version used complex instructions that confused the fast model.
"""

import json
import re
import logging
from core.llm_client import call_llm
from rag.vector_store import search_all

logger = logging.getLogger(__name__)


def run_symptom_interpreter(
    message: str,
    session_id: str,
    user_mode: str = "general",
    user_profile: dict = None,
    chat_history: list = None,
    iomt_data: dict = None,
) -> dict:
    profile = user_profile or {}
    history = chat_history or []

    # Search RAG first
    rag_result = search_all(session_id, message, pdf_results=4, kb_results=3)
    rag_context = rag_result["context_string"]

    # Very simple, reliable prompt — JSON only
    prompt = f"""Extract symptom info from this message: "{message}"

Return ONLY this JSON, nothing else:
{{"has_symptoms": true, "extracted_symptoms": ["symptom1", "symptom2"], "duration": "unknown", "symptom_summary": "brief summary", "symptom_category": "general", "needs_medical_attention": false}}

Rules:
- has_symptoms: true if health complaint, false if greeting/general question
- extracted_symptoms: list of symptoms mentioned
- duration: how long (e.g. "2 days", "1 week", "unknown")
- symptom_summary: one sentence max
- symptom_category: one of: fever, respiratory, gastrointestinal, pain, cardiac, mental health, diabetes, skin, general
- needs_medical_attention: true if serious symptoms

JSON only. No other text."""

    try:
        result = call_llm(
            prompt=prompt,
            user_mode="general",
            context="",
            chat_history=[],
            force_model="llama-3.1-8b-instant",
        )

        content = result["content"].strip()

        # Try multiple JSON extraction strategies
        parsed = _extract_json(content)

        if parsed:
            return {
                "has_symptoms":            bool(parsed.get("has_symptoms", True)),
                "extracted_symptoms":      parsed.get("extracted_symptoms", [message]),
                "duration":                parsed.get("duration", "unknown"),
                "symptom_summary":         parsed.get("symptom_summary", message),
                "symptom_category":        parsed.get("symptom_category", "general"),
                "needs_medical_attention": bool(parsed.get("needs_medical_attention", False)),
                "rag_context":             rag_context,
                "pdf_used":                rag_result["has_pdf"],
                "model_used":              result["model_used"],
            }

    except Exception as e:
        logger.warning(f"Symptom interpreter error: {e}")

    # Reliable fallback — keyword-based extraction
    return _keyword_fallback(message, rag_context, rag_result)


def _extract_json(text: str) -> dict | None:
    """Try multiple strategies to extract JSON from LLM response."""
    # Strategy 1: direct parse
    try:
        return json.loads(text)
    except Exception:
        pass

    # Strategy 2: find JSON block
    start = text.find("{")
    end   = text.rfind("}") + 1
    if start != -1 and end > start:
        try:
            return json.loads(text[start:end])
        except Exception:
            pass

    # Strategy 3: regex extract
    match = re.search(r'\{[^{}]+\}', text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except Exception:
            pass

    return None


def _keyword_fallback(message: str, rag_context: str, rag_result: dict) -> dict:
    """Reliable keyword-based symptom extraction when LLM fails."""
    msg = message.lower()

    # Detect symptoms by keywords
    symptom_keywords = {
        "fever":       ["fever", "temperature", "hot", "chills", "sweating"],
        "headache":    ["headache", "head pain", "migraine"],
        "body ache":   ["body ache", "muscle pain", "body pain", "aches"],
        "cough":       ["cough", "coughing", "dry cough"],
        "cold":        ["cold", "runny nose", "sneezing", "congestion"],
        "nausea":      ["nausea", "vomit", "vomiting", "nauseous"],
        "diarrhea":    ["diarrhea", "loose stool", "stomach upset"],
        "fatigue":     ["fatigue", "tired", "weakness", "energy", "weak"],
        "pain":        ["pain", "ache", "sore", "hurt"],
        "breathless":  ["breathless", "breathing", "breath", "chest"],
    }

    found_symptoms = []
    for symptom, keywords in symptom_keywords.items():
        if any(kw in msg for kw in keywords):
            found_symptoms.append(symptom)

    # Detect duration
    duration = "unknown"
    duration_patterns = [
        (r"(\d+)\s*day", lambda m: f"{m.group(1)} days"),
        (r"(\d+)\s*week", lambda m: f"{m.group(1)} weeks"),
        (r"since\s+(\w+)", lambda m: f"since {m.group(1)}"),
        (r"for\s+(\d+)", lambda m: f"{m.group(1)} days"),
    ]
    for pattern, formatter in duration_patterns:
        match = re.search(pattern, msg)
        if match:
            try:
                duration = formatter(match)
                break
            except Exception:
                pass

    # Detect category
    category = "general"
    if any(s in found_symptoms for s in ["fever", "headache", "body ache", "chills"]):
        category = "fever"
    elif any(s in found_symptoms for s in ["cough", "cold", "breathless"]):
        category = "respiratory"
    elif any(s in found_symptoms for s in ["nausea", "diarrhea"]):
        category = "gastrointestinal"
    elif "fatigue" in found_symptoms:
        category = "general"
    elif "pain" in found_symptoms:
        category = "pain"

    has_symptoms = len(found_symptoms) > 0 or len(msg.split()) > 5

    return {
        "has_symptoms":            has_symptoms,
        "extracted_symptoms":      found_symptoms if found_symptoms else [message[:50]],
        "duration":                duration,
        "symptom_summary":         message[:150],
        "symptom_category":        category,
        "needs_medical_attention": len(found_symptoms) >= 2,
        "rag_context":             rag_context,
        "pdf_used":                rag_result["has_pdf"],
        "model_used":              "keyword_fallback",
    }