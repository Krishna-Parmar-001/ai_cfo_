from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Optional
import requests
import json
from math import isfinite

import logging
from pymongo import MongoClient

logger = logging.getLogger("vendor_market_service")

# === AUTO DB SETUP ===
def get_storage():
    """
    Returns a dict-like object:
      - If MongoDB available (localhost:27017, db='insights'), use it.
      - Else, use a simple in-memory mock.
    """
    try:
        client = MongoClient("mongodb://localhost:27017", serverSelectionTimeoutMS=200)
        client.server_info()  # check connection
        db = client["insights"]
        logger.info("✅ Using MongoDB storage (db='insights')")
        return db
    except Exception as e:
        logger.warning("⚠️ MongoDB unavailable, using in-memory mock. Reason: %s", e)
        return {"companies": {}}

STORAGE = get_storage()

if isinstance(STORAGE, dict):
    STORAGE["companies"] = {
        "acme": {
            "company_id": "acme",
            "name": "Acme Analytics",
            "industry_tags": ["saas", "analytics"],
            "employees": 50,
            "revenue": 5000000,
            "growth_30d_pct": 12.5
        },
        "bytecorp": {
            "company_id": "bytecorp",
            "name": "ByteCorp Metrics",
            "industry_tags": ["saas", "analytics"],
            "employees": 80,
            "revenue": 7500000,
            "growth_30d_pct": 15
        },
        "datavue": {
            "company_id": "datavue",
            "name": "DataVue Labs",
            "industry_tags": ["saas", "analytics"],
            "employees": 30,
            "revenue": 3000000,
            "growth_30d_pct": 10
        }
    }



# --- MongoDB Setup (auto-fallback to mock) ---
try:
    from pymongo import MongoClient
    mongo_client = MongoClient("mongodb://localhost:27017/", serverSelectionTimeoutMS=2000)
    mongo_client.server_info()
    db = mongo_client["vendor_market_service"]
    print("✅ Connected to MongoDB")
except Exception as e:
    print("⚠️ MongoDB not available, using mock mode.")
    db = None

# --- Ollama Local LLM Setup ---
OLLAMA_API_URL = "http://127.0.0.1:11434/api/generate"
OLLAMA_MODEL = "gemma3:4b"

async def query_ollama(prompt: str) -> str:
    payload = {"model": OLLAMA_MODEL, "prompt": prompt, "stream": False}
    try:
        response = requests.post(OLLAMA_API_URL, json=payload, timeout=60)
        response.raise_for_status()
        return response.json().get("response", "").strip()
    except Exception as e:
        print(f"⚠️ Ollama query failed: {e}")
        return ""

def safe_json_parse(text: str):
    try:
        return json.loads(text)
    except:
        # Try to extract JSON-like content from text
        start, end = text.find("{"), text.rfind("}")
        if start != -1 and end != -1:
            try:
                return json.loads(text[start:end+1])
            except:
                pass
        try:
            start, end = text.find("["), text.rfind("]")
            if start != -1 and end != -1:
                return json.loads(text[start:end+1])
        except:
            pass
        return None

# --- FastAPI Initialization ---
app = FastAPI(title="Vendor & Market Data Service (Agentic AI)")

# --- Mock Data ---
mock_competitors = [
    {"name": "Acme AI", "category": "SaaS", "users": 800, "revenue": 120000, "vendors": ["AWS", "Slack", "Notion"]},
    {"name": "NeuralNest", "category": "SaaS", "users": 600, "revenue": 95000, "vendors": ["GCP", "Trello", "Notion"]}
]

mock_vendors = [
    {"vendor_name": "AWS", "category": "Cloud", "price": 500, "quality": "High"},
    {"vendor_name": "GCP", "category": "Cloud", "price": 400, "quality": "High"},
    {"vendor_name": "Slack", "category": "Communication", "price": 100, "quality": "Medium"},
    {"vendor_name": "Trello", "category": "Project Management", "price": 80, "quality": "Medium"},
    {"vendor_name": "Notion", "category": "Docs", "price": 50, "quality": "High"},
]



# --- DB Helper Functions ---
async def get_competitors_from_db(company_id: str):
    if db:
        competitors = list(db.competitors.find({"company_id": company_id}, {"_id": 0}))
        if competitors:
            return competitors
    return None

