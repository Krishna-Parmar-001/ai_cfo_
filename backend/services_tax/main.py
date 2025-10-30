"""
Tax & Filing Service (Hybrid) - main.py

Features:
- GST + TDS automatic detection & calculation
- Endpoints:
  POST  /tax/{company_id}/classify_transactions    (classify and store transactions)
  POST  /tax/{company_id}/calculate_gst           (aggregate GST)
  POST  /tax/{company_id}/calculate_tds           (aggregate TDS)
  GET   /tax/{company_id}/gst_return_data/{period}
  POST  /tax/{company_id}/generate_itr_report
  GET   /tax/{company_id}/deadlines
  GET   /tax/{company_id}/optimization_guidance
  PUT   /tax/{company_id}/settings
  POST  /tax/{company_id}/enrich_transactions     (enrich using settings)
  POST  /tax/{company_id}/seed_sample             (seed sample data)
- Integrations (stubbed with safe wrappers):
  DATA_SERVICE_URL, FINANCE_SERVICE_URL, AUDIT_SERVICE_URL, NOTIFICATION_URL
- Hybrid DB: tries MongoDB (MONGO_URI), else uses in-memory store.

How to run:
  pip install fastapi uvicorn pydantic requests pymongo
  uvicorn main:app --reload
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
import os, logging, requests, traceback

# ---------- CONFIG / ENV ----------
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
DB_NAME = os.getenv("DB_NAME", "ai_cfo_tax")
DATA_SERVICE_URL = os.getenv("DATA_SERVICE_URL", "http://localhost:8101")         # expected /data/{company_id}/transactions
FINANCE_SERVICE_URL = os.getenv("FINANCE_SERVICE_URL", "http://localhost:8102")   # example
AUDIT_SERVICE_URL = os.getenv("AUDIT_SERVICE_URL", "http://localhost:8103")       # expected /audit/{company_id}/record_filing
NOTIFICATION_URL = os.getenv("NOTIFICATION_URL", "http://localhost:8104")         # expected /notify

# ---------- Logging ----------
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("tax_service")

# ---------- Try to connect to MongoDB; fallback to in-memory ----------
USE_MONGO = False
db_client = None
db = None
try:
    from pymongo import MongoClient
    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=2000)
    # attempt server_info to confirm connection
    client.server_info()
    db_client = client
    db = client[DB_NAME]
    USE_MONGO = True
    logger.info("Connected to MongoDB at %s", MONGO_URI)
except Exception as e:
    logger.warning("MongoDB not available (%s). Falling back to in-memory DB.", str(e))
    USE_MONGO = False
    # in-memory structure
    _mem = {
        "tax_settings": {},           # keyed by company_id
        "tax_transactions": [],       # list of txn dicts (include company_id)
        "tax_returns": [],            # list of return docs
        "tax_deadlines": [],          # optional
    }
    db = _mem

# ---------- Pydantic models ----------
class Transaction(BaseModel):
    tx_id: str
    date: Optional[str] = None
    description: str
    type: str            # "sale", "purchase", "expense", "receipt", "payment", "invoice"
    category: Optional[str] = ""
    amount: float
    currency: Optional[str] = "INR"
    counterparty: Optional[str] = ""
    source: Optional[str] = ""    # "bank", "tally", "razorpay", "zoho", etc.


class TaxSettings(BaseModel):
    gst_default_rate: float = 0.18
    gst_exempt_threshold: Optional[float] = None
    tds_threshold: float = 30000
    tds_keyword_map: Dict[str, str] = Field(default_factory=lambda: {
        "consult": "194J",
        "professional": "194J",
        "contract": "194C",
        "marketing": "194C",
        "rent": "194I",
        "commission": "194H"
    })
    tds_rates_map: Dict[str, float] = Field(default_factory=lambda: {
        "194J": 0.10,
        "194C": 0.02,
        "194I": 0.10,
        "194H": 0.05
    })


# ---------- Helper DB abstraction functions ----------
def coll(name: str):
    if USE_MONGO:
        return db[name]
    else:
        return db  # in-memory operations use helper functions below

# in-memory helpers
def mem_insert(collection: str, doc: dict):
    if USE_MONGO:
        return coll(collection).insert_one(doc).inserted_id
    db[collection].append(doc)
    return len(db[collection]) - 1

def mem_find(collection: str, q: dict = None):
    if USE_MONGO:
        return list(coll(collection).find(q or {}))
    if q is None or not q:
        return list(db[collection])
    # simplistic filter
    out = []
    for d in db[collection]:
        match = True
        for k,v in q.items():
            if d.get(k) != v:
                match = False; break
        if match:
            out.append(d)
    return out

def mem_replace_one(collection: str, q: dict, newdoc: dict, upsert=False):
    if USE_MONGO:
        return coll(collection).replace_one(q, newdoc, upsert=upsert)
    for idx, d in enumerate(db[collection]):
        match = True
        for k,v in q.items():
            if d.get(k) != v:
                match = False; break
        if match:
            db[collection][idx] = newdoc
            return True
    if upsert:
        db[collection].append(newdoc)
        return True
    return False

def mem_delete_many(collection: str, q: dict = None):
    if USE_MONGO:
        return coll(collection).delete_many(q or {})
    if not q:
        db[collection] = []
        return True
    db[collection] = [d for d in db[collection] if not all(d.get(k)==v for k,v in q.items())]
    return True

# ---------- Integration wrappers (safe) ----------
def fetch_transactions_from_data_service(company_id: str) -> List[dict]:
    # expects data service endpoint: GET {DATA_SERVICE_URL}/data/{company_id}/transactions
    try:
        url = f"{DATA_SERVICE_URL}/data/{company_id}/transactions"
        resp = requests.get(url, timeout=3)
        resp.raise_for_status()
        return resp.json().get("transactions", [])
    except Exception as e:
        logger.debug("Data service fetch failed: %s", e)
        return []

def fetch_finance_summary(company_id: str) -> dict:
    try:
        url = f"{FINANCE_SERVICE_URL}/finance/{company_id}/summary"
        resp = requests.get(url, timeout=3)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        logger.debug("Finance service fetch failed: %s", e)
        return {}

def record_audit_entry(company_id: str, payload: dict):
    try:
        url = f"{AUDIT_SERVICE_URL}/audit/{company_id}/record_filing"
        resp = requests.post(url, json=payload, timeout=3)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        logger.debug("Audit service POST failed: %s", e)
        return None

def send_notification(payload: dict):
    try:
        url = f"{NOTIFICATION_URL}/notify"
        resp = requests.post(url, json=payload, timeout=3)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        logger.debug("Notification POST failed: %s", e)
        return None

# ---------- Core tax inference logic ----------
def infer_tax_for_record(rec: dict, settings: TaxSettings) -> dict:
    """
    Returns inference: is_gst_applicable, gst_rate, is_tds_applicable, tds_section, tds_rate, is_tax_inclusive
    Uses description, category, type, amount, source.
    """
    desc = (rec.get("description") or "").lower()
    cat = (rec.get("category") or "").lower()
    _type = (rec.get("type") or "").lower()
    amount = float(rec.get("amount") or 0)

    out = {
        "is_gst_applicable": False,
        "gst_rate": None,
        "is_tds_applicable": False,
        "tds_section": None,
        "tds_rate": None,
        "is_tax_inclusive": False
    }

    # --- GST inference ---
    # If record is sale/invoice -> probably GST on output
    if _type in ("sale", "invoice", "receipt") or any(w in cat for w in ["sale","service","product","subscription","invoice","goods","supply"]):
        # check for obvious exempt hints
        if "exempt" not in desc and "zero" not in desc:
            out["is_gst_applicable"] = True
            # determine rate heuristically
            if "service" in cat or "software" in cat or "subscription" in cat:
                out["gst_rate"] = 0.18
            elif "goods" in cat or "product" in cat:
                out["gst_rate"] = 0.12
            else:
                out["gst_rate"] = settings.gst_default_rate

    # If record is purchase -> input GST possible
    if _type in ("purchase", "payment"):
        # assume GST applicable on purchases of goods/services
        if any(w in cat for w in ["purchase","service","product","goods","input"]):
            out["is_gst_applicable"] = True
            out["gst_rate"] = out["gst_rate"] or settings.gst_default_rate

    # Tax inclusive detection
    if "inclusive" in desc or "gst included" in desc:
        out["is_tax_inclusive"] = True

    # --- TDS inference ---
    # look for keywords in desc or category or counterparty
    desc_fields = " ".join([desc, cat, str(rec.get("counterparty","")).lower()])
    for kw, section in settings.tds_keyword_map.items():
        if kw in desc_fields:
            out["is_tds_applicable"] = True
            out["tds_section"] = section
            out["tds_rate"] = settings.tds_rates_map.get(section, 0.0)
            break

    # threshold check (company may exempt small amounts)
    if out["is_tds_applicable"] and amount < settings.tds_threshold:
        # treat as not applicable due to threshold
        out["is_tds_applicable"] = False
        out["tds_section"] = None
        out["tds_rate"] = None

    # If narration explicitly contains 'tds' treat as applicable (strong signal)
    if "tds" in desc_fields and not out["is_tds_applicable"]:
        # attempt to find a section
        out["is_tds_applicable"] = True
        import re
        m = re.search(r"19[4|5]\d", desc_fields)
        if m:
            sec = m.group(0)
            out["tds_section"] = sec
            out["tds_rate"] = settings.tds_rates_map.get(sec, 0.0)
        else:
            # default to professional if unknown
            out["tds_section"] = settings.tds_keyword_map.get("professional", "194J")
            out["tds_rate"] = settings.tds_rates_map.get(out["tds_section"], 0.10)

    return out

# ---------- Aggregation helpers ----------
def get_company_settings(company_id: str) -> TaxSettings:
    if USE_MONGO:
        doc = coll("tax_settings").find_one({"company_id": company_id})
        if doc:
            return TaxSettings(**doc.get("settings", {}))
        else:
            return TaxSettings()
    else:
        s = db["tax_settings"].get(company_id)
        if s:
            return TaxSettings(**s)
        return TaxSettings()

def save_company_settings(company_id: str, settings: TaxSettings):
    if USE_MONGO:
        coll("tax_settings").replace_one({"company_id": company_id}, {"company_id": company_id, "settings": settings.dict()}, upsert=True)
    else:
        db["tax_settings"][company_id] = settings.dict()

# ---------- FastAPI app ----------
app = FastAPI(title="AI-CFO Tax & Filing Service (Hybrid)", version="v3")

# ---------- Endpoints ----------

@app.post("/tax/{company_id}/classify_transactions")
def classify_transactions(company_id: str, transactions: List[Transaction]):
    """
    Classify transactions for GST/TDS and store them (in Mongo or memory).
    """
    settings = get_company_settings(company_id)
    stored = []
    for t in transactions:
        rec = t.dict()
        rec["company_id"] = company_id
        inference = infer_tax_for_record(rec, settings)
        rec.update(inference)
        rec["classified_at"] = datetime.utcnow().isoformat()
        if USE_MONGO:
            coll("tax_transactions").insert_one(rec)
        else:
            db["tax_transactions"].append(rec)
        stored.append(rec)
    return {"company_id": company_id, "classified_count": len(stored), "classified_transactions": stored}


@app.post("/tax/{company_id}/enrich_transactions")
def enrich_transactions(company_id: str):
    """
    Re-run inference on existing transactions (e.g., after settings change).
    """
    settings = get_company_settings(company_id)
    if USE_MONGO:
        src = coll("tax_transactions").find({"company_id": company_id})
        updated = 0
        for rec in src:
            inf = infer_tax_for_record(rec, settings)
            rec.update(inf)
            coll("tax_transactions").replace_one({"_id": rec["_id"]}, rec)
            updated += 1
    else:
        updated = 0
        for idx, rec in enumerate(db["tax_transactions"]):
            if rec.get("company_id") == company_id:
                inf = infer_tax_for_record(rec, settings)
                db["tax_transactions"][idx].update(inf)
                updated += 1
    return {"company_id": company_id, "enriched": updated}


@app.post("/tax/{company_id}/calculate_gst")
def calculate_gst(company_id: str, use_data_service: Optional[bool] = False):
    """
    Aggregate GST for company:
    - Optionally pull transactions from Data Ingestion service if use_data_service=True
    - Otherwise use stored classified transactions
    """
    settings = get_company_settings(company_id)

    txs = []
    if use_data_service:
        txs = fetch_transactions_from_data_service(company_id)
    else:
        txs = [t for t in (mem_find("tax_transactions") if not USE_MONGO else list(coll("tax_transactions").find({"company_id": company_id}))) if t.get("company_id")==company_id]

    if not txs:
        raise HTTPException(status_code=404, detail="No transactions available for GST calculation")

    outward_taxable = 0.0
    outward_tax = 0.0
    inward_taxable = 0.0
    inward_tax = 0.0
    line_items = []

    for rec in txs:
        amt = float(rec.get("amount", 0))
        tax = 0.0
        if rec.get("is_gst_applicable"):
            rate = float(rec.get("gst_rate") or settings.gst_default_rate)
            # assume tax not already separated; if there is tax field try to use it
            if rec.get("tax") is not None:
                tax = float(rec.get("tax") or 0.0)
            else:
                # calculate tax on amount
                tax = round(amt * rate, 2)
            if rec.get("type") in ("sale","invoice","receipt"):
                outward_tax += tax
                outward_taxable += max(0.0, amt - tax) if rec.get("is_tax_inclusive") else amt
            elif rec.get("type") in ("purchase","payment"):
                inward_tax += tax
                inward_taxable += max(0.0, amt - tax) if rec.get("is_tax_inclusive") else amt

        line_items.append({"tx_id": rec.get("tx_id"), "type": rec.get("type"), "amount": amt, "is_gst_applicable": rec.get("is_gst_applicable"), "gst_rate": rec.get("gst_rate")})

    result_doc = {
        "company_id": company_id,
        "type": "gst_calculation",
        "generated_at": datetime.utcnow().isoformat(),
        "period": None,
        "outward_taxable_value": round(outward_taxable,2),
        "outward_tax": round(outward_tax,2),
        "inward_taxable_value": round(inward_taxable,2),
        "inward_tax": round(inward_tax,2),
        "line_items": line_items
    }
    # store return
    mem_insert("tax_returns", result_doc)
    # try audit record
    try:
        record_audit_entry(company_id, {"type":"gst_calculation","payload": result_doc, "status":"generated"})
    except Exception:
        pass
    return result_doc


@app.post("/tax/{company_id}/calculate_tds")
def calculate_tds(company_id: str, use_data_service: Optional[bool] = False):
    """
    Aggregate TDS for company:
    - Scans transactions (stored or from data service)
    - Retains section, rate and computed amounts
    """
    settings = get_company_settings(company_id)
    txs = []
    if use_data_service:
        txs = fetch_transactions_from_data_service(company_id)
    else:
        txs = [t for t in (mem_find("tax_transactions") if not USE_MONGO else list(coll("tax_transactions").find({"company_id": company_id}))) if t.get("company_id")==company_id]

    if not txs:
        raise HTTPException(status_code=404, detail="No transactions available for TDS calculation")

    tds_summary = []
    total_tds = 0.0

    for rec in txs:
        if rec.get("is_tds_applicable"):
            rate = float(rec.get("tds_rate") or 0.0)
            amt = float(rec.get("amount") or 0.0)
            tds_amt = round(amt * rate, 2)
            total_tds += tds_amt
            tds_summary.append({
                "tx_id": rec.get("tx_id"),
                "amount": amt,
                "tds_section": rec.get("tds_section"),
                "tds_rate": rate,
                "tds_amount": tds_amt
            })

    doc = {
        "company_id": company_id,
        "type": "tds_calculation",
        "generated_at": datetime.utcnow().isoformat(),
        "total_tds": round(total_tds,2),
        "line_items": tds_summary
    }
    mem_insert("tax_returns", doc)
    try:
        record_audit_entry(company_id, {"type":"tds_calculation","payload": doc, "status":"generated"})
    except Exception:
        pass
    return doc


@app.post("/tax/{company_id}/generate_itr_report")
def generate_itr_report(company_id: str, financial_year: Optional[str] = None):
    """
    Simplified ITR-style report using transactions:
    - income: sales/receipts
    - expenses: purchases/payments/expenses
    - subtract TDS paid (if any)
    """
    txs = [t for t in (mem_find("tax_transactions") if not USE_MONGO else list(coll("tax_transactions").find({"company_id": company_id}))) if t.get("company_id")==company_id]
    if not txs:
        raise HTTPException(status_code=404, detail="No transactions available to build ITR")

    total_income = sum(float(t.get("amount",0)) for t in txs if t.get("type") in ("sale","invoice","receipt"))
    total_expense = sum(float(t.get("amount",0)) for t in txs if t.get("type") in ("purchase","payment","expense"))
    # TDS deducted (if we stored tds_withheld or via inference)
    total_tds_deducted = 0.0
    for t in txs:
        if t.get("is_tds_applicable") and t.get("tds_rate"):
            total_tds_deducted += round(float(t.get("amount",0)) * float(t.get("tds_rate")),2)

    net_profit = round(total_income - total_expense,2)
    tax_estimate = round(net_profit * 0.25,2) if net_profit>0 else 0.0
    report = {
        "company_id": company_id,
        "type": "itr_report",
        "financial_year": financial_year,
        "generated_at": datetime.utcnow().isoformat(),
        "total_income": round(total_income,2),
        "total_expense": round(total_expense,2),
        "net_profit_before_tax": net_profit,
        "tax_estimate": tax_estimate,
        "tds_deducted": round(total_tds_deducted,2)
    }
    mem_insert("tax_returns", report)
    try:
        record_audit_entry(company_id, {"type":"itr_report","payload": report, "status":"generated"})
    except Exception:
        pass
    return report


@app.get("/tax/{company_id}/gst_return_data/{period}")
def gst_return_data(company_id: str, period: str):
    # simple: return all GST-type returns stored for this company
    returns = [r for r in (mem_find("tax_returns") if not USE_MONGO else list(coll("tax_returns").find({"company_id": company_id}))) if r.get("company_id")==company_id and r.get("type","").startswith("gst")]
    return {"company_id": company_id, "period": period, "returns": returns}


@app.get("/tax/{company_id}/deadlines")
def get_deadlines(company_id: str):
    # static defaults (could be enriched from db or external config)
    deadlines = [
        {"tax_type":"GST (GSTR-3B)", "frequency": "monthly", "next_due": "2025-11-20"},
        {"tax_type":"TDS", "frequency": "quarterly", "next_due": "2025-11-07"},
        {"tax_type":"Income Tax (Return)", "frequency":"yearly", "next_due":"2026-07-31"}
    ]
    # trigger notifications (best-effort)
    try:
        for d in deadlines:
            send_notification({"company_id": company_id, "type":"tax_deadline", "message": f"{d['tax_type']} due on {d['next_due']}"})
    except Exception:
        pass
    return {"company_id": company_id, "deadlines": deadlines}


@app.get("/tax/{company_id}/optimization_guidance")
def optimization_guidance(company_id: str):
    # basic rule based guidance
    txs = [t for t in (mem_find("tax_transactions") if not USE_MONGO else list(coll("tax_transactions").find({"company_id": company_id}))) if t.get("company_id")==company_id]
    agg = {}
    total = 0.0
    for t in txs:
        cat = t.get("category") or "other"
        amt = float(t.get("amount") or 0.0)
        agg[cat] = agg.get(cat,0.0)+amt
        total += amt
    suggestions = []
    for cat,amt in sorted(agg.items(), key=lambda kv: kv[1], reverse=True)[:5]:
        share = (amt/total) if total else 0
        if share > 0.2:
            suggestions.append({"category":cat,"spend":round(amt,2),"share":round(share,2),"suggestion":"Consider vendor consolidation or negotiate rates."})
    tips = [
        "Claim input GST where applicable; match invoices with payments.",
        "Ensure TDS deducted and deposited on time to avoid interest and notices.",
        "If small supplier, review GST composition vs regular regime with your CA."
    ]
    return {"company_id": company_id, "suggestions": suggestions or [{"message":"Spending looks diversified"}], "tips": tips}


@app.put("/tax/{company_id}/settings")
def update_settings(company_id: str, settings: TaxSettings):
    save_company_settings(company_id, settings)
    return {"company_id": company_id, "settings": settings.dict()}


@app.post("/tax/{company_id}/seed_sample")
def seed_sample(company_id: str):
    """
    Seed 3 sample transactions (Tally-style + expense + sale)
    """
    mem_delete_many("tax_transactions", {"company_id": company_id})
    sample = [
        {"company_id": company_id, "tx_id": "VOU-001", "date":"2025-09-02", "description":"Sale of goods", "type":"sale", "category":"goods", "amount":12000, "source":"tally", "tax":2160},
        {"company_id": company_id, "tx_id": "VOU-002", "date":"2025-09-10", "description":"Payment to vendor - contract", "type":"payment", "category":"contractor", "amount":40000, "source":"bank"},
        {"company_id": company_id, "tx_id": "VOU-003", "date":"2025-09-22", "description":"Consulting services - freelancer", "type":"expense", "category":"professional services", "amount":18000, "source":"tally", "tax":3240}
    ]
    for t in sample:
        if USE_MONGO:
            coll("tax_transactions").insert_one(t)
        else:
            db["tax_transactions"].append(t)
    # default settings
    default_settings = TaxSettings()
    save_company_settings(company_id, default_settings)
    return {"seeded": True, "company_id": company_id, "sample_count": len(sample)}


# ---------- Startup/shutdown hooks ----------
@app.on_event("startup")
def startup_event():
    logger.info("Tax & Filing Service starting. USE_MONGO=%s", USE_MONGO)

@app.on_event("shutdown")
def shutdown_event():
    if USE_MONGO and db_client:
        db_client.close()
        logger.info("Mongo client closed.")

# End of file
