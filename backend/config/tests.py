"""Tests for the browser transport-security block in config/settings.py.

These exist because that block's *defaults* are the security control, not
the values a deployment happens to type. Until 2026-09-06 the deployed
HTTPS site handed out session and CSRF cookies with no Secure attribute,
so a browser holding a Habitat session would send them in cleartext to
http://<the same host>/. Nothing failed, nothing looked wrong, and the
only visible symptom was two lines in `manage.py check --deploy`, which
nothing ran.

So the assertions here are deliberately about the two directions that
could silently undo the fix: a default that stops protecting a real
deployment, and a default that starts breaking local development. Both
are one keystroke apart from correct and neither shows up as a failing
request.

`manage.py test config` runs these. The transport-security classes need no
database, hence SimpleTestCase; ResponseCompressionTests drives a real
request and so uses TestCase.
"""

import importlib
import logging
import os
import platform
import random
from datetime import timedelta
from pathlib import Path
from unittest import mock

from django.conf import settings
from django.contrib.sessions.backends.db import SessionStore as DatabaseSessionStore
from django.contrib.sessions.models import Session
from django.core.cache import cache
from django.core.checks import Tags, run_checks
from django.core.management import call_command
from django.db import OperationalError, ProgrammingError, connection
from django.http import HttpResponse
from django.middleware.gzip import GZipMiddleware
from django.test import RequestFactory, SimpleTestCase, TestCase, override_settings
from django.test.utils import CaptureQueriesContext
from django.urls import reverse
from django.utils import timezone

import config.settings
from config import health
from apps.accounts.models import Membership, Organization, User
from apps.notifications.models import Notification

#: The names this module asserts on. Kept explicit so a setting silently
#: disappearing from settings.py surfaces as a None here rather than as a
#: test that quietly stops checking anything.
TRANSPORT_SETTINGS = (
    "DEBUG",
    "SESSION_COOKIE_SECURE",
    "CSRF_COOKIE_SECURE",
    "SESSION_COOKIE_HTTPONLY",
    "CSRF_COOKIE_HTTPONLY",
    "SESSION_COOKIE_SAMESITE",
    "CSRF_COOKIE_SAMESITE",
    "SECURE_HSTS_SECONDS",
    "SECURE_HSTS_INCLUDE_SUBDOMAINS",
    "SECURE_HSTS_PRELOAD",
    "SECURE_SSL_REDIRECT",
    "SECURE_PROXY_SSL_HEADER",
)


def resolve_settings(**environ):
    """Re-import settings.py under exactly `environ` and read the result.

    `clear=True` matters: these are tests about what happens when a
    variable is *absent*, so inheriting the ambient environment (which in
    CI and in a developer's shell may well set DEBUG) would let the
    defaults under test go unexercised.

    Reloading the module is safe here because `django.conf.settings`
    snapshots its values at setup and does not re-read the module, so the
    running test session's own configuration is unaffected.
    """
    with mock.patch.dict(os.environ, environ, clear=True):
        module = importlib.reload(config.settings)
        return {name: getattr(module, name, None) for name in TRANSPORT_SETTINGS}


