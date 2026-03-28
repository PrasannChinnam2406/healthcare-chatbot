"""
FILE: services/emergency_service.py

Emergency detector — runs on EVERY user message before any agent.
Uses keyword matching + pattern detection. Zero API calls — instant.

If emergency detected → safety_guard agent short-circuits the whole
pipeline and returns the emergency response immediately.
"""

import re
import os
import logging

logger = logging.getLogger(__name__)

# ── Load keyword list from file ────────────────────────────────────────────────

KEYWORDS_FILE = os.path.join(
    os.path.dirname(__file__), "..", "data", "medical_kb", "emergency_keywords.txt"
)

def _load_keywords() -> list[str]:
    try:
        with open(KEYWORDS_FILE, "r", encoding="utf-8") as f:
            return [line.strip().lower() for line in f if line.strip()]
    except Exception:
        logger.warning("emergency_keywords.txt not found — using built-in list.")
        return []

_KEYWORDS = _load_keywords()

# ── Hardcoded critical patterns (always checked regardless of file) ────────────

CRITICAL_PATTERNS = [
    r"chest\s*pain",
    r"can.?t\s*breathe",
    r"(not|stop).{0,10}breathing",
    r"heart\s*attack",
    r"stroke",
    r"(unconscious|unresponsive|collapsed|fainted)",
    r"(suicid|kill\s*myself|want\s*to\s*die|end\s*my\s*life)",
    r"(overdose|swallowed.{0,20}poison|drank.{0,20}poison)",
    r"(seizure|convulsion|fit)",
    r"(severe|heavy)\s*bleed",
    r"blood.{0,15}(vomit|stool|urine)",
    r"spo2.{0,10}(low|below|drop)",
    r"oxygen.{0,10}(low|very low|dropping)",
    r"not\s*moving",
    r"severe\s*allergic",
    r"anaphyla",
    r"face\s*(swoll|swelling)",
    r"throat\s*(swoll|closing|tighten)",
    r"very\s*high\s*(bp|blood\s*pressure)",
    r"bp\s*(above|over)\s*1[89]\d",
    r"(baby|infant|newborn).{0,20}(breath|breath|blue|limp)",
]

_COMPILED = [re.compile(p, re.IGNORECASE) for p in CRITICAL_PATTERNS]

# ── Emergency response templates ───────────────────────────────────────────────

EMERGENCY_RESPONSE = """🚨 **MEDICAL EMERGENCY DETECTED**

Based on what you've described, this may be a **medical emergency** requiring immediate attention.

## Call Emergency Services NOW

| Service | Number |
|---------|--------|
| **Ambulance (India)** | **108** |
| **National Emergency** | **112** |

## While Waiting for Help
- Keep the person **calm and still**
- **Do not give food or water**
- If unconscious and not breathing → start **CPR** if you know how
- Stay on the line with emergency services — they will guide you

## Important
Do not wait to see if symptoms improve. Get emergency help immediately.

---
*I am an AI assistant and cannot replace emergency medical services. Please call 108 now.*"""

MENTAL_HEALTH_EMERGENCY = """I'm really concerned about what you've shared, and I want you to know that **you are not alone**.

## Please Reach Out Right Now

| Helpline | Number | Available |
|----------|--------|-----------|
| **Vandrevala Foundation** | **1860-2662-345** | 24/7, Free |
| **iCall (TISS)** | **9152987821** | Mon-Sat, 8am-10pm |
| **AASRA** | **9820466627** | 24/7 |
| **Emergency** | **112** | 24/7 |

## You Matter
What you're feeling right now is real and valid. Trained counsellors are ready to listen — completely confidential, completely free.

**Please call one of these numbers right now.**

---
*If you are in immediate danger, please call 112 or go to the nearest hospital emergency.*"""


# ── Main detection function ────────────────────────────────────────────────────

