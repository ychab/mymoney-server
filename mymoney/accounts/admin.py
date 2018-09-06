from django.contrib import admin

from .models import Account


@admin.register(Account)
class AccountAdmin(admin.ModelAdmin):
    list_display = ['label', 'balance', 'currency']
    list_display_links = ['label']
    ordering = ['label']
    search_fields = ['label']
