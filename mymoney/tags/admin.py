from django.contrib import admin

from .models import Tag


class TagAdmin(admin.ModelAdmin):
    list_display = ['name']
    list_display_links = ['name']
    ordering = ['name']
    search_fields = ['name']


admin.site.register(Tag, TagAdmin)
