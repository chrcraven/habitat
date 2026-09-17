"""Test runner that clears the cache before every test.

Habitat gained its first rate limits on 2026-09-17 (D40 — see
apps/accounts/throttling.py), and DRF's throttles keep their state in the
Django cache. There is no `CACHES` setting, so that is `LocMemCache`:
**one dict, per process, for the whole test run.** Nothing in Django
resets it between tests.

The symptom is not subtle, and it is not confined to tests *about*
throttling — which is exactly why this lives in a runner rather than in a
`setUp` somewhere. Adding the signup throttle immediately failed two
long-standing D8 tests (`test_the_public_page_is_still_served`,
`test_two_blank_name_signups_get_distinct_slugs`) with `429 != 201`,
because between them they sign up more times than the hourly limit allows
and the earlier tests' requests were still in the bucket. Neither test is
about rate limiting and neither is wrong.

Fixing those two in place would have left the trap armed for the next
person who writes a sixth signup or an eleventh login anywhere in the
suite, with a failure that reads as a bug in their own feature and depends
on test *order*. Clearing once, centrally, before each test is the same
fix applied to every test that will ever be written.

Wired up by `TEST_RUNNER` in config/settings.py; `manage.py test` picks it
up with no extra arguments, so CI needs no change. A test in config/tests.py
asserts it is still configured, because the failure mode if this is
silently dropped is order-dependent flakiness in unrelated modules.
"""

import unittest

from django.core.cache import cache
from django.test.runner import DiscoverRunner


def _cache_clearing(base):
    class CacheClearingResult(base):
        def startTest(self, test):
            cache.clear()
            super().startTest(test)

    return CacheClearingResult


class HabitatTestRunner(DiscoverRunner):
    """`DiscoverRunner` plus a per-test `cache.clear()`.

    Hooked in through `get_resultclass` because that is the only per-test
    seam Django exposes to a runner — `setup_test_environment` runs once
    for the whole run, and `SimpleTestCase._pre_setup` belongs to the test
    classes, which is what this is trying not to have to edit one by one.

    It subclasses whatever the superclass asks for rather than replacing
    it, so `--debug-sql` and `--pdb` keep working (both of those are
    delivered *as* a result class). `--parallel` is deliberately left
    alone: there the result class must be DRF-of-Django's
    `RemoteTestResult`, a different type entirely, and each worker process
    has its own `LocMemCache` anyway. `manage.py test` does not run in
    parallel unless asked, and CI does not ask.
    """

    def get_resultclass(self):
        base = super().get_resultclass()
        if self.parallel and self.parallel > 1:
            return base
        return _cache_clearing(base or unittest.TextTestResult)
