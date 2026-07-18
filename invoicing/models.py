from decimal import Decimal

from django.conf import settings
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from shop.models import Counter


class Invoice(models.Model):
    STATUS_OPEN = "open"
    STATUS_PAID = "paid"
    STATUS_CHOICES = [
        (STATUS_OPEN, _("Open")),
        (STATUS_PAID, _("Paid")),
    ]

    invoice_number = models.CharField(max_length=20, unique=True, editable=False)
    customer = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="invoices"
    )
    status = models.CharField(max_length=8, choices=STATUS_CHOICES, default=STATUS_OPEN)
    total = models.DecimalField(max_digits=8, decimal_places=2, default=Decimal("0.00"))
    created_at = models.DateTimeField(auto_now_add=True)
    paid_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.invoice_number} ({self.customer})"

    def save(self, *args, **kwargs):
        if not self.invoice_number:
            self.invoice_number = Counter.next_number("invoice", "eggpay")
        super().save(*args, **kwargs)

    def mark_paid(self):
        self.status = self.STATUS_PAID
        self.paid_at = timezone.now()
        self.save(update_fields=["status", "paid_at"])
