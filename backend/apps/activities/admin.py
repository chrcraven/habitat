from django.contrib import admin
from django.contrib.gis.admin import GISModelAdmin

from .models import Activity, ActivityPhoto, ActivitySpecies, WorkflowState


class ActivitySpeciesInline(admin.TabularInline):
    model = ActivitySpecies
    extra = 1


class ActivityPhotoInline(admin.TabularInline):
    model = ActivityPhoto
    extra = 0
    fields = ["content_type", "captured_at", "uploaded_at"]
    readonly_fields = ["uploaded_at"]


@admin.register(WorkflowState)
class WorkflowStateAdmin(admin.ModelAdmin):
    list_display = ["name", "organization", "is_planned", "is_done", "order"]
    list_filter = ["organization"]


@admin.register(Activity)
class ActivityAdmin(GISModelAdmin):
    list_display = [
        "__str__",
        "organization",
        "property",
        "activity_type",
        "status",
        "is_public",
        "recorded_at",
    ]
    list_filter = ["organization", "activity_type", "status", "is_public"]
    inlines = [ActivitySpeciesInline, ActivityPhotoInline]
