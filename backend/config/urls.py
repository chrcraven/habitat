"""
Root URL configuration.

Phase 1 has no public REST API surface yet (that's Phase 4, see
/docs/roadmap.md) — just Django admin for now, which is the primary way
the author will poke at data directly while the real UI is being built.
"""

from django.contrib import admin
from django.urls import path

urlpatterns = [
    path("admin/", admin.site.urls),
]