class TransportSecurityDefaultsTests(SimpleTestCase):
    @classmethod
    def tearDownClass(cls):
        # Restore the module to the real environment's values; every
        # reload above ran under a patched os.environ that has since been
        # rolled back.
        importlib.reload(config.settings)
        super().tearDownClass()

    def test_local_dev_does_not_get_secure_cookies(self):
        """DEBUG unset (the local-dev default) must leave both cookie
        flags off.

        This is the direction that breaks people rather than exposing
        them: local dev is served over plain HTTP, and a browser silently
        declines to store a Secure cookie there, so flipping these on
        unconditionally would make login fail with no error anyone could
        read off the page.
        """
        resolved = resolve_settings()
        self.assertIs(resolved["DEBUG"], True)
        self.assertIs(resolved["SESSION_COOKIE_SECURE"], False)
        self.assertIs(resolved["CSRF_COOKIE_SECURE"], False)

    def test_deployment_gets_secure_cookies_without_being_told_to(self):
        """DEBUG=0 alone must turn both cookie flags on.

        The whole point of deriving the default from DEBUG: a deployment
        should not have to know these variables exist to get the safe
        posture. This is the assertion that fails if someone "simplifies"
        the default back to a literal False.
        """
        resolved = resolve_settings(DEBUG="0")
        self.assertIs(resolved["DEBUG"], False)
        self.assertIs(resolved["SESSION_COOKIE_SECURE"], True)
        self.assertIs(resolved["CSRF_COOKIE_SECURE"], True)

    def test_a_deployment_can_opt_back_out_of_secure_cookies(self):
        """A DEBUG=0 deployment served over plain HTTP must be able to
        turn these off explicitly, or the derived default would be a
        trap rather than a convenience."""
        resolved = resolve_settings(
            DEBUG="0", SESSION_COOKIE_SECURE="0", CSRF_COOKIE_SECURE="0"
        )
        self.assertIs(resolved["SESSION_COOKIE_SECURE"], False)
        self.assertIs(resolved["CSRF_COOKIE_SECURE"], False)

    def test_a_developer_can_opt_in_to_secure_cookies(self):
        """The override has to work in both directions — someone testing
        an HTTPS setup locally shouldn't have to fake DEBUG=0."""
        resolved = resolve_settings(SESSION_COOKIE_SECURE="1", CSRF_COOKIE_SECURE="1")
        self.assertIs(resolved["DEBUG"], True)
        self.assertIs(resolved["SESSION_COOKIE_SECURE"], True)
        self.assertIs(resolved["CSRF_COOKIE_SECURE"], True)

    def test_configmap_boolean_spellings_are_understood(self):
        """A ConfigMap writes `"true"`, not `"1"`. Treating that as unset
        would fall through to the default silently — the failure mode is
        a deployment that believes it turned something on."""
        for spelling in ("true", "True", "TRUE", "yes", "on", " 1 "):
            with self.subTest(spelling=spelling):
                self.assertIs(
                    resolve_settings(SECURE_SSL_REDIRECT=spelling)["SECURE_SSL_REDIRECT"],
                    True,
                )
        for spelling in ("0", "false", "False", "no", "off", ""):
            with self.subTest(spelling=spelling):
                self.assertIs(
                    resolve_settings(
                        DEBUG="0", SESSION_COOKIE_SECURE=spelling
                    )["SESSION_COOKIE_SECURE"],
                    # A blank value means "unset" and must fall through to
                    # the DEBUG-derived default, which here is True; every
                    # other spelling above is an explicit false.
                    spelling == "",
                )

    def test_the_httponly_asymmetry_is_pinned(self):
        """These two must differ, and each for its own reason.

        CSRF_COOKIE_HTTPONLY False is load-bearing: the SPA reads
        document.cookie for the token (frontend/src/api/client.ts) and
        every write breaks if it can't. SESSION_COOKIE_HTTPONLY True is
        what keeps an XSS from escalating to account takeover. A future
        pass that "tidies" them into agreement breaks one or the other,
        so both are asserted rather than left to Django's defaults.
        """
        resolved = resolve_settings(DEBUG="0")
        self.assertIs(resolved["SESSION_COOKIE_HTTPONLY"], True)
        self.assertIs(resolved["CSRF_COOKIE_HTTPONLY"], False)

    def test_hsts_is_off_unless_a_deployment_asks(self):
        """Off by default on purpose, unlike the cookie flags: a browser
        remembers HSTS and it cannot be recalled within its max-age, so
        committing a hostname to HTTPS-only is a deployment's decision to
        make, not a default's."""
        resolved = resolve_settings(DEBUG="0")
        self.assertEqual(resolved["SECURE_HSTS_SECONDS"], 0)
        self.assertIs(resolved["SECURE_HSTS_INCLUDE_SUBDOMAINS"], False)
        self.assertIs(resolved["SECURE_HSTS_PRELOAD"], False)

        opted_in = resolve_settings(
            DEBUG="0",
            SECURE_HSTS_SECONDS="31536000",
            SECURE_HSTS_INCLUDE_SUBDOMAINS="true",
        )
        self.assertEqual(opted_in["SECURE_HSTS_SECONDS"], 31536000)
        self.assertIs(opted_in["SECURE_HSTS_INCLUDE_SUBDOMAINS"], True)

    def test_ssl_redirect_and_proxy_header_both_default_off(self):
        """SECURE_SSL_REDIRECT on without SECURE_PROXY_SSL_HEADER is an
        infinite redirect loop behind a TLS-terminating proxy, which is
        how this deployment is served. Defaulting either one on alone
        would take the site down, so both stay off and are documented as
        a pair.
        """
        resolved = resolve_settings(DEBUG="0")
        self.assertIs(resolved["SECURE_SSL_REDIRECT"], False)
        self.assertIsNone(resolved["SECURE_PROXY_SSL_HEADER"])

    def test_proxy_header_trust_is_opt_in_only(self):
        """Trusting X-Forwarded-Proto is only safe when a proxy
        overwrites it. It must never become true as a side effect of
        DEBUG or of enabling the redirect — a client that can set the
        header itself could otherwise declare any request secure."""
        self.assertIsNone(
            resolve_settings(DEBUG="0", SECURE_SSL_REDIRECT="1")["SECURE_PROXY_SSL_HEADER"]
        )
        self.assertEqual(
            resolve_settings(TRUST_X_FORWARDED_PROTO="1")["SECURE_PROXY_SSL_HEADER"],
            ("HTTP_X_FORWARDED_PROTO", "https"),
        )


class DjangoDeployChecksTests(SimpleTestCase):
    """Runs Django's own `check --deploy` security checks against the
    settings a deployment actually resolves to.

    This is the check that would have caught the original defect, and the
    reason it didn't is simply that nothing ever ran it — it is not part
    of `manage.py check`, only of `check --deploy`, and CI runs the
    former. Automating it here closes that loop.

    It is deliberately not a restatement of the class above. That one
    asserts what settings.py *produces*; this one asserts what Django
    *thinks of the result*, so it also catches causes that live nowhere
    near this block — CsrfViewMiddleware being dropped from MIDDLEWARE
    would surface here and nowhere else in the suite.
    """

    @classmethod
    def tearDownClass(cls):
        importlib.reload(config.settings)
        super().tearDownClass()

    def test_a_deployment_raises_no_cookie_security_warnings(self):
        deployment = resolve_settings(DEBUG="0")
        with override_settings(**deployment):
            reported = {
                message.id
                for message in run_checks(
                    tags=[Tags.security], include_deployment_checks=True
                )
            }

        # W012: session cookie not Secure. W016: CSRF cookie not Secure.
        # Both were present on every deployment of this app until
        # 2026-09-06.
        self.assertNotIn("security.W012", reported)
        self.assertNotIn("security.W016", reported)

        # Stated rather than left implicit, so a later reader doesn't take
        # a green run here as "the deploy checks are clean". Three
        # warnings remain by design and are the deployment's call, not
        # this file's: W004 (HSTS off — see settings.py for why that is
        # deliberately not a code default), W008 (no app-level HTTPS
        # redirect, which needs the proxy-header pairing) and W009 (the
        # placeholder SECRET_KEY, which a real deployment overrides).
        self.assertIn("security.W004", reported)


