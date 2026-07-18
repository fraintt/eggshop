from django.conf import settings as django_settings

from .models import ShopSettings


def site_settings(request):
    return {
        "SITE_NAME": django_settings.SITE_NAME,
        "shop_settings": ShopSettings.get_solo(),
    }
