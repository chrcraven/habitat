"""Add the photo digest column on SightingPhoto (D33) and backfill it.

Mirror of apps/activities/migrations/0005 — see that file for why the hash
is computed in Postgres and why schema and data are one migration.
"""

from django.db import migrations, models

BACKFILL = """
    UPDATE sightings_sightingphoto
       SET image_sha256 = encode(sha256(image), 'hex')
     WHERE image IS NOT NULL
       AND image_sha256 = '';
"""

UNFILL = "UPDATE sightings_sightingphoto SET image_sha256 = '';"


class Migration(migrations.Migration):

    dependencies = [
        ("sightings", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="sightingphoto",
            name="image_sha256",
            field=models.CharField(blank=True, max_length=64),
        ),
        migrations.RunSQL(BACKFILL, reverse_sql=UNFILL),
    ]
