from celery import shared_task

from .services import run_monthly_invoicing


@shared_task
def run_monthly_invoicing_task():
    invoices = run_monthly_invoicing()
    return f"Created {len(invoices)} invoice(s)."
