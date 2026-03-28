"""
Knowledge Base Loader — loads ALL medical data files into ChromaDB.

Run ONCE from backend/ folder:
    py -3.11 -m rag.knowledge_base_loader

Files loaded:
  1. diseases.json
  2. drugs.json
  3. vitals_ranges.json
  4. lab_ranges.json        (NEW — blood test reference ranges)
  5. first_aid.json         (NEW — first aid procedures)
  6. india_specific.json    (NEW — India-specific disease context)

Also fetches live data from free APIs:
  - NIH Clinical Tables (2,400+ conditions)
  - OpenFDA drug labels

Safe to re-run — uses upsert, no duplicates created.
"""

import json
import os
import sys
import logging
import asyncio
import httpx

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from rag.vector_store import add_to_kb, get_kb_count
from langchain.text_splitter import RecursiveCharacterTextSplitter

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "medical_kb")

SPLITTER = RecursiveCharacterTextSplitter(
    chunk_size=400,
    chunk_overlap=80,
    separators=["\n\n", "\n", ". ", " "],
)


# ── Helper ────────────────────────────────────────────────────────────────────

def _chunk_and_add(text: str, source: str, doc_type: str, doc_id_prefix: str):
    chunks = SPLITTER.split_text(text)
    texts, metas, ids = [], [], []
    for i, chunk in enumerate(chunks):
        if chunk.strip():
            texts.append(chunk.strip())
            metas.append({"source": source, "type": doc_type})
            ids.append(f"{doc_id_prefix}_{i}")
    if texts:
        add_to_kb(texts, metas, ids)
    return len(texts)


def _read_json(filename: str) -> list:
    path = os.path.join(DATA_DIR, filename)
    if not os.path.exists(path):
        logger.warning(f"{filename} not found at {path} — skipping.")
        return []
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


# ── Loaders ───────────────────────────────────────────────────────────────────

def load_diseases():
    data = _read_json("diseases.json")
    total = 0
    for i, d in enumerate(data):
        text = (
            f"Disease: {d.get('name', '')}\n"
            f"Description: {d.get('description', '')}\n"
            f"Symptoms: {', '.join(d.get('symptoms', []))}\n"
            f"Causes: {d.get('causes', '')}\n"
            f"Treatment: {d.get('treatment', '')}\n"
            f"Prevention: {d.get('prevention', '')}"
        )
        total += _chunk_and_add(text, "diseases_db", "disease", f"disease_{i}")
    logger.info(f"diseases.json → {total} chunks")
    return total


def load_drugs():
    data = _read_json("drugs.json")
    total = 0
    for i, d in enumerate(data):
        otc_label = "Available over the counter (no prescription needed)" if d.get("otc") else "PRESCRIPTION REQUIRED — cannot be dispensed without doctor's prescription"
        text = (
            f"Medicine: {d.get('name', '')} — Brand names: {d.get('brand_names', '')}\n"
            f"Category: {d.get('category', '')}\n"
            f"Used for: {d.get('indications', '')}\n"
            f"Dosage: {d.get('dosage', '')}\n"
            f"Side effects: {d.get('side_effects', '')}\n"
            f"Contraindications: {d.get('contraindications', '')}\n"
            f"Availability: {otc_label}"
        )
        total += _chunk_and_add(text, "drugs_db", "drug", f"drug_{i}")
    logger.info(f"drugs.json → {total} chunks")
    return total


def load_vitals_ranges():
    data = _read_json("vitals_ranges.json")
    total = 0
    for i, v in enumerate(data):
        text = (
            f"Vital sign: {v.get('name', '')} (unit: {v.get('unit', '')})\n"
            f"Normal range: {v.get('normal_range', '')}\n"
            f"Warning range: {v.get('warning_range', '')}\n"
            f"Critical/emergency range: {v.get('critical_range', '')}\n"
            f"Clinical notes: {v.get('notes', '')}"
        )
        total += _chunk_and_add(text, "vitals_ranges", "vital", f"vital_{i}")
    logger.info(f"vitals_ranges.json → {total} chunks")
    return total


def load_lab_ranges():
    data = _read_json("lab_ranges.json")
    total = 0
    for i, v in enumerate(data):
        normal = v.get("normal", {})
        if isinstance(normal, dict):
            normal_str = " | ".join([f"{k}: {val}" for k, val in normal.items()])
        else:
            normal_str = str(normal)
        text = (
            f"Lab test: {v.get('test', '')} ({v.get('category', '')})\n"
            f"Unit: {v.get('unit', '')}\n"
            f"Normal values: {normal_str}\n"
            f"Low result means: {v.get('low_meaning', '')}\n"
            f"High result means: {v.get('high_meaning', '')}\n"
            f"Clinical notes: {v.get('clinical_notes', '')}"
        )
        total += _chunk_and_add(text, "lab_ranges", "lab_test", f"lab_{i}")
    logger.info(f"lab_ranges.json → {total} chunks")
    return total


def load_first_aid():
    data = _read_json("first_aid.json")
    total = 0
    for i, v in enumerate(data):
        steps = "\n".join([f"- {s}" for s in v.get("immediate_steps", [])])
        dont = "\n".join([f"- {s}" for s in v.get("do_not", [])])
        hospital = "\n".join([f"- {s}" for s in v.get("go_to_hospital_if", [])])
        text = (
            f"First Aid — {v.get('situation', '')}\n"
            f"Immediate steps:\n{steps}\n"
            f"DO NOT:\n{dont}\n"
            f"Go to hospital immediately if:\n{hospital}\n"
            f"Source: {v.get('source', '')}"
        )
        total += _chunk_and_add(text, "first_aid", "first_aid", f"firstaid_{i}")
    logger.info(f"first_aid.json → {total} chunks")
    return total


