from django.urls import include, path

from . import views

app_name = "accounts"

urlpatterns = [
    path("signup/", views.signup, name="signup"),
    path("activate/<uidb64>/<token>/", views.activate, name="activate"),
    path("set-language/", views.set_language, name="set_language"),
    path("", include("django.contrib.auth.urls")),
]
