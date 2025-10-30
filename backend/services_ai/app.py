# app.py
import os
import io
import math
import re
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Tuple

from fastapi import FastAPI, Path, Body, Query
from fastapi.responses import StreamingResponse, JSONResponse
from pydantic import BaseModel
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from apscheduler.schedulers.background import BackgroundScheduler
import atexit


# Try pymongo for optional Mongo usage
try:
    import pymongo
    MONGO_PRESENT = True
except Exception:
    MONGO_PRESENT = False

app = FastAPI(title="AI-CFO Insights v2 — Reasoning + What-If (Single file)")

# -------------------------
# Request models
# -------------------------
class ChatRequest(BaseModel):
    query: str

# -------------------------
# DataStore: Mongo if present else simulate 6 months
# -------------------------
class DataStore:
    def __init__(self):
        self.use_mongo = False
        self.client = None
        self.db = None
        if MONGO_PRESENT:
            mongo_uri = os.getenv("MONGO_URI", "mongodb://localhost:27017")
            try:
                client = pymongo.MongoClient(mongo_uri, serverSelectionTimeoutMS=1500)
                client.admin.command("ping")
                self.client = client
                self.db = client.get_database(os.getenv("MONGO_DB", "ai_cfo_demo"))
                self.use_mongo = True
                print("Connected to MongoDB:", mongo_uri)
            except Exception as e:
                print("Mongo unreachable; falling back to simulated data. Error:", e)
                self.use_mongo = False
        else:
            print("pymongo not installed; using simulated data.")
            self.use_mongo = False

        if not self.use_mongo:
            self._simulate_6_months()

    def _simulate_6_months(self):
        today = datetime.now().date()
        base = pd.Timestamp(today.replace(day=1))
        months = [(base - pd.DateOffset(months=i)).strftime("%Y-%m") for i in reversed(range(6))]
        rng = np.random.default_rng(42)
        categories = ["Payroll", "Marketing", "SaaS", "Ops", "Other"]

        # Expenses monthly per category
        exp_rows = []
        for i, m in enumerate(months):
            payroll = int(220000 + i * 12000 + rng.integers(-5000, 5000))
            marketing = int(40000 + rng.integers(-8000, 8000))
            saas = int(28000 + rng.integers(-3000, 3000))
            ops = int(16000 + rng.integers(-2000, 2000))
            other = int(8000 + rng.integers(-2000, 2000))
            amounts = [payroll, marketing, saas, ops, other]
            for cat, amt in zip(categories, amounts):
                exp_rows.append({"month": m, "category": cat, "amount": float(amt)})

        self.expenses_df = pd.DataFrame(exp_rows)

        # Revenue monthly (Product + Services)
        rev_rows = []
        for i, m in enumerate(months):
            product = int(250000 + i * 8000 + rng.integers(-7000,7000))
            services = int(40000 + rng.integers(-5000,5000))
            rev_rows.append({"month": m, "source": "Product", "amount": float(product)})
            rev_rows.append({"month": m, "source": "Services", "amount": float(services)})
        self.revenue_df = pd.DataFrame(rev_rows)

        # Cash timeseries: compute balance iteratively
        cash_rows = []
        balance = 700000.0
        for m in months:
            inflow = float(self.revenue_df[self.revenue_df["month"] == m]["amount"].sum() + rng.integers(-5000,5000))
            outflow = float(self.expenses_df[self.expenses_df["month"] == m]["amount"].sum() + rng.integers(-5000,5000))
            # small random adjustments
            shock = float(rng.integers(-20000,20000))
            if shock > 0:
                inflow += shock * 0.5
            else:
                outflow += abs(shock) * 0.5
            balance = max(0.0, balance + inflow - outflow)
            cash_rows.append({"month": m, "cash_in": inflow, "cash_out": outflow, "balance": float(balance)})
        self.cash_df = pd.DataFrame(cash_rows)

        # Unpaid invoices
        inv = [
            {"invoice_id": "INV-101", "amount": 150000.0, "days_past_due": 12, "status": "unpaid"},
            {"invoice_id": "INV-102", "amount": 80000.0, "days_past_due": 40, "status": "unpaid"},
            {"invoice_id": "INV-103", "amount": 45000.0, "days_past_due": 5, "status": "unpaid"},
        ]
        self.invoices_df = pd.DataFrame(inv)

        # metadata
        self.meta = {"company": "Demo Startup Pvt Ltd", "as_of": str(today), "months": months}

    # Accessors
    def expenses_for_month(self, month: str) -> pd.DataFrame:
        if self.use_mongo:
            col = self.db["expenses"]
            df = pd.DataFrame(list(col.find({"month": month})))
            return df
        return self.expenses_df[self.expenses_df["month"] == month].reset_index(drop=True)

    def revenue_for_month(self, month: str) -> pd.DataFrame:
        if self.use_mongo:
            col = self.db["revenue"]
            df = pd.DataFrame(list(col.find({"month": month})))
            return df
        return self.revenue_df[self.revenue_df["month"] == month].reset_index(drop=True)

    def cash_timeseries(self) -> pd.DataFrame:
        if self.use_mongo:
            col = self.db["cash"]
            df = pd.DataFrame(list(col.find({})))
            return df
        return self.cash_df.copy()

    def latest_cash_balance(self) -> float:
        if self.use_mongo:
            doc = self.db["cash"].find_one(sort=[("month", -1)])
            return float(doc.get("balance", 0.0)) if doc else 0.0
        return float(self.cash_df["balance"].iloc[-1])

    def latest_month(self) -> str:
        if self.use_mongo:
            # naive fallback
            doc = self.db["meta"].find_one({}) or {}
            return doc.get("latest_month", self.cash_df["month"].iloc[-1] if hasattr(self, "cash_df") else "")
        return self.meta["months"][-1]

    def previous_month(self) -> str:
        if self.use_mongo:
            months = sorted([d["month"] for d in list(self.db["cash"].find({}, {"month":1}))]) if "cash" in self.db.list_collection_names() else []
            return months[-2] if len(months) >= 2 else months[-1] if months else ""
        return self.meta["months"][-2] if len(self.meta["months"]) >= 2 else self.meta["months"][-1]

    def get_unpaid_invoices(self) -> pd.DataFrame:
        if self.use_mongo:
            col = self.db["invoices"]
            df = pd.DataFrame(list(col.find({"status":"unpaid"})))
            return df
        return self.invoices_df.copy()

    def get_meta(self) -> Dict[str,Any]:
        if self.use_mongo:
            return self.db["meta"].find_one({}) or {}
        return self.meta.copy()


