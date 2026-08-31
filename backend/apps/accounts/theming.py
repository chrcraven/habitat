"""Shared constants for the public-site "constrained theme controls"
feature (owner decision, 2026-08-31 — see /docs/open-questions.md,
"Public site storytelling / custom content"): a fixed, safe set of theme
knobs mapped to scoped CSS custom properties on the public site, NOT a
raw CSS field — that was the actual decision made, over the alternative
(a free-text CSS override) that the same doc weighed and rejected on
public-facing-injection-risk grounds. Shared by Organization and
Property (see models.py), which each carry their own independent set of
these fields.
"""

from django.core.validators import RegexValidator
from django.db import models

# This regex *is* the security guardrail for these fields, not just a UI
# nicety: a 6-digit hex code can't contain `;`, `}`, `url(...)`, or
# anything else CSS-meaningful, so a value that passes this can be
# dropped straight into a CSS custom property on the public site with no
# further escaping. Never relax this to accept arbitrary CSS color syntax
# (named colors, rgb(), css vars, ...) without re-examining that.
HEX_COLOR_VALIDATOR = RegexValidator(
    regex=r"^#[0-9a-fA-F]{6}$", message="Enter a 6-digit hex color, e.g. #2f6f4f."
)

# Cap on the header banner image, same reasoning as ActivityPhoto/
# SightingPhoto's MAX_PHOTO_BYTES (see apps/activities/views.py) but
# smaller — this is one decorative image per org/property, not a photo
# gallery.
MAX_THEME_IMAGE_BYTES = 5 * 1024 * 1024


class ThemeFont(models.TextChoices):
    """A fixed set of safe, system font stacks — no arbitrary font-family
    text and no externally-loaded webfonts, so choosing a font never adds
    a new network request/third-party dependency to the public site. See
    frontend/src/utils/theme.ts for the matching CSS stacks."""

    SANS = "sans", "Sans-serif"
    SERIF = "serif", "Serif"
    ROUNDED = "rounded", "Rounded"
    MONOSPACE = "monospace", "Monospace"


def theme_color_field():
    """A blank-by-default hex-color field — blank means "inherit the
    default (or, for a Property, its Organization's) styling", not
    "black" or "invalid". A factory function, not a shared field
    instance, since a single Django field object can't be attached to
    more than one model."""
    return models.CharField(max_length=7, blank=True, validators=[HEX_COLOR_VALIDATOR])
