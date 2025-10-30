# utils/proposal_generator.py
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from datetime import datetime

def generate_proposal_pdf(path: str, client_name: str, period: str, scope: list, audit_id: str):
    c = canvas.Canvas(path, pagesize=A4)
    width, height = A4
    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, height - 80, "AI Audit Agent – Engagement Letter")
    c.setFont("Helvetica", 11)
    c.drawString(50, height - 120, f"Client: {client_name}")
    c.drawString(50, height - 140, f"Audit Period: {period}")
    c.drawString(50, height - 160, f"Audit ID: {audit_id}")
    c.drawString(50, height - 190, "Scope:")
    y = height - 210
    for s in scope:
        c.drawString(70, y, f"- {s}")
        y -= 18
    y -= 10
    disclaimer = ("This is an AI-generated draft engagement letter. "
                  "It is not CA-signed and is for proposal purposes only. "
                  "Final engagement must be approved and signed by a qualified Chartered Accountant.")
    textobject = c.beginText(50, y)
    textobject.setFont("Helvetica", 10)
    for line in split_text(disclaimer, 80):
        textobject.textLine(line)
    c.drawText(textobject)
    c.setFont("Helvetica-Oblique", 9)
    c.drawString(50, 50, "Draft – Not legally binding")
    c.showPage()
    c.save()


def split_text(text, n):
    # naive wrap
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
