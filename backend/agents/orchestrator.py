"""
FILE: agents/orchestrator.py  — FINAL VERSION

Key fixes:
1. Passes severity + has_pdf to all LLM calls
2. Smart routing: document queries use document prompt
3. Supabase chat history save for logged-in users
4. Cleaner context building
"""

import logging
import asyncio
from core.llm_client import call_llm, _is_document_query
from core.session_manager import (
    get_session, add_message, set_iomt_data, get_chat_history
)
from agents.safety_guard        import run_safety_guard
from agents.symptom_interpreter import run_symptom_interpreter
from agents.severity_assessor   import run_severity_assessor
from agents.diagnosis_support   import run_diagnosis_support
from agents.treatment_recommender import run_treatment_recommender
from agents.iomt_analyser       import run_iomt_analyser
from rag.vector_store           import search_all

logger = logging.getLogger(__name__)

CONVERSATIONAL = [
    "hello", "hi", "hey", "thanks", "thank you", "ok", "okay", "bye",
    "who are you", "what can you do", "namaste", "good morning", "good evening",
]

def _is_conversational(msg: str) -> bool:
    m = msg.lower().strip()
    return len(m.split()) <= 6 and any(kw in m for kw in CONVERSATIONAL)


async def process_message(
    session_id: str,
    message:    str,
    user_mode:  str = "general",
    iomt_data:  dict | None = None,
) -> dict:

    session      = get_session(session_id)
    user_profile = session.get("user_profile", {})
    chat_history = session.get("chat_history", [])
    stored_iomt  = session.get("iomt_data") or iomt_data
    has_pdf      = session.get("pdf_filename") is not None

    if iomt_data:
        set_iomt_data(session_id, iomt_data)

    result = {
        "response":            "",
        "is_emergency":        False,
        "emergency_response":  "",
        "severity":            "low",
        "has_prescription":    False,
        "vitals_risk":         "normal",
        "vitals_alerts":       [],
        "suggested_questions": [],
        "sources":             [],
        "model_used":          "",
        "agents_used":         [],
    }

    agents_used = []

    # ── Step 1: Safety Guard ──────────────────────────────────────────────────
    agents_used.append("safety_guard")
    safety = run_safety_guard(message, stored_iomt)
    result["vitals_risk"]   = safety["vitals_risk"]
    result["vitals_alerts"] = safety["vitals_alerts"]

    if safety["should_stop"]:
        result.update({
            "is_emergency":      True,
            "emergency_response": safety["emergency_response"],
            "response":          safety["emergency_response"],
            "agents_used":       agents_used,
        })
        add_message(session_id, "user",      message)
        add_message(session_id, "assistant", safety["emergency_response"])
        return result

    # ── Step 2: Conversational fast path ─────────────────────────────────────
    if _is_conversational(message):
        agents_used.append("direct_llm")
        llm_result = call_llm(
            prompt=message, user_mode=user_mode,
            chat_history=chat_history, severity="low", has_pdf=False,
        )
        result.update({
            "response":            llm_result["content"],
            "model_used":          llm_result["model_used"],
            "agents_used":         agents_used,
            "suggested_questions": _suggestions("general", "low"),
        })
        add_message(session_id, "user",      message)
        add_message(session_id, "assistant", llm_result["content"])
        return result

    # ── Step 3: Get RAG context ───────────────────────────────────────────────
    rag_result  = search_all(session_id, message, pdf_results=5, kb_results=4)
    rag_context = rag_result["context_string"]
    pdf_used    = rag_result["has_pdf"]

    # ── Step 4: Document query fast path ─────────────────────────────────────
    if has_pdf and _is_document_query(message):
        agents_used.append("document_agent")
        llm_result = call_llm(
            prompt=message, user_mode="document",
            context=rag_context, chat_history=chat_history,
            severity="low", has_pdf=True,
        )
        sources = ["Your uploaded document"]
        if rag_result["has_kb"]:
            sources.append("Medical knowledge base")

        result.update({
            "response":            llm_result["content"],
            "model_used":          llm_result["model_used"],
            "agents_used":         agents_used,
            "sources":             sources,
            "suggested_questions": [
                "What are the key findings?",
                "What methodology was used?",
                "What are the limitations?",
                "What is the conclusion?",
            ],
        })
        add_message(session_id, "user",      message)
        add_message(session_id, "assistant", llm_result["content"])
        return result

    # ── Step 5: IoMT analysis ─────────────────────────────────────────────────
    vitals_context = ""
    if stored_iomt:
        agents_used.append("iomt_analyser")
        iomt_result    = run_iomt_analyser(stored_iomt, message, user_mode, user_profile)
        vitals_context = iomt_result["vitals_context"]
        result["vitals_risk"]   = iomt_result["risk_level"]
        result["vitals_alerts"] = iomt_result["risk_flags"]

    # ── Step 6: Symptom interpretation ───────────────────────────────────────
    agents_used.append("symptom_interpreter")
    symptom = run_symptom_interpreter(
        message=message, session_id=session_id,
        user_mode=user_mode, user_profile=user_profile,
        chat_history=chat_history, iomt_data=stored_iomt,
    )

    full_context = ""
    if vitals_context:
        full_context += f"{vitals_context}\n\n"
    if rag_context:
        full_context += rag_context

    # ── Step 7: Severity assessment ───────────────────────────────────────────
    agents_used.append("severity_assessor")
    sev = run_severity_assessor(
        symptom_summary    = symptom["symptom_summary"],
        extracted_symptoms = symptom["extracted_symptoms"],
        symptom_category   = symptom.get("symptom_category", "general"),
        duration           = symptom["duration"],
        user_mode          = user_mode,
        user_profile       = user_profile,
        iomt_data          = stored_iomt,
        vitals_alerts      = result["vitals_alerts"],
    )
    severity = sev["severity"]
    result["severity"] = severity

    # ── Step 8: Diagnosis ─────────────────────────────────────────────────────
    agents_used.append("diagnosis_support")
    diag = await run_diagnosis_support(
        symptom_summary    = symptom["symptom_summary"],
        extracted_symptoms = symptom["extracted_symptoms"],
        symptom_category   = symptom.get("symptom_category", "general"),
        severity           = severity,
        user_mode          = user_mode,
        user_profile       = user_profile,
        iomt_data          = stored_iomt,
        rag_context        = full_context,
        chat_history       = chat_history,
    )

    # ── Step 9: Treatment ─────────────────────────────────────────────────────
    agents_used.append("treatment_recommender")
    treat = await run_treatment_recommender(
        symptom_summary       = symptom["symptom_summary"],
        extracted_symptoms    = symptom["extracted_symptoms"],
        severity              = severity,
        most_likely_condition = diag["most_likely"],
        user_mode             = user_mode,
        user_profile          = user_profile,
        iomt_data             = stored_iomt,
        rag_context           = full_context,
        chat_history          = chat_history,
    )

    # ── Step 10: Assemble final response ──────────────────────────────────────
    final = _assemble(diag["diagnosis_response"], treat["treatment_response"], severity, user_mode)

    # Build sources
    sources = []
    if pdf_used:
        sources.append("Your uploaded document")
    sources.append("Medical knowledge base (WHO/ICMR guidelines)")
    if treat["drug_validation"].get("has_warnings"):
        sources.append("OpenFDA drug safety database")

    result.update({
        "response":            final,
        "has_prescription":    treat["has_prescription"],
        "model_used":          treat["model_used"],
        "agents_used":         agents_used,
        "sources":             sources,
        "suggested_questions": _suggestions(symptom.get("symptom_category","general"), severity),
    })

    add_message(session_id, "user",      message)
    add_message(session_id, "assistant", final)

    # Save to Supabase if user logged in
    asyncio.create_task(_save_to_supabase(session_id, message, final))

    return result


