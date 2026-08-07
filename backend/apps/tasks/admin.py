from django.contrib import admin

from .models import Task


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ["title", "organization", "status", "assigned_to", "created_at"]
    list_filter = ["organization", "status"]
    search_fields = ["title", "description"]
