from django.conf import settings
from django.db import models


class Profile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="profile"
    )
    language = models.CharField(
        max_length=5, choices=settings.LANGUAGES, default=settings.LANGUAGE_CODE
    )

    def __str__(self):
        return f"{self.user} profile"
