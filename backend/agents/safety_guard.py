"""
FILE: agents/safety_guard.py

Agent 1 — Safety Guard
Runs FIRST on every single message before any other agent.
If emergency detected → returns immediately, no other agent runs.
Zero API calls — pure keyword + pattern matching, instant response.
"""

from services.emergency_service import detect_emergency, check_vitals_emergency


def run_safety_guard(
    message: str,
    iomt_data: dict | None = None,
) -> dict:
    """
    Scan message and IoMT vitals for emergencies.

    Returns:
    {
        "is_emergency":      bool,
        "is_mental_health":  bool,
        "emergency_response": str,   (pre-written response if emergency)
        "vitals_alerts":     list,   (list of vitals warning strings)
        "vitals_risk":       str,    (normal / warning / critical)
        "should_stop":       bool,   (True = stop pipeline, return response now)
    }
    """
    result = {
        "is_emergency":       False,
        "is_mental_health":   False,
        "emergency_response": "",
        "vitals_alerts":      [],
        "vitals_risk":        "normal",
        "should_stop":        False,
    }

    # 1. Check message for emergency keywords
    emergency = detect_emergency(message)
    if emergency["is_emergency"]:
        result["is_emergency"]       = True
        result["is_mental_health"]   = emergency["is_mental_health"]
        result["emergency_response"] = emergency["response"]
        result["should_stop"]        = True
        return result

    # 2. Check IoMT vitals if available
    if iomt_data:
        vitals_check = check_vitals_emergency(iomt_data)
        result["vitals_alerts"] = vitals_check["alerts"]
        result["vitals_risk"]   = vitals_check["risk_level"]

        if vitals_check["is_critical"]:
            alert_text = "\n".join(vitals_check["alerts"])
            result["is_emergency"] = True
            result["emergency_response"] = (
                f"🚨 **CRITICAL VITALS DETECTED**\n\n"
                f"{alert_text}\n\n"
                f"**Call emergency services immediately:**\n"
                f"- Ambulance: **108**\n"
                f"- National Emergency: **112**\n\n"
                f"Do not wait. Seek medical attention right now."
            )
            result["should_stop"] = True

    return result