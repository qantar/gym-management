"""PDF generation using ReportLab."""
from io import BytesIO
from datetime import datetime
from decimal import Decimal
from typing import Optional, List, Dict, Any

try:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import mm, cm
    from reportlab.lib.colors import HexColor, black, white
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
        HRFlowable, KeepTogether,
    )
    from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False

BRAND_PURPLE = HexColor("#6c63ff") if REPORTLAB_AVAILABLE else None
BRAND_DARK   = HexColor("#0f1117") if REPORTLAB_AVAILABLE else None
GRAY         = HexColor("#9ba3c0") if REPORTLAB_AVAILABLE else None
LIGHT_GRAY   = HexColor("#f0f2ff") if REPORTLAB_AVAILABLE else None


def _base_doc(buffer: BytesIO, title: str) -> "SimpleDocTemplate":
    return SimpleDocTemplate(
        buffer, pagesize=A4,
        rightMargin=20*mm, leftMargin=20*mm,
        topMargin=20*mm, bottomMargin=20*mm,
        title=title,
    )


def generate_invoice_pdf(invoice: Dict[str, Any], member: Dict[str, Any], branch: Dict[str, Any]) -> bytes:
    """Generate professional invoice PDF."""
    if not REPORTLAB_AVAILABLE:
        return b"%PDF-1.4 placeholder - install reportlab"

    buffer = BytesIO()
    doc = _base_doc(buffer, f"Invoice {invoice['invoice_number']}")
    styles = getSampleStyleSheet()

    elements = []

    # Header
    header_data = [
        [
            Paragraph(f"<font size=20 color='#6c63ff'><b>GymOS</b></font><br/><font size=9 color='#9ba3c0'>ENTERPRISE</font>", styles["Normal"]),
            Paragraph(f"<font size=18><b>INVOICE</b></font><br/><font size=9 color='#9ba3c0'>{invoice['invoice_number']}</font>", ParagraphStyle("right", parent=styles["Normal"], alignment=TA_RIGHT)),
        ]
    ]
    header_table = Table(header_data, colWidths=[90*mm, 80*mm])
    header_table.setStyle(TableStyle([
        ("VALIGN", (0,0), (-1,-1), "TOP"),
        ("BOTTOMPADDING", (0,0), (-1,-1), 12),
    ]))
    elements.append(header_table)
    elements.append(HRFlowable(width="100%", thickness=2, color=BRAND_PURPLE))
    elements.append(Spacer(1, 5*mm))

    # Branch + Member info
    bill_data = [
        [
            Paragraph(f"<b>From:</b><br/>{branch.get('name','GymOS')}<br/>{branch.get('address','')} <br/>{branch.get('phone','')} ", styles["Normal"]),
            Paragraph(f"<b>Bill To:</b><br/>{member.get('first_name','')} {member.get('last_name','')}<br/>{member.get('email','') or ''}<br/>{member.get('phone','')}", styles["Normal"]),
            Paragraph(
                f"<b>Invoice Date:</b> {invoice.get('created_at','')[:10]}<br/>"
                f"<b>Due Date:</b> {invoice.get('due_date','')[:10]}<br/>"
                f"<b>Status:</b> {invoice.get('status','').upper()}",
                ParagraphStyle("right", parent=styles["Normal"], alignment=TA_RIGHT)
            ),
        ]
    ]
    bill_table = Table(bill_data, colWidths=[58*mm, 58*mm, 54*mm])
    bill_table.setStyle(TableStyle([("VALIGN", (0,0), (-1,-1), "TOP"), ("TOPPADDING", (0,0), (-1,-1), 4)]))
    elements.append(bill_table)
    elements.append(Spacer(1, 8*mm))

    # Line items table
    items_header = [["Description", "Qty", "Unit Price", "Amount"]]
    items_data = items_header + [
        [
            invoice.get("description", "Membership / Service"),
            "1",
            f"SAR {float(invoice.get('subtotal', 0)):,.2f}",
            f"SAR {float(invoice.get('subtotal', 0)):,.2f}",
        ]
    ]
    items_table = Table(items_data, colWidths=[90*mm, 15*mm, 35*mm, 30*mm])
    items_table.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), BRAND_PURPLE),
        ("TEXTCOLOR", (0,0), (-1,0), white),
        ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
        ("FONTSIZE", (0,0), (-1,0), 9),
        ("ALIGN", (1,0), (-1,-1), "RIGHT"),
        ("ROWBACKGROUNDS", (0,1), (-1,-1), [white, LIGHT_GRAY]),
        ("FONTSIZE", (0,1), (-1,-1), 9),
        ("BOTTOMPADDING", (0,0), (-1,-1), 6),
        ("TOPPADDING", (0,0), (-1,-1), 6),
        ("GRID", (0,0), (-1,-1), 0.25, GRAY),
    ]))
    elements.append(items_table)
    elements.append(Spacer(1, 5*mm))

    # Totals
    sub = float(invoice.get("subtotal", 0))
    disc = float(invoice.get("discount_amount", 0))
    tax = float(invoice.get("tax_amount", 0))
    total = float(invoice.get("total", 0))
    paid = float(invoice.get("amount_paid", 0))
    due = float(invoice.get("amount_due", 0))

    totals_data = [
        ["Subtotal:", f"SAR {sub:,.2f}"],
        ["Discount:", f"-SAR {disc:,.2f}"],
        [f"VAT ({invoice.get('tax_rate', 15)}%):", f"SAR {tax:,.2f}"],
        ["", ""],
        ["TOTAL:", f"SAR {total:,.2f}"],
        ["Amount Paid:", f"SAR {paid:,.2f}"],
        ["Amount Due:", f"SAR {due:,.2f}"],
    ]
    totals_table = Table(totals_data, colWidths=[110*mm, 60*mm])
    totals_table.setStyle(TableStyle([
        ("ALIGN", (1,0), (1,-1), "RIGHT"),
        ("FONTSIZE", (0,0), (-1,-1), 9),
        ("TOPPADDING", (0,0), (-1,-1), 3),
        ("FONTNAME", (0,4), (-1,4), "Helvetica-Bold"),
        ("FONTSIZE", (0,4), (1,4), 12),
        ("TEXTCOLOR", (0,4), (-1,4), BRAND_PURPLE),
        ("LINEABOVE", (0,4), (-1,4), 1, BRAND_PURPLE),
        ("TEXTCOLOR", (1,6), (1,6), HexColor("#ff6b6b")),
    ]))
    elements.append(totals_table)
    elements.append(Spacer(1, 12*mm))

    # Footer
    elements.append(HRFlowable(width="100%", thickness=0.5, color=GRAY))
    elements.append(Spacer(1, 3*mm))
    elements.append(Paragraph(
        "<font size=8 color='#9ba3c0'>Thank you for your business. "
        "For queries contact us at the branch. This is a computer-generated invoice.</font>",
        ParagraphStyle("footer", parent=styles["Normal"], alignment=TA_CENTER)
    ))

    doc.build(elements)
    return buffer.getvalue()