class ResponseCompressionTests(TestCase):
    """Responses are compressed (D31).

    Nothing in this app was compressed until GZipMiddleware was added to
    MIDDLEWARE: the deployed host returned no `content-encoding` even when
    gzip was explicitly offered. That matters here more than it would in
    most apps, because the org-wide list endpoints are unpaginated by
    decision — every record reaches the browser — and their payloads are
    long runs of repeated JSON keys, which is the shape gzip is best at.
    Measured ~7x on this app's own list output.

    These are integration tests against real responses rather than an
    assertion that the middleware is in the list, because the thing worth
    pinning is the *observable* — a middleware present but ordered so that
    something below it rewrites the body afterwards would satisfy a
    settings check and compress nothing.
    """

    def test_a_real_api_response_is_compressed_through_the_installed_stack(self):
        """The only test here that proves the middleware is *installed*
        rather than merely importable — every other test in this class
        drives GZipMiddleware directly and would pass just as happily with
        the settings.py line deleted.

        It needs a response over 200 bytes, because the middleware returns
        short ones untouched *before* it patches anything — so a tiny
        endpoint like /api/auth/csrf/ proves nothing either way, which is
        worth knowing before reaching for one.
        """
        org = Organization.objects.create(name="Compression Prairie")
        user = User.objects.create_user(email="gz@example.com", password="pw-12345678")
        Membership.objects.create(organization=org, user=user, role=Membership.Role.ADMIN)
        for i in range(5):
            Notification.objects.create(
                organization=org,
                recipient=user,
                verb=Notification.Verb.TASK_ASSIGNED,
                message=f"You were assigned the task \"Restore the swale, phase {i}\".",
            )
        self.client.force_login(user)

        response = self.client.get("/api/notifications/", HTTP_ACCEPT_ENCODING="gzip, deflate")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers.get("Content-Encoding"), "gzip")
        # Vary is what stops a shared cache handing compressed bytes to a
        # client that never asked for them.
        self.assertIn("Accept-Encoding", response.headers.get("Vary", ""))

    def test_a_large_response_is_actually_smaller_on_the_wire(self):
        """The claim, measured end to end rather than asserted."""
        body = b'{"name": "Prairie restoration activity", "status": "planned"}, ' * 200

        compressed = self._through_middleware(body, accept_encoding="gzip")
        uncompressed = self._through_middleware(body, accept_encoding="")

        self.assertEqual(compressed.headers.get("Content-Encoding"), "gzip")
        self.assertIsNone(uncompressed.headers.get("Content-Encoding"))
        self.assertLess(
            len(compressed.content),
            len(uncompressed.content) / 4,
            "the compressed response is not meaningfully smaller",
        )

    def test_a_client_that_cannot_accept_gzip_still_gets_readable_bytes(self):
        """The direction that would break everything rather than merely
        fail to help. Compression must be negotiated, never assumed."""
        body = b'{"activities": []} ' * 100

        response = self._through_middleware(body, accept_encoding="")

        self.assertNotIn("Content-Encoding", response.headers)
        self.assertEqual(response.content, body)

    def test_already_compressed_bytes_are_not_re_compressed(self):
        """Habitat stores photos in the database and serves them back as
        raw bytes (see apps/accounts/blobs.py). Gzipping a JPEG costs CPU
        to make the response *bigger*; the middleware must hand those
        through untouched."""
        # Incompressible by construction — a deterministic pseudo-random
        # stream stands in for already-compressed image bytes.
        rng = random.Random(0)
        body = bytes(rng.randrange(256) for _ in range(4096))

        response = self._through_middleware(body, accept_encoding="gzip")

        self.assertNotIn(
            "Content-Encoding",
            response.headers,
            "incompressible bytes were gzipped anyway, making the response larger",
        )
        self.assertEqual(response.content, body)

    def test_breach_padding_is_active(self):
        """The mitigation the decision to enable compression rests on.

        BREACH is the standing objection to gzipping responses, and the
        answer here is not "we accept it" but "the pinned Django mitigates
        it": GZipMiddleware pads each compressed response with a
        random-length prefix, so compressed length is no longer a clean
        oracle. Asserted because it is a property of the Django version,
        not of this repo — a downgrade past it would silently remove the
        grounds for the setting above.
        """
        self.assertGreater(
            getattr(GZipMiddleware, "max_random_bytes", 0),
            0,
            "GZipMiddleware no longer pads compressed responses — the BREACH "
            "reasoning recorded in settings.py no longer holds",
        )

    def _through_middleware(self, body, accept_encoding):
        """Drive the real GZipMiddleware over a response of our own, so the
        size claim can be made on a payload big enough to matter without
        seeding hundreds of rows."""
        request = RequestFactory().get("/", HTTP_ACCEPT_ENCODING=accept_encoding)
        middleware = GZipMiddleware(lambda r: HttpResponse(body, content_type="application/json"))
        return middleware(request)


