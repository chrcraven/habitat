"""
Root URL configuration.

Phase 1's API surface (`/api/...`) is for the Habitat frontend itself, not
the documented, versioned public API planned for Phase 4 (see
/docs/roadmap.md) — no `/api/v1/` prefix or auth-by-API-key yet, just
session auth for the one app that consumes it right now.
"""

from django.contrib import admin
from django.urls import include, path

from . import health

urlpatterns = [
    # First, for two reasons. A probe hits these every few seconds, so
    # resolving them before nine `include()`s is free; and being first
    # means no app can ever shadow the path a deployment's probes point
    # at by registering it later. See config/health.py — and note there
    # are two, because liveness and readiness are answers to different
    # questions and Kubernetes reacts to them very differently.
    path("api/health/", health.liveness, name="health-live"),
    path("api/health/ready/", health.readiness, name="health-ready"),
    path("admin/", admin.site.urls),
    path("api/", include("apps.accounts.urls")),
    path("api/", include("apps.species.urls")),
    path("api/", include("apps.activities.urls")),
    path("api/", include("apps.sightings.urls")),
    path("api/", include("apps.tasks.urls")),
    path("api/", include("apps.notifications.urls")),
    path("api/", include("apps.feedback.urls")),
    path("api/", include("apps.pages.urls")),
    path("api/public/", include("apps.public_site.urls")),
]
