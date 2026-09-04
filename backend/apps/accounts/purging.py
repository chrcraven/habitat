"""
Hard-purging soft-deleted Properties once their 30-day restore window has
passed — see /docs/open-questions.md ("Soft delete") for the decided shape
(Property-only, 30 days, admin-restorable, cascading).

This module exists because the promise had no performer. The retention
window is stated to users in `docs/manual/properties.md` ("After 30 days
it's removed for good"), but until now the only thing that could carry it
out was `manage.py purge_deleted_properties`, which nothing in this repo
ever ran — so a user who deleted a property to be rid of its data didn't
(see build-questions.md, 2026-09-04, D1). Three mechanisms were on the
table; two are now wired up here, and neither needs the still-undecided
hosting model:

- **On backend startup** (`backend/entrypoint.sh`) — sweeps the whole
  database on every container start/redeploy, deliberately non-fatal so a
  purge failure can't stop the app from booting.
- **Lazily, when an admin reads the "Recently deleted" list or restores
  from it** (`PropertyViewSet.deleted`/`restore`) — keeps the list honest
  about its own 30-day claim, and makes it impossible to restore a
  property whose window has already closed.

A real cron (the third option) is still the thing to add if a deployment
wants purging to happen at a specific hour rather than "on the next
restart or the next admin visit"; nothing here gets in its way — the
management command still works and is still idempotent.

Property.activities is a real CASCADE (see apps/activities/models.py), so
deleting the Property row itself already takes its activities (and their
photos/species-links/sighting-links) with it. Sighting.property is
SET_NULL instead (a sighting's point may or may not sit inside any drawn
boundary — see apps/sightings/models.py), which would otherwise leave a
purged property's sightings behind as still-visible, now-orphaned records
instead of removing them — the opposite of what was decided ("a hard
delete removes the property *and all its associated records* (sightings,
activities, photos, sighting<->activity links, etc.)"). So the purge
explicitly deletes each property's sightings first (their own photos and
any sighting<->activity links cascade from that), then the property.
"""

from datetime import datetime
from typing import NamedTuple

from django.db import transaction
from django.utils import timezone

from apps.accounts.models import Property


class PurgedProperty(NamedTuple):
    """What was purged, captured *before* the rows went away so a caller
    can report on it afterwards."""

    name: str
    organization_name: str
    deleted_at: datetime
    sighting_rows: int

    def __str__(self):
        return (
            f"{self.name} (org: {self.organization_name}, "
            f"deleted {self.deleted_at:%Y-%m-%d})"
        )


def properties_due_for_purge(organization=None):
    """Soft-deleted properties whose restore window has closed. Pass an
    organization to bound the sweep to one account (what the lazy
    request-time callers do); omit it to sweep everything (the startup
    sweep and the management command)."""
    due = Property.all_objects.deleted().filter(
        deleted_at__lte=timezone.now() - Property.PURGE_AFTER
    )
    if organization is not None:
        due = due.filter(organization=organization)
    return due.select_related("organization")


def purge_due_properties(organization=None):
    """Hard-deletes everything `properties_due_for_purge` finds, returning
    a PurgedProperty per property removed (empty list when nothing is
    due — the common case, and the reason the callers can afford to run
    this on every visit).

    Each property is its own transaction: a failure part-way through a
    sweep must not leave a property whose sightings are gone but which is
    itself still sitting in the restore list.
    """
    # Imported here rather than at module scope: apps.sightings imports
    # from apps.accounts, so a top-level import would be circular.
    from apps.sightings.models import Sighting

    purged = []
    # Materialised before the first delete — the loop deletes rows out of
    # the very table this queryset selects from.
    for property_ in list(properties_due_for_purge(organization)):
        name = property_.name
        organization_name = property_.organization.name
        deleted_at = property_.deleted_at
        with transaction.atomic():
            sighting_rows, _ = Sighting.objects.filter(property=property_).delete()
            property_.delete()
        purged.append(
            PurgedProperty(
                name=name,
                organization_name=organization_name,
                deleted_at=deleted_at,
                sighting_rows=sighting_rows,
            )
        )
    return purged