class StaticFilesAndTestIsolationTests(SimpleTestCase):
    """Two settings-level guarantees added alongside the production image
    (D5 Q2) and the first rate limits (D40), both of which fail silently.

    They live here for the reason this module exists at all: `manage.py
    check` — what CI runs — does not include the deploy checks, so a
    settings-level promise that nothing asserts is a promise nobody is
    keeping.
    """

    def test_static_files_have_somewhere_to_be_collected_to(self):
        """Django admin is load-bearing in this app — it is the only place
        Organization.custom_html_allowed, the per-tenant custom-HTML
        kill-switch, can be set. With DEBUG=0 and no STATIC_ROOT its CSS
        and JS 404, which looks like a broken page rather than a missing
        setting, and `manage.py collectstatic` has nowhere to write.
        """
        self.assertTrue(settings.STATIC_ROOT, "STATIC_ROOT is unset; collectstatic has no target")
        self.assertIn(
            "whitenoise.middleware.WhiteNoiseMiddleware",
            settings.MIDDLEWARE,
            "nothing serves STATIC_ROOT once DEBUG is off",
        )

    def test_whitenoise_sits_above_gzip_and_below_security(self):
        """Both middlewares want the slot immediately after
        SecurityMiddleware and only one can have it. WhiteNoise answers a
        static request in its *request* phase, so the response only
        travels back up through what is listed above it — second means
        gzip never re-compresses a file that CompressedManifestStatic-
        FilesStorage already compressed once at collectstatic time.

        Asserted rather than commented because the cost of getting it
        wrong is invisible: the bytes are identical either way and only
        the CPU differs.
        """
        order = settings.MIDDLEWARE
        security = order.index("django.middleware.security.SecurityMiddleware")
        whitenoise = order.index("whitenoise.middleware.WhiteNoiseMiddleware")
        gzip = order.index("django.middleware.gzip.GZipMiddleware")
        self.assertEqual(security, 0, "SecurityMiddleware must stay first")
        self.assertLess(security, whitenoise)
        self.assertLess(whitenoise, gzip)

    def test_the_cache_is_cleared_between_tests(self):
        """Rate-limit state lives in the Django cache, and with no CACHES
        setting that is one LocMemCache dict for the whole test run.
        Nothing in Django resets it between tests, so a test that signs up
        six times poisons an unrelated test later in the same run — which
        is exactly what happened to two D8 tests the moment the signup
        throttle landed.

        config/test_runner.py clears it before every test. Pinned here
        because if that is dropped the symptom is order-dependent failures
        in other modules, which is about the worst debugging signal
        available.
        """
        # Written first, deliberately: if the assertion below fails the
        # method stops there, and the behavioural half of this pair would
        # then be asserting against a key nobody ever set — green for the
        # wrong reason, in exactly the run where it matters most.
        cache.set("a-key-a-previous-test-might-have-left", "stale")
        self.assertIsNotNone(cache.get("a-key-a-previous-test-might-have-left"))

        self.assertEqual(settings.TEST_RUNNER, "config.test_runner.HabitatTestRunner")

    def test_the_previous_test_left_nothing_behind(self):
        """The other half of the pair above: asserting the runner *name* is
        a claim about configuration, this is a claim about behaviour.
        unittest runs methods in alphabetical order within a class, and
        "the_cache_is_cleared" sorts before "the_previous_test", so the key
        set there has been written by the time this runs.
        """
        self.assertIsNone(
            cache.get("a-key-a-previous-test-might-have-left"),
            "cache state survived from one test into the next",
        )


# ---------------------------------------------------------------------
# D43 (2026-09-17) — the health and readiness endpoints.
#
# The defect these exist for is not a wrong answer, it is a *vacuous* one:
# `GET /healthz` on the deployed frontend returned 200 with 549 bytes,
# byte-identical to a path that does not exist, because nginx serves the
# SPA fallback for everything. A readiness probe pointed there is a green
# light that cannot go red. Pointed at the backend instead, it was a Django
# 404 — which would crashloop a healthy pod.
#
# So most of what follows is mechanism tests, because almost every wrong
# fix here returns a perfectly plausible 200. The five wrong fixes were
# built and measured rather than predicted; what caught each is recorded at
# the bottom of this section, including the two predictions that were wrong.
# ---------------------------------------------------------------------

#: Exactly what each endpoint may report. Asserted as a *set*, not
#: "contains", because the failure worth catching is an extra key — a
#: helpful "django": "5.2.17" or "database_host" added later. A
#: contains-check cannot see an addition (D40's lesson: a suite that only
#: looks for missing things is blind to duplicated and added ones).
LIVENESS_KEYS = {"status", "version", "revision"}
READINESS_KEYS = {"status", "version", "revision", "database"}


