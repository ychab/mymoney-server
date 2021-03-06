from django.contrib import admin

from .models import Transaction


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = [
        'label', 'date', 'status', 'amount', 'reconciled', 'scheduled',
        'payment_method',
    ]
    list_display_links = ['label']
    list_filter = ['date', 'status', 'reconciled']
    ordering = ['-date']
    date_hierarchy = 'date'
    search_fields = ['label']
