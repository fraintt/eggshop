from django.conf import settings
from django.db.models import Sum
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET

from invoicing.models import Invoice
from shop.models import Order


def _check_token(request) -> bool:
    if not settings.HA_API_TOKEN:
        return False
    auth = request.headers.get("Authorization", "")
    expected = f"Token {settings.HA_API_TOKEN}"
    return auth == expected


@csrf_exempt
@require_GET
def summary(request):
    if not _check_token(request):
        return JsonResponse({"detail": "Invalid or missing token."}, status=401)

    now = timezone.now()

    new_orders = Order.objects.filter(
        status__in=[Order.STATUS_PENDING, Order.STATUS_CONFIRMED]
    ).count()

    awaiting_invoice = Order.objects.filter(
        status=Order.STATUS_COMPLETED, invoice__isnull=True
    ).count()

    total_unpaid = (
        Invoice.objects.filter(status=Invoice.STATUS_OPEN).aggregate(s=Sum("total"))["s"] or 0
    )

    total_paid_this_month = (
        Invoice.objects.filter(
            status=Invoice.STATUS_PAID, paid_at__year=now.year, paid_at__month=now.month
        ).aggregate(s=Sum("total"))["s"]
        or 0
    )

    total_paid_all_time = (
        Invoice.objects.filter(status=Invoice.STATUS_PAID).aggregate(s=Sum("total"))["s"] or 0
    )

    open_invoices = Invoice.objects.filter(status=Invoice.STATUS_OPEN).count()

    return JsonResponse(
        {
            "new_orders": new_orders,
            "orders_awaiting_invoice": awaiting_invoice,
            "open_invoices": open_invoices,
            "total_unpaid_eur": float(total_unpaid),
            "total_paid_this_month_eur": float(total_paid_this_month),
            "total_paid_all_time_eur": float(total_paid_all_time),
            "generated_at": now.isoformat(),
        }
    )
