from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils import translation

from accounts.utils import user_language


def _send(template_prefix: str, context: dict, to: list[str], subject_template: str, subject_kwargs: dict, language: str):
    if not to:
        return
    with translation.override(language):
        text_body = render_to_string(f"{template_prefix}.txt", context)
        subject = translation.gettext(subject_template) % subject_kwargs
    msg = EmailMultiAlternatives(
        subject=f"[{settings.SITE_NAME}] {subject}",
        body=text_body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=to,
    )
    msg.send(fail_silently=False)


def _admin_recipients() -> list[str]:
    if settings.ADMIN_NOTIFICATION_EMAIL:
        return [settings.ADMIN_NOTIFICATION_EMAIL]
    User = get_user_model()
    return list(
        User.objects.filter(is_staff=True, is_active=True)
        .exclude(email="")
        .values_list("email", flat=True)
    )


def send_new_order_admin_notification(order):
    _send(
        "shop/email/new_order_admin",
        {"order": order},
        _admin_recipients(),
        "New order %(number)s",
        {"number": order.order_number},
        settings.LANGUAGE_CODE,
    )


def send_order_confirmation_customer(order):
    _send(
        "shop/email/order_placed_customer",
        {"order": order},
        [order.customer.email],
        "Order %(number)s received",
        {"number": order.order_number},
        user_language(order.customer),
    )


def send_order_cancelled(order, cancelled_by_admin: bool):
    if cancelled_by_admin:
        _send(
            "shop/email/order_cancelled_customer",
            {"order": order},
            [order.customer.email],
            "Order %(number)s was cancelled",
            {"number": order.order_number},
            user_language(order.customer),
        )
    else:
        _send(
            "shop/email/order_cancelled_admin",
            {"order": order},
            _admin_recipients(),
            "Customer cancelled order %(number)s",
            {"number": order.order_number},
            settings.LANGUAGE_CODE,
        )
