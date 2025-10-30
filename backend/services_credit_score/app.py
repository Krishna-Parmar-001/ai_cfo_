# credit_score_service/app.py
import asyncio
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import JSONResponse
from datetime import datetime, timezone
from typing import Optional, List, Dict
from motor.motor_asyncio import AsyncIOMotorClient
import os

from db import init_db, get_client
from mock_data import generate_mock_financial_data
from utils.scoring import compute_score_and_breakdown
from schemas import CreditScoreResponse, RankedStartupItem, RecalcResponse

app = FastAPI(title="Credit Score Service (Startups)")

# Initialize DB on startup
@app.on_event("startup")
async def startup_event():
    init_db()
    # create indexes
    db = init_db()
    await db.credit_scores.create_index("company_id", unique=True)
    await db.score_factors_history.create_index([("company_id", 1), ("timestamp", -1)])

@app.on_event("shutdown")
async def shutdown_event():
    client = get_client()
    client.close()

def now_iso():
    return datetime.now(tz=timezone.utc)

@app.get("/credit-score/{company_id}", response_model=CreditScoreResponse)
async def get_credit_score(company_id: str):
    db = init_db()
    doc = await db.credit_scores.find_one({"company_id": company_id})
    if not doc:
        raise HTTPException(status_code=404, detail="company not found")
    # Convert last_updated to ISO-aware
    return {
        "company_id": doc["company_id"],
        "score": int(doc["score"]),
        "last_updated": doc["last_updated"],
        "breakdown": doc["breakdown"]
    }

@app.post("/credit-score/recalculate/{company_id}", response_model=RecalcResponse)
async def recalculate_credit_score(company_id: str, seed: Optional[int] = None, company_name: Optional[str] = None, industry: Optional[str] = None):
    """
    Recalculate using mocked data (optionally pass seed for deterministic result).
    If the company doesn't exist in credit_scores it will be created.
    """
    db = init_db()

    # 1) get mocked financials
    factors = generate_mock_financial_data(seed=seed)

    # 2) compute score and breakdown
    new_score, breakdown = compute_score_and_breakdown(factors)

    now = now_iso()

    # 3) upsert credit_scores
    company_name = company_name or f"Company-{company_id}"
    industry = industry or "Unknown"

    credit_doc = {
        "company_id": company_id,
        "company_name": company_name,
        "industry": industry,
        "score": int(new_score),
        "last_updated": now,
        "breakdown": breakdown
    }

    await db.credit_scores.update_one(
        {"company_id": company_id},
        {"$set": credit_doc},
        upsert=True
    )

    # 4) record factors history
    history_doc = {
        "company_id": company_id,
        "timestamp": now,
        "factors": factors
    }
    await db.score_factors_history.insert_one(history_doc)

    return {"message": "Recalculation completed", "company_id": company_id, "new_score": int(new_score)}

@app.get("/investor/ranked-startups", response_model=List[RankedStartupItem])
async def get_ranked_startups(min_score: int = Query(0, ge=0, le=900), industry: Optional[str] = None, limit: int = Query(50, ge=1)):
    """
    Returns startups with score >= min_score, optionally filtered by industry, sorted by score desc.
    Also returns the revenue_growth_rate as growth_rate for convenience.
    """
    db = init_db()
    query = {"score": {"$gte": int(min_score)}}
    if industry:
        query["industry"] = industry

    cursor = db.credit_scores.find(query).sort("score", -1).limit(int(limit))
    results = []
    async for doc in cursor:
        growth = None
        try:
            growth = float(doc.get("breakdown", {}).get("revenue_growth_rate", {}).get("value", 0.0))
        except Exception:
            growth = 0.0
        results.append({
            "company_id": doc["company_id"],
            "company_name": doc.get("company_name", ""),
            "industry": doc.get("industry", ""),
            "score": int(doc.get("score", 0)),
            "growth_rate": growth
        })
    return results

@app.get("/health")
async def health():
    # very small health endpoint to verify DB connectivity
    try:
        db = init_db()
        await db.command("ping")
        return {"status": "ok"}
    except Exception as e:
        return JSONResponse(status_code=503, content={"status": "error", "detail": str(e)})
