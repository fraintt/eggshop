from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils import translation

from accounts.utils import user_language

from .pdf import build_invoice_pdf


def send_invoice_created(invoice):
    if not invoice.customer.email:
        return
    language = user_language(invoice.customer)
    with translation.override(language):
        body = render_to_string("invoicing/email/invoice_created.txt", {"invoice": invoice})
        subject = translation.gettext("Invoice %(number)s") % {"number": invoice.invoice_number}
        pdf_bytes = build_invoice_pdf(invoice)
    msg = EmailMultiAlternatives(
        subject=f"[{settings.SITE_NAME}] {subject}",
        body=body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[invoice.customer.email],
    )
    msg.attach(f"{invoice.invoice_number}.pdf", pdf_bytes, "application/pdf")
    msg.send(fail_silently=False)


def send_invoice_paid(invoice):
    if not invoice.customer.email:
        return
    language = user_language(invoice.customer)
    with translation.override(language):
        body = render_to_string("invoicing/email/invoice_paid.txt", {"invoice": invoice})
        subject = translation.gettext("Invoice %(number)s - payment received") % {
            "number": invoice.invoice_number
        }
    msg = EmailMultiAlternatives(
        subject=f"[{settings.SITE_NAME}] {subject}",
        body=body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[invoice.customer.email],
    )
    msg.send(fail_silently=False)
