from django.urls import path

from . import api_views

urlpatterns = [
    path("invoices", api_views.invoices, name="api-invoices"),
    path("invoices/generate", api_views.generate, name="api-generate-invoice"),
    path("invoices/<int:invoice_id>", api_views.invoice_detail, name="api-invoice-detail"),
    path("payments/initiate", api_views.initiate_payment_view, name="api-initiate-payment"),
    path("payments/callback", api_views.payment_callback, name="api-payment-callback"),
    path("payments/<uuid:payment_id>", api_views.payment_status, name="api-payment-status"),
    path("receipts/<int:receipt_id>/pdf", api_views.receipt_pdf, name="api-receipt-pdf"),
    path("reconciliation", api_views.reconciliation, name="api-payment-reconciliation"),
]
