"""
FILE: services/who_icd_service.py

WHO ICD-11 API Service — Official Disease Classification
Gives your chatbot official WHO disease codes and descriptions.

Your keys are already in .env:
  WHO_ICD_CLIENT_ID=0214cfd8-...
  WHO_ICD_CLIENT_SECRET=nXVTw07m...

How it works:
  1. Get OAuth token using your client ID + secret
  2. Use token to search diseases by name
  3. Returns ICD-11 code, official name, definition

Token is cached for 1 hour — only refreshed when expired.
So it does NOT make an API call on every user message.
Only called when a diagnosis is confirmed by the agents.
"""

import httpx
import logging
import time
from core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

ICD_TOKEN_URL  = "https://icdaccessmanagement.who.int/connect/token"
ICD_API_BASE   = "https://id.who.int/icd/entity"
ICD_SEARCH_URL = "https://id.who.int/icd/release/11/2024-01/mms/search"

# ── Token cache ────────────────────────────────────────────────────────────────
_cached_token: str | None = None
_token_expiry: float = 0.0


async def _get_access_token() -> str | None:
    """
    Get OAuth2 access token from WHO ICD API.
    Caches token for 1 hour — avoids unnecessary auth calls.
    """
    global _cached_token, _token_expiry

    # return cached token if still valid (with 60s buffer)
    if _cached_token and time.time() < (_token_expiry - 60):
        return _cached_token

    if not settings.who_icd_enabled:
        return None

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            r = await client.post(
                ICD_TOKEN_URL,
                data={
                    "client_id":     settings.WHO_ICD_CLIENT_ID,
                    "client_secret": settings.WHO_ICD_CLIENT_SECRET,
                    "scope":         "icdapi_access",
                    "grant_type":    "client_credentials",
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )
            r.raise_for_status()
            data = r.json()

            _cached_token  = data["access_token"]
            _token_expiry  = time.time() + int(data.get("expires_in", 3600))
            logger.info("WHO ICD-11 token refreshed successfully.")
            return _cached_token

    except Exception as e:
        logger.warning(f"WHO ICD-11 token fetch failed: {e}")
        return None


# ── Search disease ─────────────────────────────────────────────────────────────

async def search_icd11_disease(query: str, max_results: int = 3) -> list[dict]:
    """
    Search WHO ICD-11 database for a disease name.

    Returns list of:
    {
        "icd11_code": str,      e.g. "1C8Z"
        "name": str,            official WHO disease name
        "definition": str,      short clinical definition
        "url": str              link to WHO disease page
    }

    Returns empty list if API unavailable — system continues without it.
    """
    token = await _get_access_token()
    if not token:
        return []

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            r = await client.get(
                ICD_SEARCH_URL,
                params={
                    "q":              query,
                    "useFlexisearch":  "true",
                    "flatResults":    "true",
                    "highlightingEnabled": "false",
                },
                headers={
                    "Authorization":  f"Bearer {token}",
                    "Accept":         "application/json",
                    "Accept-Language": "en",
                    "API-Version":    "v2",
                },
            )
            r.raise_for_status()
            data = r.json()

        results = []
        for item in data.get("destinationEntities", [])[:max_results]:
            results.append({
                "icd11_code": item.get("theCode", ""),
                "name":       item.get("title", ""),
                "definition": item.get("definition", "")[:300],
                "url":        item.get("id", ""),
            })

        return results

    except Exception as e:
        logger.warning(f"WHO ICD-11 search failed for '{query}': {e}")
        return []


# ── Format for LLM context ─────────────────────────────────────────────────────

def format_icd_for_context(icd_results: list[dict]) -> str:
    """
    Format ICD-11 results as a short context string for the LLM.
    Only used in medical professional mode.
    """
    if not icd_results:
        return ""

    lines = ["WHO ICD-11 Classification:"]
    for r in icd_results:
        if r["icd11_code"] and r["name"]:
            lines.append(f"  • {r['name']} — ICD-11 Code: {r['icd11_code']}")
            if r["definition"]:
                lines.append(f"    {r['definition']}")

    return "\n".join(lines)


# ── Test function ──────────────────────────────────────────────────────────────

async def test_who_icd():
    """Quick test — run to verify WHO ICD API is working."""
    print("Testing WHO ICD-11 API...")
    results = await search_icd11_disease("dengue fever")
    if results:
        print(f"SUCCESS — Found {len(results)} results:")
        for r in results:
            print(f"  {r['name']} — Code: {r['icd11_code']}")
    else:
        print("No results or API unavailable.")


if __name__ == "__main__":
    import asyncio
    asyncio.run(test_who_icd())