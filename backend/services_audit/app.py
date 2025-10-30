# app.py
import os
import uuid
import csv
import io
import asyncio
from decimal import Decimal, InvalidOperation
from datetime import datetime
from typing import List

from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Query
from fastapi.responses import FileResponse, JSONResponse
from motor.motor_asyncio import AsyncIOMotorClient
import aiofiles

from utils.ocr_utils import ocr_pdf_to_text
from utils.proposal_generator import generate_proposal_pdf
from utils.report_generator import generate_audit_report_pdf
from utils.rules_engine import run_rules_on_transactions, normalize_tx
from decouple import config

MONGO_URI: str = config("MONGO_URI")
DB_NAME: str = config("DB_NAME")

UPLOAD_DIR = "uploads"
REPORTS_DIR = "reports"

os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(REPORTS_DIR, exist_ok=True)

app = FastAPI(title="AI Audit Agent")

# Motor client
client = AsyncIOMotorClient(MONGO_URI)
db = client[DB_NAME]


@app.post("/audit/initiate")
async def initiate_audit(payload: dict):
    """
    Starts a new audit session and generates an Engagement Letter (Proposal PDF).
    Body: { client_name, period, scope: [ ... ] }
    """
    client_name = payload.get("client_name")
    period = payload.get("period")
    scope = payload.get("scope", [])

    if not client_name or not period:
        raise HTTPException(status_code=400, detail="client_name and period required")

    audit_id = str(uuid.uuid4())

    # store audit metadata
    audit_doc = {
        "audit_id": audit_id,
        "client_name": client_name,
        "period": period,
        "scope": scope,
        "status": "proposal_created",
        "created_at": datetime.utcnow()
    }
    await db.audits.insert_one(audit_doc)

    # generate proposal pdf synchronously in thread to keep API responsive
    proposal_path = os.path.join(REPORTS_DIR, f"{audit_id}_proposal.pdf")
    await asyncio.to_thread(generate_proposal_pdf, proposal_path, client_name, period, scope, audit_id)

    # store proposal path
    await db.audits.update_one({"audit_id": audit_id}, {"$set": {"proposal_letter": proposal_path}})

    # log
    await db.audit_logs.insert_one({"audit_id": audit_id, "action": "proposal_created", "timestamp": datetime.utcnow()})

    return {"audit_id": audit_id, "status": "proposal_created", "proposal_pdf": proposal_path}


@app.post("/upload")
async def upload_file(audit_id: str = Query(...), file: UploadFile = File(...)):
    """
    Upload CSV or PDF for given audit_id. OCR PDFs; parse CSVs.
    """
    # check audit exists
    audit = await db.audits.find_one({"audit_id": audit_id})
    if not audit:
        raise HTTPException(status_code=404, detail="audit_id not found")

    filename = file.filename
    ext = filename.split(".")[-1].lower()

    dest_dir = os.path.join(UPLOAD_DIR, audit_id)
    os.makedirs(dest_dir, exist_ok=True)
    dest_path = os.path.join(dest_dir, f"{uuid.uuid4().hex}_{filename}")

    # save uploaded file
    async with aiofiles.open(dest_path, "wb") as out_file:
        content = await file.read()
        await out_file.write(content)

    uploaded_count = 0

    if ext in ("csv",):
        # parse CSV and normalize
        text_io = io.StringIO(content.decode("utf-8", errors="replace"))
        reader = csv.DictReader(text_io)
        tx_docs = []
        for row in reader:
            tx = normalize_tx(row)
            tx["audit_id"] = audit_id
            tx_docs.append(tx)
        if tx_docs:
            await db.transactions.insert_many(tx_docs)
            uploaded_count = len(tx_docs)
    elif ext in ("pdf",):
        # run OCR on pdf bytes in thread
        text = await ocr_pdf_to_text(content)
        # naive parsing: look for CSV-like lines or regex; but we try to parse lines with amounts
        tx_docs = []
        for line in text.splitlines():
            row = attempt_parse_line_to_tx(line)
            if row:
                row["audit_id"] = audit_id
                tx_docs.append(row)
        # If no lines parsed, insert a meta doc capturing OCR text for later manual review
        if tx_docs:
            await db.transactions.insert_many(tx_docs)
            uploaded_count = len(tx_docs)
        else:
            await db.ocr_texts.insert_one({"audit_id": audit_id, "source_file": filename, "text": text, "created_at": datetime.utcnow()})
            uploaded_count = 0
    else:
        raise HTTPException(status_code=400, detail="Unsupported file type. Only CSV and PDF allowed")

    await db.audit_logs.insert_one({"audit_id": audit_id, "action": "upload", "file": filename, "uploaded_count": uploaded_count, "timestamp": datetime.utcnow()})

    return {"audit_id": audit_id, "uploaded": uploaded_count}


