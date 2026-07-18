from django.conf import settings
from django.contrib.auth import get_user_model, login
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.http import HttpResponseRedirect
from django.shortcuts import redirect, render
from django.template.loader import render_to_string
from django.utils import translation
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode

from .forms import SignUpForm
from .models import Profile

User = get_user_model()


def _send_activation_email(request, user):
    uidb64 = urlsafe_base64_encode(force_bytes(user.pk))
    token = default_token_generator.make_token(user)
    activation_path = f"/accounts/activate/{uidb64}/{token}/"
    activation_url = request.build_absolute_uri(activation_path)
    body = render_to_string(
        "accounts/email/activation.txt",
        {"user": user, "activation_url": activation_url},
    )
    send_mail(
        subject=f"[{settings.SITE_NAME}] Confirm your email",
        message=body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
    )


def signup(request):
    if request.method == "POST":
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_active = False
            user.save()
            # The signal that creates the Profile has already run by now
            # (post_save on User) - remember whichever language the visitor
            # was browsing in when they signed up, so their emails match it.
            Profile.objects.update_or_create(
                user=user, defaults={"language": translation.get_language() or settings.LANGUAGE_CODE}
            )
            _send_activation_email(request, user)
            return render(request, "accounts/activation_sent.html", {"user": user})
    else:
        form = SignUpForm()
    return render(request, "accounts/signup.html", {"form": form})


def activate(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user is not None and default_token_generator.check_token(user, token):
        user.is_active = True
        user.save(update_fields=["is_active"])
        login(request, user)
        return redirect("shop:home")

    return render(request, "accounts/activation_invalid.html")


def set_language(request):
    """Switches the UI language for this browser (via cookie) and, for
    logged-in users, remembers the choice on their profile so background
    emails (order/invoice notifications) are sent in that language too."""
    lang = request.POST.get("language") or request.GET.get("language")
    next_url = request.POST.get("next") or request.GET.get("next") or "/"

    valid_codes = {code for code, _ in settings.LANGUAGES}
    if lang not in valid_codes:
        lang = settings.LANGUAGE_CODE

    translation.activate(lang)
    if request.user.is_authenticated:
        Profile.objects.update_or_create(user=request.user, defaults={"language": lang})

    response = HttpResponseRedirect(next_url)
    response.set_cookie(
        settings.LANGUAGE_COOKIE_NAME,
        lang,
        max_age=365 * 24 * 60 * 60,
    )
    return response
