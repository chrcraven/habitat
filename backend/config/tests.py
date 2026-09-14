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
import os
import random
from unittest import mock

from django.core.checks import Tags, run_checks
from django.http import HttpResponse
from django.middleware.gzip import GZipMiddleware
from django.test import RequestFactory, SimpleTestCase, TestCase, override_settings

import config.settings
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
