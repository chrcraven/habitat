"""
Root URL configuration.

Phase 1's API surface (`/api/...`) is for the Habitat frontend itself, not
the documented, versioned public API planned for Phase 4 (see
/docs/roadmap.md) — no `/api/v1/` prefix or auth-by-API-key yet, just
session auth for the one app that consumes it right now.
"""

from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include("apps.accounts.urls")),
    path("api/", include("apps.species.urls")),
    path("api/", include("apps.activities.urls")),
    path("api/", include("apps.sightings.urls")),
    path("api/", include("apps.tasks.urls")),
    path("api/", include("apps.notifications.urls")),
    path("api/", include("apps.feedback.urls")),
    path("api/public/", include("apps.public_site.urls")),
]
