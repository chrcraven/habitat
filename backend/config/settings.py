"""
Django settings for the Habitat backend.

Phase 1 (single-user MVP) settings — see /CLAUDE.md and /docs/roadmap.md
for what is and isn't in scope yet. Kept deliberately simple (no
django-environ, no multi-file settings split) until there's an actual need
for it; revisit if/when deployment environments diverge meaningfully.
"""

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.environ.get("SECRET_KEY", "insecure-dev-key-change-me")
DEBUG = os.environ.get("DEBUG", "1") == "1"
ALLOWED_HOSTS = [
    h.strip()
    for h in os.environ.get("ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")
    if h.strip()
]

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.gis",
    "rest_framework",
    "rest_framework_gis",
    "corsheaders",
    "apps.accounts",
    "apps.species",
    "apps.activities",
    "apps.sightings",
    "apps.tasks",
    "apps.notifications",
    "apps.public_site",
    "apps.feedback",
    "apps.pages",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.contrib.gis.db.backends.postgis",
        "NAME": os.environ.get("POSTGRES_DB", "habitat"),
        "USER": os.environ.get("POSTGRES_USER", "habitat"),
        "PASSWORD": os.environ.get("POSTGRES_PASSWORD", "habitat"),
        "HOST": os.environ.get("POSTGRES_HOST", "db"),
        "PORT": os.environ.get("POSTGRES_PORT", "5432"),
    }
}

AUTH_USER_MODEL = "accounts.User"

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.SessionAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
}

# Photos are stored in the DB as BinaryField (decided — see
# /docs/data-model-notes.md), so an upload has to fit under Django's
# request-body memory cap, not just Postgres's own limits. Raised from the
# 2.5MB default to fit a phone camera photo; the activity/sighting photo
# views enforce their own 8MB per-file cap on top of this. Doesn't address
# the DB-growth question in /docs/open-questions.md ("Photo storage
# growth") — just the immediate "a phone photo 415s on upload" bug.
DATA_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024
FILE_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024

# Phase 1 has no separate deployed frontend origin yet beyond local dev.
CORS_ALLOWED_ORIGINS = [
    o.strip()
    for o in os.environ.get(
        "CORS_ALLOWED_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173"
    ).split(",")
    if o.strip()
]
# The frontend dev server runs on a different port, which counts as a
# different *origin* even though it's the same *site* (localhost) — the
# session cookie is still sent (SameSite=Lax default covers this), but the
# browser needs explicit permission to read the response and to include
# credentials, and Django's CSRF check needs the origin trusted.
CORS_ALLOW_CREDENTIALS = True
# Settable independently of CORS_ALLOWED_ORIGINS, defaulting to it (which
# is the behavior this had when it was a plain alias). The split matters
# for the isolated public-site origin below: that origin needs to *read*
# /api/public/... cross-origin, but it must never be CSRF-trusted for the
# authenticated app — trusting an origin that serves author-supplied
# content is exactly what isolating it was meant to prevent. So a
# deployment adds it to CORS_ALLOWED_ORIGINS only, and pins
# CSRF_TRUSTED_ORIGINS to the app's own origin.
CSRF_TRUSTED_ORIGINS = [
    o.strip() for o in os.environ.get("CSRF_TRUSTED_ORIGINS", "").split(",") if o.strip()
] or CORS_ALLOWED_ORIGINS

# Used to build the org-invite accept link (see apps/accounts/invitations.py)
# — the frontend origin, not the API's. Defaults to the Vite dev server.
FRONTEND_URL = os.environ.get("FRONTEND_URL", "http://localhost:5173")

# Where the *public* site is served from, when it lives on its own origin
# (the isolated-origin decision — see /docs/open-questions.md, "Public site
# storytelling / custom content"). Blank, the default, means the public
# pages are served from the same origin as the app, which is how every
# deployment behaves until this is set. Setting it (to e.g.
# "https://public.habitat.dev.cravenator.com") is what relocates the public
# site: every public link and QR code the app hands out points there
# instead. The matching frontend variable is VITE_PUBLIC_SITE_URL.
PUBLIC_SITE_URL = os.environ.get("PUBLIC_SITE_URL", "").strip().rstrip("/")

