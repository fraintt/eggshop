from django.urls import path

from . import views

app_name = "invoicing"

urlpatterns = [
    path("", views.invoice_list, name="invoice_list"),
    path("<str:invoice_number>/", views.invoice_detail, name="invoice_detail"),
    path("<str:invoice_number>/pdf/", views.invoice_pdf, name="invoice_pdf"),
    path("<str:invoice_number>/qr.png", views.invoice_qr, name="invoice_qr"),
]