STORE = DataStore()

# -------------------------
# Auto API caller placeholder
# -------------------------
class AutoAPICaller:
    def __init__(self, endpoints: Optional[Dict[str,str]] = None):
        self.endpoints = endpoints or {}

    def call(self, name: str, payload: Dict[str, Any] = None) -> Dict[str, Any]:
        if name == "vendor_recommendation":
            return {"recommendations": [{"vendor":"PayrollX","savings_per_month":12000}, {"vendor":"CloudSaver","savings_per_month":8000}]}
        if name == "bank_balance":
            return {"balance": STORE.latest_cash_balance()}
        return {"mocked": True, "service": name, "payload": payload}

API = AutoAPICaller()

# -------------------------
# Reasoning engine parts
# -------------------------
class Signal:
    def __init__(self, metric: str, prev: float, curr: float, abs_change: float, pct_change: float, severity: str):
        self.metric = metric
        self.previous_value = prev
        self.current_value = curr
        self.absolute_change = abs_change
        self.pct_change = pct_change
        self.severity = severity
        self.timestamp = datetime.now().isoformat()

class ChangeDetector:
    def __init__(self, threshold_pct: float = 0.10):
        self.threshold_pct = threshold_pct

    def detect(self, prev: float, curr: float) -> Optional[Signal]:
        if prev == 0:
            if curr != 0:
                return Signal("unknown", prev, curr, curr - prev, float("inf"), "high")
            return None
        diff = curr - prev
        pct = diff / prev
        if abs(pct) >= self.threshold_pct:
            sev = "high" if abs(pct) >= 0.25 else ("medium" if abs(pct) >= 0.10 else "low")
            return Signal("unknown", prev, curr, diff, pct, sev)
        return None

class AttributionEngine:
    def attribute(self, prev_df: pd.DataFrame, curr_df: pd.DataFrame, key_col: str, val_col: str, top_n: int = 3) -> Dict[str,Any]:
        merged = pd.merge(prev_df, curr_df, on=key_col, how='outer', suffixes=('_prev','_curr')).fillna(0)
        merged['delta'] = merged[f'{val_col}_curr'] - merged[f'{val_col}_prev']
        total_delta = merged['delta'].sum()
        if abs(total_delta) < 1e-9:
            merged['contrib_pct'] = 0.0
        else:
            merged['contrib_pct'] = merged['delta'] / total_delta * 100
        merged['abs_delta'] = merged['delta'].abs()
        merged = merged.sort_values(by='abs_delta', ascending=False)
        top = merged.head(top_n)
        return {"merged": merged, "top": top, "total_delta": total_delta}

