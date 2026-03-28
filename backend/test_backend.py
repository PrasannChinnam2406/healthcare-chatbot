"""
FILE: backend/test_backend.py

Full backend test — run this before starting the server to verify everything works.
Tests all major features: chat, PDF, vitals, emergency detection.

Usage:
    py -3.11 test_backend.py
"""

import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def print_section(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print('='*60)


def print_result(label, value, ok=True):
    icon = "✓" if ok else "✗"
    print(f"  {icon} {label}: {value}")


# ── Test 1: LLM Connection ────────────────────────────────────────────────────

def test_llm():
    print_section("TEST 1: LLM Connection")
    from core.llm_client import call_llm
    result = call_llm("Hello, what can you do?", user_mode="general")
    ok = bool(result.get("content"))
    print_result("Model used", result.get("model_used", "unknown"), ok)
    print_result("Response length", f"{len(result.get('content',''))} chars", ok)
    return ok


# ── Test 2: ChromaDB KB ───────────────────────────────────────────────────────

def test_knowledge_base():
    print_section("TEST 2: Knowledge Base (ChromaDB)")
    from rag.vector_store import search_kb, get_kb_count
    count = get_kb_count()
    ok1   = count > 0
    print_result("KB chunks loaded", count, ok1)

    results = search_kb("fever headache body ache", n_results=3)
    ok2     = len(results) > 0
    print_result("Search results", len(results), ok2)
    if results:
        print_result("Top result source", results[0]["metadata"].get("source","?"), True)
    return ok1 and ok2


# ── Test 3: Safety Guard ──────────────────────────────────────────────────────

def test_safety_guard():
    print_section("TEST 3: Safety Guard")
    from agents.safety_guard import run_safety_guard

    # Should detect emergency
    result1 = run_safety_guard("I have severe chest pain and cannot breathe")
    ok1     = result1["is_emergency"] and result1["should_stop"]
    print_result("Emergency detected (chest pain)", ok1, ok1)

    # Should NOT detect emergency
    result2 = run_safety_guard("I have a mild headache")
    ok2     = not result2["is_emergency"]
    print_result("No false positive (mild headache)", ok2, ok2)

    # Mental health detection
    result3 = run_safety_guard("I want to kill myself")
    ok3     = result3["is_emergency"] and result3["is_mental_health"]
    print_result("Mental health emergency detected", ok3, ok3)

    # Vitals emergency
    result4 = run_safety_guard("check my vitals", {"spo2": 85, "heart_rate": 110})
    ok4     = result4["is_emergency"]
    print_result("Critical vitals detected (SpO2 85%)", ok4, ok4)

    return ok1 and ok2 and ok3 and ok4


# ── Test 4: Full Pipeline ─────────────────────────────────────────────────────

async def test_full_pipeline():
    print_section("TEST 4: Full Agent Pipeline")
    from agents.orchestrator import process_message

    result = await process_message(
        session_id = "test_full_001",
        message    = "I have fever 101F, headache and body ache since 2 days. What medicines should I take?",
        user_mode  = "patient",
    )

    ok1 = bool(result.get("response"))
    ok2 = result.get("severity") in ("low", "moderate", "high", "critical")
    ok3 = len(result.get("agents_used", [])) >= 4
    ok4 = result.get("has_prescription") == True

    print_result("Response generated", f"{len(result.get('response',''))} chars", ok1)
    print_result("Severity assessed", result.get("severity","?"), ok2)
    print_result("Agents ran", str(result.get("agents_used",[])), ok3)
    print_result("Prescription included", result.get("has_prescription"), ok4)
    print_result("Model used", result.get("model_used","?"), True)

    print("\n  Response preview:")
    preview = result.get("response","")[:400].replace("\n"," ")
    print(f"  {preview}...")

    return ok1 and ok2 and ok3


# ── Test 5: User modes ────────────────────────────────────────────────────────

async def test_user_modes():
    print_section("TEST 5: User Modes (General vs Medical)")
    from agents.orchestrator import process_message

    # General mode
    r1 = await process_message(
        session_id = "test_mode_gen",
        message    = "what is diabetes",
        user_mode  = "general",
    )
    ok1 = bool(r1.get("response"))
    print_result("General mode response", f"{len(r1.get('response',''))} chars", ok1)

    # Medical mode
    r2 = await process_message(
        session_id = "test_mode_med",
        message    = "patient presents with polydipsia polyuria weight loss, HbA1c 9.5%",
        user_mode  = "medical",
    )
    ok2 = bool(r2.get("response"))
    print_result("Medical mode response", f"{len(r2.get('response',''))} chars", ok2)

    return ok1 and ok2


# ── Test 6: WHO ICD API ───────────────────────────────────────────────────────

async def test_who_icd():
    print_section("TEST 6: WHO ICD-11 API")
    from services.who_icd_service import search_icd11_disease
    results = await search_icd11_disease("malaria")
    ok      = len(results) > 0
    print_result("ICD-11 results found", len(results), ok)
    if results:
        print_result("First result", f"{results[0]['name']} — {results[0]['icd11_code']}", True)
    return ok


# ── Main ──────────────────────────────────────────────────────────────────────

async def main():
    print("\nHealthBot — Complete Backend Test Suite")
    print("Make sure venv is active and .env is configured\n")

    results = {}

    try:
        results["LLM Connection"]    = test_llm()
    except Exception as e:
        print(f"  ✗ LLM test FAILED: {e}")
        results["LLM Connection"]    = False

    try:
        results["Knowledge Base"]    = test_knowledge_base()
    except Exception as e:
        print(f"  ✗ KB test FAILED: {e}")
        results["Knowledge Base"]    = False

    try:
        results["Safety Guard"]      = test_safety_guard()
    except Exception as e:
        print(f"  ✗ Safety guard test FAILED: {e}")
        results["Safety Guard"]      = False

    try:
        results["Full Pipeline"]     = await test_full_pipeline()
    except Exception as e:
        print(f"  ✗ Pipeline test FAILED: {e}")
        results["Full Pipeline"]     = False

    try:
        results["User Modes"]        = await test_user_modes()
    except Exception as e:
        print(f"  ✗ User modes test FAILED: {e}")
        results["User Modes"]        = False

    try:
        results["WHO ICD-11 API"]    = await test_who_icd()
    except Exception as e:
        print(f"  ✗ WHO ICD test FAILED: {e}")
        results["WHO ICD-11 API"]    = False

    # Summary
    print_section("TEST SUMMARY")
    all_passed = True
    for test, passed in results.items():
        icon = "✓" if passed else "✗"
        print(f"  {icon} {test}")
        if not passed:
            all_passed = False

    print()
    if all_passed:
        print("  ALL TESTS PASSED — Backend is ready!")
        print("  Next step: run the server with:")
        print("    py -3.11 main.py")
    else:
        print("  Some tests failed. Check errors above.")

    print()


if __name__ == "__main__":
    asyncio.run(main())