def attempt_parse_line_to_tx(line: str):
    """
    Very basic heuristic to pull date, amount, invoice no, description from a single OCR line.
    This is intentionally simple; real world requires robust parsers.
    """
    import re
    line = line.strip()
    if not line:
        return None

    # try to find an amount (numbers with optional commas, decimals)
    amt_match = re.search(r'([0-9]{1,3}(?:[,][0-9]{3})*(?:\.[0-9]{1,2})?)', line.replace("₹", ""))
    date_match = re.search(r'(\d{4}[-/]\d{2}[-/]\d{2}|\d{2}[-/]\d{2}[-/]\d{4})', line)
    inv_match = re.search(r'INV[\s\-]*\d+', line, re.IGNORECASE)

    if not amt_match:
        return None

    amount_raw = amt_match.group(1).replace(",", "")
    try:
        amount = float(amount_raw)
    except:
        amount = 0.0

    tx = {
        "date": date_match.group(1) if date_match else None,
        "description": line,
        "amount": amount,
        "invoice_no": inv_match.group(0) if inv_match else None,
        "gst_amount": 0,
        "source": "ocr_pdf"
    }
    return tx


@app.post("/audit/{audit_id}/run")
async def run_audit(audit_id: str):
    """
    Performs reconciliation and rule-based audit.
    """
    audit = await db.audits.find_one({"audit_id": audit_id})
    if not audit:
        raise HTTPException(status_code=404, detail="audit_id not found")

    # fetch transactions
    cursor = db.transactions.find({"audit_id": audit_id})
    txs = await cursor.to_list(length=None)

    # run rules engine
    findings = run_rules_on_transactions(txs)

    if findings:
        # insert findings
        await db.findings.insert_many([{**f, "audit_id": audit_id, "created_at": datetime.utcnow()} for f in findings])

    # reconciliation: find bank txs without ledger matches
    bank_txs = [t for t in txs if t.get("source") == "bank"]
    ledger_txs = [t for t in txs if t.get("source") == "ledger"]

    unmatched_bank = []
    for b in bank_txs:
        matched = False
        for l in ledger_txs:
            if match_transactions(b, l):
                matched = True
                break
        if not matched:
            unmatched_bank.append(b)
            await db.findings.insert_one({
                "audit_id": audit_id,
                "rule": "Unmatched bank transaction",
                "severity": "medium",
                "description": f"Bank tx {b.get('invoice_no') or b.get('description')} amount {b.get('amount')} not found in ledger",
                "created_at": datetime.utcnow()
            })

    # generate report
    report_path = os.path.join(REPORTS_DIR, f"{audit_id}.pdf")
    # gather summary stats
    num_tx = len(txs)
    date_range = get_date_range_of_txs(txs)
    findings_cursor = db.findings.find({"audit_id": audit_id})
    all_findings = await findings_cursor.to_list(length=None)

    await asyncio.to_thread(generate_audit_report_pdf, report_path, audit_id, audit, num_tx, date_range, all_findings)

    # update audits collection
    await db.audits.update_one({"audit_id": audit_id}, {"$set": {"status": "done", "report_path": report_path, "completed_at": datetime.utcnow()}})

    await db.audit_logs.insert_one({"audit_id": audit_id, "action": "audit_run", "timestamp": datetime.utcnow()})

    return {"audit_id": audit_id, "status": "done"}


@app.get("/audit/{audit_id}/findings")
async def get_findings(audit_id: str):
    cursor = db.findings.find({"audit_id": audit_id})
    items = await cursor.to_list(length=None)
    # simplify output
    out = [{"rule": i["rule"], "severity": i.get("severity", "low"), "description": i.get("description")} for i in items]
    return out


@app.get("/audit/{audit_id}/report")
async def get_report(audit_id: str):
    audit = await db.audits.find_one({"audit_id": audit_id})
    if not audit:
        raise HTTPException(status_code=404, detail="audit_id not found")
    report_path = audit.get("report_path")
    if not report_path or not os.path.exists(report_path):
        raise HTTPException(status_code=404, detail="report not found")
    return FileResponse(report_path, media_type="application/pdf", filename=f"{audit_id}.pdf")


@app.get("/audit/{audit_id}/logs")
async def get_logs(audit_id: str):
    cursor = db.audit_logs.find({"audit_id": audit_id}).sort("timestamp", 1)
    items = await cursor.to_list(length=None)
    for i in items:
        i["_id"] = str(i["_id"])
    return items


# --- helpers ---

def match_transactions(a: dict, b: dict) -> bool:
    """
    Simple matching strategy:
    - if invoice_no present and equal -> match
    - else if amounts equal (within small tolerance) and date within 3 days -> match
    """
    try:
        if a.get("invoice_no") and b.get("invoice_no"):
            if str(a.get("invoice_no")).strip().lower() == str(b.get("invoice_no")).strip().lower():
                return True
        a_amt = float(a.get("amount") or 0)
        b_amt = float(b.get("amount") or 0)
        if abs(a_amt - b_amt) <= 1.0:  # ₹1 tolerance
            # check dates
            a_date = parse_date(a.get("date"))
            b_date = parse_date(b.get("date"))
            if a_date and b_date:
                delta = abs((a_date - b_date).days)
                if delta <= 3:
                    return True
            else:
                return True
    except Exception:
        return False
    return False


def parse_date(d):
    if not d:
        return None
    for fmt in ("%Y-%m-%d", "%d-%m-%Y", "%d/%m/%Y", "%Y/%m/%d"):
        try:
            return datetime.strptime(d, fmt)
        except:
            continue
    return None


def get_date_range_of_txs(txs):
    dates = [parse_date(t.get("date")) for t in txs if parse_date(t.get("date")) is not None]
    if not dates:
        return None
    return {"min": min(dates).strftime("%Y-%m-%d"), "max": max(dates).strftime("%Y-%m-%d")}
