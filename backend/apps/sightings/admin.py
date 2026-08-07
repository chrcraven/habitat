from django.contrib import admin
from django.contrib.gis.admin import GISModelAdmin

from .models import Sighting, SightingActivityLink, SightingPhoto


class SightingPhotoInline(admin.TabularInline):
    model = SightingPhoto
    extra = 0
    fields = ["content_type", "captured_at", "uploaded_at"]
    readonly_fields = ["uploaded_at"]


class SightingActivityLinkInline(admin.TabularInline):
    model = SightingActivityLink
    fk_name = "sighting"
    extra = 0
    readonly_fields = ["linked_at"]


@admin.register(Sighting)
class SightingAdmin(GISModelAdmin):
    list_display = [
        "__str__",
        "organization",
        "property",
        "species",
        "is_public",
        "observed_at",
    ]
    list_filter = ["organization", "species", "is_public"]
    inlines = [SightingPhotoInline, SightingActivityLinkInline]