class HealthEndpointTests(TestCase):
    """`manage.py test config.tests.HealthEndpointTests`.

    TestCase rather than SimpleTestCase: the readiness endpoint's whole job
    is to talk to a real database, and asserting that against a mock would
    be asserting the mock.
    """

    def setUp(self):
        self.live_url = reverse("health-live")
        self.ready_url = reverse("health-ready")

    # -- liveness: it must answer, and it must answer alone --------------

    def test_liveness_returns_ok(self):
        response = self.client.get(self.live_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "ok")

    def test_liveness_needs_no_authentication(self):
        """A kubelet carries no session cookie. If this ever requires one,
        every probe fails and the pod is killed for being healthy.
        """
        self.assertEqual(self.client.get(self.live_url).status_code, 200)

    def test_liveness_issues_no_database_queries_even_with_a_session(self):
        """The mechanism test for the liveness/readiness split.

        A session cookie is sent **on purpose**, and it is the whole point
        of the test. Anything that resolves `request.user` — DRF's default
        SessionAuthentication, or a `login_required`, or a middleware added
        later — runs a query against the session table, but **only when a
        cookie is present**. Without one this test passes against such a
        view, so a probe-shaped request (no cookie) would look fine while a
        logged-in browser tab took a database query, and the endpoint's one
        guarantee would hold by luck of who was asking.
        """
        user = User.objects.create_user(email="probe@example.com", password="pw-12345678")
        self.client.force_login(user)
        self.assertIn("sessionid", self.client.cookies)

        with self.assertNumQueries(0):
            response = self.client.get(self.live_url)
        self.assertEqual(response.status_code, 200)

    def test_liveness_still_answers_when_the_database_is_unreachable(self):
        """The reason there are two endpoints rather than one.

        `livenessProbe` failing makes the kubelet **kill** the container.
        If this endpoint checked the database, a database restart would kill
        every pod — and killing them does not fix a database, so a
        ten-second blip becomes CrashLoopBackOff that outlives it.
        """
        with mock.patch.object(
            connection, "cursor", side_effect=OperationalError("connection refused")
        ):
            response = self.client.get(self.live_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "ok")

    # -- readiness: it must actually check, and fail when it should ------

    def test_readiness_reports_ok_against_a_real_database(self):
        response = self.client.get(self.ready_url)
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["status"], "ok")
        self.assertEqual(body["database"], "ok")

    def test_readiness_needs_no_authentication(self):
        self.assertEqual(self.client.get(self.ready_url).status_code, 200)

    def test_readiness_actually_reaches_the_database(self):
        """Mechanism: a readiness check that returns a hardcoded 200 is
        indistinguishable from this one in every response byte.
        """
        with CaptureQueriesContext(connection) as captured:
            self.assertEqual(self.client.get(self.ready_url).status_code, 200)
        statements = [q["sql"] for q in captured.captured_queries]
        self.assertTrue(
            any("postgis_lib_version" in sql for sql in statements),
            f"readiness issued no PostGIS probe; statements were {statements!r}",
        )

    def test_readiness_is_unavailable_when_the_database_is_unreachable(self):
        with mock.patch.object(
            connection, "cursor", side_effect=OperationalError("connection refused")
        ):
            response = self.client.get(self.ready_url)
        self.assertEqual(response.status_code, 503)
        body = response.json()
        self.assertEqual(body["status"], "unavailable")
        self.assertEqual(body["database"], "unavailable")

    def test_readiness_is_unavailable_on_a_database_with_no_postgis(self):
        """The D42 database, and the **only** test that rules out `SELECT 1`.

        A plain PostgreSQL instance — what a stock Kubernetes Postgres
        operator hands you — connects fine, authenticates fine, and answers
        `SELECT 1` fine. Measured on a real plain PostgreSQL 16 (D42): the
        DDL `accounts/0001_initial` emits fails with `type "geometry" does
        not exist`, so every request touching a geometry column 500s while
        a `SELECT 1` readiness check sits green. That is the vacuous green
        light this module exists to remove, one layer in.
        """
        real_cursor = connection.cursor

        class _NoPostGIS:
            def __init__(self, inner):
                self._inner = inner

            def __enter__(self):
                self._cursor = self._inner.__enter__()
                return self

            def __exit__(self, *exc):
                return self._inner.__exit__(*exc)

            def execute(self, sql, *args, **kwargs):
                if "postgis_lib_version" in sql:
                    raise ProgrammingError(
                        'function postgis_lib_version() does not exist'
                    )
                return self._cursor.execute(sql, *args, **kwargs)

            def fetchone(self):
                return self._cursor.fetchone()

        with mock.patch.object(
            connection, "cursor", side_effect=lambda *a, **k: _NoPostGIS(real_cursor(*a, **k))
        ):
            response = self.client.get(self.ready_url)

        self.assertEqual(
            response.status_code,
            503,
            "readiness went green on a database with no PostGIS — a "
            "connectivity-only check (SELECT 1) would do exactly this",
        )

    def test_readiness_does_not_report_the_database_error(self):
        """The driver's message routinely names the host, port and user.
        It belongs in the pod log, which an operator can read and a caller
        cannot.
        """
        secret = "host=db-prod-internal.example user=habitat"
        with mock.patch.object(
            connection, "cursor", side_effect=OperationalError(secret)
        ):
            with mock.patch.object(logging.getLogger("config.health"), "exception"):
                response = self.client.get(self.ready_url)
        self.assertEqual(response.status_code, 503)
        self.assertNotIn("db-prod-internal", response.content.decode())
        self.assertNotIn("habitat", response.content.decode())

    # -- what may be reported, and what may not --------------------------

    def test_the_endpoints_report_exactly_their_documented_keys(self):
        for url, expected in ((self.live_url, LIVENESS_KEYS), (self.ready_url, READINESS_KEYS)):
            with self.subTest(url=url):
                self.assertEqual(set(self.client.get(url).json()), expected)

    def test_no_infrastructure_version_is_disclosed(self):
        """`version`/`revision` are public on purpose — the images and the
        repository are public, so the tag and the commit already are. The
        Django, Python and PostGIS versions are not, and knowing them tells
        an unauthenticated caller which CVEs to try.
        """
        import django

        for url in (self.live_url, self.ready_url):
            body = self.client.get(url).content.decode()
            with self.subTest(url=url):
                self.assertNotIn(django.get_version(), body)
                self.assertNotIn(platform.python_version(), body)
                self.assertNotIn(connection.ops.postgis_lib_version(), body)

    def test_the_response_does_not_depend_on_the_accept_header(self):
        """This test is why these two are plain Django views.

        Written against the first, DRF-based version of the module, it
        failed with **406 != 200** — `renderer_classes([JSONRenderer])`
        does not make DRF ignore `Accept: text/html`, it makes DRF refuse
        the request. A monitor or browser sending a browser-ish Accept
        header would have been told the pod is unhealthy. Leaving DRF's
        renderer list alone instead serves the browsable-API HTML page from
        a health endpoint. A JsonResponse negotiates nothing and is neither.
        """
        for url in (self.live_url, self.ready_url):
            response = self.client.get(url, HTTP_ACCEPT="text/html")
            with self.subTest(url=url):
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response["Content-Type"], "application/json")

    def test_the_probes_are_not_drf_views(self):
        """Mechanism for the two tests above and the throttle test below.

        Every other endpoint in this app is `@api_view`, so converting
        these "for consistency" is the attractive wrong change — and it
        reintroduces the 406, and re-exposes the probes to any
        `DEFAULT_THROTTLE_CLASSES` or authentication default added to
        settings.py later, in a deployment, without this file being edited.
        `@api_view` attaches the generated APIView class as `.cls`; a plain
        Django view has no such attribute.
        """
        for view in (health.liveness, health.readiness):
            with self.subTest(view=view.__name__):
                self.assertFalse(
                    hasattr(view, "cls"),
                    f"{view.__name__} is a DRF view again — it now inherits "
                    "every REST_FRAMEWORK default, including future ones",
                )

    def test_probe_responses_are_not_cacheable(self):
        """A cached 200 is a readiness answer that keeps saying yes after it
        stopped being true — this defect wearing a different hat.
        """
        for url in (self.live_url, self.ready_url):
            with self.subTest(url=url):
                self.assertEqual(self.client.get(url)["Cache-Control"], "no-store")

    # -- build identity -------------------------------------------------

    @override_settings(VERSION="", REVISION="")
    def test_identity_is_null_when_the_image_was_not_told(self):
        """Null, not `"unknown"` or `"dev"` or `"0.0.0"`.

        Those read like values, and a version that looks like a value while
        being a placeholder is the confident-wrong-answer shape this repo
        keeps finding. A locally built image genuinely does not know what it
        is, and `latest` genuinely has no version number (zero git tags —
        D37), so null is the true answer in both cases rather than a gap.
        """
        for url in (self.live_url, self.ready_url):
            body = self.client.get(url).json()
            with self.subTest(url=url):
                self.assertIsNone(body["version"])
                self.assertIsNone(body["revision"])

    @override_settings(VERSION="1.4.2", REVISION="0123456789abcdef")
    def test_identity_reports_what_the_image_was_built_with(self):
        for url in (self.live_url, self.ready_url):
            body = self.client.get(url).json()
            with self.subTest(url=url):
                self.assertEqual(body["version"], "1.4.2")
                self.assertEqual(body["revision"], "0123456789abcdef")

    def test_the_identity_settings_exist_and_default_to_blank(self):
        """Pinned because the endpoint reads them through `settings`, so
        deleting them from settings.py is an AttributeError at probe time —
        i.e. a 500 on the URL a deployment relies on to decide whether this
        process is healthy.
        """
        self.assertEqual(settings.VERSION, "")
        self.assertEqual(settings.REVISION, "")

    # -- the two loud failure modes --------------------------------------

    def test_probes_are_never_throttled(self):
        """A kubelet asks every few seconds, forever.

        There is deliberately no DEFAULT_THROTTLE_CLASSES (see
        settings.py), but "be consistent, throttle everything" is an
        attractive future change, and a throttled probe returns 429 —
        which the kubelet reads as failure and acts on by killing or
        de-routing a pod that is perfectly fine.
        """
        for url in (self.live_url, self.ready_url):
            codes = {self.client.get(url).status_code for _ in range(30)}
            with self.subTest(url=url):
                self.assertEqual(codes, {200}, f"a probe was refused: saw {codes}")

    @override_settings(ALLOWED_HOSTS=["habitat.example.com"])
    def test_a_probe_that_does_not_send_a_known_host_is_refused(self):
        """Not a defect — Django working as designed — and the single most
        likely reason a correct probe fails on a correct pod.

        Kubernetes defaults an HTTP probe's Host header to the **pod IP**,
        which is never in ALLOWED_HOSTS, so Django answers 400
        DisallowedHost and the kubelet kills a healthy container. Pinned
        here so docs/deployment-config.md's probe recipe (which sets the
        Host header explicitly) is a checkable claim rather than folklore,
        and so that "just add '*' to ALLOWED_HOSTS" shows up as a change to
        this test instead of a quiet loosening.
        """
        response = self.client.get(self.live_url, HTTP_HOST="10.42.0.7")
        self.assertEqual(response.status_code, 400)


