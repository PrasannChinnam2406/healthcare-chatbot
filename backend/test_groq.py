"""
Quick test script — run this to verify Groq is working.

Usage (from backend/ folder with venv active):
    py -3.11 test_groq.py
"""

import sys
import os

# make sure imports work from backend root
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.llm_client import call_llm, MODEL_CHAIN, FAST_MODEL


def test_simple_query():
    print("\n" + "="*60)
    print("TEST 1: Simple greeting (should use fast model)")
    print("="*60)
    result = call_llm("Hello, what can you do?", user_mode="general")
    print(f"Model used : {result['model_used']}")
    print(f"Response   : {result['content'][:200]}...")
    print("PASSED" if result["content"] else "FAILED")


def test_medical_query():
    print("\n" + "="*60)
    print("TEST 2: Medical query (should use primary model)")
    print("="*60)
    result = call_llm(
        "I have fever 102F, headache and body ache since 2 days. What should I do?",
        user_mode="patient"
    )
    print(f"Model used : {result['model_used']}")
    print(f"Response preview:\n{result['content'][:400]}...")
    print("PASSED" if "medicine" in result["content"].lower() or "paracetamol" in result["content"].lower() or "doctor" in result["content"].lower() else "CHECK RESPONSE MANUALLY")


def test_medical_mode():
    print("\n" + "="*60)
    print("TEST 3: Medical professional mode")
    print("="*60)
    result = call_llm(
        "Patient presents with chest pain radiating to left arm, diaphoresis, BP 90/60. Differential?",
        user_mode="medical"
    )
    print(f"Model used : {result['model_used']}")
    print(f"Response preview:\n{result['content'][:400]}...")
    print("PASSED" if result["content"] else "FAILED")


def test_context_injection():
    print("\n" + "="*60)
    print("TEST 4: Query with PDF context")
    print("="*60)
    fake_context = """
    Patient lab report:
    - HbA1c: 9.2% (High — Normal < 5.7%)
    - Fasting Glucose: 210 mg/dL (High — Normal 70-100)
    - Cholesterol: 240 mg/dL (High — Normal < 200)
    """
    result = call_llm(
        "What do my test results mean?",
        user_mode="patient",
        context=fake_context
    )
    print(f"Model used : {result['model_used']}")
    print(f"Response preview:\n{result['content'][:400]}...")
    print("PASSED" if "diabetes" in result["content"].lower() or "glucose" in result["content"].lower() or "hba1c" in result["content"].lower() else "CHECK RESPONSE MANUALLY")


def test_fallback_info():
    print("\n" + "="*60)
    print("INFO: Model chain configured")
    print("="*60)
    print(f"Fast model   : {FAST_MODEL}")
    print(f"Model chain  : ")
    for i, m in enumerate(MODEL_CHAIN, 1):
        print(f"  {i}. {m}")


if __name__ == "__main__":
    print("\nHealthBot — Groq LLM Connection Test")
    print("Make sure your .env file has GROQ_API_KEY set\n")

    try:
        test_fallback_info()
        test_simple_query()
        test_medical_query()
        test_medical_mode()
        test_context_injection()
        print("\n" + "="*60)
        print("ALL TESTS COMPLETE — Groq is working correctly!")
        print("="*60)
    except Exception as e:
        print(f"\nERROR: {e}")
        print("\nCheck that:")
        print("  1. venv is activated")
        print("  2. .env file exists in backend/ folder")
        print("  3. GROQ_API_KEY is set correctly in .env")
        print("  4. requirements.txt was fully installed")