class ExplainEngine:
    def summarize(self, metric_name: str, signal: Signal, attribution: Dict[str,Any]) -> str:
        merged = attribution.get('merged') if attribution else None
        top = attribution.get('top') if attribution else None
        total = attribution.get('total_delta') if attribution else 0.0
        direction = "increased" if signal.absolute_change > 0 else "decreased"
        if merged is None or abs(total) < 1e-6:
            return f"{metric_name.capitalize()} {direction} by {signal.pct_change:.1%} (₹{signal.absolute_change:,.0f}). No single category dominates the change."
        # find category column name
        cat_col = None
        for c in merged.columns:
            if 'category' in c:
                cat_col = c.replace('_prev','').replace('_curr','')
                break
        parts = []
        for _, row in top.iterrows():
            cat = row.get(cat_col) if cat_col in row else row.get('category', 'unknown')
            parts.append(f"{cat} {'↑' if row['delta']>0 else '↓'} ₹{abs(row['delta']):,.0f} (contrib {row['contrib_pct']:.1f}%)")
        parts_text = "; ".join(parts)
        explanation = f"{metric_name.capitalize()} {direction} by {signal.pct_change:.1%} (₹{signal.absolute_change:,.0f}). Top drivers: {parts_text}."
        # heuristic recs
        recs = []
        if any("Payroll" in str(x) for x in top.get('category', top.index) if 'category' in top.columns):
            recs.append("Review recent hires/payroll; consider headcount adjustments or contractor conversions.")
        if any("SaaS" in str(x) for x in top.get('category', top.index) if 'category' in top.columns):
            recs.append("Audit SaaS usage and reduce unused licenses.")
        if recs:
            explanation += " Recommendations: " + " ".join(recs)
        return explanation

DETECTOR = ChangeDetector(threshold_pct=0.10)
ATTRIB = AttributionEngine()
EXPLAIN = ExplainEngine()

# -------------------------
# KPI helpers
# -------------------------
def monthly_burn(month: str) -> float:
    df = STORE.expenses_for_month(month)
    return float(df['amount'].sum()) if not df.empty else 0.0

def monthly_revenue(month: str) -> float:
    df = STORE.revenue_for_month(month)
    return float(df['amount'].sum()) if not df.empty else 0.0

def revenue_growth_pct(prev: str, curr: str) -> float:
    p = monthly_revenue(prev)
    c = monthly_revenue(curr)
    if p == 0:
        return float('inf') if c != 0 else 0.0
    return (c - p) / p

def profit_loss(month: str) -> float:
    return monthly_revenue(month) - monthly_burn(month)

def runway_months(balance: float, burn: float) -> Optional[float]:
    if burn <= 0:
        return None
    return balance / burn

def cash_timeseries_df() -> pd.DataFrame:
    return STORE.cash_timeseries().copy()

