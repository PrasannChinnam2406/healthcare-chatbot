"""
FILE: agents/treatment_recommender.py

Agent 5 — Treatment Recommender
Generates medicine recommendations with dosage, care steps, diet advice.
Validates medicines against OpenFDA + RxNorm before responding.
"""

import logging
import asyncio
from core.llm_client import call_llm
from rag.vector_store import search_kb
from services.openfda_service import validate_prescription, format_validation_for_context

logger = logging.getLogger(__name__)


async def run_treatment_recommender(
    symptom_summary: str,
    extracted_symptoms: list,
    severity: str,
    most_likely_condition: str,
    user_mode: str = "general",
    user_profile: dict = None,
    iomt_data: dict = None,
    rag_context: str = "",
    chat_history: list = None,
) -> dict:
    """
    Generates treatment recommendations validated against drug safety APIs.

    Returns:
    {
        "treatment_response": str,
        "medicines_mentioned": list[str],
        "drug_validation":     dict,
        "has_prescription":    bool,
        "model_used":          str,
    }
    """
    profile = user_profile or {}
    history = chat_history or []

    # Get drug-specific KB context
    drug_query    = f"treatment medicine dosage {most_likely_condition} {symptom_summary}"
    drug_chunks   = search_kb(drug_query, n_results=4)
    drug_context  = "\n".join([c["text"] for c in drug_chunks])

    full_context = ""
    if rag_context:
        full_context += f"{rag_context}\n\n"
    if drug_context:
        full_context += f"Drug reference:\n{drug_context}"

    # Build patient-specific constraints
    contraindication_notes = _get_contraindications(profile)

    # Build prompt
    prompt = _build_treatment_prompt(
        symptom_summary    = symptom_summary,
        symptoms           = extracted_symptoms,
        severity           = severity,
        condition          = most_likely_condition,
        user_mode          = user_mode,
        profile            = profile,
        iomt_data          = iomt_data,
        contraindications  = contraindication_notes,
    )

    result = call_llm(
        prompt       = prompt,
        user_mode    = user_mode,
        context      = full_context,
        chat_history = history,
    )

    response_text = result["content"]

    # Extract medicine names from response for validation
    medicines = _extract_medicine_names(response_text)

    # Validate medicines against OpenFDA + RxNorm
    drug_validation = {}
    validation_context = ""
    if medicines:
        try:
            drug_validation    = await validate_prescription(medicines)
            validation_context = format_validation_for_context(drug_validation)
        except Exception as e:
            logger.warning(f"Drug validation failed: {e}")

    # If validation found warnings, regenerate with that context
    if validation_context:
        enhanced_prompt = f"{prompt}\n\nImportant drug safety notes to incorporate:\n{validation_context}"
        result2 = call_llm(
            prompt       = enhanced_prompt,
            user_mode    = user_mode,
            context      = full_context,
            chat_history = history,
        )
        response_text = result2["content"]
        result        = result2

    return {
        "treatment_response":  response_text,
        "medicines_mentioned": medicines,
        "drug_validation":     drug_validation,
        "has_prescription":    len(medicines) > 0,
        "model_used":          result["model_used"],
    }


