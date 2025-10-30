# backend/finance_core_service_standalone.py

# --- 1. IMPORTS ---
import os
import sys
import logging
from typing import List, Dict, Any
from datetime import datetime, timedelta
from dotenv import load_dotenv
import pymongo
from pathlib import Path

import pandas as pd
import uvicorn
from fastapi import FastAPI, APIRouter, HTTPException, status, Query, Body
from pydantic import BaseModel

# --- 2. LOAD .ENV & CONNECT TO MONGODB ---
dotenv_path = Path(__file__).resolve().parent / ".env"
load_dotenv(dotenv_path=dotenv_path)
MONGODB_URI = os.getenv("MONGODB_URI")
if not MONGODB_URI:
    raise ValueError(f"MONGODB_URI not found. Looked for .env file at: {dotenv_path}")

client = pymongo.MongoClient(MONGODB_URI)
db = client.get_database("ZypheryDB")
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

log = get_logger("FinanceCoreService (Port 8005)")

# --- 4. HELPER FUNCTION ---
def _get_transactions_df(company_id: str) -> pd.DataFrame:
    log.info(f"Fetching normalized transactions for {company_id} from MongoDB...")
    try:
        transactions = list(normalized_collection.find({"company_id": company_id}))
        if not transactions:
            log.warning(f"No transactions found for {company_id} in MongoDB.")
            return pd.DataFrame()
        log.info(f"Successfully fetched {len(transactions)} transactions.")
        df = pd.DataFrame(transactions)
        df['transaction_date'] = pd.to_datetime(df['transaction_date'])
        df['due_date'] = pd.to_datetime(df['due_date'], errors='coerce')
        # Ensure 'amount' is numeric, coercing errors to NaN (which pandas handles)
        df['amount'] = pd.to_numeric(df['amount'], errors='coerce')
        # Optionally, fill NaN amounts with 0 if that makes sense for your logic
        # df['amount'] = df['amount'].fillna(0)
        return df
    except Exception as e:
        log.error(f"Error fetching/processing data from MongoDB: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get data from database: {str(e)}")


def _get_latest_cash_balance(company_id: str) -> float:
    log.info(f"Fetching latest cash balance for {company_id}...")
    try:
        latest_bank_tx = normalized_collection.find_one(
            {"company_id": company_id, "source_system": "bank_transactions", "balance": {"$exists": True, "$ne": None}},
            sort=[("transaction_date", pymongo.DESCENDING)]
        )
        if latest_bank_tx:
            balance = float(latest_bank_tx['balance'])
            log.info(f"Found latest balance: {balance} from transaction {latest_bank_tx['original_id']} on {latest_bank_tx['transaction_date']}")
            return balance
    except Exception as e:
        log.error(f"Error fetching latest balance from MongoDB: {e}")
    log.warning(f"No bank balance data found for {company_id}. Falling back to 0.")
    return 0.0 # Fallback to 0 instead of mock

# --- 5. REQUEST BODY MODEL ---
class ForecastRequest(BaseModel):
    spend_change_pct: float = 0.0
    revenue_change_pct: float = 0.0
    class Config: schema_extra = {"example": {"spend_change_pct": 20, "revenue_change_pct": -10}}

# --- 6. FASTAPI APP AND ROUTER SETUP ---
app = FastAPI(
    title="ZYPHERY - Standalone Finance Core (Service 5)",
    description="Reads from MongoDB to perform financial calculations.",
    version="1.3.1" # Bumped version
)
router = APIRouter()

# --- [ UPDATED: Removed 'async' ] ---
@router.get("/financials/{company_id}/runway", status_code=status.HTTP_200_OK)
def get_financial_runway(company_id: str): # REMOVED async
    df = _get_transactions_df(company_id)
    if df.empty: raise HTTPException(status_code=404, detail="No transaction data available.")
    cash_balance = _get_latest_cash_balance(company_id)
    ninety_days_ago = datetime.now() - timedelta(days=90)
    recent_df = df[df['transaction_date'] >= ninety_days_ago]
    if recent_df.empty:
        return {"message": "No transactions found in the last 90 days.", "data": {}}
    total_revenue_90d = recent_df[recent_df['amount'] > 0]['amount'].sum()
    total_burn_90d = abs(recent_df[recent_df['amount'] < 0]['amount'].sum())
    avg_monthly_revenue = round((total_revenue_90d / 90) * 30, 2)
    avg_monthly_burn = round((total_burn_90d / 90) * 30, 2)
    baseline_net_burn = avg_monthly_burn - avg_monthly_revenue
    runway_months = "infinite (Profitable)" if baseline_net_burn <= 0 else round(cash_balance / baseline_net_burn, 1) if baseline_net_burn != 0 else "infinite (zero net burn)"
    return {"company_id": company_id, "current_cash_balance": cash_balance, "monthly_burn_rate": avg_monthly_burn, "monthly_net_burn": baseline_net_burn, "monthly_revenue": avg_monthly_revenue, "current_runway_months": runway_months, "calculation_based_on_days": 90}

