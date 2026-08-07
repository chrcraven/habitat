from django.contrib import admin

from .models import Species


@admin.register(Species)
class SpeciesAdmin(admin.ModelAdmin):
    list_display = ["common_name", "scientific_name", "organization"]
    list_filter = ["organization"]
    search_fields = ["common_name", "scientific_name"]
