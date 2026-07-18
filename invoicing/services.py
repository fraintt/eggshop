from django.db import transaction

from shop.models import Order

from . import emails
from .models import Invoice


def run_monthly_invoicing() -> list[Invoice]:
    """Bundles every 'completed' order that isn't on an invoice yet into a
    new open invoice, one per customer. Customers with nothing outstanding
    are skipped - no empty invoices. Existing open invoices are left
    untouched; unpaid orders never get merged into a later invoice."""

    customer_ids = (
        Order.objects.filter(status=Order.STATUS_COMPLETED, invoice__isnull=True)
        .values_list("customer_id", flat=True)
        .distinct()
    )

    created_invoices = []
    for customer_id in customer_ids:
        with transaction.atomic():
            orders = Order.objects.select_for_update().filter(
                customer_id=customer_id,
                status=Order.STATUS_COMPLETED,
                invoice__isnull=True,
            )
            if not orders.exists():
                continue
            total = sum((o.total for o in orders), start=0)
            invoice = Invoice.objects.create(customer_id=customer_id, total=total)
            orders.update(invoice=invoice, status=Order.STATUS_INVOICED)
            created_invoices.append(invoice)

    for invoice in created_invoices:
        emails.send_invoice_created(invoice)

    return created_invoices
