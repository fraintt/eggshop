from django.urls import path

from . import views

app_name = "shop"

urlpatterns = [
    path("", views.home, name="home"),
    path("orders/", views.order_list, name="order_list"),
    path("orders/<str:order_number>/cancel/", views.order_cancel, name="order_cancel"),
]
