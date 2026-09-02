"""
Authored public-site pages — the first slice of the "public site
storytelling" feature (see /docs/open-questions.md, "Public site
storytelling / custom content", and /build-questions.md for the full
decided shape). An org or property's public site used to be exactly one
auto-generated view; that view is now named **Explore** and is one page
among possibly several a logged-in member can author, with the org/
property owner picking which page is shown at the public URL root (the
"landing page" — see Organization.landing_page / Property.landing_page in
apps/accounts/models.py).

Explore itself is deliberately **not** a stored Page row — it's a virtual,
always-present page representing the existing auto-generated boundary/
activities/sightings/photos view (apps/public_site). Every scope (an org,
or one of its properties) implicitly has an Explore page whether or not it
has ever authored one of these; `RESERVED_PAGE_SLUGS` keeps an authored
page from claiming the "explore" slug and colliding with it.

Content format: two of them, `markdown` (the default, and what every page
authored before 2026-09-02 is) and `html`.

**Markdown** is rendered to sanitized HTML at read time (see .rendering)
and inlined into the public site's own DOM. It is safe there precisely
*because* it's sanitized — the raw source never reaches a visitor.

**HTML** is the author's own document, verbatim, scripts included — the
owner's 2026-09-02 decision (see /docs/open-questions.md, "Public site
storytelling / custom content"). It is deliberately **never** inlined the
way markdown is. It's served as its own document
(`/api/public/.../pages/<slug>/document/`) under
`Content-Security-Policy: sandbox allow-scripts` and embedded in an
`<iframe sandbox="allow-scripts">` *without* `allow-same-origin`, so the
browser gives it a unique opaque origin: no cookies, no access to the
embedding page, no same-origin requests. That sandbox — not sanitization,
and not which hostname serves it — is what makes arbitrary author script
safe to allow at all. See apps/public_site/views.py#_page_document.

Two gates decide whether the `html` format may be *used* at all, checked
together in .custom_html: a deployment-level setting
(`CUSTOM_PAGE_HTML_ENABLED`, off by default) and a per-organization
kill-switch (`Organization.custom_html_allowed`, deliberately not editable
from the org's own admin console — see that field's docstring).
"""

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q

from apps.accounts.models import Organization, Property, User

# "explore" is the one slug no authored page may take, at either scope —
# it's reserved for the built-in virtual page described above.
RESERVED_PAGE_SLUGS = {"explore"}


class ContentFormat(models.TextChoices):
    MARKDOWN = "markdown", "Markdown"
    HTML = "html", "Custom HTML"


class PageQuerySet(models.QuerySet):
    def public(self):
        return self.filter(is_public=True)


class Page(models.Model):
    """A single authored page, scoped to either an Organization (its
    `property` is null — an org-level "portfolio" page) or one of that
    org's Properties (`property` is set — shown on that property's own
    public page). `organization` is always set, even for a property-scoped
    page, so every page can be listed/managed by org without an extra join
    — see PageViewSet.get_queryset.
    """

    organization = models.ForeignKey(
        Organization, on_delete=models.CASCADE, related_name="pages"
    )
    property = models.ForeignKey(
        Property,
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="pages",
        help_text="Leave unset for an organization-level page; set to scope "
        "this page to one property's public page instead.",
    )
    title = models.CharField(max_length=255)
    # Slug is unique per scope: among an org's own org-level pages
    # (property IS NULL), or among one property's own pages — see the
    # constraints below. Auto-generated from title, same convention as
    # Organization.slug/Property.slug (apps/accounts/slugs.py).
    slug = models.SlugField(max_length=255, blank=True)
    content_format = models.CharField(
        max_length=16,
        choices=ContentFormat.choices,
        default=ContentFormat.MARKDOWN,
        help_text="How `body` is interpreted when the public site renders "
        "this page — see this module's docstring.",
    )
    body = models.TextField(
        blank=True,
        help_text="Markdown (rendered to sanitized HTML at read time — see "
        "apps/pages/rendering.py), or, when content_format is 'html', the "
        "author's own document served verbatim inside a sandboxed frame.",
    )
    is_public = models.BooleanField(
        default=True,
        help_text="Whether this page is visible on the public site at all "
        "(independent of whether it's the landing page).",
    )
    position = models.PositiveIntegerField(
        default=0, help_text="Sort order within its scope, ascending."
    )
    created_by = models.ForeignKey(
        User, null=True, blank=True, on_delete=models.SET_NULL, related_name="authored_pages"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = PageQuerySet.as_manager()

    class Meta:
        ordering = ["position", "id"]
        constraints = [
            models.UniqueConstraint(
                fields=["organization", "slug"],
                condition=Q(property__isnull=True),
                name="unique_org_page_slug",
            ),
            models.UniqueConstraint(
                fields=["property", "slug"],
                condition=Q(property__isnull=False),
                name="unique_property_page_slug",
            ),
        ]

    # A method rather than a @property: this model has its own `property`
    # field (the Property FK above), which shadows the builtin decorator
    # inside the class body.
    def is_custom_html(self) -> bool:
        return self.content_format == ContentFormat.HTML

    def clean(self):
        if self.property_id and self.property.organization_id != self.organization_id:
            raise ValidationError("A property-scoped page must belong to its own organization.")
        if self.is_custom_html() and len(self.body.encode("utf-8")) > settings.CUSTOM_PAGE_HTML_MAX_BYTES:
            raise ValidationError("This page's HTML is larger than the allowed limit.")

    def save(self, *args, **kwargs):
        if not self.slug:
            from apps.accounts.slugs import unique_slug

            filters = {"property": self.property} if self.property_id else {"organization": self.organization, "property__isnull": True}
            self.slug = unique_slug(
                Page,
                self.title,
                fallback="page",
                filters=filters,
                exclude_pk=self.pk,
                reserved=RESERVED_PAGE_SLUGS,
            )
        super().save(*args, **kwargs)

    def __str__(self):
        scope = self.property.name if self.property_id else self.organization.name
        return f"{self.title} ({scope})"