# What each wrong fix actually costs, measured by building all eight and
# running this section — then correcting this table, because two of the
# predictions written here first were wrong. (D38/D40's standing rule: "each
# wrong fix is caught by its own test" is a claim to measure, not to assert.)
#
#   1. liveness checks the DB too        3 red: the two liveness mechanism
#      (the single-endpoint                    tests, AND the key-set test,
#      recommendation)                         because liveness starts
#                                              reporting `database`. Not
#                                              predicted.
#   2. converted to DRF views            3 red: no-queries, not-a-DRF-view,
#      ("be consistent with the app")          Accept-header.
#   3. readiness does `SELECT 1`         2 red: the SQL mechanism test and
#                                              the no-PostGIS test. Predicted
#                                              only the second — but the
#                                              mechanism test greps the SQL
#                                              for `postgis_lib_version`, so
#                                              it sees this too.
#   4. readiness swallows the            3 red: both unavailable tests AND
#      exception (`ready = True`)              the error-disclosure test,
#                                              which asserts 503 before it
#                                              looks at the body.
#   5. identity defaults to "unknown"    1 red: the null test, and it is the
#                                              ONLY sole catcher in this
#                                              section. Delete that one test
#                                              and a health endpoint that
#                                              confidently reports a
#                                              placeholder version ships
#                                              green.
#   6. DRF + `AnonRateThrottle`          3 red: identical to #2 — **the
#      ("rate limit everything")               throttle test does not fire.**
#
# #6 is the one worth reading, because the wrong fix is more wrong than it
# looks. `AnonRateThrottle` reads its rate from
# DEFAULT_THROTTLE_RATES["anon"], which this project does not set, so
# `rate` is None and SimpleRateThrottle.allow_request returns True
# unconditionally. Adding that class throttles **nothing at all** — a
# security control that refuses nobody, which is D40's own finding about
# NUM_PROXIES in a second place. So the fix a reviewer would approve as
# "probes are rate limited now" would be inert, and the test that looks
# like it guards this passes for the wrong reason.
#
#   7. DRF + a throttle with a real      4 red: #2's three plus the throttle
#      rate (what copying                      test. This is the variant the
#      apps/accounts/throttling.py             throttle test exists for.
#      produces)
#
# And one measurement that is not a wrong fix but a positive claim:
#
#   8. a global DEFAULT_THROTTLE_CLASSES 0 red. Adding a 5/min anon throttle
#      of 5/min added to settings.py           to REST_FRAMEWORK does not
#                                              reach these views at all.
#
# #8 is the payoff of not using DRF here, measured rather than argued: the
# most likely future change that would break a probe (a project-wide rate
# limit) cannot touch these two endpoints, because they never enter DRF's
# dispatch. The plain-view choice is a structural guarantee, not a style
# preference — which is what `test_the_probes_are_not_drf_views` protects.


