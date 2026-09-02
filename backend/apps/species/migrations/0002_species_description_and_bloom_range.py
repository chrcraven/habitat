"""
Species gains a public description and an annual bloom range (owner
decision, 2026-09-02 — see /CLAUDE.md's task log and build-questions.md).

`notes` -> `description` is a rename, not a new field: the existing field
was already served unauthenticated (SightingSerializer nests
SpeciesSerializer as `species_detail`, which the public site serves), and
no UI ever rendered or wrote it — so the name promised a privacy it never
had. RenameField keeps whatever anyone wrote through Django admin or the
API directly; nothing is dropped.
"""

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("species", "0001_initial"),
    ]

    operations = [
        migrations.RenameField(
            model_name="species", old_name="notes", new_name="description"
        ),
        migrations.AlterField(
            model_name="species",
            name="description",
            field=models.TextField(
                blank=True,
                help_text="Shown publicly wherever this species appears on the public site.",
            ),
        ),
        migrations.AddField(
            model_name="species",
            name="bloom_start",
            field=models.PositiveSmallIntegerField(
                blank=True,
                help_text="Month/day the bloom period starts, stored as MMDD.",
                null=True,
                validators=[
                    django.core.validators.MinValueValidator(101),
                    django.core.validators.MaxValueValidator(1231),
                ],
            ),
        ),
        migrations.AddField(
            model_name="species",
            name="bloom_end",
            field=models.PositiveSmallIntegerField(
                blank=True,
                help_text="Month/day the bloom period ends, stored as MMDD. May be "
                "earlier than bloom_start — a bloom period can wrap the year.",
                null=True,
                validators=[
                    django.core.validators.MinValueValidator(101),
                    django.core.validators.MaxValueValidator(1231),
                ],
            ),
        ),
    ]
