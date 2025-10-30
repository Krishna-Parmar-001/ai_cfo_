# utils/report_generator.py
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from datetime import datetime

def generate_audit_report_pdf(path: str, audit_id: str, audit_meta: dict, num_tx: int, date_range: dict, findings: list):
    c = canvas.Canvas(path, pagesize=A4)
    width, height = A4

    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, height - 60, f"AI Audit Agent – Audit Report")
    c.setFont("Helvetica", 10)
    c.drawString(50, height - 80, f"Audit ID: {audit_id}")
    if audit_meta:
        c.drawString(50, height - 95, f"Client: {audit_meta.get('client_name')}")
        c.drawString(50, height - 110, f"Period: {audit_meta.get('period')}")

    c.drawString(50, height - 140, f"Overview:")
    c.drawString(70, height - 155, f"Total transactions processed: {num_tx}")
    if date_range:
        c.drawString(70, height - 170, f"Date range: {date_range.get('min')} to {date_range.get('max')}")

    y = height - 200
    c.drawString(50, y, "Findings:")
    y -= 20
    if not findings:
        c.drawString(70, y, "No findings flagged.")
    else:
        for f in findings:
            # try to keep within page; do simple pagination
            if y < 120:
                c.showPage()
                y = height - 80
            c.setFont("Helvetica-Bold", 10)
            c.drawString(60, y, f"{f.get('rule')} [{f.get('severity')}]")
            y -= 14
            c.setFont("Helvetica", 9)
            desc = f.get("description", "")
            for line in wrap_text(desc, 80):
                if y < 120:
                    c.showPage()
                    y = height - 80
                c.drawString(70, y, line)
                y -= 12
            y -= 6

    # risk summary
    high = len([f for f in findings if f.get("severity") == "high"])
    medium = len([f for f in findings if f.get("severity") == "medium"])
    low = len([f for f in findings if f.get("severity") == "low"])
    y -= 10
    c.setFont("Helvetica-Bold", 11)
    c.drawString(50, y, "Risk Summary:")
    y -= 16
    c.setFont("Helvetica", 10)
    c.drawString(70, y, f"High severity findings: {high}")
    y -= 14
    c.drawString(70, y, f"Medium severity findings: {medium}")
    y -= 14
    c.drawString(70, y, f"Low severity findings: {low}")
    y -= 24

    # basic overall rating
    overall = "Low"
    if high > 0:
        overall = "High"
    elif medium > 2:
        overall = "Medium"
    c.drawString(70, y, f"Overall risk rating: {overall}")

    y -= 40
    # AI generated recommendations (simple template)
    c.setFont("Helvetica-Bold", 11)
    c.drawString(50, y, "AI-Generated Recommendations:")
    y -= 18
    c.setFont("Helvetica", 10)
    recs = [
        "Obtain missing invoices and supporting documents for transactions flagged as 'Missing invoice'.",
        "Review high-value transactions for GST applicability and correct accounting.",
        "Investigate duplicate invoice numbers and confirm legitimacy.",
        "Reconcile bank entries that do not appear in the ledger; check for timing differences or missed entries."
    ]
    for r in recs:
        if y < 120:
            c.showPage()
            y = height - 80
        for line in wrap_text(r, 80):
            c.drawString(70, y, line)
            y -= 12
        y -= 6

    c.setFont("Helvetica-Oblique", 9)
    c.drawString(50, 50, f"Draft — Not CA Signed. Generated on {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC")
    c.showPage()
    c.save()


def wrap_text(text, n):
    words = text.split()
    lines = []
    cur = []
    cur_len = 0
    for w in words:
        if cur_len + len(w) + 1 > n:
            lines.append(" ".join(cur))
            cur = [w]
            cur_len = len(w)
        else:
            cur.append(w)
            cur_len += len(w) + 1
    if cur:
        lines.append(" ".join(cur))
    return lines
