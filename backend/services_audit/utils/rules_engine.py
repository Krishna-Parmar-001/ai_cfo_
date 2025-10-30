# utils/rules_engine.py
from decimal import Decimal

def normalize_tx(row: dict) -> dict:
    """
    Accepts a csv.DictReader row-like dict and returns normalized transaction dict:
    { date, description, amount (float), invoice_no, gst_amount (float), source }
    """
    def parse_amount(v):
        if v is None:
            return 0.0
        try:
            return float(str(v).replace(",", "").replace("₹", "").strip())
        except:
            return 0.0

    tx = {
        "date": row.get("date") or row.get("Date") or row.get("dt"),
        "description": row.get("description") or row.get("desc") or row.get("narration") or "",
        "amount": parse_amount(row.get("amount") or row.get("Amount") or row.get("amt")),
        "invoice_no": row.get("invoice_no") or row.get("inv") or row.get("invoice") or None,
        "gst_amount": parse_amount(row.get("gst_amount") or row.get("GST") or row.get("gst")),
        "source": row.get("source") or row.get("Source") or "ledger"
    }
    return tx


def run_rules_on_transactions(txs: list) -> list:
    findings = []
    for tx in txs:
        amt = float(tx.get("amount") or 0)
        gst = float(tx.get("gst_amount") or 0)
        invoice_no = tx.get("invoice_no")
        desc = tx.get("description") or ""

        # rule: missing invoice
        if not invoice_no:
            findings.append({
                "rule": "Missing invoice",
                "severity": "high" if amt > 100000 else "medium",
                "description": f"Transaction on {tx.get('date')} amount {amt} has missing invoice"
            })
        # high-value without GST
        if amt > 250000 and gst == 0:
            findings.append({
                "rule": "High-value tx missing GST",
                "severity": "high",
                "description": f"{amt} on {tx.get('date')} lacks GST"
            })
        # suspicious low GST (less than 5% when gst present)
        if gst > 0:
            if gst < (amt * 0.05):
                findings.append({
                    "rule": "Suspicious low GST",
                    "severity": "medium",
                    "description": f"GST {gst} appears low for amount {amt} on {tx.get('date')}"
                })

        # duplicate invoice no: needs collection-level check - simplified here
    # duplicate invoice numbers across txs
    inv_counts = {}
    for tx in txs:
        inv = tx.get("invoice_no")
        if inv:
            inv_counts[inv] = inv_counts.get(inv, 0) + 1
    for inv, cnt in inv_counts.items():
        if cnt > 1:
            findings.append({
                "rule": "Duplicate invoice number",
                "severity": "medium",
                "description": f"Invoice {inv} appears {cnt} times"
            })
    return findings