def _build_treatment_prompt(
    symptom_summary: str,
    symptoms: list,
    severity: str,
    condition: str,
    user_mode: str,
    profile: dict,
    iomt_data: dict | None,
    contraindications: str,
) -> str:

    patient_ctx = ""
    if profile.get("age"):
        patient_ctx += f"Age: {profile['age']}. "
    if profile.get("sex"):
        patient_ctx += f"Sex: {profile['sex']}. "
    if profile.get("known_conditions"):
        patient_ctx += f"Has: {', '.join(profile['known_conditions'])}. "
    if profile.get("allergies"):
        patient_ctx += f"Allergic to: {', '.join(profile['allergies'])}. "

    if user_mode == "medical":
        return f"""
{patient_ctx}
Condition: {condition} | Severity: {severity}
Symptoms: {', '.join(symptoms)}
{contraindications}

Provide evidence-based treatment protocol:
## Pharmacological Treatment
For each drug: generic name (Indian brand), dose, route, frequency, duration, monitoring.
Flag prescription-only drugs clearly.

## Non-Pharmacological Management
Specific interventions beyond medication.

## Follow-Up
When to reassess, what to monitor, referral criteria.

## Drug Interactions
Note any significant interactions especially with patient's current medications.
"""

    elif user_mode == "patient":
        return f"""
{patient_ctx}
Most likely condition: {condition}
Severity: {severity}
Symptoms: {', '.join(symptoms)}
{contraindications}

Provide detailed treatment advice:
## Medicines

For EACH recommended medicine write:
**[Medicine Name] ([Brand Name e.g. Crocin, Dolo 650])**
- Dosage: exact amount
- Frequency: how many times daily
- Duration: number of days
- Take with: food/water/empty stomach
- Warning: any important cautions

Only recommend medicines available OTC in India.
If prescription needed write: "⚕️ This requires a doctor's prescription"

## Home Care Steps
Specific actions to do at home.

## Diet and Hydration
What to eat, avoid, and drink.

## When to See a Doctor Immediately
Clear red flag symptoms as bullet points.
"""

    else:  # general mode
        return f"""
{patient_ctx}
Complaint: {symptom_summary}
Severity: {severity}
{contraindications}

Give friendly, clear treatment advice:
1. What medicines can help (common OTC medicines available in India with names)
2. Simple home care steps
3. When to see a doctor

Keep it simple and easy to understand.
"""


def _get_contraindications(profile: dict) -> str:
    """Build contraindication notes from patient profile."""
    notes = []
    conditions  = [c.lower() for c in profile.get("known_conditions", [])]
    allergies   = [a.lower() for a in profile.get("allergies", [])]
    medications = profile.get("current_medications", [])

    if "liver" in " ".join(conditions) or "liver disease" in conditions:
        notes.append("CAUTION: Patient has liver disease — avoid hepatotoxic drugs, reduce paracetamol dose")
    if "kidney" in " ".join(conditions) or "renal" in " ".join(conditions):
        notes.append("CAUTION: Patient has kidney disease — adjust drug doses, avoid NSAIDs")
    if "diabetes" in conditions:
        notes.append("NOTE: Patient is diabetic — monitor glucose, some antibiotics affect glucose control")
    if "hypertension" in conditions:
        notes.append("NOTE: Patient has hypertension — avoid high-sodium ORS, caution with NSAIDs")
    if "penicillin" in allergies:
        notes.append("ALLERGY: Penicillin allergy — avoid Amoxicillin and all beta-lactam antibiotics")
    if "sulpha" in " ".join(allergies) or "sulfonamide" in " ".join(allergies):
        notes.append("ALLERGY: Sulpha drug allergy — avoid Cotrimoxazole")
    if medications:
        notes.append(f"Current medications to check interactions with: {', '.join(medications)}")

    return "\n".join(notes) if notes else ""


def _extract_medicine_names(text: str) -> list[str]:
    """Extract medicine names from treatment response for API validation."""
    common_medicines = [
        "paracetamol", "crocin", "dolo", "ibuprofen", "brufen", "combiflam",
        "cetirizine", "zyrtec", "azithromycin", "azee", "amoxicillin", "amoxil",
        "metformin", "pantoprazole", "omeprazole", "ondansetron", "loperamide",
        "doxycycline", "ciprofloxacin", "metronidazole", "flagyl",
        "amlodipine", "telmisartan", "atenolol", "aspirin", "clopidogrel",
    ]
    text_lower  = text.lower()
    found       = []
    for med in common_medicines:
        if med in text_lower and med not in found:
            found.append(med)
    return found[:5]  # limit to 5 for API call efficiency