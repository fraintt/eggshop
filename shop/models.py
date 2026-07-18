from decimal import Decimal

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models, transaction
from django.utils.translation import gettext_lazy as _


class Counter(models.Model):
    """Simple persistent sequence used to mint human-friendly numbers
    like egg0001 / eggpay0001 without gaps or collisions."""

    key = models.CharField(max_length=32, unique=True)
    value = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"{self.key}={self.value}"

    @classmethod
    def next_number(cls, key: str, prefix: str, padding: int = 4) -> str:
        with transaction.atomic():
            counter, _ = cls.objects.select_for_update().get_or_create(key=key)
            counter.value += 1
            counter.save(update_fields=["value"])
            return f"{prefix}{counter.value:0{padding}d}"


class ShopSettings(models.Model):
    """Singleton row holding shop-wide, admin-editable configuration."""

    price_per_pack = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        default=Decimal("3.00"),
        help_text="Price in EUR for one pack of 10 eggs.",
    )
    iban = models.CharField(
        max_length=34,
        blank=True,
        help_text="IBAN used to generate the Pay by Square QR code on invoices.",
    )
    bic = models.CharField(
        max_length=11,
        blank=True,
        help_text="Optional. Bank BIC/SWIFT code.",
    )
    beneficiary_name = models.CharField(
        max_length=100,
        blank=True,
        help_text="Name shown to the payer in their banking app.",
    )

    class Meta:
        verbose_name = "Shop settings"
        verbose_name_plural = "Shop settings"

    def __str__(self):
        return "Shop settings"

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        pass

    @classmethod
    def get_solo(cls) -> "ShopSettings":
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj


class Order(models.Model):
    STATUS_PENDING = "pending"
    STATUS_CONFIRMED = "confirmed"
    STATUS_COMPLETED = "completed"
    STATUS_INVOICED = "invoiced"
    STATUS_PAID = "paid"
    STATUS_CANCELLED = "cancelled"

    STATUS_CHOICES = [
        (STATUS_PENDING, _("Pending")),
        (STATUS_CONFIRMED, _("Confirmed")),
        (STATUS_COMPLETED, _("Completed (delivered)")),
        (STATUS_INVOICED, _("Invoiced")),
        (STATUS_PAID, _("Paid")),
        (STATUS_CANCELLED, _("Cancelled")),
    ]

    # Orders in these statuses can still be cancelled by the customer or admin.
    CANCELLABLE_STATUSES = (STATUS_PENDING, STATUS_CONFIRMED)
    # Orders in these statuses are locked - no further changes.
    LOCKED_STATUSES = (STATUS_COMPLETED, STATUS_INVOICED, STATUS_PAID, STATUS_CANCELLED)

    order_number = models.CharField(max_length=20, unique=True, editable=False)
    customer = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="orders"
    )
    packs = models.PositiveIntegerField(
        validators=[MinValueValidator(1)],
        help_text="Number of packs of 10 eggs.",
    )
    price_per_pack = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        help_text="Price per pack locked in at the time the order was placed.",
    )
    status = models.CharField(max_length=12, choices=STATUS_CHOICES, default=STATUS_PENDING)
    cancellation_reason = models.TextField(blank=True)
    invoice = models.ForeignKey(
        "invoicing.Invoice",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="orders",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.order_number} ({self.customer})"

    def save(self, *args, **kwargs):
        if not self.order_number:
            self.order_number = Counter.next_number("order", "egg")
        if self.price_per_pack is None:
            self.price_per_pack = ShopSettings.get_solo().price_per_pack
        super().save(*args, **kwargs)

    @property
    def eggs(self) -> int:
        return self.packs * 10

    @property
    def total(self) -> Decimal:
        return self.packs * self.price_per_pack

    @property
    def can_be_cancelled(self) -> bool:
        return self.status in self.CANCELLABLE_STATUSES

    @property
    def is_locked(self) -> bool:
        return self.status in self.LOCKED_STATUSES