# -------------------------
# Reasoning: core "reason_about" function (A,B,C)
# -------------------------
def reason_about(company_id: str) -> Dict[str,Any]:
    """
    Returns structured reasoning:
    - causes: list of natural language reasons for key metric changes
    - predictions: list of simple predictions (runway, what-if linear)
    - details: structured attribution outputs for traceability
    """
    curr = STORE.latest_month()
    prev = STORE.previous_month()
    if not curr:
        curr = STORE.get_meta()['months'][-1]
    if not prev:
        prev = STORE.get_meta()['months'][-2] if len(STORE.get_meta()['months'])>=2 else curr

    # compute KPI values
    burn_curr = monthly_burn(curr); burn_prev = monthly_burn(prev)
    rev_curr = monthly_revenue(curr); rev_prev = monthly_revenue(prev)
    rev_growth = revenue_growth_pct(prev, curr)
    pl = profit_loss(curr)
    balance = STORE.latest_cash_balance()
    runway = runway_months(balance, burn_curr)

    results = {"kpis": {
        "month_current": curr,
        "month_previous": prev,
        "burn": {"current": burn_curr, "previous": burn_prev},
        "revenue": {"current": rev_curr, "previous": rev_prev, "growth_pct": rev_growth},
        "profit_loss": {"amount": pl, "status": "profit" if pl>=0 else "loss"},
        "cash_balance": balance,
        "runway_months": runway
    }}

    # Detection & Attribution for burn
    burn_signal = DETECTOR.detect(burn_prev, burn_curr)
    burn_attrib = None; burn_narr = None
    if burn_signal:
        burn_signal.metric = "burn_rate"
        prev_df = STORE.expenses_for_month(prev).rename(columns={"amount":"amount_prev"})
        curr_df = STORE.expenses_for_month(curr).rename(columns={"amount":"amount_curr"})
        prev_df2 = prev_df.rename(columns={"category":"category","amount_prev":"amount"})
        curr_df2 = curr_df.rename(columns={"category":"category","amount_curr":"amount"})
        burn_attrib = ATTRIB.attribute(prev_df2, curr_df2, key_col="category", val_col="amount", top_n=3)
        burn_narr = EXPLAIN.summarize("burn rate", burn_signal, burn_attrib)

    # Detection & Attribution for revenue
    rev_signal = DETECTOR.detect(rev_prev, rev_curr)
    rev_attrib = None; rev_narr = None
    if rev_signal:
        rev_signal.metric = "revenue"
        prev_r = STORE.revenue_for_month(prev).rename(columns={"amount":"amount_prev"})
        curr_r = STORE.revenue_for_month(curr).rename(columns={"amount":"amount_curr"})
        prev_r2 = prev_r.rename(columns={"source":"source","amount_prev":"amount"})
        curr_r2 = curr_r.rename(columns={"source":"source","amount_curr":"amount"})
        rev_attrib = ATTRIB.attribute(prev_r2, curr_r2, key_col="source", val_col="amount", top_n=3)
        rev_narr = EXPLAIN.summarize("revenue", rev_signal, rev_attrib)

    # Cash attribution using overdue invoices heuristic
    cash_signal = None; cash_attrib = None; cash_narr = None
    try:
        cash_df = STORE.cash_timeseries()
        if len(cash_df) >= 2:
            prev_balance = float(cash_df['balance'].iloc[-2])
            curr_balance = float(cash_df['balance'].iloc[-1])
            cash_signal = DETECTOR.detect(prev_balance, curr_balance)
            if cash_signal:
                unpaid = STORE.get_unpaid_invoices()
                overdue_total = float(unpaid['amount'].sum()) if isinstance(unpaid, pd.DataFrame) else 0.0
                prev_df = pd.DataFrame([{"category":"overdue_receivables","amount": overdue_total*0.9}, {"category":"other","amount": prev_balance - overdue_total*0.9}])
                curr_df = pd.DataFrame([{"category":"overdue_receivables","amount": overdue_total}, {"category":"other","amount": curr_balance - overdue_total}])
                cash_attrib = ATTRIB.attribute(prev_df, curr_df, key_col="category", val_col="amount", top_n=3)
                cash_narr = EXPLAIN.summarize("cash balance", cash_signal, cash_attrib)
    except Exception:
        pass

    # Build causal natural-language reasons (high-level)
    causes = []
    if burn_narr:
        causes.append(burn_narr)
    if rev_narr:
        causes.append(rev_narr)
    if cash_narr:
        causes.append(cash_narr)
    # If profit negative and causes not explicit, add combined explanation
    if pl < 0 and not causes:
        # compare relative changes
        if burn_prev and rev_prev:
            exp_change = (burn_curr - burn_prev) / (burn_prev or 1)
            rev_change = (rev_curr - rev_prev) / (rev_prev or 1)
            if abs(exp_change) > abs(rev_change):
                causes.append(f"Profit is negative because expenses rose by {exp_change:.1%} while revenue changed by {rev_change:.1%}.")
            else:
                causes.append(f"Profit is negative primarily due to revenue falling by {abs(rev_change):.1%} while expenses were stable.")
        else:
            causes.append("Profit negative — check revenue and expenses for anomalies.")

    # Predictions: runway and simple what-if templates
    preds = []
    if runway is not None:
        preds.append(f"At current burn (₹{burn_curr:,.0f}/month) and cash balance (₹{balance:,.0f}), estimated runway is {runway:.2f} months.")
    else:
        preds.append("Runway cannot be computed (monthly burn is zero).")

    # small what-if: if burn continues, predict next-month balance
    next_balance = balance - burn_curr
    preds.append(f"If current burn continues without change, projected balance after one month: ₹{next_balance:,.0f}.")

    # return structured reasoning
    details = {
        "burn": {"signal": vars(burn_signal) if burn_signal else None, "attribution": burn_attrib},
        "revenue": {"signal": vars(rev_signal) if rev_signal else None, "attribution": rev_attrib},
        "cash": {"signal": vars(cash_signal) if cash_signal else None, "attribution": cash_attrib}
    }

    return {"causes": causes, "predictions": preds, "details": details, "kpis": results["kpis"]}

