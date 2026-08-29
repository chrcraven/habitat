from django.contrib import admin

from .models import Feedback


@admin.register(Feedback)
class FeedbackAdmin(admin.ModelAdmin):
    list_display = ["organization", "submitted_by", "status", "created_at"]
    list_filter = ["organization", "status"]
    search_fields = ["message"]
