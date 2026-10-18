from django.contrib import admin

from .models import Invoice, InvoiceLine, Payment, Receipt

admin.site.register(Invoice)
admin.site.register(InvoiceLine)
admin.site.register(Payment)
admin.site.register(Receipt)
