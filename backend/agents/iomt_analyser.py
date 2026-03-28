
"""
FILE: agents/iomt_analyser.py
 
Agent 6 — IoMT Vitals Analyser
Reads IoMT device data, calculates risk levels, generates clinical summary.
Runs when IoMT data is available alongside user query.
Placeholder-safe — works with or without real IoMT API keys.
"""
 
import logging
from core.llm_client import call_llm
from services.emergency_service import check_vitals_emergency
 
logger = logging.getLogger(__name__)
 
 
def run_iomt_analyser(
    iomt_data: dict,
    symptom_summary: str = "",
    user_mode: str = "general",
    user_profile: dict = None,
) -> dict:
    """
    Analyses IoMT vitals and generates risk assessment + recommendations.
 
    Returns:
    {
        "vitals_summary":     str,
        "risk_level":         str,   (normal / warning / critical)
        "risk_flags":         list[str],
        "vitals_context":     str,   (formatted for LLM context injection)
        "recommendation":     str,
        "model_used":         str,
    }
    """
    if not iomt_data:
        return {
            "vitals_summary":  "No IoMT data available.",
            "risk_level":      "normal",
            "risk_flags":      [],
            "vitals_context":  "",
            "recommendation":  "",
            "model_used":      "none",
        }
 
    profile = user_profile or {}
 
    # Rule-based vitals check first
    vitals_check = check_vitals_emergency(iomt_data)
 
    # Build formatted vitals string
    vitals_lines = []
    fields = [
        ("heart_rate",   "Heart Rate",   "bpm"),
        ("spo2",         "SpO2",         "%"),
        ("temperature",  "Temperature",  "°C"),
        ("systolic_bp",  "Systolic BP",  "mmHg"),
        ("diastolic_bp", "Diastolic BP", "mmHg"),
        ("glucose",      "Glucose",      "mg/dL"),
    ]
    for key, label, unit in fields:
        val = iomt_data.get(key)
        if val is not None:
            vitals_lines.append(f"{label}: {val} {unit}")
 
    vitals_text = "\n".join(vitals_lines)
 
    # Build context string for other agents
    vitals_context = f"Current IoMT readings:\n{vitals_text}"
    if vitals_check["alerts"]:
        vitals_context += f"\nAlerts: {'; '.join(vitals_check['alerts'])}"
 
    # Use LLM to generate a natural-language vitals summary
    prompt = f"""
Patient vitals from IoMT device:
{vitals_text}
 
Patient complaint: {symptom_summary or 'Routine monitoring'}
Patient profile: Age {profile.get('age', 'unknown')}, Sex {profile.get('sex', 'unknown')}
Known conditions: {', '.join(profile.get('known_conditions', [])) or 'none'}
 
Provide a brief clinical assessment of these vitals in 2-3 sentences.
State whether each reading is normal, concerning, or critical.
Give one clear recommendation based on the overall picture.
Keep it concise and {'technical' if user_mode == 'medical' else 'easy to understand'}.
"""
 
    try:
        result = call_llm(
            prompt=prompt,
            user_mode=user_mode,
            force_model="llama-3.1-8b-instant",
        )
        vitals_summary = result["content"]
        model_used     = result["model_used"]
    except Exception as e:
        logger.warning(f"IoMT LLM summary failed: {e}")
        vitals_summary = vitals_text
        model_used     = "fallback"
 
    # Generate recommendation
    if vitals_check["is_critical"]:
        recommendation = "🚨 Critical vitals detected. Seek emergency medical care immediately. Call 108."
    elif vitals_check["risk_level"] == "warning":
        recommendation = "⚠️ Some vitals are outside normal range. Consult a doctor today."
    else:
        recommendation = "✅ Vitals are within acceptable range. Continue monitoring."
 
    return {
        "vitals_summary":  vitals_summary,
        "risk_level":      vitals_check["risk_level"],
        "risk_flags":      vitals_check["alerts"],
        "vitals_context":  vitals_context,
        "recommendation":  recommendation,
        "model_used":      model_used,
    }