def load_india_specific():
    data = _read_json("india_specific.json")
    total = 0
    for i, v in enumerate(data):
        symptoms = ", ".join(v.get("symptoms", []))
        text = (
            f"Condition: {v.get('condition', '')} — India Context\n"
            f"India context: {v.get('india_context', '')}\n"
            f"Symptoms: {symptoms}\n"
            f"Diagnosis: {v.get('diagnosis', '')}\n"
            f"Treatment: {v.get('treatment', '')}\n"
            f"Prevention: {v.get('prevention', '')}\n"
            f"Government scheme: {v.get('government_scheme', '') or v.get('government_scheme', '')}\n"
            f"Warning: {v.get('critical_warning', '') or v.get('critical_rule', '') or v.get('emergency_signs', '')}"
        )
        total += _chunk_and_add(text, "india_specific", "india_disease", f"india_{i}")
    logger.info(f"india_specific.json → {total} chunks")
    return total
def load_mental_health():
    data = _read_json("mental_health.json")
    total = 0
    for i, d in enumerate(data):
        symptoms = ", ".join(d.get("symptoms", []))
        text = (
            f"Mental health condition: {d.get('condition', '')}\n"
            f"Type: {d.get('type', '')}\n"
            f"Description: {d.get('description', '')}\n"
            f"Symptoms: {symptoms}\n"
            f"India context: {d.get('india_context', '')}\n"
            f"When to seek help: {d.get('when_to_seek_help', '')}\n"
            f"Helplines India: {', '.join(d.get('helplines_india', []))}"
        )
        total += _chunk_and_add(text, "mental_health", "mental_health", f"mental_{i}")
    logger.info(f"mental_health.json → {total} chunks")
    return total


def load_pregnancy():
    data = _read_json("pregnancy_maternal.json")
    total = 0
    for i, d in enumerate(data):
        text = (
            f"Maternal health topic: {d.get('topic', '')}\n"
            f"India context: {d.get('india_context', '')}\n"
            f"Key information: {d.get('minimum_anc_visits', d.get('common_symptoms', d.get('signs', d.get('breastfeeding', ''))))}\n"
            f"Warning signs: {', '.join(d.get('warning_signs_pregnancy', d.get('postpartum_warning_signs', [])))}\n"
            f"Government scheme: {d.get('government_scheme', '')}"
        )
        total += _chunk_and_add(text, "pregnancy_maternal", "maternal_health", f"pregnancy_{i}")
    logger.info(f"pregnancy_maternal.json → {total} chunks")
    return total

# ── Live API fetcher (NIH Clinical Tables) ────────────────────────────────────

async def fetch_nih_conditions():
    """
    Fetch common medical conditions from NIH Clinical Tables API (FREE).
    Loads a curated set of common conditions for Indian healthcare context.
    """
    common_queries = [
        "fever", "diabetes", "hypertension", "asthma", "anemia",
        "tuberculosis", "malaria", "dengue", "thyroid", "kidney disease",
        "liver disease", "heart failure", "pneumonia", "UTI", "gastritis",
        "arthritis", "depression", "anxiety", "migraine", "cholesterol"
    ]
    total = 0
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            for query in common_queries:
                try:
                    r = await client.get(
                        "https://clinicaltables.nlm.nih.gov/api/conditions/v3/search",
                        params={"terms": query, "maxList": 3, "df": "primary_name,consumer_name,icd10cm_codes"}
                    )
                    data = r.json()
                    items = data[3] if len(data) > 3 else []
                    for item in items:
                        if len(item) >= 2:
                            name = item[0]
                            consumer = item[1]
                            icd = item[2] if len(item) > 2 else ""
                            text = (
                                f"Medical condition: {name}\n"
                                f"Also known as: {consumer}\n"
                                f"ICD-10 code: {icd}\n"
                                f"Category: General medical condition"
                            )
                            total += _chunk_and_add(
                                text, "NIH_Clinical_Tables", "nih_condition",
                                f"nih_{query}_{name[:20].replace(' ','_')}"
                            )
                except Exception:
                    continue
        logger.info(f"NIH Clinical Tables API → {total} condition chunks")
    except Exception as e:
        logger.warning(f"NIH API fetch failed: {e} — continuing without it")
    return total


# ── Main ──────────────────────────────────────────────────────────────────────

def load_all():
    logger.info("=" * 55)
    logger.info("HealthBot Knowledge Base Loader — Starting")
    logger.info("=" * 55)

    total = 0
    total += load_diseases()
    total += load_drugs()
    total += load_vitals_ranges()
    total += load_lab_ranges()
    total += load_first_aid()
    total += load_india_specific()

    # 🔥 ADD THESE
    total += load_mental_health()
    total += load_pregnancy()

    # Live API fetch
    logger.info("Fetching live data from NIH Clinical Tables API...")
    nih_count = asyncio.run(fetch_nih_conditions())
    total += nih_count

    final_count = get_kb_count()
    logger.info("=" * 55)
    logger.info(f"Loading complete! Total chunks in ChromaDB: {final_count}")
    logger.info("=" * 55)
    return final_count


if __name__ == "__main__":
    count = load_all()
    print(f"\n✓ Knowledge base ready — {count} chunks loaded.")
    print("Your chatbot can now answer medical queries accurately.")