# -------------------------
# What-if simulation util (linear)
# -------------------------
def parse_what_if(query: str) -> Optional[Dict[str,Any]]:
    """
    Parses queries like:
    - "what if expenses increase by 10%"
    - "what if revenue drops 5 percent"
    Returns dict: {"target":"expenses"/"revenue", "direction":"increase"/"decrease", "pct":0.10}
    """
    q = query.lower()
    m = re.search(r"what if\s+(expenses|expense|revenue|burn|cash)\s+(increase|decrease|drops|rise|drops by|increases by|increased by|decreased by)?\s*([0-9]+(?:\.[0-9]+)?)\s*%?", q)
    if not m:
        # alternative: "if expenses increase by 10%"
        m2 = re.search(r"if\s+(expenses|expense|revenue|burn|cash)\s+(increase|decrease|drops|rise|increases|decreases)\s+by\s*([0-9]+(?:\.[0-9]+)?)\s*%?", q)
        if not m2:
            return None
        target = m2.group(1)
        direction = m2.group(2)
        pct = float(m2.group(3))/100.0
        return {"target": target, "direction": "increase" if "increase" in direction or "rise" in direction else "decrease", "pct": pct}
    target = m.group(1)
    direction = m.group(2) or ""
    pct = float(m.group(3))/100.0
    dir_clean = "increase" if "increase" in direction or "rise" in direction else "decrease"
    return {"target": target, "direction": dir_clean, "pct": pct}

def simulate_what_if(company_id: str, wi: Dict[str,Any]) -> Dict[str,Any]:
    """
    Applies simple linear simulation:
    - If target is expenses/burn: scale current-month expenses by (1 +/- pct) and recompute runway, profit.
    - If target is revenue: scale current revenue.
    """
    curr = STORE.latest_month(); prev = STORE.previous_month()
    if not curr:
        curr = STORE.get_meta()['months'][-1]
    # base KPIs
    burn_curr = monthly_burn(curr)
    rev_curr = monthly_revenue(curr)
    balance = STORE.latest_cash_balance()
    # interpret target
    t = wi['target']
    pct = wi['pct']
    dir = wi['direction']
    factor = 1 + pct if dir == "increase" else 1 - pct
    # map names
    if t.startswith("expense") or t == "burn" or t.startswith("payroll") or t == "expenses":
        new_burn = burn_curr * factor
        new_rev = rev_curr
    elif t.startswith("rev") or t == "revenue":
        new_rev = rev_curr * factor
        new_burn = burn_curr
    else:
        # fallback: unknown target
        return {"error": "unknown target for what-if simulation", "wi": wi}
    new_runway = runway_months(balance, new_burn)
    new_profit = new_rev - new_burn
    return {
        "scenario": wi,
        "baseline": {"burn": burn_curr, "revenue": rev_curr, "runway_months": runway_months(balance, burn_curr), "profit": rev_curr - burn_curr},
        "projected": {"burn": new_burn, "revenue": new_rev, "runway_months": new_runway, "profit": new_profit}
    }

