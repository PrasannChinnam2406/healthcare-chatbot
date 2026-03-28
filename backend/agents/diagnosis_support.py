"""
FILE: agents/diagnosis_support.py

Agent 4 — Diagnosis Support
Generates differential diagnosis using RAG context + LLM reasoning.
Optionally cross-validates with WHO ICD-11 in medical professional mode.
"""

import logging
from core.llm_client import call_llm
from rag.vector_store import search_kb

logger = logging.getLogger(__name__)


async def run_diagnosis_support(
    symptom_summary: str,
    extracted_symptoms: list,
    symptom_category: str,
    severity: str,
    user_mode: str = "general",
    user_profile: dict = None,
    iomt_data: dict = None,
    rag_context: str = "",
    chat_history: list = None,
) -> dict:
    """
    Generates diagnosis support based on symptoms and retrieved medical context.

    Returns:
    {
        "possible_conditions":  list[str],
        "most_likely":          str,
        "icd11_codes":          list[dict],  (medical mode only)
        "diagnosis_context":    str,
        "model_used":           str,
    }
    """
    profile = user_profile or {}
    history = chat_history or []

    # Build patient context
    patient_ctx = _build_patient_context(profile, iomt_data, severity)

    # Get additional KB context specifically for diagnosis
    symptom_query = f"diagnosis {symptom_summary} {' '.join(extracted_symptoms[:5])}"
    kb_chunks     = search_kb(symptom_query, n_results=4)
    extra_context = "\n".join([c["text"] for c in kb_chunks])

    # Combine all context
    full_context = ""
    if rag_context:
        full_context += f"{rag_context}\n\n"
    if extra_context:
        full_context += f"Additional medical reference:\n{extra_context}"

    # Build diagnosis prompt based on user mode
    if user_mode == "medical":
        prompt = _build_medical_prompt(
            symptom_summary, extracted_symptoms, patient_ctx, severity
        )
    elif user_mode == "patient":
        prompt = _build_patient_prompt(
            symptom_summary, extracted_symptoms, patient_ctx, severity
        )
    else:
        prompt = _build_general_prompt(
            symptom_summary, extracted_symptoms, patient_ctx
        )

    result = call_llm(
        prompt=prompt,
        user_mode=user_mode,
        context=full_context,
        chat_history=history,
    )

    # Get ICD-11 codes for medical mode
    icd11_codes = []
    if user_mode == "medical":
        icd11_codes = await _get_icd_codes(symptom_summary)

    # Extract possible conditions from response for structured use
    possible_conditions = _extract_conditions(
        extracted_symptoms, symptom_category
    )

    return {
        "possible_conditions": possible_conditions,
        "most_likely":         possible_conditions[0] if possible_conditions else "",
        "icd11_codes":         icd11_codes,
        "diagnosis_context":   full_context[:500],
        "diagnosis_response":  result["content"],
        "model_used":          result["model_used"],
    }


def _build_general_prompt(
    symptom_summary: str,
    symptoms: list,
    patient_ctx: str,
) -> str:
    return f"""
{patient_ctx}

The patient reports: {symptom_summary}
Symptoms: {', '.join(symptoms)}

Provide a helpful, clear health assessment explaining:
1. What this likely is in simple language
2. Why these symptoms occur together
3. What the patient should do next

Use simple language, no heavy medical jargon.
"""


def _build_patient_prompt(
    symptom_summary: str,
    symptoms: list,
    patient_ctx: str,
    severity: str,
) -> str:
    return f"""
{patient_ctx}
Severity assessed: {severity}

Patient complaint: {symptom_summary}
Symptoms: {', '.join(symptoms)}

Provide a detailed assessment including:
## What This Likely Is
Explain the most probable condition clearly.

## Why You Have These Symptoms
Explain the mechanism in simple terms.

## Severity Assessment
Explain why this is {severity} severity.

Be specific and thorough. The patient wants to understand their condition.
"""


def _build_medical_prompt(
    symptom_summary: str,
    symptoms: list,
    patient_ctx: str,
    severity: str,
) -> str:
    return f"""
{patient_ctx}
Severity: {severity}

Clinical presentation: {symptom_summary}
Symptoms: {', '.join(symptoms)}

Provide clinical differential diagnosis:
## Differential Diagnosis
List top 3-5 conditions ranked by probability with brief clinical reasoning for each.

## Most Likely Diagnosis
Primary diagnosis with supporting features.

## Key Distinguishing Features
What findings would confirm or rule out each differential.

## Recommended Investigations
Specific tests to order with rationale.

Use clinical terminology appropriate for a medical professional.
"""


def _build_patient_context(
    profile: dict,
    iomt_data: dict | None,
    severity: str,
) -> str:
    parts = []
    if profile.get("age"):
        parts.append(f"Age: {profile['age']}")
    if profile.get("sex"):
        parts.append(f"Sex: {profile['sex']}")
    if profile.get("known_conditions"):
        parts.append(f"Known conditions: {', '.join(profile['known_conditions'])}")
    if profile.get("current_medications"):
        parts.append(f"Medications: {', '.join(profile['current_medications'])}")
    if profile.get("allergies"):
        parts.append(f"Allergies: {', '.join(profile['allergies'])}")
    if iomt_data:
        vitals = []
        if iomt_data.get("heart_rate"):
            vitals.append(f"HR {iomt_data['heart_rate']} bpm")
        if iomt_data.get("spo2"):
            vitals.append(f"SpO2 {iomt_data['spo2']}%")
        if iomt_data.get("temperature"):
            vitals.append(f"Temp {iomt_data['temperature']}°C")
        if iomt_data.get("systolic_bp"):
            vitals.append(f"BP {iomt_data['systolic_bp']}/{iomt_data.get('diastolic_bp','?')}")
        if vitals:
            parts.append(f"Vitals: {', '.join(vitals)}")
    return "Patient context: " + " | ".join(parts) if parts else ""


def _extract_conditions(symptoms: list, category: str) -> list:
    """Simple rule-based condition extraction as structured output."""
    category_map = {
        "respiratory": ["Upper respiratory tract infection", "Bronchitis", "Pneumonia"],
        "gastrointestinal": ["Gastroenteritis", "Peptic ulcer", "IBS"],
        "fever": ["Viral fever", "Dengue fever", "Malaria", "Typhoid"],
        "pain": ["Musculoskeletal pain", "Tension headache", "Migraine"],
        "mental health": ["Anxiety disorder", "Depression", "Stress"],
        "cardiac": ["Hypertension", "Angina", "Palpitations"],
    }
    return category_map.get(category.lower(), ["Requires clinical evaluation"])


async def _get_icd_codes(symptom_summary: str) -> list:
    """Fetch ICD-11 codes for medical mode — non-blocking."""
    try:
        from services.who_icd_service import search_icd11_disease
        codes = await search_icd11_disease(symptom_summary, max_results=2)
        return codes
    except Exception as e:
        logger.warning(f"ICD-11 lookup failed: {e}")
        return []