def generate_payslip_pdf(slip: Dict[str, Any], staff: Dict[str, Any], run: Dict[str, Any]) -> bytes:
    """Generate pay slip PDF."""
    if not REPORTLAB_AVAILABLE:
        return b"%PDF-1.4 placeholder"

    buffer = BytesIO()
    doc = _base_doc(buffer, "Pay Slip")
    styles = getSampleStyleSheet()
    elements = []

    # Header
    elements.append(Paragraph("<font size=16 color='#6c63ff'><b>GymOS Enterprise</b></font>", styles["Normal"]))
    elements.append(Paragraph("<font size=12><b>PAY SLIP</b></font>", styles["Normal"]))
    elements.append(Spacer(1, 3*mm))
    elements.append(HRFlowable(width="100%", thickness=2, color=BRAND_PURPLE))
    elements.append(Spacer(1, 4*mm))

    # Employee info
    info = [
        ["Employee ID:", staff.get("employee_id", "—"), "Period:", f"{run.get('period_start', '')} to {run.get('period_end', '')}"],
        ["Department:", staff.get("department", "—"), "Pay Date:", run.get("pay_date", "—")],
        ["Designation:", staff.get("designation", "—"), "Status:", run.get("status", "—").upper()],
    ]
    info_table = Table(info, colWidths=[35*mm, 55*mm, 25*mm, 55*mm])
    info_table.setStyle(TableStyle([
        ("FONTNAME", (0,0), (0,-1), "Helvetica-Bold"),
        ("FONTNAME", (2,0), (2,-1), "Helvetica-Bold"),
        ("FONTSIZE", (0,0), (-1,-1), 9),
        ("TOPPADDING", (0,0), (-1,-1), 3),
    ]))
    elements.append(info_table)
    elements.append(Spacer(1, 6*mm))

    # Earnings vs Deductions
    earnings_data = [
        ["EARNINGS", "Amount", "DEDUCTIONS", "Amount"],
        ["Base Salary", f"SAR {float(slip.get('base_salary',0)):,.2f}", "GOSI (10%)", f"SAR {float(slip.get('deduction_gosi',0)):,.2f}"],
        ["Overtime", f"SAR {float(slip.get('overtime_pay',0)):,.2f}", "Absence", f"SAR {float(slip.get('deduction_absence',0)):,.2f}"],
        ["Commission", f"SAR {float(slip.get('commission',0)):,.2f}", "Other", f"SAR {float(slip.get('deduction_other',0)):,.2f}"],
        ["Bonus", f"SAR {float(slip.get('bonus',0)):,.2f}", "", ""],
        ["", "", "", ""],
        ["GROSS PAY", f"SAR {float(slip.get('gross',0)):,.2f}", "TOTAL DEDUCTIONS", f"SAR {float(slip.get('total_deductions',0)):,.2f}"],
    ]
    ed_table = Table(earnings_data, colWidths=[45*mm, 35*mm, 45*mm, 45*mm])
    ed_table.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (1,0), HexColor("#e8f5e9")),
        ("BACKGROUND", (2,0), (3,0), HexColor("#fce4ec")),
        ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
        ("FONTNAME", (0,-1), (-1,-1), "Helvetica-Bold"),
        ("FONTSIZE", (0,0), (-1,-1), 9),
        ("ALIGN", (1,0), (1,-1), "RIGHT"),
        ("ALIGN", (3,0), (3,-1), "RIGHT"),
        ("GRID", (0,0), (-1,-1), 0.25, GRAY),
        ("TOPPADDING", (0,0), (-1,-1), 4),
        ("BOTTOMPADDING", (0,0), (-1,-1), 4),
    ]))
    elements.append(ed_table)
    elements.append(Spacer(1, 5*mm))

    # Net pay
    net = float(slip.get("net", 0))
    elements.append(Paragraph(
        f"<font size=14><b>NET PAY: SAR {net:,.2f}</b></font>",
        ParagraphStyle("net", parent=styles["Normal"], textColor=BRAND_PURPLE)
    ))

    doc.build(elements)
    return buffer.getvalue()