# -------------------------
# PDF generation w/ Reasoning Summary
# -------------------------
def generate_insights_pdf_bytes(insights_struct: Dict[str,Any]) -> io.BytesIO:
    buf = io.BytesIO()
    meta = STORE.get_meta()
    with PdfPages(buf) as pp:
        # Page 1: Exec summary + Reasoning
        fig = plt.figure(figsize=(8.27, 11.69))
        title = f"AI-CFO Insights v2 - {meta.get('company','(unknown)')} - {insights_struct.get('kpis',{}).get('month_current','')}"
        fig.suptitle(title, fontsize=12)
        lines = []
        k = insights_struct.get('kpis', {})
        lines.append(f"Runway (months): {k.get('runway_months'):.2f}" if k.get('runway_months') is not None else "Runway: N/A")
        lines.append(f"Monthly Burn (current): ₹{k.get('burn',{}).get('current',0):,.0f}")
        rg = k.get('revenue',{}).get('growth_pct')
        if isinstance(rg, float) and math.isfinite(rg):
            lines.append(f"Revenue growth (MoM): {rg:.1%}")
        else:
            lines.append("Revenue growth (MoM): inf or N/A")
        lines.append(f"Profit/Loss (current): ₹{k.get('profit_loss',{}).get('amount',0):,.0f} — {k.get('profit_loss',{}).get('status','')}")
        lines.append("")
        lines.append("Reasoning Summary:")
        for cause in insights_struct.get('causes', []):
            lines.append("- " + cause)
        lines.append("")
        lines.append("Predictions:")
        for p in insights_struct.get('predictions', []):
            lines.append("- " + p)
        plt.axis('off')
        plt.text(0.02, 0.98, "\n".join(lines), va='top', wrap=True, fontsize=10)
        pp.savefig(fig, bbox_inches='tight'); plt.close(fig)

        # Page 2: Expenses comparison (prev vs curr)
        curr = insights_struct.get('kpis',{}).get('month_current')
        prev = insights_struct.get('kpis',{}).get('month_previous')
        prev_exp = STORE.expenses_for_month(prev)
        curr_exp = STORE.expenses_for_month(curr)
        merged = pd.merge(prev_exp, curr_exp, on="category", how="outer", suffixes=("_prev","_curr")).fillna(0)
        cats = merged['category'].tolist()
        prev_vals = merged['amount_prev'].tolist()
        curr_vals = merged['amount_curr'].tolist()
        x = np.arange(len(cats)); width = 0.35
        fig, ax = plt.subplots(figsize=(8.27, 4.5))
        ax.bar(x - width/2, prev_vals, width, label=f'Prev ({prev})')
        ax.bar(x + width/2, curr_vals, width, label=f'Curr ({curr})')
        ax.set_xticks(x); ax.set_xticklabels(cats, rotation=25, ha='right')
        ax.set_ylabel('Amount (₹)'); ax.set_title('Expense Breakdown: Previous vs Current'); ax.legend()
        pp.savefig(fig, bbox_inches='tight'); plt.close(fig)

        # Page 3: Revenue trend (6 months)
        if not STORE.use_mongo:
            rev_ts = STORE.revenue_df.groupby("month")["amount"].sum().reset_index()
            months = rev_ts['month'].tolist(); rev_vals = rev_ts['amount'].tolist()
        else:
            rev_ts = STORE.revenue_df
            months = rev_ts['month'].tolist(); rev_vals = rev_ts['amount'].tolist()
        fig, ax = plt.subplots(figsize=(8.27, 4.5))
        ax.plot(months, rev_vals, marker='o')
        ax.set_xlabel('Month'); ax.set_ylabel('Revenue (₹)'); ax.set_title('Revenue (6 months)')
        ax.grid(alpha=0.3); plt.xticks(rotation=25)
        pp.savefig(fig, bbox_inches='tight'); plt.close(fig)

        # Page 4: Cash In/Out trend (6 months)
        cash_ts = STORE.cash_timeseries()
        fig, ax = plt.subplots(figsize=(8.27, 4.5))
        ax.plot(cash_ts['month'], cash_ts['cash_in'], marker='o', label='Cash In')
        ax.plot(cash_ts['month'], cash_ts['cash_out'], marker='o', label='Cash Out')
        ax.set_xlabel('Month'); ax.set_ylabel('Amount (₹)'); ax.set_title('Cash In / Cash Out (6 months)')
        ax.legend(); ax.grid(alpha=0.3); plt.xticks(rotation=25)
        pp.savefig(fig, bbox_inches='tight'); plt.close(fig)

        # Page 5: Profit/Loss + Runway gauge
        fig = plt.figure(figsize=(8.27, 4.5))
        plt.axis('off')
        pl_amt = insights_struct['kpis']['profit_loss']['amount']
        pl_status = insights_struct['kpis']['profit_loss']['status']
        plt.text(0.02, 0.9, f"Profit / Loss for {insights_struct['kpis']['month_current']}: ₹{pl_amt:,.0f}", fontsize=12)
        plt.text(0.02, 0.85, f"Status: {'PROFIT' if pl_status=='profit' else 'LOSS'}", fontsize=12, color=('green' if pl_status=='profit' else 'red'))
        months_val = insights_struct['kpis']['runway_months'] or 0.0
        ax = fig.add_axes([0.1, 0.25, 0.8, 0.15])
        ax.barh([0], [min(months_val, 12)], height=0.5)
        ax.set_xlim(0, max(12, months_val+1))
        ax.set_yticks([]); ax.set_xlabel('Months of Runway (capped at 12)')
        pp.savefig(fig, bbox_inches='tight'); plt.close(fig)

    buf.seek(0)
    return buf

