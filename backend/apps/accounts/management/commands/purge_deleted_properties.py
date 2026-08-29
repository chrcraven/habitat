"""
Hard-purges soft-deleted Properties once their 30-day restore window has
passed — see /docs/open-questions.md ("Soft delete") for the decided shape
(Property-only, 30 days, admin-restorable, cascading).

Run on a schedule (cron / whatever the eventual hosting setup provides —
see /docs/open-questions.md, "Hosting/ops model"); nothing in this repo
schedules it automatically yet, so run it manually
(`manage.py purge_deleted_properties`) until that's decided. Safe to run
as often as you like — a property not yet past its purge_at is left alone.

Property.activities is a real CASCADE (see apps/activities/models.py), so
deleting the Property row itself already takes its activities (and their
photos/species-links/sighting-links) with it. Sighting.property is
SET_NULL instead (a sighting's point may or may not sit inside any drawn
boundary — see apps/sightings/models.py), which would otherwise leave a
purged property's sightings behind as still-visible, now-orphaned records
instead of removing them — the opposite of what was decided ("a hard
delete removes the property *and all its associated records* (sightings,
activities, photos, sighting<->activity links, etc.)"). So this command
explicitly deletes each property's sightings first (their own photos and
any sighting<->activity links cascade from that), then the property.
"""

from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.accounts.models import Property
from apps.sightings.models import Sighting


class Command(BaseCommand):
    help = (
        "Hard-deletes properties that were soft-deleted more than 30 days "
        "ago, along with their sightings (activities cascade automatically)."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="List what would be purged without deleting anything.",
        )

    def handle(self, *args, **options):
        due = Property.all_objects.deleted().filter(deleted_at__lte=timezone.now() - Property.PURGE_AFTER)
        if not due.exists():
            self.stdout.write("Nothing due for purge.")
            return

        for property_ in due:
            label = f"{property_.name} (org: {property_.organization.name}, deleted {property_.deleted_at:%Y-%m-%d})"
            if options["dry_run"]:
                self.stdout.write(f"Would purge: {label}")
                continue
            sighting_count, _ = Sighting.objects.filter(property=property_).delete()
            property_.delete()
            self.stdout.write(
                self.style.SUCCESS(f"Purged: {label} (+{sighting_count} sighting-related rows)")
            )
