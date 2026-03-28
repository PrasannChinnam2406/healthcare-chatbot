"""
FILE: core/llm_client.py  — FINAL VERSION WITH PRODUCTION PROMPTS

System prompts optimised for:
- Clean bullet-point only responses
- Short, readable, ChatGPT-style output
- Smart context detection (PDF vs health query)
- No unnecessary disclaimers for non-health topics
"""

import logging
from groq import Groq, APIStatusError, APIConnectionError, RateLimitError
from core.config import get_settings

logger   = logging.getLogger(__name__)
settings = get_settings()
client   = Groq(api_key=settings.GROQ_API_KEY)

# ── Model chain ───────────────────────────────────────────────────────────────
MODEL_CHAIN = [
    "llama-3.3-70b-versatile",
    "llama-3.1-70b-versatile",
    "mixtral-8x7b-32768",
    "gemma2-9b-it",
    "llama-3.1-8b-instant",
]
FAST_MODEL = "llama-3.1-8b-instant"

# ── Simple query detection ────────────────────────────────────────────────────
SIMPLE_KEYWORDS = [
    "hello", "hi", "hey", "thanks", "thank you", "ok", "okay", "bye",
    "who are you", "what can you do", "good morning", "namaste", "good night",
]

def _is_simple(text: str) -> bool:
    t = text.lower().strip()
    return len(t.split()) <= 5 and any(kw in t for kw in SIMPLE_KEYWORDS)

# ── Detect if query is about an uploaded document ─────────────────────────────
RESEARCH_KEYWORDS = [
    "paper", "study", "research", "article", "abstract", "title", "author",
    "conclusion", "methodology", "findings", "results", "journal", "reference",
    "document", "pdf", "report", "uploaded", "this paper", "the paper",
    "what does", "summarize", "summary of",
]

def _is_document_query(text: str) -> bool:
    t = text.lower()
    return any(kw in t for kw in RESEARCH_KEYWORDS)

# ── System prompts ────────────────────────────────────────────────────────────

SYSTEM_PROMPTS = {

"general": """You are HealthBot — a friendly AI healthcare assistant for India.
Respond like ChatGPT: clear, structured, easy to read.

FORMAT YOUR RESPONSE LIKE THIS:
### Summary
- 1–2 short lines about the likely issue

### What to do
- Simple action bullets (one per line)

### Medicines (only if clearly needed)
- **Name** (Indian brand e.g. Dolo 650) — dose — frequency — key warning

### See a doctor if
- Important warning signs only (2–4 bullets max)

STRICT RULES:
- Use ONLY bullet points under each section. No paragraphs.
- Maximum 150 words total.
- Simple language — no medical jargon.
- Each bullet = one short sentence.
- Only suggest safe OTC medicines available in India.
- Never invent drug names or dosages.
- If serious symptoms: add "⚠️ This needs urgent medical attention."
- End with a single line disclaimer ONLY for health advice:
  *For informational purposes only. Consult a doctor for diagnosis.*
- Do NOT add disclaimer for non-health topics or document questions.
- Always respond in markdown.""",

"patient": """You are HealthBot — a healthcare AI assistant for patients.
Give structured, practical, easy-to-understand health guidance.

FORMAT:
### Likely condition
- Short explanation (simple words, 1–2 bullets)

### What to do
- Clear action steps (bullets)

### Medicines
- **Name** (Indian brand) — exact dose — frequency — duration
- ⚠️ Warning if important (one line only)
- If prescription needed: "⚕️ Requires doctor prescription"

### Diet & care
- What to eat / avoid (3–4 bullets max)

### See a doctor if
- Clear warning signs (3–5 bullets)

STRICT RULES:
- Max 180 words total.
- Bullet points ONLY — no paragraphs.
- No repeated information across sections.
- Only safe OTC medicines available in India.
- Never invent dosages.
- If cause unclear: "Exact cause needs examination."
- End with: *For informational purposes only. Consult a doctor.*
- No disclaimer for non-health/document queries.
- Always respond in markdown.""",

"medical": """You are HealthBot — a clinical decision support AI.
Respond in concise, professional, structured format.

FORMAT:
### Differential diagnosis
- Ranked list with brief 1-line reasoning each

### Investigations
- Essential tests only (bullets)

### Management
- **Drug** (generic + brand) — dose — route — duration
- One drug per bullet

### Red flags
- Critical warning signs requiring immediate action

STRICT RULES:
- Bullet points ONLY. No paragraphs.
- Be precise and concise.
- No unnecessary disclaimers.
- Do not hallucinate clinical data.
- If insufficient data: "Further evaluation required."
- ICD-11 code if applicable.
- Always respond in markdown.""",

# Special prompt for document/PDF queries — no health disclaimer
"document": """You are HealthBot — an AI assistant that analyses uploaded documents.
The user has uploaded a document and is asking questions about it.

Your job:
- Answer accurately from the document content provided
- Be clear and structured
- Use bullet points for lists, normal text for explanations
- If information is not in the document, say so clearly

FORMAT based on question type:
- For summaries: ### Summary followed by bullet points
- For specific questions: Direct answer with supporting details
- For comparisons: Use a structured list

RULES:
- Do NOT add medical disclaimers for document questions
- Do NOT suggest medicines or diagnoses unless explicitly in the document
- Answer only from the provided context
- If not found in document: "This information is not available in the uploaded document."
- Always respond in markdown.""",
}