# -------------------------
# Nudges generator
# -------------------------
def generate_nudges(insights_struct: Dict[str,Any]) -> List[Dict[str,Any]]:
    nudges = []
    k = insights_struct['kpis']
    months = k.get('runway_months')
    if months is not None:
        if months < 3:
            nudges.append({"severity":"high", "message": f"Runway under 3 months ({months:.2f}). Immediate action required."})
        elif months < 6:
            nudges.append({"severity":"medium", "message": f"Runway under 6 months ({months:.2f}). Consider cost controls."})
    if k['profit_loss']['amount'] < 0:
        nudges.append({"severity":"high", "message": f"Negative profit this month: ₹{k['profit_loss']['amount']:,.0f}."})
    unpaid = STORE.get_unpaid_invoices()
    if isinstance(unpaid, pd.DataFrame) and not unpaid.empty:
        overdue = unpaid[unpaid['days_past_due'] > 30]
        if not overdue.empty:
            nudges.append({"severity":"medium", "message": f"{len(overdue)} invoices >30 days past due totaling ₹{overdue['amount'].sum():,.0f}."})
    return nudges

# -------------------------
# Chat intent detection + response builder
# -------------------------
def detect_intent(query: str) -> str:
    q = query.lower()
    if "what if" in q or re.search(r"\bif\b.*\b\d+%|\bwhat if\b", q):
        return "what_if"
    if re.search(r"\bwhy\b|\bwhy is\b|\bwhat happened\b", q):
        return "why"
    if re.search(r"\brunway\b|\bhow long\b", q):
        return "runway"
    if re.search(r"\bburn\b|\bmonthly burn\b|\bspend\b", q):
        return "burn"
    if re.search(r"\brevenue\b|\bgrowth\b", q):
        return "revenue"
    if re.search(r"\bcash\b|\binflow\b|\boutflow\b", q):
        return "cash"
    if re.search(r"\bprofit\b|\bloss\b", q):
        return "profit"
    return "summary"

def chat_handle(company_id: str, query: str) -> Dict[str,Any]:
    intent = detect_intent(query)
    insights_struct = reason_about(company_id)
    if intent == "what_if":
        parsed = parse_what_if(query)
        if not parsed:
            return {"answer": "I couldn't parse the what-if scenario. Try: 'What if expenses increase by 10%?'."}
        sim = simulate_what_if(company_id, parsed)
        baseline = sim['baseline']; proj = sim['projected']
        ans = (f"Scenario: {parsed['target']} {parsed['direction']} by {parsed['pct']*100:.1f}%.\n"
               f"Baseline - Burn: ₹{baseline['burn']:,.0f}, Revenue: ₹{baseline['revenue']:,.0f}, Runway: {baseline['runway_months']:.2f} months, Profit: ₹{baseline['profit']:,.0f}.\n"
               f"Projected - Burn: ₹{proj['burn']:,.0f}, Revenue: ₹{proj['revenue']:,.0f}, Runway: {proj['runway_months']:.2f} months, Profit: ₹{proj['profit']:,.0f}.")
        return {"answer": ans, "intent": intent, "simulation": sim}
    if intent == "why":
        # compose causes + top-level summary
        causes = insights_struct.get('causes', [])
        preds = insights_struct.get('predictions', [])
        text = ""
        if causes:
            text += "Causes:\n" + "\n".join(f"- {c}" for c in causes)
        else:
            text += "No immediate dominant cause detected from month-to-month comparisons."
        if preds:
            text += "\n\nPredictions:\n" + "\n".join(f"- {p}" for p in preds)
        return {"answer": text.strip(), "intent": intent, "details": insights_struct.get('details')}
    # direct KPI intents
    if intent == "runway":
        r = insights_struct['kpis']['runway_months']
        return {"answer": f"Estimated runway: {r:.2f} months." if r is not None else "Runway: N/A", "intent": intent}
    if intent == "burn":
        b = insights_struct['kpis']['burn']
        narr = insights_struct['details'].get('burn',{}).get('attribution')
        return {"answer": f"Monthly burn is ₹{b['current']:,.0f} (prev ₹{b['previous']:,.0f}).", "intent": intent, "attribution": narr}
    if intent == "revenue":
        r = insights_struct['kpis']['revenue']
        return {"answer": f"Revenue this month ₹{r['current']:,.0f} (growth {r['growth_pct']:.1%}).", "intent": intent}
    if intent == "cash":
        bal = insights_struct['kpis']['cash_balance']
        return {"answer": f"Latest cash balance ₹{bal:,.0f}. See cash in/out trend for details.", "intent": intent}
    if intent == "profit":
        p = insights_struct['kpis']['profit_loss']
        return {"answer": f"Profit/Loss this month: ₹{p['amount']:,.0f}. Status: {p['status']}.", "intent": intent}
    # default summary
    k = insights_struct['kpis']
    return {"answer": f"Runway: {k['runway_months']:.2f} months. Burn: ₹{k['burn']['current']:,.0f}. Revenue: ₹{k['revenue']['current']:,.0f}.", "intent": "summary"}



