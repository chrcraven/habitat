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


def _env_flag(name, default):
    """Read a boolean environment variable.

    Accepts the `1`/`0` spelling this file already uses for DEBUG plus the
    `true`/`yes`/`on` spellings a ConfigMap tends to grow, so a deployment
    that writes `SESSION_COOKIE_SECURE: "true"` gets what it meant rather
    than silently falling through to the default. Unset or blank returns
    `default`, which for the transport settings below is itself derived
    from DEBUG rather than hardcoded.
    """
    raw = os.environ.get(name)
    if raw is None or not raw.strip():
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


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
    # Serves everything under STATIC_ROOT (see the static-files block
    # below) straight from this process, so the production image needs no
    # second server in front of it for Django admin's own CSS and JS.
    #
    # It sits *above* GZipMiddleware, and that ordering is a decision
    # rather than an accident — the two both want to be "immediately after
    # SecurityMiddleware" and only one can be. Django's middleware
    # short-circuit semantics settle it: WhiteNoise answers a static
    # request in its *request* phase without calling anything below, so
    # the response only travels back up through the middleware listed
    # above it. Second means gzip never sees a static file, which is what
    # we want — CompressedManifestStaticFilesStorage compresses those
    # files once at collectstatic time and WhiteNoise serves the stored
    # .gz/.br copy, where GZipMiddleware would re-compress the same bytes
    # on every request. Third would mean paying that CPU forever for no
    # smaller a response.
    #
    # Nothing about GZipMiddleware's own invariant changes: it stays below
    # SecurityMiddleware and above every middleware that writes an API
    # response body, so it still compresses last. WhiteNoise never touches
    # a non-static URL, so no API response's path is altered by this line.
    "whitenoise.middleware.WhiteNoiseMiddleware",
    # Compresses every response the client will accept gzip for. Measured
    # 7.0x on this app's list payloads, which are long runs of repeated
    # JSON keys — the single cheapest thing available to the transfer cost
    # of the unpaginated org-wide lists (D31). Nothing was compressed
    # before this line existed.
    #
    # Position is deliberate and not interchangeable. process_response runs
    # bottom-up, so a middleware listed *early* compresses *late* — after
    # everything below has finished writing the body and its headers. That
    # is Django's own documented ordering (security, then gzip, then the
    # rest) and it is what keeps CorsMiddleware's headers intact. It stays
    # below SecurityMiddleware, which must remain first.
    #
    # On BREACH, the risk this middleware is usually cautioned about: it is
    # mitigated in the Django version this project pins, not merely
    # accepted. GZipMiddleware.max_random_bytes (100) pads each compressed
    # response with a random-length prefix, which is precisely the
    # defence against compression-ratio oracles. On top of that, checked
    # rather than assumed: no CSRF token appears in any response *body*
    # here — /api/auth/csrf/ returns a fixed {"detail": ...} and only sets
    # the cookie, and the client reads the token from document.cookie.
    # The one token-bearing body in the app is InvitationSerializer's
    # `accept_url`, which is admin-only and whose token is emailed anyway.
    # So: enabled everywhere, with no per-view exemption.
    #
    # Harmless where it can't help: the middleware returns the original
    # response when compression doesn't actually shrink it, so the image
    # endpoints that serve already-compressed PNG/JPEG bytes are passed
    # through unchanged rather than bloated.
    "django.middleware.gzip.GZipMiddleware",
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

# --- Static files ------------------------------------------------------
#
# Until 2026-09-17 this was STATIC_URL and nothing else, which is fine
# while DEBUG=1: `runserver` serves each app's static/ directory itself.
# With DEBUG=0 it serves none of them, and there was nowhere to collect
# them to either — so Django admin's CSS and JS 404 on any real
# deployment. That is not cosmetic here: admin is the only place
# Organization.custom_html_allowed, the per-tenant custom-HTML
# kill-switch, can be set (see apps/pages/custom_html.py).
#
# Django normalises the relative STATIC_URL below to "/static/"; it is
# left relative only because nothing gains from changing it.
STATIC_URL = "static/"
# Where `manage.py collectstatic` writes, and what WhiteNoiseMiddleware
# serves from. The production image runs collectstatic at build time so
# the directory ships inside the image; it is gitignored and simply
# absent in a dev checkout, which WhiteNoise tolerates (it serves nothing
# rather than failing to start).
STATIC_ROOT = BASE_DIR / "staticfiles"

STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {
        # Hashed filenames plus a pre-compressed .gz/.br copy of each, so
        # WhiteNoise serves compressed bytes off disk instead of gzipping
        # the same file on every request (see the middleware comment).
        #
        # Deliberately only when DEBUG is off, and the asymmetry is the
        # usual manifest-storage trap: this backend refuses to resolve any
        # {% static %} name that is not in the staticfiles.json manifest
        # collectstatic writes, so enabling it in a checkout where nobody
        # has run collectstatic turns every admin page into a 500. Tied to
        # DEBUG for the same reason the cookie flags below are — the flag
        # that already separates a laptop from a deployment.
        "BACKEND": (
            "django.contrib.staticfiles.storage.StaticFilesStorage"
            if DEBUG
            else "whitenoise.storage.CompressedManifestStaticFilesStorage"
        )
    },
}

# WhiteNoise otherwise decides this from Django's *runtime* DEBUG, which
# is not the same question: Django's test runner forces DEBUG off for the
# duration of a run, so a developer's `manage.py test` would take the
# production path and scan STATIC_ROOT before anything had been collected
# into it. Keyed to the env-derived DEBUG above, a checkout serves static
# files straight from each app's own directory, exactly as `runserver`
# does, and only a real deployment reads the collected tree.
WHITENOISE_AUTOREFRESH = DEBUG

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Clears the cache before every test. Rate-limit state lives in the cache
# and LocMemCache is one process-global dict, so without this a test that
# signs up six times poisons an unrelated test later in the run. See
# config/test_runner.py for the failure it was written for.
TEST_RUNNER = "config.test_runner.HabitatTestRunner"

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.SessionAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    # There is deliberately no DEFAULT_THROTTLE_CLASSES and no
    # DEFAULT_THROTTLE_RATES. The two rate limits this app has (D40) bound
    # the two endpoints that were measured, not every endpoint, and each
    # class carries its own `rate` next to the measurement that justifies
    # it — see apps/accounts/throttling.py, and the same treatment
    # MAX_PHOTO_BYTES and MAX_THEME_IMAGE_BYTES already get. Keeping the
    # numbers out of here also keeps settings.py free of an import from an
    # app module, which at settings-import time is not yet loadable.
    #
    # How many reverse proxies sit in front of this process, which is what
    # decides where DRF reads the client address from.
    #
    # The default is 0 — REMOTE_ADDR only, X-Forwarded-For never trusted —
    # and it is deliberately NOT DRF's own default of None. With None, DRF
    # keys the throttle on the whole X-Forwarded-For chain when the header
    # is present, and that header is set by the client: an attacker varies
    # it per request and is never throttled, which is the throttle
    # silently doing nothing. Getting this wrong in the other direction is
    # merely too strict — behind an un-declared proxy every request looks
    # like it comes from the proxy, so the limit becomes global instead of
    # per-client. Refusing too much is a visible bug; refusing nothing is
    # not, so the default fails in the visible direction.
    #
    # A deployment behind a proxy that *overwrites* X-Forwarded-For sets
    # this to the number of such hops (usually 1; a k8s ingress in front
    # of another proxy is 2). Same opt-in posture, and the same reason, as
    # TRUST_X_FORWARDED_PROTO below.
    "NUM_PROXIES": int(os.environ.get("THROTTLE_NUM_PROXIES", "0") or "0"),
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

# --- Browser transport security ---------------------------------------
#
# Environment-driven like everything else here (see
# /docs/deployment-config.md), but the *default* is the load-bearing part
# of this block, so it's spelled out rather than left to be inferred.
#
# The two cookie flags default to `not DEBUG` instead of to a fixed
# value. A hardcoded True breaks every developer: local dev serves the
# app over plain HTTP (http://localhost:5173 against http://localhost:8000)
# and a browser silently refuses to store a Secure cookie there, so
# nobody could log in. A hardcoded False is what shipped until
# 2026-09-06, and it left the deployed HTTPS site handing out session and
# CSRF cookies carrying no Secure attribute at all — which means a
# browser holding a Habitat session will send them, in cleartext, to
# http://<the same host>/anything. That host answers on port 80, serves
# no HTTPS redirect, and sends no HSTS header, so nothing upstream closes
# the gap either.
#
# Tying the default to DEBUG means the flag that already distinguishes "a
# developer's laptop" from "a real deployment" also flips these, and a
# deployment gets the safe posture without having to know these variables
# exist. A DEBUG=0 deployment genuinely served over plain HTTP (there is
# none today) opts back out explicitly with SESSION_COOKIE_SECURE=0 /
# CSRF_COOKIE_SECURE=0.
SESSION_COOKIE_SECURE = _env_flag("SESSION_COOKIE_SECURE", not DEBUG)
CSRF_COOKIE_SECURE = _env_flag("CSRF_COOKIE_SECURE", not DEBUG)

