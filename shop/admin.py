from django.contrib import admin, messages

from . import emails
from .models import Order, ShopSettings


@admin.register(ShopSettings)
class ShopSettingsAdmin(admin.ModelAdmin):
    list_display = ("price_per_pack", "iban", "beneficiary_name")

    def has_add_permission(self, request):
        # Singleton - only allow editing the one existing row.
        return not ShopSettings.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        "order_number",
        "customer",
        "packs",
        "eggs",
        "total",
        "status",
        "created_at",
    )
    list_filter = ("status", "created_at")
    search_fields = ("order_number", "customer__username", "customer__email")
    readonly_fields = ("order_number", "price_per_pack", "created_at", "updated_at", "invoice")
    actions = ["mark_confirmed", "mark_completed", "cancel_orders"]

    @admin.display(description="Eggs")
    def eggs(self, obj):
        return obj.eggs

    @admin.display(description="Total (EUR)")
    def total(self, obj):
        return f"{obj.total:.2f}"

    @admin.action(description="Mark selected orders as confirmed")
    def mark_confirmed(self, request, queryset):
        updated = queryset.filter(status=Order.STATUS_PENDING).update(status=Order.STATUS_CONFIRMED)
        self.message_user(request, f"{updated} order(s) confirmed.", messages.SUCCESS)

    @admin.action(description="Mark selected orders as completed (delivered)")
    def mark_completed(self, request, queryset):
        updated = queryset.filter(status=Order.STATUS_CONFIRMED).update(status=Order.STATUS_COMPLETED)
        self.message_user(request, f"{updated} order(s) marked completed.", messages.SUCCESS)

    @admin.action(description="Cancel selected orders (out of stock / other reason)")
    def cancel_orders(self, request, queryset):
        count = 0
        for order in queryset.filter(status__in=Order.CANCELLABLE_STATUSES):
            order.status = Order.STATUS_CANCELLED
            if not order.cancellation_reason:
                order.cancellation_reason = "Cancelled by admin."
            order.save(update_fields=["status", "cancellation_reason", "updated_at"])
            emails.send_order_cancelled(order, cancelled_by_admin=True)
            count += 1
        self.message_user(request, f"{count} order(s) cancelled and customer notified.", messages.SUCCESS)
