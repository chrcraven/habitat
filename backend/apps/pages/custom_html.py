"""
The two gates on author-supplied HTML/JS pages, in one place so the
authoring API, the public read surface and the frontend's own feature
detection can't drift apart from each other.

Both must be true for an organization to use `ContentFormat.HTML`:

1. **The deployment allows it at all** — `CUSTOM_PAGE_HTML_ENABLED`
   (`HABITAT_CUSTOM_PAGE_HTML=1`), off by default so upgrading never
   silently starts serving author documents.
2. **This organization hasn't been switched off** —
   `Organization.custom_html_allowed`, the per-tenant kill-switch from the
   isolated-origin checklist (/build-questions.md, item 10). Default True;
   only a deployment operator can flip it, via Django admin.

Neither gate is the *security* control — the sandbox is (see
apps/public_site/views.py#_page_document). These decide who's *allowed to
author*, which is a policy question: arbitrary script lets an author
mislead their own page's visitors, and the kill-switch is the answer to
that when it happens.
"""

from django.conf import settings


def deployment_allows_custom_html() -> bool:
    return bool(settings.CUSTOM_PAGE_HTML_ENABLED)


def organization_allows_custom_html(organization) -> bool:
    """Both gates, for one organization. `organization` may be None (no
    active membership), which is never allowed."""
    if organization is None:
        return False
    return deployment_allows_custom_html() and organization.custom_html_allowed


def max_html_bytes() -> int:
    return settings.CUSTOM_PAGE_HTML_MAX_BYTES
