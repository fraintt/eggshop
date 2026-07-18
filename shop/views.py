from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from . import emails
from .forms import CancelOrderForm, OrderForm
from .models import Order, ShopSettings


@login_required
def home(request):
    shop_settings = ShopSettings.get_solo()

    if request.method == "POST":
        form = OrderForm(request.POST)
        if form.is_valid():
            order = Order.objects.create(
                customer=request.user,
                packs=form.cleaned_data["packs"],
                price_per_pack=shop_settings.price_per_pack,
            )
            emails.send_new_order_admin_notification(order)
            emails.send_order_confirmation_customer(order)
            messages.success(request, f"Order {order.order_number} placed. Thanks!")
            return redirect("shop:home")
    else:
        form = OrderForm()

    recent_orders = request.user.orders.all()[:5]
    return render(
        request,
        "shop/home.html",
        {
            "form": form,
            "shop_settings": shop_settings,
            "recent_orders": recent_orders,
        },
    )


@login_required
def order_list(request):
    orders = request.user.orders.all()
    return render(request, "shop/order_list.html", {"orders": orders})


@login_required
def order_cancel(request, order_number):
    order = get_object_or_404(Order, order_number=order_number, customer=request.user)
    if not order.can_be_cancelled:
        messages.error(request, "This order can no longer be cancelled.")
        return redirect("shop:order_list")

    if request.method == "POST":
        form = CancelOrderForm(request.POST)
        if form.is_valid():
            order.status = Order.STATUS_CANCELLED
            order.cancellation_reason = form.cleaned_data["reason"]
            order.save(update_fields=["status", "cancellation_reason", "updated_at"])
            emails.send_order_cancelled(order, cancelled_by_admin=False)
            messages.success(request, f"Order {order.order_number} cancelled.")
            return redirect("shop:order_list")
    else:
        form = CancelOrderForm()

    return render(request, "shop/order_cancel.html", {"order": order, "form": form})