def generate_members_report_pdf(members: List[Dict], branch_name: str) -> bytes:
    """Generate members list report PDF."""
    if not REPORTLAB_AVAILABLE:
        return b"%PDF-1.4 placeholder"

    buffer = BytesIO()
    doc = _base_doc(buffer, "Members Report")
    styles = getSampleStyleSheet()
    elements = []

    elements.append(Paragraph(f"<font size=16 color='#6c63ff'><b>GymOS Enterprise</b></font>", styles["Normal"]))
    elements.append(Paragraph(f"<font size=12><b>Members Report — {branch_name}</b></font>", styles["Normal"]))
    elements.append(Paragraph(f"<font size=9 color='#9ba3c0'>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}</font>", styles["Normal"]))
    elements.append(Spacer(1, 4*mm))
    elements.append(HRFlowable(width="100%", thickness=1, color=BRAND_PURPLE))
    elements.append(Spacer(1, 4*mm))

    # Summary
    active = sum(1 for m in members if m.get("status") == "active")
    elements.append(Paragraph(f"<b>Total: {len(members)}</b> members &nbsp;|&nbsp; <b>{active}</b> active", styles["Normal"]))
    elements.append(Spacer(1, 4*mm))

    # Table
    data = [["ID", "Name", "Phone", "Status", "Check-ins", "Joined"]]
    for m in members[:500]:  # limit
        data.append([
            m.get("member_id", ""),
            f"{m.get('first_name','')} {m.get('last_name','')}",
            m.get("phone", ""),
            m.get("status", "").upper(),
            str(m.get("total_checkins", 0)),
            str(m.get("created_at", ""))[:10],
        ])

    tbl = Table(data, colWidths=[22*mm, 48*mm, 30*mm, 20*mm, 18*mm, 22*mm])
    tbl.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), BRAND_PURPLE),
        ("TEXTCOLOR", (0,0), (-1,0), white),
        ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
        ("FONTSIZE", (0,0), (-1,-1), 8),
        ("ROWBACKGROUNDS", (0,1), (-1,-1), [white, LIGHT_GRAY]),
        ("GRID", (0,0), (-1,-1), 0.25, GRAY),
        ("TOPPADDING", (0,0), (-1,-1), 3),
        ("BOTTOMPADDING", (0,0), (-1,-1), 3),
    ]))
    elements.append(tbl)
    doc.build(elements)
    return buffer.getvalue()
