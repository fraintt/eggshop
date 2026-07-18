from django.contrib import admin, messages
from django.shortcuts import redirect
from django.urls import path
from django.utils.html import format_html

from . import emails
from .models import Invoice
from .services import run_monthly_invoicing


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    change_list_template = "invoicing/admin/invoice_change_list.html"
    list_display = ("invoice_number", "customer", "total", "status", "created_at", "paid_at")
    list_filter = ("status", "created_at")
    search_fields = ("invoice_number", "customer__username", "customer__email")
    readonly_fields = ("invoice_number", "total", "created_at", "paid_at")
    actions = ["mark_as_paid"]

    @admin.action(description="Mark selected invoices as paid")
    def mark_as_paid(self, request, queryset):
        count = 0
        for invoice in queryset.filter(status=Invoice.STATUS_OPEN):
            invoice.mark_paid()
            emails.send_invoice_paid(invoice)
            count += 1
        self.message_user(request, f"{count} invoice(s) marked paid.", messages.SUCCESS)

    def get_urls(self):
        urls = [
            path(
                "run-invoicing/",
                self.admin_site.admin_view(self.run_invoicing_view),
                name="invoicing_run_invoicing",
            ),
        ]
        return urls + super().get_urls()

    def run_invoicing_view(self, request):
        created = run_monthly_invoicing()
        if created:
            names = ", ".join(i.invoice_number for i in created)
            self.message_user(
                request,
                format_html("Created {} invoice(s): {}", len(created), names),
                messages.SUCCESS,
            )
        else:
            self.message_user(
                request, "No completed, unbilled orders found - nothing to invoice.", messages.INFO
            )
        return redirect("admin:invoicing_invoice_changelist")
