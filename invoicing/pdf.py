from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.platypus import (
    Image,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

from shop.models import ShopSettings

from .qr import build_qr_png


def build_invoice_pdf(invoice) -> bytes:
    shop_settings = ShopSettings.get_solo()
    buf = BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        topMargin=20 * mm,
        bottomMargin=20 * mm,
        leftMargin=20 * mm,
        rightMargin=20 * mm,
        title=invoice.invoice_number,
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "EggTitle", parent=styles["Title"], textColor=colors.HexColor("#8A5A22")
    )
    normal = styles["Normal"]

    elements = [
        Paragraph("🥚 Egg Shop - Invoice", title_style),
        Spacer(1, 4 * mm),
        Paragraph(f"<b>Invoice number:</b> {invoice.invoice_number}", normal),
        Paragraph(f"<b>Date:</b> {invoice.created_at.strftime('%d.%m.%Y')}", normal),
        Paragraph(
            f"<b>Customer:</b> {invoice.customer.get_full_name() or invoice.customer.username} "
            f"({invoice.customer.email})",
            normal,
        ),
        Spacer(1, 6 * mm),
    ]

    data = [["Order #", "Packs", "Eggs", "Price/pack", "Total"]]
    for order in invoice.orders.all().order_by("created_at"):
        data.append(
            [
                order.order_number,
                str(order.packs),
                str(order.eggs),
                f"EUR {order.price_per_pack:.2f}",
                f"EUR {order.total:.2f}",
            ]
        )
    data.append(["", "", "", "Total", f"EUR {invoice.total:.2f}"])

    table = Table(data, colWidths=[35 * mm, 20 * mm, 20 * mm, 35 * mm, 35 * mm])
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#F2A93B")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#4A3728")),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
                ("LINEBELOW", (0, 0), (-1, 0), 0.5, colors.grey),
                ("LINEABOVE", (0, -1), (-1, -1), 0.5, colors.grey),
                ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    elements.append(table)
    elements.append(Spacer(1, 8 * mm))

    if shop_settings.iban:
        elements.append(Paragraph("<b>Pay by Square</b> - scan with your banking app:", normal))
        elements.append(Spacer(1, 2 * mm))
        qr_bytes = build_qr_png(invoice)
        qr_image = Image(BytesIO(qr_bytes), width=40 * mm, height=40 * mm)
        elements.append(qr_image)
        elements.append(Spacer(1, 2 * mm))
        elements.append(Paragraph(f"IBAN: {shop_settings.iban}", normal))
        if shop_settings.beneficiary_name:
            elements.append(Paragraph(f"Beneficiary: {shop_settings.beneficiary_name}", normal))
        elements.append(Paragraph(f"Amount: EUR {invoice.total:.2f}", normal))
        elements.append(Paragraph(f"Payment note: {invoice.invoice_number}", normal))
    else:
        elements.append(
            Paragraph(
                "No IBAN configured yet - ask the shop admin to set one in Shop Settings "
                "so future invoices include a payment QR code.",
                normal,
            )
        )

    doc.build(elements)
    return buf.getvalue()