def detect_emergency(text: str) -> dict:
    """
    Scan a message for emergency signals.

    Returns:
    {
        "is_emergency":    bool,
        "is_mental_health": bool,
        "matched_pattern": str,
        "response":        str   (pre-written emergency response)
    }
    """
    text_lower = text.lower()

    # 1. Check mental health / suicide keywords first (separate response)
    mental_patterns = [
        r"(suicid|kill\s*myself|want\s*to\s*die|end\s*my\s*life|self.?harm)",
        r"(no\s*reason\s*to\s*live|life\s*is\s*worthless|better\s*off\s*dead)",
    ]
    for p in mental_patterns:
        if re.search(p, text_lower, re.IGNORECASE):
            return {
                "is_emergency":     True,
                "is_mental_health": True,
                "matched_pattern":  p,
                "response":         MENTAL_HEALTH_EMERGENCY,
            }

    # 2. Check compiled critical patterns
    for pattern in _COMPILED:
        match = pattern.search(text_lower)
        if match:
            return {
                "is_emergency":     True,
                "is_mental_health": False,
                "matched_pattern":  match.group(),
                "response":         EMERGENCY_RESPONSE,
            }

    # 3. Check keyword list from file
    for keyword in _KEYWORDS:
        if keyword and keyword in text_lower:
            return {
                "is_emergency":     True,
                "is_mental_health": False,
                "matched_pattern":  keyword,
                "response":         EMERGENCY_RESPONSE,
            }

    return {
        "is_emergency":     False,
        "is_mental_health": False,
        "matched_pattern":  "",
        "response":         "",
    }


# ── IoMT vitals emergency check ────────────────────────────────────────────────

def check_vitals_emergency(vitals: dict) -> dict:
    """
    Check IoMT vitals for critical values.
    Called by iomt_analyser agent when new vitals arrive.

    vitals: {
        "heart_rate":    float,
        "spo2":          float,
        "temperature":   float,    (Celsius)
        "systolic_bp":   float,
        "diastolic_bp":  float,
        "glucose":       float,    (mg/dL)
    }
    """
    alerts = []
    is_critical = False

    hr  = vitals.get("heart_rate")
    spo2 = vitals.get("spo2")
    temp = vitals.get("temperature")
    sbp  = vitals.get("systolic_bp")
    dbp  = vitals.get("diastolic_bp")
    gluc = vitals.get("glucose")

    if spo2 is not None:
        if spo2 < 90:
            alerts.append(f"🚨 CRITICAL: SpO2 {spo2}% — Dangerously low oxygen. Emergency care needed.")
            is_critical = True
        elif spo2 < 94:
            alerts.append(f"⚠️ WARNING: SpO2 {spo2}% — Below normal. Monitor closely.")

    if hr is not None:
        if hr > 150 or hr < 40:
            alerts.append(f"🚨 CRITICAL: Heart rate {hr} bpm — Requires immediate medical attention.")
            is_critical = True
        elif hr > 120 or hr < 50:
            alerts.append(f"⚠️ WARNING: Heart rate {hr} bpm — Outside normal range.")

    if temp is not None:
        if temp > 40.0:
            alerts.append(f"🚨 CRITICAL: Temperature {temp}°C — High fever requiring urgent care.")
            is_critical = True
        elif temp > 38.5:
            alerts.append(f"⚠️ WARNING: Temperature {temp}°C — Fever. Monitor and treat.")
        elif temp < 35.0:
            alerts.append(f"🚨 CRITICAL: Temperature {temp}°C — Hypothermia. Warm patient immediately.")
            is_critical = True

    if sbp is not None:
        if sbp > 180:
            alerts.append(f"🚨 CRITICAL: BP {sbp}/{dbp or '?'} mmHg — Hypertensive crisis. Emergency care.")
            is_critical = True
        elif sbp < 80:
            alerts.append(f"🚨 CRITICAL: BP {sbp}/{dbp or '?'} mmHg — Severe hypotension / shock.")
            is_critical = True
        elif sbp > 140:
            alerts.append(f"⚠️ WARNING: BP {sbp}/{dbp or '?'} mmHg — High. Check again in 10 minutes.")

    if gluc is not None:
        if gluc < 54:
            alerts.append(f"🚨 CRITICAL: Glucose {gluc} mg/dL — Severe hypoglycemia. Give sugar immediately.")
            is_critical = True
        elif gluc > 400:
            alerts.append(f"🚨 CRITICAL: Glucose {gluc} mg/dL — Dangerously high. Seek emergency care.")
            is_critical = True
        elif gluc < 70:
            alerts.append(f"⚠️ WARNING: Glucose {gluc} mg/dL — Low. Eat or drink sugar now.")
        elif gluc > 250:
            alerts.append(f"⚠️ WARNING: Glucose {gluc} mg/dL — High. Check with doctor.")

    # determine overall risk level
    if is_critical:
        risk_level = "critical"
    elif alerts:
        risk_level = "warning"
    else:
        risk_level = "normal"

    return {
        "risk_level":  risk_level,
        "is_critical": is_critical,
        "alerts":      alerts,
        "alert_count": len(alerts),
    }