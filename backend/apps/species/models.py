"""
Species: each Organization maintains its own species reference list rather
than Habitat integrating an external taxonomy (GBIF, USDA PLANTS) — decided,
see /docs/data-model-notes.md ("Activity record" > species/treatment
details). Activities and Sightings within an Organization both resolve
against this same list, which is what makes a sighting-to-activity link
(e.g., a Field Bindweed sighting and a Field Bindweed treatment) meaningful.
"""

from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from apps.accounts.models import Organization

#: A bloom endpoint is stored as MMDD (May 1 -> 501, November 15 -> 1115).
#: See Species.bloom_start for why, and bloom_ordinal/format_bloom below
#: for the conversion the serializer uses.
BLOOM_MIN = 101  # January 1
BLOOM_MAX = 1231  # December 31


def bloom_ordinal(month, day):
    return month * 100 + day


def bloom_parts(value):
    """MMDD -> (month, day). None passes straight through."""
    if value is None:
        return None, None
    return divmod(value, 100)


class Species(models.Model):
    organization = models.ForeignKey(
        Organization, on_delete=models.CASCADE, related_name="species"
    )
    common_name = models.CharField(max_length=255)
    scientific_name = models.CharField(max_length=255, blank=True)
    # Renamed from `notes` on 2026-09-02 (migration species/0002). The
    # field was already in the *public* sighting payload — SightingSerializer
    # nests SpeciesSerializer as `species_detail`, which
    # apps/public_site/views.py serves unauthenticated — but no UI had ever
    # rendered or written it, so calling it "notes" promised a privacy it
    # never had. Owner decision the same day: this is the species
    # description, shown on the public site, and the name now says so.
    description = models.TextField(
        blank=True,
        help_text="Shown publicly wherever this species appears on the public site.",
    )

    # Bloom period — annual and recurring, so a plain DateField is the
    # wrong shape twice over: it carries a year this has no use for, and
    # it silently drifts once that year is in the past. Stored instead as
    # MMDD integers (see BLOOM_MIN/BLOOM_MAX above), which keeps the two
    # ends directly comparable for the "what's blooming on this date"
    # filter while carrying no year at all.
    #
    # A range is allowed to **wrap the year** (November -> February), which
    # is why there's no start <= end validation anywhere: rejecting that
    # would rule out every winter-blooming species. The wrap is handled
    # explicitly instead — see apps/species/views.py#SpeciesViewSet.
    bloom_start = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(BLOOM_MIN), MaxValueValidator(BLOOM_MAX)],
        help_text="Month/day the bloom period starts, stored as MMDD.",
    )
    bloom_end = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(BLOOM_MIN), MaxValueValidator(BLOOM_MAX)],
        help_text="Month/day the bloom period ends, stored as MMDD. May be "
        "earlier than bloom_start — a bloom period can wrap the year.",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def blooms_on(self, ordinal):
        """Whether this species is in bloom on the given MMDD.

        The Python mirror of the queryset filter in views.py — same two
        cases, kept together so the wrap logic is written down once as a
        readable rule and once as SQL, rather than only as SQL.
        """
        if self.bloom_start is None or self.bloom_end is None:
            return False
        if self.bloom_start <= self.bloom_end:
            return self.bloom_start <= ordinal <= self.bloom_end
        # Wraps the year: in bloom from the start date to Dec 31, and
        # again from Jan 1 to the end date.
        return ordinal >= self.bloom_start or ordinal <= self.bloom_end

    class Meta:
        verbose_name_plural = "species"
        constraints = [
            models.UniqueConstraint(
                fields=["organization", "common_name"],
                name="unique_common_name_per_organization",
            )
        ]

    def __str__(self):
        return self.common_name
