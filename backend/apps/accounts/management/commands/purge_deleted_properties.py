"""
Manual/scheduled entry point for the soft-delete purge. The actual work
(and the reasoning about what has to be deleted explicitly vs. what
cascades) lives in apps/accounts/purging.py, which the backend's own
startup script and the "Recently deleted" admin views also call — this
command is the hands-on and cron-friendly way in, not the only performer
it used to be. See that module's docstring, and build-questions.md
(2026-09-04, D1) for why it stopped being the only one.
"""

from django.core.management.base import BaseCommand

from apps.accounts.purging import properties_due_for_purge, purge_due_properties


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
        if options["dry_run"]:
            due = list(properties_due_for_purge())
            if not due:
                self.stdout.write("Nothing due for purge.")
                return
            for property_ in due:
                self.stdout.write(
                    f"Would purge: {property_.name} "
                    f"(org: {property_.organization.name}, "
                    f"deleted {property_.deleted_at:%Y-%m-%d})"
                )
            return

        purged = purge_due_properties()
        if not purged:
            self.stdout.write("Nothing due for purge.")
            return
        for record in purged:
            self.stdout.write(
                self.style.SUCCESS(
                    f"Purged: {record} (+{record.sighting_rows} sighting-related rows)"
                )
            )
