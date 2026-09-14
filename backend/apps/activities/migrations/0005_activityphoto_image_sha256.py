"""Add the photo digest column (D33) and backfill it in one migration.

Schema and data together on purpose, so no half-applied state can exist —
the `0003_activity_type` precedent. A row with a blank digest is served
with no `ETag` at all, i.e. exactly the pre-D33 behaviour, so leaving the
backfill to a later migration would mean every photo that already existed
stayed permanently uncacheable while new ones were fine: a half-fix that
looks complete because every new upload works.

The hash is computed **by Postgres**, not in Python. The obvious loop —
iterate the rows, hash `photo.image`, save — would pull every stored photo
through the migration process, and D32 measured what that table is on
track to hold (tens of gigabytes for a small org). `encode(sha256(...))`
keeps the bytes in the database. It is Postgres-specific, which this
project already is unreservedly: GeoDjango against PostGIS is a decided,
documented requirement, not a swappable backend. `sha256()` needs
PostgreSQL 11+; the pinned image is 16.

Reverse blanks the column rather than trying to be clever: un-applying
this migration drops it in the next operation anyway, and a reversible
no-op would make `sqlmigrate --backwards` read as if data were preserved.
"""

from django.db import migrations, models

BACKFILL = """
    UPDATE activities_activityphoto
       SET image_sha256 = encode(sha256(image), 'hex')
     WHERE image IS NOT NULL
       AND image_sha256 = '';
"""

UNFILL = "UPDATE activities_activityphoto SET image_sha256 = '';"


class Migration(migrations.Migration):

    dependencies = [
        ("activities", "0004_unique_activity_species"),
    ]

    operations = [
        migrations.AddField(
            model_name="activityphoto",
            name="image_sha256",
            field=models.CharField(blank=True, max_length=64),
        ),
        migrations.RunSQL(BACKFILL, reverse_sql=UNFILL),
    ]
