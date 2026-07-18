from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render

from .models import Invoice
from .pdf import build_invoice_pdf
from .qr import build_qr_png


@login_required
def invoice_list(request):
    invoices = request.user.invoices.all()
    return render(request, "invoicing/invoice_list.html", {"invoices": invoices})


@login_required
def invoice_detail(request, invoice_number):
    invoice = get_object_or_404(Invoice, invoice_number=invoice_number, customer=request.user)
    return render(request, "invoicing/invoice_detail.html", {"invoice": invoice})


@login_required
def invoice_pdf(request, invoice_number):
    invoice = get_object_or_404(Invoice, invoice_number=invoice_number, customer=request.user)
    pdf_bytes = build_invoice_pdf(invoice)
    response = HttpResponse(pdf_bytes, content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="{invoice.invoice_number}.pdf"'
    return response


@login_required
def invoice_qr(request, invoice_number):
    invoice = get_object_or_404(Invoice, invoice_number=invoice_number, customer=request.user)
    return HttpResponse(build_qr_png(invoice), content_type="image/png")