ALERT_STORE = []  # in-memory fallback if Mongo not available

def evaluate_alerts(company_id: str):
    insights_struct = reason_about(company_id)
    nudges = generate_nudges(insights_struct)
    timestamp = datetime.now().isoformat()
    for n in nudges:
        n.update({"company_id": company_id, "timestamp": timestamp})
    if STORE.use_mongo:
        col = STORE.db["alerts"]
        col.insert_many(nudges)
    else:
        ALERT_STORE.clear()
        ALERT_STORE.extend(nudges)
    print(f"[Scheduler] Alerts updated for {company_id} at {timestamp}")
    return nudges


def run_scheduler():
    scheduler = BackgroundScheduler()
    scheduler.add_job(lambda: evaluate_alerts("demo_company"), "interval", hours=24)
    scheduler.start()
    atexit.register(lambda: scheduler.shutdown(wait=False))
    print("[Scheduler] Started — runs every 24 hours.")

@app.on_event("startup")
async def startup_event():
    run_scheduler()

# -------------------------
# API endpoints
# -------------------------
@app.get("/insights/{company_id}/current")
def insights_current(company_id: str = Path(...), json: Optional[bool] = Query(False, description="Return JSON instead of PDF")):
    """
    Returns PDF by default. Use ?json=true to get JSON structured insights + reasoning.
    """
    insights_struct = reason_about(company_id)
    if json:
        return JSONResponse(insights_struct)
    pdf_buf = generate_insights_pdf_bytes(insights_struct)
    filename = f"insights_{company_id}_{datetime.now().strftime('%Y%m%d')}.pdf"
    headers = {"Content-Disposition": f'attachment; filename="{filename}"'}
    return StreamingResponse(pdf_buf, media_type="application/pdf", headers=headers)

@app.get("/insights/{company_id}/current/json")
def insights_current_json(company_id: str = Path(...)):
    insights_struct = reason_about(company_id)
    return JSONResponse(insights_struct)

@app.post("/chat/{company_id}")
def chat_endpoint(company_id: str = Path(...), body: ChatRequest = Body(...)):
    res = chat_handle(company_id, body.query)
    return JSONResponse(res)

@app.get("/nudges/{company_id}/active")
def nudges_endpoint(company_id: str = Path(...)):
    insights_struct = reason_about(company_id)
    nudges = generate_nudges(insights_struct)
    return JSONResponse({"company_id": company_id, "nudges": nudges})

@app.post("/chat/{company_id}/upload")
def chat_upload_placeholder(company_id: str = Path(...)):
    # placeholder to accept uploaded data in future
    return JSONResponse({"status":"ok", "message":"Upload endpoint placeholder — wire ingestion service here."})

@app.get("/alerts/{company_id}/active")
def get_active_alerts(company_id: str = Path(...)):
    if STORE.use_mongo:
        col = STORE.db["alerts"]
        docs = list(col.find({"company_id": company_id}).sort("timestamp", -1))
        return JSONResponse({"company_id": company_id, "alerts": docs})
    return JSONResponse({"company_id": company_id, "alerts": ALERT_STORE})

@app.post("/alerts/{company_id}/evaluate")
def evaluate_now(company_id: str = Path(...)):
    alerts = evaluate_alerts(company_id)
    return JSONResponse({"company_id": company_id, "alerts": alerts, "manual": True})


# -------------------------
# Run directly
# -------------------------
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=int(os.getenv("PORT", 8000)), reload=True)
