from io import BytesIO

import pay_by_square
import qrcode

from shop.models import ShopSettings


def build_qr_string(invoice) -> str:
    """Builds the Pay by Square payload string for an invoice.

    Note: no variable symbol is used (by request) - the invoice number is
    included as a free-text payment note instead, e.g. 'eggpay0001'.
    """
    shop_settings = ShopSettings.get_solo()
    return pay_by_square.generate(
        amount=float(invoice.total),
        iban=shop_settings.iban,
        swift=shop_settings.bic or "",
        beneficiary_name=shop_settings.beneficiary_name or "",
        note=invoice.invoice_number,
    )


def build_qr_png(invoice) -> bytes:
    code = build_qr_string(invoice)
    img = qrcode.make(code)
    buf = BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()