class SessionEvictionTests(TestCase):
    """Tests for the `clearsessions` sweep in `backend/entrypoint.sh` (D49a).

    Habitat stores sessions as database rows — the inherited Django default,
    since settings.py sets no SESSION_ENGINE — and `auth.login()` writes one
    per login that nothing removed until 2026-09-20. A login with a valid
    prior cookie replaces its own row (`cycle_key()`), but a login without
    one — a lapsed session, cleared cookies, a new device, a private window —
    leaves a fresh row behind permanently.

    **Stated plainly, because a green suite here should not imply more than
    it does: this section does not meet this repo's usual bar.** No invariant
    regressed; at **672 bytes a row** (measured by writing 1,000 sessions
    through the real `login()` against PostgreSQL 16) and roughly one row
    per user per device per fortnight, the whole table is ~850 KB a year
    for a 25-contributor org — against ~52 GB of photos, which is the
    thing that actually accumulates (D32, and already the owner's). D49a
    is worth shipping because it is one line of Django's own command, not
    because the bytes matter.

    What earns the tests is the *other* half, which is not small: the fix
    has a silent-no-op form, and this repo has now found five of those
    (D40's NUM_PROXIES, D43's AnonRateThrottle, D45's six mail variables,
    D46's declared-but-unrun EmailValidator, and this). Measured on the
    pinned Django 5.2.17 against real PostgreSQL, seeding 6 expired and 4
    live rows per engine:

        db              exit 0   6 removed, 4 kept
        cached_db       exit 0   6 removed, 4 kept
        cache           exit 0   0 removed  <-- `clear_expired` is `pass`
        file            exit 0   0 removed  <-- clears files, not rows
        signed_cookies  exit 0   0 removed  <-- no store to clear

    Three of five engines make the command exit 0, print nothing, raise
    nothing, and remove nothing. The `NotImplementedError` branch in
    Django's own command handles a case none of the shipped backends take.
    That matters here rather than in the abstract because
    docs/deployment-config.md already tells an operator to configure a
    shared cache backend before scaling — and an operator who stands up
    Redis is one plausible step from SESSION_ENGINE=cache, at which point
    the boot log still says "clearing expired sessions..." forever.
    """

    def _seed(self):
        """6 expired rows and 4 live ones, with the preconditions asserted.

        The assertions are not ceremony. The first version of this
        measurement seeded nothing (the seed script's directory, not the
        working directory, was on sys.path) and every engine scored a
        clean 0 rows left — a vacuous result that reads exactly like a
        pass. D46's lesson in a fixture: assert the properties that make
        your example an example.
        """
        now = timezone.now()
        Session.objects.all().delete()
        for i in range(6):
            Session.objects.create(
                session_key=f"expired{i:033d}",
                session_data="x",
                expire_date=now - timedelta(days=1),
            )
        for i in range(4):
            Session.objects.create(
                session_key=f"live{i:036d}",
                session_data="x",
                expire_date=now + timedelta(days=7),
            )
        self.assertEqual(Session.objects.count(), 10, "seed did not seed")
        self.assertEqual(
            Session.objects.filter(expire_date__lt=now).count(),
            6,
            "no expired rows were seeded, so this proves nothing",
        )
        return now

    # -- the premise -----------------------------------------------------

    def test_the_session_engine_is_still_the_inherited_default(self):
        """Not a correctness assertion — a deliberateness one, and the
        distinction is worth stating because measuring it corrected this
        section's own first draft.

        That draft called this test "a session is a database row" and
        predicted `cached_db` would pass it. `cached_db` fails it, and is
        nonetheless perfectly correct: its sessions *are* rows and it *does*
        evict them (measured). The assertion was narrower than the property
        its name claimed — D46's trap, in a test that reads as though it
        pins a property while actually pinning one exact string.

        Kept as an exact match anyway, with the name and message fixed to
        say so, because it gives the two tests a useful gradient: this one
        alone going red means someone changed the engine to something safe
        and should confirm it, whereas this one *and*
        `test_the_configured_engine_is_one_that_can_actually_evict` going
        red means the new engine cannot evict at all. Nobody has ever
        *chosen* this value — it is Django's default, inherited, which is
        D49b's Q1 — so a change to it deserves one deliberate look.
        """
        self.assertEqual(
            settings.SESSION_ENGINE,
            "django.contrib.sessions.backends.db",
            "SESSION_ENGINE changed. If the new engine still evicts "
            "(cached_db does), this is safe — update this test. If the "
            "evict test below is also red, the boot-time sweep is now a "
            "silent no-op.",
        )
        self.assertFalse(
            settings.SESSION_SAVE_EVERY_REQUEST,
            "a row written per request rather than per login would change "
            "the rate this sweep exists for by orders of magnitude",
        )

    def test_expired_rows_are_not_removed_by_the_passage_of_time(self):
        """Expiry is not eviction, and conflating them is how this survived.

        A row past its expire_date is dead weight that stays in the table
        forever. It is also the reason the attractive wrong fix is wrong:
        SESSION_COOKIE_AGE changes how long people stay logged in — a
        user-visible product decision nobody has made — and removes not
        one row, which is what this test pins.
        """
        now = self._seed()
        self.assertEqual(
            Session.objects.filter(expire_date__lt=now).count(),
            6,
            "expired rows vanished with no sweep, so the next test proves "
            "nothing about what removed them",
        )

    # -- the mechanism ---------------------------------------------------

    def test_the_configured_engine_is_one_that_can_actually_evict(self):
        """The only thing standing between this sweep and the inert forms.

        Asserted structurally rather than by outcome, for the same reason
        `test_the_probes_are_not_drf_views` is: the outcome tests below
        would go red too, but they would read as "eviction broke", whereas
        the fix is to reconsider the engine. `cached_db` subclasses the db
        store and passes deliberately — it evicts, measured. `cache`,
        `file` and `signed_cookies` do not subclass it and do not evict.
        """
        store = importlib.import_module(settings.SESSION_ENGINE).SessionStore
        self.assertTrue(
            issubclass(store, DatabaseSessionStore),
            f"SESSION_ENGINE is {settings.SESSION_ENGINE}, whose "
            f"clear_expired() does not delete session rows. `clearsessions` "
            f"will still exit 0 and print nothing, so entrypoint.sh will go "
            f"on reporting a sweep that removes nothing.",
        )

    def test_the_boot_sequence_actually_runs_the_sweep(self):
        """D45's lesson: a control is only a control if it runs on the path
        the operator's log comes from. A command that works and is invoked
        nowhere is the same table growing forever.

        Deliberately a text assertion rather than a behavioural one — this
        is a shell script, and nothing else in the suite can reach it. It
        is weak, and it is the only thing connecting the tests above to the
        running deployment.
        """
        entrypoint = (Path(settings.BASE_DIR) / "entrypoint.sh").read_text()
        self.assertIn(
            "manage.py clearsessions",
            entrypoint,
            "entrypoint.sh no longer sweeps expired sessions",
        )
        self.assertIn(
            "clearsessions failed; continuing startup",
            entrypoint,
            "the sweep must stay outside `set -e` for the same reason the "
            "property purge is: a failed cleanup is a problem to fix, not a "
            "reason to refuse to boot",
        )

    # -- the outcome -----------------------------------------------------

    def test_the_sweep_removes_expired_rows_and_keeps_live_ones(self):
        """The real management command against the real table."""
        now = self._seed()
        call_command("clearsessions")
        self.assertEqual(
            Session.objects.filter(expire_date__lt=now).count(),
            0,
            "expired rows survived the sweep",
        )
        self.assertEqual(
            Session.objects.count(),
            4,
            "the sweep took live sessions with it — every logged-in user "
            "would be signed out on every container start",
        )

    def test_the_sweep_is_idempotent(self):
        """It runs on every boot, and a deployment restarts for reasons
        that have nothing to do with sessions.
        """
        self._seed()
        for _ in range(3):
            call_command("clearsessions")
        self.assertEqual(Session.objects.count(), 4)

    def test_the_sweep_is_a_no_op_on_an_empty_table(self):
        """The overwhelmingly common case on a small instance: it must not
        error, because entrypoint.sh prints a WARNING when it does.
        """
        Session.objects.all().delete()
        call_command("clearsessions")
        self.assertEqual(Session.objects.count(), 0)

    # -- the severity claim ----------------------------------------------

    def test_an_expired_row_does_not_authenticate(self):
        """Pinned because it is the claim that makes this *not* a security
        finding, and the docs say so. A reader who assumes the opposite
        would reasonably treat D49a as urgent; it is not. An un-swept row
        is dead weight, not a live credential.
        """
        now = self._seed()
        expired_key = (
            Session.objects.filter(expire_date__lt=now)
            .values_list("session_key", flat=True)
            .first()
        )
        self.assertEqual(
            DatabaseSessionStore(expired_key).load(),
            {},
            "an expired session row still loaded its contents",
        )


