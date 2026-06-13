"""PDF generation using ReportLab. Graceful fallback if not installed."""
from io import BytesIO
from datetime import datetime
from typing import Optional, List, Dict, Any

try:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.lib.units import mm
    from reportlab.lib.colors import HexColor, black, white
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable,
    )
    from reportlab.lib.enums import TA_CENTER, TA_RIGHT
    from reportlab.lib.styles import ParagraphStyle
    _RL = True
except ImportError:
    _RL = False

_PURPLE = HexColor("#6c63ff") if _RL else None
_GRAY   = HexColor("#9ba3c0") if _RL else None
_LGRAY  = HexColor("#f0f2ff") if _RL else None


def _doc(buf: BytesIO, title: str):
    return SimpleDocTemplate(
        buf, pagesize=A4,
        rightMargin=20 * mm, leftMargin=20 * mm,
        topMargin=20 * mm, bottomMargin=20 * mm,
        title=title,
    )


def _tstyle(commands):
    return TableStyle(commands)


def generate_invoice_pdf(
    invoice: Dict[str, Any],
    member: Dict[str, Any],
    branch: Dict[str, Any],
) -> bytes:
    if not _RL:
        return b"%PDF-1.4 placeholder (install reportlab)"

    buf = BytesIO()
    doc = _doc(buf, "Invoice " + invoice.get("invoice_number", ""))
    styles = getSampleStyleSheet()
    N = styles["Normal"]
    right_style = ParagraphStyle("R", parent=N, alignment=TA_RIGHT)
    center_style = ParagraphStyle("C", parent=N, alignment=TA_CENTER)
    elems = []

    # --- Header ---
    elems.append(Table(
        [[
            Paragraph("<font size=20 color='#6c63ff'><b>GymOS</b></font><br/>"
                      "<font size=9 color='#9ba3c0'>ENTERPRISE</font>", N),
            Paragraph("<font size=18><b>INVOICE</b></font><br/>"
                      "<font size=9 color='#9ba3c0'>" + invoice.get("invoice_number", "") + "</font>", right_style),
        ]],
        colWidths=[90 * mm, 80 * mm],
    ))
    elems.append(HRFlowable(width="100%", thickness=2, color=_PURPLE))
    elems.append(Spacer(1, 5 * mm))

    # --- From / Bill To / Dates ---
    member_name = member.get("first_name", "") + " " + member.get("last_name", "")
    elems.append(Table(
        [[
            Paragraph("<b>From:</b><br/>" + branch.get("name", "GymOS") + "<br/>" +
                      branch.get("address", "") + "<br/>" + branch.get("phone", ""), N),
            Paragraph("<b>Bill To:</b><br/>" + member_name + "<br/>" +
                      (member.get("email") or "") + "<br/>" + member.get("phone", ""), N),
            Paragraph(
                "<b>Date:</b> " + str(invoice.get("created_at", ""))[:10] + "<br/>"
                "<b>Due:</b> " + str(invoice.get("due_date", ""))[:10] + "<br/>"
                "<b>Status:</b> " + str(invoice.get("status", "")).upper(),
                right_style,
            ),
        ]],
        colWidths=[58 * mm, 58 * mm, 54 * mm],
    ))
    elems.append(Spacer(1, 8 * mm))

    # --- Line items ---
    sub = float(invoice.get("subtotal", 0))
    items = [
        ["Description", "Qty", "Unit Price", "Amount"],
        [invoice.get("description") or "Membership / Service", "1",
         "SAR {:,.2f}".format(sub), "SAR {:,.2f}".format(sub)],
    ]
    t = Table(items, colWidths=[90 * mm, 15 * mm, 35 * mm, 30 * mm])
    t.setStyle(_tstyle([
        ("BACKGROUND", (0, 0), (-1, 0), _PURPLE),
        ("TEXTCOLOR", (0, 0), (-1, 0), white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [white, _LGRAY]),
        ("GRID", (0, 0), (-1, -1), 0.25, _GRAY),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    elems.append(t)
    elems.append(Spacer(1, 5 * mm))

    # --- Totals ---
    disc = float(invoice.get("discount_amount", 0))
    tax  = float(invoice.get("tax_amount", 0))
    tot  = float(invoice.get("total", 0))
    paid = float(invoice.get("amount_paid", 0))
    due  = float(invoice.get("amount_due", 0))
    tax_rate = invoice.get("tax_rate", 15)

    totals = Table(
        [
            ["Subtotal:", "SAR {:,.2f}".format(sub)],
            ["Discount:", "-SAR {:,.2f}".format(disc)],
            ["VAT ({}%):".format(tax_rate), "SAR {:,.2f}".format(tax)],
            ["", ""],
            ["TOTAL:", "SAR {:,.2f}".format(tot)],
            ["Amount Paid:", "SAR {:,.2f}".format(paid)],
            ["Amount Due:", "SAR {:,.2f}".format(due)],
        ],
        colWidths=[110 * mm, 60 * mm],
    )
    totals.setStyle(_tstyle([
        ("ALIGN", (1, 0), (1, -1), "RIGHT"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("FONTNAME", (0, 4), (-1, 4), "Helvetica-Bold"),
        ("FONTSIZE", (0, 4), (1, 4), 12),
        ("TEXTCOLOR", (0, 4), (-1, 4), _PURPLE),
        ("LINEABOVE", (0, 4), (-1, 4), 1, _PURPLE),
        ("TEXTCOLOR", (1, 6), (1, 6), HexColor("#ff6b6b")),
    ]))
    elems.append(totals)
    elems.append(Spacer(1, 12 * mm))
    elems.append(HRFlowable(width="100%", thickness=0.5, color=_GRAY))
    elems.append(Spacer(1, 3 * mm))
    elems.append(Paragraph(
        "<font size=8 color='#9ba3c0'>Thank you for your business. "
        "This is a computer-generated invoice.</font>",
        center_style,
    ))
    doc.build(elems)
    return buf.getvalue()


def generate_payslip_pdf(
    slip: Dict[str, Any],
    staff: Dict[str, Any],
    run: Dict[str, Any],
) -> bytes:
    if not _RL:
        return b"%PDF-1.4 placeholder"

    buf = BytesIO()
    doc = _doc(buf, "Pay Slip")
    styles = getSampleStyleSheet()
    N = styles["Normal"]
    elems = []

    elems.append(Paragraph("<font size=16 color='#6c63ff'><b>GymOS Enterprise</b></font>", N))
    elems.append(Paragraph("<font size=12><b>PAY SLIP</b></font>", N))
    elems.append(Spacer(1, 3 * mm))
    elems.append(HRFlowable(width="100%", thickness=2, color=_PURPLE))
    elems.append(Spacer(1, 4 * mm))

    info = Table(
        [
            ["Employee ID:", staff.get("employee_id", ""), "Period:",
             "{} to {}".format(run.get("period_start", ""), run.get("period_end", ""))],
            ["Department:", staff.get("department", ""), "Pay Date:", run.get("pay_date", "")],
            ["Designation:", staff.get("designation", ""), "Status:", str(run.get("status", "")).upper()],
        ],
        colWidths=[35 * mm, 55 * mm, 25 * mm, 55 * mm],
    )
    info.setStyle(_tstyle([
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTNAME", (2, 0), (2, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
    ]))
    elems.append(info)
    elems.append(Spacer(1, 6 * mm))

    def sar(v):
        return "SAR {:,.2f}".format(float(v or 0))

    ed = Table(
        [
            ["EARNINGS", "Amount", "DEDUCTIONS", "Amount"],
            ["Base Salary", sar(slip.get("base_salary")), "GOSI (10%)", sar(slip.get("deduction_gosi"))],
            ["Overtime",    sar(slip.get("overtime_pay")), "Absence",   sar(slip.get("deduction_absence"))],
            ["Commission",  sar(slip.get("commission")),   "Other",     sar(slip.get("deduction_other"))],
            ["Bonus",       sar(slip.get("bonus")),        "", ""],
            ["", "", "", ""],
            ["GROSS PAY",   sar(slip.get("gross")), "TOTAL DEDUCTIONS", sar(slip.get("total_deductions"))],
        ],
        colWidths=[45 * mm, 35 * mm, 45 * mm, 45 * mm],
    )
    ed.setStyle(_tstyle([
        ("BACKGROUND", (0, 0), (1, 0), HexColor("#e8f5e9")),
        ("BACKGROUND", (2, 0), (3, 0), HexColor("#fce4ec")),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("ALIGN", (1, 0), (1, -1), "RIGHT"),
        ("ALIGN", (3, 0), (3, -1), "RIGHT"),
        ("GRID", (0, 0), (-1, -1), 0.25, _GRAY),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    elems.append(ed)
    elems.append(Spacer(1, 5 * mm))
    elems.append(Paragraph(
        "<font size=14 color='#6c63ff'><b>NET PAY: " + sar(slip.get("net")) + "</b></font>", N
    ))
    doc.build(elems)
    return buf.getvalue()


def generate_members_report_pdf(members: List[Dict], branch_name: str) -> bytes:
    if not _RL:
        return b"%PDF-1.4 placeholder"

    buf = BytesIO()
    doc = _doc(buf, "Members Report")
    styles = getSampleStyleSheet()
    N = styles["Normal"]
    elems = []

    elems.append(Paragraph("<font size=16 color='#6c63ff'><b>GymOS Enterprise</b></font>", N))
    elems.append(Paragraph("<font size=12><b>Members Report — " + branch_name + "</b></font>", N))
    elems.append(Paragraph(
        "<font size=9 color='#9ba3c0'>Generated: " + datetime.now().strftime("%Y-%m-%d %H:%M") + "</font>", N
    ))
    elems.append(Spacer(1, 4 * mm))
    elems.append(HRFlowable(width="100%", thickness=1, color=_PURPLE))
    elems.append(Spacer(1, 4 * mm))

    active = sum(1 for m in members if m.get("status") == "active")
    elems.append(Paragraph(
        "<b>Total: {}</b> members &nbsp;|&nbsp; <b>{}</b> active".format(len(members), active), N
    ))
    elems.append(Spacer(1, 4 * mm))

    data = [["ID", "Name", "Phone", "Status", "Check-ins", "Joined"]]
    for m in members[:500]:
        data.append([
            m.get("member_id", ""),
            (m.get("first_name", "") + " " + m.get("last_name", "")).strip(),
            m.get("phone", ""),
            m.get("status", "").upper(),
            str(m.get("total_checkins", 0)),
            str(m.get("created_at", ""))[:10],
        ])

    tbl = Table(data, colWidths=[22 * mm, 48 * mm, 30 * mm, 20 * mm, 18 * mm, 22 * mm])
    tbl.setStyle(_tstyle([
        ("BACKGROUND", (0, 0), (-1, 0), _PURPLE),
        ("TEXTCOLOR", (0, 0), (-1, 0), white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [white, _LGRAY]),
        ("GRID", (0, 0), (-1, -1), 0.25, _GRAY),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]))
    elems.append(tbl)
    doc.build(elems)
    return buf.getvalue()
