# backend/ingestion_service_standalone.py

# --- 1. IMPORTS ---
import os
import sys
import logging
import uuid
import json
from datetime import datetime, timezone
from typing import List, Dict, Any, Callable
from pydantic import BaseModel
from dotenv import load_dotenv
import pymongo
from bson import ObjectId
from pathlib import Path

import uvicorn
from fastapi import FastAPI, APIRouter, HTTPException, status

# --- 2. LOAD .ENV & CONNECT TO MONGODB ---
dotenv_path = Path(__file__).resolve().parent / ".env"
load_dotenv(dotenv_path=dotenv_path)
MONGODB_URI = os.getenv("MONGODB_URI")
if not MONGODB_URI:
    raise ValueError(f"MONGODB_URI not found. Looked for .env file at: {dotenv_path}")

client = pymongo.MongoClient(MONGODB_URI)
db = client.get_database("ZypheryDB")
raw_data_jobs_collection = db.raw_data_jobs
normalized_collection = db.normalized_transactions

# --- 3. LOGGER SETUP ---
def get_logger(name: str):
    logger = logging.getLogger(name)
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s', '%Y-%m-%d %H:%M:%S')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    return logger

log = get_logger("IngestionServiceStandalone (Port 8004)")

# --- 4. NORMALIZATION HELPER FUNCTIONS ---
def _get_common_fields(original_id: str, source_system: str) -> Dict:
    return {"transaction_id": str(uuid.uuid4()), "original_id": str(original_id), "source_system": source_system, "due_date": None, "payment_method": None, "ingested_at": datetime.now(timezone.utc).isoformat()}
def _parse_date(date_str: Any, default_day=1) -> str | None:
    if not date_str or not isinstance(date_str, str): return None
    try:
        if len(date_str) == 7 and date_str.count('-') == 1: return datetime.strptime(f"{date_str}-{default_day}", '%Y-%m-%d').date().isoformat()
        return datetime.fromisoformat(date_str.rstrip('Z')).date().isoformat()
    except ValueError:
        try: return datetime.strptime(date_str, '%Y-%m-%d').date().isoformat()
        except Exception: return None

# ... (all other _normalize functions are unchanged) ...
def _normalize_google_sheet(row: Dict) -> Dict:
    normalized = _get_common_fields(row.get('row_id'), 'google_sheets_export'); amount = float(row.get('amount', 0)); category = row.get('category', ''); tx_type = "income" if category.lower() == 'revenue' else "expense"; final_amount = abs(amount) if tx_type == "income" else -abs(amount)
    normalized.update({"transaction_date": _parse_date(row.get('period')), "amount": final_amount, "currency": "INR", "transaction_type": tx_type, "status": "completed", "category": category, "description": row.get('notes'), "counterparty": None}); return normalized
def _normalize_notion(row: Dict) -> Dict:
    normalized = _get_common_fields(row.get('id'), 'notion_expenses')
    normalized.update({"transaction_date": _parse_date(row.get('Date')), "amount": -abs(float(row.get('Amount', 0))), "currency": "INR", "transaction_type": "expense", "status": "completed", "category": row.get('Category'), "description": row.get('Name'), "counterparty": "Uber" if "uber" in row.get('Name', '').lower() else None}); return normalized
def _normalize_razorpay(row: Dict) -> Dict:
    normalized = _get_common_fields(row.get('id'), 'razorpay_payments'); amount_paise = int(row.get('amount', 0)); tx_timestamp = int(row.get('created_at', 0))
    normalized.update({"transaction_date": datetime.fromtimestamp(tx_timestamp, tz=timezone.utc).isoformat(), "amount": amount_paise / 100.0, "currency": row.get('currency', 'INR').upper(), "transaction_type": "income", "status": row.get('status'), "category": "Sales", "description": f"Payment from {row.get('email') or row.get('contact')}", "counterparty": row.get('email') or row.get('contact'), "payment_method": row.get('method')}); return normalized
def _normalize_tally(row: Dict) -> Dict:
    normalized = _get_common_fields(row.get('voucher_id'), 'tally_vouchers'); voucher_type = row.get('voucher_type', '').lower(); amount = float(row.get('amount', 0)); tx_type = "expense" if voucher_type in ['payment', 'debit note', 'purchase'] else "income"; final_amount = -abs(amount) if tx_type == "expense" else abs(amount)
    normalized.update({"transaction_date": _parse_date(row.get('date')), "amount": final_amount, "currency": "INR", "transaction_type": tx_type, "status": "completed", "category": row.get('ledger'), "description": row.get('narration'), "counterparty": row.get('party_name')}); return normalized

# --- [ UPDATED FUNCTION ] ---
def _normalize_bank(row: Dict) -> Dict:
    normalized = _get_common_fields(row.get('transaction_id'), 'bank_transactions')
    tx_type = row.get('type', '').lower(); amount = float(row.get('amount', 0)); description = row.get('description', '')
    final_amount = -amount if tx_type == 'debit' else amount
    tx_type_normalized = "expense" if tx_type == 'debit' else "income"
    counterparty = "Client A" if "Client A" in description else None
    category = "Client Payment" if "Client A" in description else "Bank Transaction"
    payment_method = "NEFT" if "NEFT" in description else "UPI" if "UPI" in description else None
    
    normalized.update({
        "transaction_date": _parse_date(row.get('date')),
        "amount": final_amount,
        "currency": "INR",
        "transaction_type": tx_type_normalized,
        "status": "completed",
        "category": category,
        "description": description,
        "counterparty": counterparty,
        "payment_method": payment_method,
        "balance": float(row.get('balance', 0))  # <-- THIS IS THE NEW LINE
    })
    return normalized
