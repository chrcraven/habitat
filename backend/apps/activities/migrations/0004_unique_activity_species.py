"""
Put a unique constraint behind ActivitySpecies' "already linked" guard
(D18 — see /docs/open-questions.md and build-questions.md).

`activity_species_list`'s POST has always rejected a duplicate species on
an activity with a 400, but it does so via `get_or_create`, which is an
unlocked SELECT-then-INSERT. That is only race-safe when the database can
reject the loser's INSERT; with no constraint, two concurrent POSTs both
succeed and the pair ends up with two rows, after which every later POST
for it raises MultipleObjectsReturned — a 500 that never clears on its
own. See ActivitySpecies.Meta for the full mechanism.

This is deliberately one migration rather than two, because AddConstraint
fails outright on a database that already holds duplicates: the dedupe and
the constraint are only correct together, and running them as one unit
means a half-applied state can't exist. Same reasoning as
0003_org_defined_activity_types.

Dedupe rule: keep the lowest id for each (activity, species) pair and
delete the rest. The kept row is the one the app itself would have
returned — `get_or_create`'s own `get()` on a duplicated pair is what
raises today, and every other read path (`species_names`, the panel's
list) is ordered by insertion, so the earliest row is the one users have
been seeing and editing. The deletions are printed rather than performed
silently, since on a real deployment this is data leaving the database.

Reversing drops the constraint only. Deleted duplicate rows are not
restored — they cannot be, and they were rows the app's own stated rule
said should never have existed.
"""

from django.db import migrations, models


def drop_duplicate_activity_species(apps, schema_editor):
    ActivitySpecies = apps.get_model("activities", "ActivitySpecies")

    seen = set()
    doomed = []
    # Ordered by id so the first row seen for a pair is the lowest-id one,
    # i.e. the row that is kept.
    for link_id, activity_id, species_id in ActivitySpecies.objects.order_by("id").values_list(
        "id", "activity_id", "species_id"
    ):
        pair = (activity_id, species_id)
        if pair in seen:
            doomed.append(link_id)
        else:
            seen.add(pair)

    if doomed:
        print(
            f"\n  D18: removing {len(doomed)} duplicate ActivitySpecies row(s) "
            f"before adding the unique constraint (ids: {doomed})"
        )
        ActivitySpecies.objects.filter(id__in=doomed).delete()


def noop_reverse(apps, schema_editor):
    """Deleted duplicates aren't restorable, and shouldn't be — the app's
    own rule always said one row per (activity, species) pair."""


class Migration(migrations.Migration):
    dependencies = [
        ("activities", "0003_org_defined_activity_types"),
    ]

    operations = [
        migrations.RunPython(drop_duplicate_activity_species, noop_reverse),
        migrations.AddConstraint(
            model_name="activityspecies",
            constraint=models.UniqueConstraint(
                fields=["activity", "species"], name="unique_activity_species"
            ),
        ),
    ]
