"""
Species: each Organization maintains its own species reference list rather
than Habitat integrating an external taxonomy (GBIF, USDA PLANTS) — decided,
see /docs/data-model-notes.md ("Activity record" > species/treatment
details). Activities and Sightings within an Organization both resolve
against this same list, which is what makes a sighting-to-activity link
(e.g., a Field Bindweed sighting and a Field Bindweed treatment) meaningful.
"""

from django.db import models

from apps.accounts.models import Organization


class Species(models.Model):
    organization = models.ForeignKey(
        Organization, on_delete=models.CASCADE, related_name="species"
    )
    common_name = models.CharField(max_length=255)
    scientific_name = models.CharField(max_length=255, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

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
