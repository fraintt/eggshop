from django.urls import path

from . import views

app_name = "haapi"

urlpatterns = [
    path("summary/", views.summary, name="summary"),
]