def _assemble(diag: str, treat: str, severity: str, user_mode: str) -> str:
    """Combine diagnosis and treatment, avoiding duplication."""
    if not treat or treat.strip() == diag.strip():
        return diag
    # If treatment response is clearly different and adds value, combine
    if len(treat) > 100 and treat not in diag:
        return f"{diag}\n\n{treat}"
    return diag


def _suggestions(category: str, severity: str) -> list:
    base = [
        "What medicines should I take?",
        "When should I see a doctor?",
        "What foods should I avoid?",
    ]
    extras = {
        "fever":          ["Could this be dengue?", "How to bring down fever quickly?"],
        "respiratory":    ["Is this contagious?",   "Should I wear a mask?"],
        "gastrointestinal": ["What should I eat?",  "How to prevent dehydration?"],
        "mental health":  ["Free counselling helplines in India?", "How to manage anxiety?"],
        "diabetes":       ["What is a normal blood sugar?",        "Which foods spike sugar?"],
        "cardiac":        ["How to monitor blood pressure at home?"],
    }.get(category.lower(), [])

    if severity in ("high", "critical"):
        extras = ["What are the emergency warning signs?"] + extras

    return (extras + base)[:4]


async def _save_to_supabase(session_id: str, user_msg: str, assistant_msg: str):
    """Save messages to Supabase for logged-in users (non-blocking)."""
    try:
        from database.supabase_client import get_supabase
        sb = get_supabase()
        if not sb:
            return
        # Save user message
        sb.table("chat_messages").insert({
            "session_id": session_id,
            "role":       "user",
            "content":    user_msg,
        }).execute()
        # Save assistant message
        sb.table("chat_messages").insert({
            "session_id": session_id,
            "role":       "assistant",
            "content":    assistant_msg,
        }).execute()
    except Exception as e:
        logger.debug(f"Supabase save skipped: {e}")