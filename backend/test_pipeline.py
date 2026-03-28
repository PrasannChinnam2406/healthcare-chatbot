import asyncio
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agents.orchestrator import process_message

async def test():
    result = await process_message(
        session_id = "test_session_001",
        message    = "I have fever 101F, headache and body ache since 2 days",
        user_mode  = "patient",
    )
    print("Response:", result["response"][:500])
    print("Severity:", result["severity"])
    print("Agents used:", result["agents_used"])
    print("Has prescription:", result["has_prescription"])

asyncio.run(test())