# Custom HTML/JS authoring for public-site pages (the owner's 2026-09-02
# decision — see /docs/open-questions.md, "Public site storytelling /
# custom content"). Off by default, so no deployment starts serving
# author-supplied documents just because it upgraded: with this unset,
# every Page stays markdown-only and behaves exactly as it did before this
# setting existed.
#
# The security control is NOT this flag — it's how such a page is served:
# never inlined into the public site's own DOM, always fetched as its own
# document at /api/public/.../pages/<slug>/document/, which carries
# `Content-Security-Policy: sandbox allow-scripts` (a unique opaque origin,
# no cookies, no same-origin access) and is embedded in a
# `<iframe sandbox="allow-scripts">` without allow-same-origin. See
# apps/public_site/views.py#_page_document. PUBLIC_SITE_URL above is
# defence in depth on top of that, not a precondition for it — the
# recommended production shape is both.
CUSTOM_PAGE_HTML_ENABLED = os.environ.get("HABITAT_CUSTOM_PAGE_HTML", "0") == "1"
# Hard cap on an HTML page's stored source, per the isolated-origin
# checklist's "size limits" item (/build-questions.md). Author documents
# live in the same database as everything else (see "Photo storage growth"
# in /docs/open-questions.md), and an unbounded text field served to every
# visitor is a denial-of-service surface as much as a storage one.
CUSTOM_PAGE_HTML_MAX_BYTES = int(os.environ.get("HABITAT_CUSTOM_PAGE_HTML_MAX_BYTES", str(512 * 1024)))

# Real email delivery is still undecided (see /docs/open-questions.md,
# "Hosting/ops model") — defaults to Django's console backend, which just
# logs the message instead of sending it, so the org-invite flow
# (apps/accounts/invitations.py) always also surfaces the accept link
# directly in the API/UI as a fallback. Set EMAIL_BACKEND to
# "django.core.mail.backends.smtp.EmailBackend" (and the EMAIL_HOST_* vars
# below) for a deployment that should actually deliver mail.
EMAIL_BACKEND = os.environ.get("EMAIL_BACKEND", "django.core.mail.backends.console.EmailBackend")
DEFAULT_FROM_EMAIL = os.environ.get("DEFAULT_FROM_EMAIL", "noreply@habitat.local")
EMAIL_HOST = os.environ.get("EMAIL_HOST", "")
EMAIL_PORT = int(os.environ.get("EMAIL_PORT", "587"))
EMAIL_HOST_USER = os.environ.get("EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD = os.environ.get("EMAIL_HOST_PASSWORD", "")
EMAIL_USE_TLS = os.environ.get("EMAIL_USE_TLS", "1") == "1"

# In-app feedback pipeline (see /docs/open-questions.md, "App feedback /
# build workflow" — decided 2026-08-29). Off by default so this doesn't
# silently show up on every deployment; set HABITAT_FEEDBACK_ENABLED=1 on
# whichever environment should have it (e.g. dev, not necessarily prod).
# Gates both the submission UI/endpoint and the org-scoped review list —
# not the retrieval endpoints below, which have their own gate (an unset
# token always denies, regardless of this flag).
FEEDBACK_ENABLED = os.environ.get("HABITAT_FEEDBACK_ENABLED", "0") == "1"
# Shared secret for the feedback *pull* endpoints (apps/feedback/views.py
# #feedback_pull / #feedback_mark_synced), checked as an
# `Authorization: Bearer <token>` header — see apps/feedback/auth.py. Not
# a Django user/session credential: the caller is an external scheduled
# routine, not a logged-in Habitat user. Never commit a real value here —
# set HABITAT_FEEDBACK_TOKEN in the server's environment, and the same
# value in that routine's own environment config (e.g. on claude.ai).
# Left unset (empty string), the pull endpoints reject every request.
FEEDBACK_API_TOKEN = os.environ.get("HABITAT_FEEDBACK_TOKEN", "")