# These four match Django's own current defaults. They're pinned here so
# they sit next to the ones above and so changing one is a deliberate
# edit rather than a silent consequence of a Django upgrade — and because
# the asymmetry between the two HTTPONLY values is deliberate and
# non-obvious:
#
#   CSRF_COOKIE_HTTPONLY must stay False. The SPA reads document.cookie
#   to put the token in an X-CSRFToken header (frontend/src/api/client.ts),
#   so making it HttpOnly would break every state-changing request.
#
#   SESSION_COOKIE_HTTPONLY must stay True. Nothing in the frontend reads
#   the session cookie, and keeping it unreadable to JavaScript is what
#   holds an XSS to the page instead of handing over the account.
SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_HTTPONLY = False
SESSION_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_SAMESITE = "Lax"

# HSTS tells a browser to refuse plain HTTP to this host for max-age
# seconds. Deliberately OFF by default even though the cookie flags above
# default on, and the asymmetry is the point: a browser *remembers* HSTS
# and there is no way to call it back within its max-age, so committing a
# hostname to HTTPS-only is a deployment decision with a tail, not
# something a code default should make on a deployment's behalf. The
# Secure flags above are what actually stop the cookies leaking; this is
# defence in depth for the very first navigation to the host.
# Recommended value once a deployment has settled on HTTPS: 31536000.
SECURE_HSTS_SECONDS = int(os.environ.get("SECURE_HSTS_SECONDS", "0") or "0")
SECURE_HSTS_INCLUDE_SUBDOMAINS = _env_flag("SECURE_HSTS_INCLUDE_SUBDOMAINS", False)
SECURE_HSTS_PRELOAD = _env_flag("SECURE_HSTS_PRELOAD", False)

# Have Django itself redirect plain HTTP to HTTPS. Off by default, and
# the pairing with the setting below it is not optional: behind a
# TLS-terminating proxy Django only learns the original scheme from
# SECURE_PROXY_SSL_HEADER, so turning this on WITHOUT that produces an
# infinite redirect loop — every proxied request looks like plain HTTP to
# Django, which redirects it to HTTPS, which the proxy terminates and
# forwards as HTTP again. Enable the two together or neither.
SECURE_SSL_REDIRECT = _env_flag("SECURE_SSL_REDIRECT", False)

# Opt-in, and it has to stay opt-in. This makes Django believe an
# X-Forwarded-Proto header about whether the original request was HTTPS,
# which is only safe when a proxy in front of the app *overwrites* that
# header on every request. Where a client can set it directly, trusting
# it lets any request declare itself secure — which defeats
# SECURE_SSL_REDIRECT above and would let a Secure cookie be issued over
# a plaintext connection.
SECURE_PROXY_SSL_HEADER = (
    ("HTTP_X_FORWARDED_PROTO", "https")
    if _env_flag("TRUST_X_FORWARDED_PROTO", False)
    else None
)

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

# Who a stuck user should contact about *this* deployment — an email
# address, a URL, a name, whatever the operator wants read aloud in a
# sentence. Surfaced in the "forgot password" reply
# (apps/accounts/views.py#password_reset_requested_detail), which is the
# one screen whose reader is already locked out of the app and therefore
# has no in-app route to the Help link that would otherwise explain
# things.
#
# Blank, the default, keeps the generic "whoever runs this Habitat
# instance" wording this had when Habitat was one deployment — so nothing
# changes for a deployment that ignores this variable. It became worth
# configuring once there were two (a dev instance and a production one,
# owner's decision 2026-09-17): the same sentence can no longer name one
# operator by implication.
#
# Never derive it from anything in the request. The reply must stay
# byte-identical whoever asks, which is what keeps that endpoint from
# being a user-enumeration oracle.
SUPPORT_CONTACT = os.environ.get("HABITAT_SUPPORT_CONTACT", "").strip()

# Which build this process is running, reported by /api/health/ (see
# config/health.py). Blank means "this image was not told", which the
# endpoint reports as null rather than inventing a value.
#
# These are the one pair of variables in this file a *deployment* should
# normally leave alone. Every other value here belongs to the environment;
# these two belong to the image, and ../Dockerfile sets them from build
# arguments that .github/workflows/docker-publish.yml fills in from the
# git tag and commit. A ConfigMap can still override them, and doing so
# is how the answer starts being wrong — a version somebody has to
# remember to update is a version that eventually lies, and this repo
# fears a confident wrong answer more than a missing one.
#
# Blank here is also the honest answer for `latest`: it is published from a
# push to main, and main has no version number (zero git tags — D37).
# REVISION is what identifies that image, which is why there are two.
VERSION = os.environ.get("HABITAT_VERSION", "").strip()
REVISION = os.environ.get("HABITAT_REVISION", "").strip()

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
