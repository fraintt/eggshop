from django.conf import settings


def user_language(user) -> str:
    """Best-effort preferred language for a user, used to render emails sent
    from background tasks/admin actions where there's no active request to
    read a language cookie from."""
    try:
        return user.profile.language
    except Exception:
        return settings.LANGUAGE_CODE