# --- [ UPDATED: Removed 'async' ] ---
@router.get("/financials/{company_id}/pnl", status_code=status.HTTP_200_OK)
def get_profit_and_loss( # REMOVED async
    company_id: str,
    start_date: str = Query(..., description="Start date in YYYY-MM-DD format"),
    end_date: str = Query(..., description="End date in YYYY-MM-DD format")
):
    df = _get_transactions_df(company_id)
    if df.empty: raise HTTPException(status_code=404, detail="No transaction data available.")
    try: start = pd.to_datetime(start_date); end = pd.to_datetime(end_date)
    except ValueError: raise HTTPException(status_code=422, detail="Invalid date format. Use YYYY-MM-DD.")
    period_df = df[(df['transaction_date'] >= start) & (df['transaction_date'] <= end)]
    if period_df.empty: return {"message": "No data found for the specified period.", "data": {}}
    revenue_df = period_df[period_df['amount'] > 0]; total_revenue = round(revenue_df['amount'].sum(), 2)
    expenses_df = period_df[period_df['amount'] < 0]; expenses_by_category = round(expenses_df.groupby('category')['amount'].sum().abs(), 2).to_dict(); total_expenses = round(expenses_df['amount'].sum(), 2)
    net_profit = round(total_revenue + total_expenses, 2)
    return {"company_id": company_id, "period_start": start_date, "period_end": end_date, "profit_and_loss_summary": {"total_revenue": total_revenue, "total_expenses": abs(total_expenses), "net_profit": net_profit, "profit_margin_pct": round((net_profit / total_revenue) * 100, 2) if total_revenue != 0 else 0}, "expenses_breakdown": expenses_by_category}

# --- [ UPDATED: Removed 'async' ] ---
@router.post("/financials/{company_id}/forecast", status_code=status.HTTP_200_OK)
def get_what_if_forecast( # REMOVED async
    company_id: str,
    body: ForecastRequest = Body(...)
):
    df = _get_transactions_df(company_id)
    if df.empty: raise HTTPException(status_code=404, detail="No transaction data available.")
    cash_balance = _get_latest_cash_balance(company_id)
    ninety_days_ago = datetime.now() - timedelta(days=90)
    recent_df = df[df['transaction_date'] >= ninety_days_ago]
    if recent_df.empty: raise HTTPException(status_code=404, detail="No data in last 90 days to create a forecast.")
    total_revenue_90d = recent_df[recent_df['amount'] > 0]['amount'].sum()
    total_burn_90d = abs(recent_df[recent_df['amount'] < 0]['amount'].sum())
    baseline_revenue = round((total_revenue_90d / 90) * 30, 2); baseline_burn = round((total_burn_90d / 90) * 30, 2)
    baseline_net_burn = baseline_burn - baseline_revenue; baseline_runway = "infinite" if baseline_net_burn <= 0 else round(cash_balance / baseline_net_burn, 1) if baseline_net_burn != 0 else "infinite (zero net burn)"
    projected_revenue = baseline_revenue * (1 + body.revenue_change_pct / 100); projected_burn = baseline_burn * (1 + body.spend_change_pct / 100)
    projected_net_burn = projected_burn - projected_revenue; projected_runway = "infinite (Profitable)" if projected_net_burn <= 0 else round(cash_balance / projected_net_burn, 1) if projected_net_burn != 0 else "infinite (zero net burn)"
    return {"company_id": company_id, "cash_balance": cash_balance, "inputs": body.dict(), "baseline": {"monthly_revenue": baseline_revenue, "monthly_burn": baseline_burn, "monthly_net_burn": round(baseline_net_burn, 2), "runway_months": baseline_runway}, "projected": {"monthly_revenue": round(projected_revenue, 2), "monthly_burn": round(projected_burn, 2), "monthly_net_burn": round(projected_net_burn, 2), "runway_months": projected_runway}}

app.include_router(router, prefix="/financials", tags=["Finance Core"])

# --- 7. MAIN EXECUTION BLOCK ---
if __name__ == "__main__":
    port = 8005
    log.info(f"🚀 Starting Standalone Finance Core (Service 5) on http://127.0.0.1:{port}")
    uvicorn.run(__name__ + ":app", host="0.0.0.0", port=port, reload=True)