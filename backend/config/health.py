"""Liveness and readiness endpoints, and the build identity they report.

Added 2026-09-17 for D43. Until then `health`, `healthz`, `readyz`, `livez`
and `version` appeared in **zero** `urls.py` in this backend, so a
deployment had no probe target — and what it got when it guessed was worse
than nothing. Measured on the dev host: `GET /healthz` returned **200 with
549 bytes, byte-identical to a path that does not exist**, because the
frontend's nginx serves the SPA fallback for everything (see
../../frontend/nginx.conf). An operator pointing a readiness probe at the
frontend gets a green light that cannot go red, with the backend down and
the database unreachable. Pointing it at the *backend* instead got a Django
404, which would crashloop a perfectly healthy pod.

Why this lives in `config/` and not in an app: it reports on the
deployment, not on any domain model. It has no models, no organization
scoping and no role check, and the question it answers ("is this process
serving, and can it reach its database") is the same question whichever
apps happen to be installed. `config/tests.py` and `config/test_runner.py`
are here for the same reason.

Two endpoints, not one
----------------------
The queued recommendation was a single `/api/health/` that touches the
database. That is one endpoint doing two jobs, and Kubernetes treats the
two answers *very* differently:

    livenessProbe  fails -> kubelet KILLS the container
    readinessProbe fails -> kubelet stops routing traffic to it

So a single database-checking endpoint named "health" — which is the name
a `livenessProbe` reaches for — turns a ten-second database restart into
every pod being killed, and killing them does not fix a database. The blip
outlives itself as CrashLoopBackOff. That is D43's own failure shape
(loud, and wrong in the other direction) reintroduced by D43's fix, so:

    GET /api/health/        liveness.  Never touches the database.
    GET /api/health/ready/  readiness. Touches the database.

Both report the build identity, so "what is running?" is answerable from
either one.

Plain Django views, deliberately not DRF
---------------------------------------
Every other endpoint in this app is `@api_view`. These two are not, and the
reason is the same principle as the split above: **the endpoint that tells
you whether the app works should depend on as little of the app as
possible.** A DRF view inherits whatever `REST_FRAMEWORK` grows later — a
`DEFAULT_THROTTLE_CLASSES` would start answering probes with 429, a
`DEFAULT_AUTHENTICATION_CLASSES` change would start resolving
`request.user` and so querying the session table, a renderer change would
change the body — and each of those breaks the probe silently, in a
deployment, without touching this file.

This was not a hunch; it was measured. The first version of this module was
DRF-based with `renderer_classes([JSONRenderer])` pinned so the body could
not depend on the caller's `Accept` header. It doesn't — instead DRF
answers `Accept: text/html` with **406 Not Acceptable**, because content
negotiation cannot satisfy that request. A probe or monitor that sends a
browser-ish Accept header would have been told the pod is unhealthy, and an
operator checking the URL in a browser would have seen a 406 and gone
looking for the wrong bug. Leaving the renderer list alone instead would
have served the browsable-API *HTML page* from a health endpoint. Neither
is what a probe should get, and a `JsonResponse` is both without
negotiating anything.

What remains in the path is middleware, which is deliberate: ALLOWED_HOSTS
is enforced there, and a probe that bypassed it would be testing something
the real traffic doesn't go through.

What these deliberately do NOT report
-------------------------------------
The Django, Python, PostgreSQL and PostGIS versions, the hostname, and any
settings value. They are unauthenticated, because a kubelet probe carries
no session, so every byte here is public. `version` and `revision` are the
exception and the reason is specific rather than a shrug: the images are
published *publicly* (`cravenator/habitat-backend` on Docker Hub) and the
repository is public, so the release tag and the commit sha are already
public facts. An infrastructure version number is not, and knowing it tells
an attacker which CVEs to try.

A failed readiness check reports a fixed string and logs the exception,
rather than returning the driver's message — that message routinely
contains the database host, port and user.
"""

import logging

from django.conf import settings
from django.db import connection
from django.http import JsonResponse
from django.views.decorators.http import require_GET

logger = logging.getLogger(__name__)


def _identity():
    """The build this process is running, or nulls if it wasn't told.

    Both values are **baked into the image** by ../Dockerfile from build
    arguments the publish workflow passes, rather than supplied by the
    deployment's own environment. That is the load-bearing half: a version
    an operator has to remember to set is a version that will eventually be
    set wrong, and a *confidently wrong* version is worse than an absent
    one — it is the shape this repo keeps finding, something reporting
    success while being wrong. Baked in, it is right without anyone acting.

    `None` rather than `"unknown"` or `"dev"` when unset, because those read
    like values. A locally built image genuinely does not know what it is
    and should say so.

    `version` is null on the `latest` image by design, not by omission:
    `latest` is published from a push to main, and a push to main has no
    version number (there are zero git tags — D37). `revision` is what
    identifies that image, which is why both fields exist rather than one.
    """
    return {
        "version": settings.VERSION or None,
        "revision": settings.REVISION or None,
    }


def _probe_response(payload, status=200):
    """A probe response must never be cached by anything in between.

    A cached 200 is a readiness check that keeps saying yes after the answer
    changed, which is the entire defect D43 is about wearing a different hat.
    """
    response = JsonResponse(payload, status=status)
    response["Cache-Control"] = "no-store"
    return response


@require_GET
def liveness(request):
    """Is this process alive and serving? Wire this to `livenessProbe`.

    Answers from the process itself and touches nothing else, so the only
    way it fails is the only thing a liveness probe should act on: the
    process is gone, wedged, or not listening. A dependency being down is a
    readiness question.
    """
    return _probe_response({"status": "ok", **_identity()})


@require_GET
def readiness(request):
    """Can this process serve real requests? Wire this to `readinessProbe`.

    The check is `SELECT postgis_lib_version()` — Django's own PostGIS
    backend probe — and the choice of query is the point. `SELECT 1` would
    report ready against a plain PostgreSQL database, which is exactly the
    deployment D42 measured: it connects, it answers, and then every request
    that touches a geometry column fails. A readiness check that goes green
    on a database the application cannot actually use is the vacuous green
    light this whole module exists to remove, one layer in.

    It deliberately does **not** check whether migrations are applied.
    `entrypoint.sh` runs `migrate` inside `set -e` before exec'ing the
    server, so a process that is answering at all has already migrated; if
    it failed, there is nothing here to ask. Checking anyway would load the
    migration graph on every probe to re-derive something the startup
    sequence guarantees.
    """
    payload = {"status": "ok", **_identity(), "database": "ok"}
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT postgis_lib_version()")
            row = cursor.fetchone()
        ready = bool(row) and row[0] is not None
        if not ready:
            logger.error("readiness: PostGIS probe returned no version")
    except Exception:
        # Broad on purpose: a readiness probe's job is to answer, and every
        # distinct failure here (refused connection, auth failure, missing
        # extension, exhausted pool) has the identical correct answer —
        # don't route traffic here. `exception` puts the real cause in the
        # pod log, where an operator can read it and a caller cannot.
        logger.exception("readiness: database probe failed")
        ready = False

    if not ready:
        payload["status"] = "unavailable"
        payload["database"] = "unavailable"
        return _probe_response(payload, status=503)
    return _probe_response(payload)