# --- [ END UPDATED FUNCTION ] ---

def _parse_line_item(line_items: Any, desc_key: str, amt_key: str) -> (str, float):
    if not line_items: return "Line item details missing", 0.0
    try:
        items = json.loads(line_items.replace("'", "\"")) if isinstance(line_items, str) else line_items
        if isinstance(items, list) and len(items) > 0: first_item = items[0]; return first_item.get(desc_key, "Unknown Item"), float(first_item.get(amt_key, 0.0))
    except Exception: pass
    return str(line_items), 0.0
def _normalize_quickbooks(row: Dict) -> Dict:
    normalized = _get_common_fields(row.get('Id'), 'qbo_invoices'); desc, _ = _parse_line_item(row.get('Line'), 'Description', 'Amount'); normalized.update({"transaction_date": _parse_date(row.get('TxnDate')), "due_date": _parse_date(row.get('DueDate')), "amount": float(row.get('TotalAmt', 0)), "currency": row.get('CurrencyRef', 'INR'), "transaction_type": "invoice", "status": row.get('TxnStatus'), "category": "Sales", "description": desc, "counterparty": row.get('CustomerRef')}); return normalized
def _normalize_zoho(row: Dict) -> Dict:
    normalized = _get_common_fields(row.get('invoice_id'), 'zoho_invoices'); desc, _ = _parse_line_item(row.get('line_items'), 'desc', 'rate'); normalized.update({"transaction_date": _parse_date(row.get('date')), "due_date": _parse_date(row.get('due_date')), "amount": float(row.get('total', 0)), "currency": row.get('currency', 'INR'), "transaction_type": "invoice", "status": row.get('status'), "category": "Sales", "description": desc, "counterparty": row.get('customer_id')}); return normalized

# --- 5. MASTER MAPPER & PROCESSING FUNCTION (Unchanged) ---
MASTER_MAPPER: Dict[str, Callable] = {
    "google_sheets_export": _normalize_google_sheet, "notion_expenses": _normalize_notion,
    "razorpay_payments": _normalize_razorpay, "tally_vouchers": _normalize_tally,
    "bank_transactions": _normalize_bank, "qbo_invoices": _normalize_quickbooks,
    "zoho_invoices": _normalize_zoho
}
def _process_job(job: Dict) -> Dict:
    source_system = job['source_system']; raw_rows = job['data']; log.info(f"Normalizing job {job['_id']} ('{source_system}') with {len(raw_rows)} rows.")
    mapper_function = MASTER_MAPPER.get(source_system)
    if not mapper_function: raise ValueError(f"No mapper for '{source_system}'")
    normalized_rows_to_insert = []; error_count = 0
    for row in raw_rows:
        try:
            normalized_row = mapper_function(row); normalized_row['company_id'] = job['company_id'] 
            normalized_rows_to_insert.append(normalized_row)
        except Exception as e:
            error_count += 1; log.error(f"Failed to normalize row. Error: {e}. Row: {row}")
    if normalized_rows_to_insert:
        normalized_collection.insert_many(normalized_rows_to_insert)
    raw_data_jobs_collection.update_one(
        {"_id": job['_id']},
        {"$set": {"status": "processed", "processed_at": datetime.now(), "error_count": error_count}}
    )
    return {"job_id": str(job['_id']), "rows_processed": len(normalized_rows_to_insert), "rows_failed": error_count}

# --- 6. FASTAPI APP AND ROUTER SETUP (Unchanged) ---
app = FastAPI(
    title="ZYPHERY - Standalone Ingestion Service (Service 4)",
    description="Reads 'pending' jobs from MongoDB, normalizes, and writes to DB.",
    version="1.1.0" # You can update this to 1.2.0 if you like
)
router = APIRouter()
@router.post("/process/all", status_code=status.HTTP_200_OK)
async def process_all_pending_jobs():
    log.info("Processing all pending ingestion jobs...")
    try:
        pending_jobs = list(raw_data_jobs_collection.find({"status": "pending"}))
        if not pending_jobs:
            log.info("No pending jobs found."); return {"message": "No pending jobs to process."}
        log.info(f"Found {len(pending_jobs)} pending jobs to process.")
        results = []
        for job in pending_jobs:
            try:
                result = _process_job(job); results.append(result)
            except Exception as e:
                log.error(f"Failed to process job {job['_id']}: {e}")
                raw_data_jobs_collection.update_one({"_id": job['_id']}, {"$set": {"status": "failed", "error": str(e)}})
                results.append({"job_id": str(job['_id']), "status": "failed", "error": str(e)})
        return {"message": "Processing complete.", "jobs_processed": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An internal error occurred: {str(e)}")
@router.get("/transactions", status_code=status.HTTP_200_OK)
async def get_all_normalized_transactions():
    try:
        transactions = list(normalized_collection.find())
        for tx in transactions:
            tx['_id'] = str(tx['_id'])
        return {"count": len(transactions), "data": transactions}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch transactions: {str(e)}")
app.include_router(router, prefix="/ingest", tags=["Ingestion"])

# --- 7. MAIN EXECUTION BLOCK ---
if __name__ == "__main__":
    port = 8004
    log.info(f"🚀 Starting Standalone Ingestion Service (Service 4) on http://127.0.0.1:{port}")
    uvicorn.run(__name__ + ":app", host="0.0.0.0", port=port, reload=True)