# What each wrong fix actually costs, measured in this suite rather than
# predicted (this repo's prediction has been wrong in the same direction
# four times running -- D38, D40, D45, D48 -- so the table below is a
# transcript of eight runs, not a design intention):
#
#   1. clearsessions deleted from       1 red: the boot test.
#      entrypoint.sh
#   2. sweep moved under `set -e`       1 red: the boot test.
#      (the `|| echo WARNING` dropped)
#   3. SESSION_COOKIE_AGE shortened     1 red: the boot test.
#      *instead of* sweeping
#   4. SESSION_ENGINE = cache           4 red, including the evict test.
#   5. SESSION_ENGINE = file            4 red, including the evict test.
#   6. SESSION_ENGINE = cached_db       1 red: the deliberateness test only.
#      (NOT a wrong fix)                It evicts. Safe; update that test.
#   7. SESSION_SAVE_EVERY_REQUEST=True  1 red: the deliberateness test.
#
# **`test_the_boot_sequence_actually_runs_the_sweep` is the sole catcher
# for #1, #2 and #3 — three different wrong fixes, one test.** Delete it
# and all three ship green: a management command that works perfectly,
# is covered by five passing tests, and is invoked by nothing. It is also
# the weakest assertion here (a grep over a shell script), which is worth
# sitting with rather than tidying away — weak and load-bearing are not
# opposites, and nothing else in this suite can reach a shell script.
#
# #3 is the attractive wrong fix named in the queue, and the measurement
# shows why the naming was right: shortening the cookie lifetime *looks*
# like the same fix, fails only that one test, and removes no rows at all
# while silently signing people out sooner.
#
# #4/#6 are the pair worth reading together. Both are one-word edits to
# the same setting; one makes the sweep inert and the other is fine. The
# difference is invisible in the diff, invisible in the boot log (both
# exit 0 and print nothing), and shows up here as 4 red versus 1.
#
# Stated rather than left to be inferred: three tests in this section
# caught **nothing** in any of the seven variants above --
# test_expired_rows_are_not_removed_by_the_passage_of_time,
# test_the_sweep_is_a_no_op_on_an_empty_table, and
# test_an_expired_row_does_not_authenticate. They are kept deliberately
# and for different reasons: the first is what makes the outcome test
# mean anything (without it, "the rows are gone" could be the passage of
# time rather than the sweep); the second is the case that actually runs
# on almost every real boot, where an error would print a WARNING an
# operator would have to chase; and the third pins the claim that an
# un-swept row is dead weight rather than a live credential, which is the
# whole reason this is a tidy-up and not a security fix.
