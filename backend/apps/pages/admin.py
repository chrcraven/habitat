from django.contrib import admin

from .models import Page


@admin.register(Page)
class PageAdmin(admin.ModelAdmin):
    list_display = ["title", "organization", "property", "is_public", "position"]
    list_filter = ["organization", "is_public"]
    search_fields = ["title", "slug"]
