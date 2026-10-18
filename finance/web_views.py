from django.shortcuts import get_object_or_404, render
from django.views.decorators.csrf import csrf_protect

from .models import Payment
from .services import MockPaymentGateway, process_callback


@csrf_protect
def mock_checkout(request, payment_id):
    payment = get_object_or_404(Payment.objects.select_related("invoice"), pk=payment_id)
    message = ""
    if request.method == "POST":
        status = request.POST.get("action", "CANCELLED")
        payload = {"paymentReference": payment.payment_reference, "gatewayOrderReference": payment.gateway_order_reference, "amount": str(payment.amount), "currency": payment.currency, "status": status}
        result, outcome = process_callback(request, payload, MockPaymentGateway().sign(payload))
        message = "Payment processed." if result else f"Payment failed: {outcome}"
    return render(request, "payment_checkout.html", {"payment": payment, "message": message})