async def get_vendors_from_db(company_id: str):
    if db:
        vendors = list(db.vendor_recommendations.find({"company_id": company_id}, {"_id": 0}))
        if vendors:
            return vendors
    return None

# --- Agentic AI Logic ---
async def fetch_competitors(company_id: str):
    # 1️⃣ Try DB
    data = await get_competitors_from_db(company_id)
    if data:
        print("📦 Competitors found in DB")
        return data

    # 2️⃣ Try LLM
    prompt = f"""
    You are a market analyst AI.
    Find 2-3 real or realistic competitors for a startup with ID '{company_id}'.
    Return **only valid JSON**, nothing else. Use this structure:
    [
        {{
            "name": "string",
            "category": "string",
            "users": number,
            "revenue": number,
            "vendors": ["string", "string"]
        }}
    ]
    If unsure, make realistic assumptions.
    """
    llm_text = await query_ollama(prompt)
    llm_json = safe_json_parse(llm_text)
    if llm_json:
        print("🧠 Competitors generated by LLM (Ollama)")
        return llm_json

    # 3️⃣ Fallback Mock
    print("🧩 Using mock competitors")
    return mock_competitors


async def fetch_vendors(company_id: str):
    # 1️⃣ Try DB
    data = await get_vendors_from_db(company_id)
    if data:
        print("📦 Vendors found in DB")
        return data

    # 2️⃣ Try LLM
    prompt = f"""
    You are a financial procurement AI.
    Suggest 3-4 better/cheaper vendors for company '{company_id}' based on startup best practices.
    Return **only valid JSON**, nothing else. Use this structure:
    [
        {{
            "vendor_name": "string",
            "category": "string",
            "price": number,
            "quality": "High" | "Medium" | "Low"
        }}
    ]
    """
    llm_text = await query_ollama(prompt)
    llm_json = safe_json_parse(llm_text)
    if llm_json:
        print("🧠 Vendors generated by LLM (Ollama)")
        return llm_json

    # 3️⃣ Fallback Mock
    print("🧩 Using mock vendors")
    return mock_vendors


async def compare_vendor_efficiency(all_users_data: List[Dict]):
    """
    Compare spending patterns among all users internally.
    """
    insights = []
    for category in {"Cloud", "Communication", "Docs"}:
        cheaper_vendor = min(mock_vendors, key=lambda v: v["price"])
        insights.append(
            {
                "category": category,
                "recommendation": f"Consider switching to '{cheaper_vendor['vendor_name']}' "
                                  f"for cheaper {category} services without revealing user data."
            }
        )
    return insights

# --- API Endpoints ---
@app.get("/")
async def root():
    return {"message": "Vendor & Market Data Service (Agentic AI) is running."}

@app.get("/market/{company_id}/radar")
async def market_radar(company_id: str):
    competitors = await fetch_competitors(company_id)
    if not competitors:
        raise HTTPException(status_code=404, detail="No competitors found.")
    return {"company_id": company_id, "competitors": competitors}

@app.get("/vendors/{company_id}/recommendations")
async def vendor_recommendations(company_id: str):
    vendors = await fetch_vendors(company_id)
    internal_insights = await compare_vendor_efficiency([])
    return {"company_id": company_id, "recommendations": vendors, "insights": internal_insights}

@app.get("/market/{company_id}/competitor/{competitor_id}")
async def competitor_details(company_id: str, competitor_id: str):
    competitors = await fetch_competitors(company_id)
    competitor = next((c for c in competitors if str(c.get("name")).lower() == competitor_id.lower()), None)
    if not competitor:
        raise HTTPException(status_code=404, detail="Competitor not found.")

    prompt = f"""
    Compare this startup with its competitor and explain why the competitor may perform better.
    User company: {company_id}
    Competitor: {json.dumps(competitor, indent=2)}
    Return a short insight (2-3 sentences) in JSON as:
    {{
        "reason": "why competitor performs better",
        "suggestion": "how user can improve"
    }}
    """
    ai_text = await query_ollama(prompt)
    ai_json = safe_json_parse(ai_text)
    return {"competitor": competitor, "ai_insight": ai_json or {"reason": "No AI insight available."}}


