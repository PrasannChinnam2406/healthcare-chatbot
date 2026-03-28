"""
FILE: agents/severity_assessor.py

Agent 3 — Severity Assessor
Determines urgency level based on symptoms + IoMT vitals.
Outputs: low / moderate / high / critical
"""

import json
import logging
from core.llm_client import call_llm

logger = logging.getLogger(__name__)

# Severity level definitions used across the system
SEVERITY_LEVELS = {
    "low":      "Mild symptoms. Home care likely sufficient. Monitor for changes.",
    "moderate": "Symptoms need attention. See a doctor within 24-48 hours.",
    "high":     "Significant symptoms. See a doctor today.",
    "critical": "Requires immediate emergency care. Go to hospital now or call 108.",
}


def run_severity_assessor(
    symptom_summary: str,
    extracted_symptoms: list,
    symptom_category: str,
    duration: str,
    user_mode: str = "general",
    user_profile: dict = None,
    iomt_data: dict = None,
    vitals_alerts: list = None,
) -> dict:
    """
    Assesses severity of the patient's condition.

    Returns:
    {
        "severity":          str,   (low / moderate / high / critical)
        "severity_reason":   str,
        "urgent_flags":      list[str],
        "model_used":        str,
    }
    """
    profile     = user_profile or {}
    alerts      = vitals_alerts or []

    # Build context for assessment
    context_parts = []

    if extracted_symptoms:
        context_parts.append(f"Reported symptoms: {', '.join(extracted_symptoms)}")
    if duration:
        context_parts.append(f"Duration: {duration}")
    if symptom_category:
        context_parts.append(f"Category: {symptom_category}")

    # Vitals context
    if iomt_data:
        if iomt_data.get("spo2") and iomt_data["spo2"] < 95:
            context_parts.append(f"SpO2 low: {iomt_data['spo2']}%")
        if iomt_data.get("temperature") and iomt_data["temperature"] > 38:
            context_parts.append(f"Fever: {iomt_data['temperature']}°C")
        if iomt_data.get("heart_rate"):
            context_parts.append(f"Heart rate: {iomt_data['heart_rate']} bpm")
        if iomt_data.get("systolic_bp"):
            context_parts.append(f"BP: {iomt_data['systolic_bp']}/{iomt_data.get('diastolic_bp','?')} mmHg")

    if alerts:
        context_parts.append(f"Vitals alerts: {'; '.join(alerts)}")

    # Patient risk factors
    if profile.get("age") and int(profile.get("age", 0)) > 60:
        context_parts.append("Patient is elderly (above 60) — higher risk")
    if profile.get("age") and int(profile.get("age", 0)) < 5:
        context_parts.append("Patient is a young child (below 5) — higher risk")
    if profile.get("known_conditions"):
        context_parts.append(f"Comorbidities: {', '.join(profile['known_conditions'])}")

    assessment_context = "\n".join(context_parts)

    prompt = f"""
Patient information:
{assessment_context}

Patient complaint: {symptom_summary}

Assess the severity level. Respond ONLY with valid JSON:
{{
  "severity": "low or moderate or high or critical",
  "severity_reason": "Brief clinical reason for this severity level",
  "urgent_flags": ["flag1 if any", "flag2 if any"]
}}

Severity guide:
- low: mild symptoms, stable vitals, no red flags, home care ok
- moderate: concerning symptoms, see doctor in 24-48 hours
- high: significant distress, abnormal vitals, see doctor today
- critical: life-threatening signs, emergency care needed immediately

Do not add text outside the JSON.
"""

    try:
        result = call_llm(
            prompt=prompt,
            user_mode="general",
            context="",
            force_model="llama-3.1-8b-instant",
        )

        content = result["content"].strip()
        start   = content.find("{")
        end     = content.rfind("}") + 1
        if start != -1 and end > start:
            parsed = json.loads(content[start:end])
        else:
            raise ValueError("No JSON in response")

        severity = parsed.get("severity", "moderate").lower()
        if severity not in SEVERITY_LEVELS:
            severity = "moderate"

        return {
            "severity":        severity,
            "severity_reason": parsed.get("severity_reason", ""),
            "urgent_flags":    parsed.get("urgent_flags", []),
            "model_used":      result["model_used"],
        }

    except Exception as e:
        logger.warning(f"Severity assessor failed: {e}. Using moderate as default.")

        # Rule-based fallback when LLM fails
        severity = _rule_based_severity(
            extracted_symptoms, iomt_data, profile, alerts
        )
        return {
            "severity":        severity,
            "severity_reason": "Assessed based on symptom patterns",
            "urgent_flags":    alerts[:3],
            "model_used":      "rule_based_fallback",
        }


def _rule_based_severity(
    symptoms: list,
    iomt_data: dict | None,
    profile: dict,
    vitals_alerts: list,
) -> str:
    """Simple rule-based fallback severity assessment."""

    # Critical vitals
    if iomt_data:
        spo2 = iomt_data.get("spo2", 100)
        temp = iomt_data.get("temperature", 37)
        sbp  = iomt_data.get("systolic_bp", 120)
        hr   = iomt_data.get("heart_rate", 75)
        if spo2 < 90 or temp > 40 or sbp > 180 or sbp < 80 or hr > 150 or hr < 40:
            return "critical"
        if spo2 < 94 or temp > 38.5 or sbp > 140:
            return "high"

    # High severity symptoms
    high_keywords = [
        "chest pain", "breathing", "breath", "unconscious", "seizure",
        "fits", "severe", "blood", "bleed", "stroke", "paralysis"
    ]
    symptom_text = " ".join(symptoms).lower()
    if any(k in symptom_text for k in high_keywords):
        return "high"

    # Elderly or young child with any symptoms
    age = int(profile.get("age", 30) or 30)
    if (age > 60 or age < 5) and symptoms:
        return "moderate"

    # Duration-independent mild symptoms
    if len(symptoms) <= 2:
        return "low"

    return "moderate"