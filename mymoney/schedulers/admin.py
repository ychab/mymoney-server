from django.contrib import admin

from .models import Scheduler


@admin.register(Scheduler)
class SchedulerAdmin(admin.ModelAdmin):
    list_display = ['label', 'account', 'date', 'status', 'amount',
                    'reconciled', 'payment_method', 'type',
                    'recurrence', 'last_action', 'state']
    list_display_links = ['label']
    list_filter = ['type', 'state']
    ordering = ['-last_action']
    date_hierarchy = 'last_action'
    search_fields = ['label']