from fastapi import FastAPI, HTTPException
from difflib import SequenceMatcher
from datetime import datetime


@app.get("/market/{company_id}/populate_competitors")
async def populate_competitors_for_company(company_id: str):
    """
    Enhanced competitor discovery + reasoning.
    Now stores results back into DB.
    """

    # 1️⃣ Load company
    if isinstance(STORAGE, dict):
        company_doc = STORAGE["companies"].get(company_id)
        all_companies = list(STORAGE["companies"].values())
    else:
        company_doc = STORAGE.companies.find_one({"company_id": company_id})
        all_companies = list(STORAGE.companies.find({}))

    if not company_doc:
        raise HTTPException(status_code=404, detail=f"Company '{company_id}' not found")

    # 2️⃣ Determine category
    category_tags = company_doc.get("industry_tags") or company_doc.get("categories") or []
    if isinstance(category_tags, str):
        category_tags = [category_tags]
    if not category_tags:
        category_tags = ["general"]

    # 3️⃣ Exact category matches
    competitors = [
        c for c in all_companies
        if c.get("company_id") != company_id and
           set(c.get("industry_tags", [])) & set(category_tags)
    ]

    # 4️⃣ Fuzzy fallback if no exact matches
    if not competitors:
        def similar(a, b):
            return SequenceMatcher(None, a.lower(), b.lower()).ratio() > 0.6

        for c in all_companies:
            if c.get("company_id") == company_id:
                continue
            tags = c.get("industry_tags", [])
            if any(similar(t1, t2) for t1 in category_tags for t2 in tags):
                competitors.append(c)

    # 5️⃣ Metric comparison & reasoning
    def norm(x):
        try:
            return float(x)
        except:
            return 0.0

    user_metrics = {
        "employees": norm(company_doc.get("employees")),
        "revenue": norm(company_doc.get("revenue")),
        "growth": norm(company_doc.get("growth_30d_pct"))
    }

    def advantage(cv, uv):
        if uv == 0:
            return 1.0 if cv > 0 else 0.5
        ratio = cv / uv
        return min(max(ratio / 2.0, 0), 1)

    results = []
    for comp in competitors:
        comp_metrics = {
            "employees": norm(comp.get("employees")),
            "revenue": norm(comp.get("revenue")),
            "growth": norm(comp.get("growth_30d_pct"))
        }

        score = (
            0.4 * advantage(comp_metrics["revenue"], user_metrics["revenue"])
            + 0.35 * advantage(comp_metrics["growth"], user_metrics["growth"])
            + 0.25 * advantage(comp_metrics["employees"], user_metrics["employees"])
        )

        reasoning = []
        reasoning.append(f"Competitor **{comp.get('name')}** shares or resembles category {comp.get('industry_tags')}.")
        if comp_metrics["revenue"] > user_metrics["revenue"]:
            reasoning.append("They generate higher revenue.")
        if comp_metrics["growth"] > user_metrics["growth"]:
            reasoning.append("Their growth rate is stronger.")
        if comp_metrics["employees"] > user_metrics["employees"]:
            reasoning.append("They have a larger team.")
        if not reasoning:
            reasoning.append("Performance is roughly comparable.")

        results.append({
            "competitor_id": comp.get("company_id"),
            "name": comp.get("name"),
            "comparison_score": round(score, 3),
            "reasoning": " ".join(reasoning)
        })

    # 6️⃣ Sort competitors
    results_sorted = sorted(results, key=lambda r: r["comparison_score"], reverse=True)

    # 7️⃣ Auto-store the result
    analysis_doc = {
        "company_id": company_id,
        "category": category_tags,
        "timestamp": datetime.utcnow().isoformat(),
        "competitors": results_sorted
    }

    if isinstance(STORAGE, dict):
        STORAGE["companies"][company_id]["competitor_analysis"] = analysis_doc
    else:
        STORAGE.companies.update_one(
            {"company_id": company_id},
            {"$set": {"competitor_analysis": analysis_doc}},
            upsert=True
        )

    return {
        "message": "✅ Competitor analysis updated",
        "company": company_doc.get("name"),
        "category": category_tags,
        "competitor_count": len(results_sorted),
        "competitors": results_sorted
    }


# --- Run Command ---
# uvicorn vendor_market_service:app --reload