# ── Tone modifier based on severity ──────────────────────────────────────────
TONE_ADDITIONS = {
    "critical": "\n\n🚨 SEVERITY: CRITICAL — Respond with urgency. Emphasise emergency care immediately.",
    "high":     "\n\n⚠️ SEVERITY: HIGH — Respond carefully. Recommend seeing a doctor today.",
    "moderate": "\n\n📋 SEVERITY: MODERATE — Respond helpfully. Recommend monitoring and care.",
    "low":      "",
}

# ── Build message list ────────────────────────────────────────────────────────
def _build_messages(
    prompt: str,
    user_mode: str,
    context: str,
    chat_history: list,
    severity: str = "low",
    has_pdf: bool = False,
) -> list:
    # Choose correct system prompt
    if has_pdf and _is_document_query(prompt):
        system_prompt = SYSTEM_PROMPTS["document"]
    else:
        system_prompt = SYSTEM_PROMPTS.get(user_mode, SYSTEM_PROMPTS["general"])

    # Add severity tone
    system_prompt += TONE_ADDITIONS.get(severity, "")

    messages = [{"role": "system", "content": system_prompt}]

    if context and context.strip():
        source_label = "From the uploaded document and medical knowledge base" if has_pdf else "From medical knowledge base"
        messages.append({
            "role": "system",
            "content": f"{source_label}:\n\n{context}\n\nUse this context to give accurate, specific answers."
        })

    # Last 8 turns only
    for msg in chat_history[-8:]:
        messages.append(msg)

    messages.append({"role": "user", "content": prompt})
    return messages

# ── Fallback chain ────────────────────────────────────────────────────────────
def _call_chain(messages: list, max_tokens: int = 400) -> tuple[str, str]:
    last_err = None
    for model in MODEL_CHAIN:
        try:
            r = client.chat.completions.create(
                model=model, messages=messages,
                temperature=0.35, max_tokens=max_tokens,
            )
            return r.choices[0].message.content, model
        except RateLimitError:
            logger.warning(f"Rate limit on {model}, trying next...")
            last_err = f"Rate limit {model}"
        except APIStatusError as e:
            if e.status_code in (404, 400):
                logger.warning(f"Model {model} unavailable, trying next...")
                last_err = str(e)
            else:
                last_err = str(e)
        except Exception as e:
            logger.error(f"Error on {model}: {e}")
            last_err = str(e)
    raise RuntimeError(f"All models failed. Last error: {last_err}")

# ── Public API ────────────────────────────────────────────────────────────────
def call_llm(
    prompt: str,
    user_mode: str = "general",
    context: str = "",
    chat_history: list = [],
    force_model: str = None,
    severity: str = "low",
    has_pdf: bool = False,
) -> dict:
    """Non-streaming LLM call."""
    # Fast path for simple queries
    if _is_simple(prompt) and not force_model:
        try:
            msgs = _build_messages(prompt, user_mode, "", [], "low", False)
            r = client.chat.completions.create(
                model=FAST_MODEL, messages=msgs,
                temperature=0.3, max_tokens=200,
            )
            return {"content": r.choices[0].message.content, "model_used": FAST_MODEL}
        except Exception:
            pass

    msgs = _build_messages(prompt, user_mode, context, chat_history, severity, has_pdf)

    if force_model:
        try:
            r = client.chat.completions.create(
                model=force_model, messages=msgs,
                temperature=0.35, max_tokens=400,
            )
            return {"content": r.choices[0].message.content, "model_used": force_model}
        except Exception:
            pass

    content, model = _call_chain(msgs, max_tokens=400)
    return {"content": content, "model_used": model}


def call_llm_stream(
    prompt: str,
    user_mode: str = "general",
    context: str = "",
    chat_history: list = [],
    force_model: str = None,
    severity: str = "low",
    has_pdf: bool = False,
):
    """Streaming LLM call — yields tokens."""
    msgs = _build_messages(prompt, user_mode, context, chat_history, severity, has_pdf)

    if force_model:
        models_to_try = [force_model] + [m for m in MODEL_CHAIN if m != force_model]
    elif _is_simple(prompt):
        models_to_try = [FAST_MODEL]
    else:
        models_to_try = MODEL_CHAIN

    for model in models_to_try:
        try:
            stream = client.chat.completions.create(
                model=model, messages=msgs,
                temperature=0.35, max_tokens=400,
                stream=True,
            )
            for chunk in stream:
                delta = chunk.choices[0].delta.content
                if delta:
                    yield delta
            yield f"\n\n<!-- model_used:{model} -->"
            return
        except RateLimitError:
            logger.warning(f"Stream rate limit on {model}, trying next...")
            continue
        except APIStatusError as e:
            if e.status_code in (404, 400):
                continue
            continue
        except Exception as e:
            logger.error(f"Stream error on {model}: {e}")
            continue

    yield "\n\nSorry, I'm having trouble connecting. Please try again."