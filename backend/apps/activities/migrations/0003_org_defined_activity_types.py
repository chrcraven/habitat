"""
Activity type: fixed enum -> org-defined table (owner decision,
2026-09-02, answering real user feedback — see /CLAUDE.md's task log and
build-questions.md).

This is deliberately one migration rather than three, because the middle
step is a **data backfill** and the schema either side of it is only
correct together: creating the table and adding the FK is useless without
repointing existing rows, and dropping the old string column before they
are repointed loses the data outright. Running them as one unit means a
half-applied state can't exist.

Order of operations:
  1. create ActivityType,
  2. add a nullable FK alongside the existing string column,
  3. backfill — seed each org's types, then repoint every activity,
  4. drop the string column, rename the FK into its place, make it
     required.

The default type list is frozen here on purpose. apps/activities/signals.py
has its own copy for seeding *new* organizations; that list is allowed to
change later, while this one must keep describing what this migration
actually did.
"""

import django.db.models.deletion
from django.db import migrations, models

#: The Phase-1 `Activity.ActivityType` enum, value -> label, frozen as of
#: this migration. The labels are what an org sees from here on; the
#: values only exist to match what's already stored in the string column.
LEGACY_TYPES = [
    ("seeding", "Seeding"),
    ("planting", "Planting"),
    ("treatment", "Treatment"),
    ("removal", "Removal"),
    ("monitoring", "Monitoring"),
    ("maintenance", "Maintenance"),
    ("intervention", "Intervention (general)"),
    ("other", "Other"),
]


def backfill_activity_types(apps, schema_editor):
    Organization = apps.get_model("accounts", "Organization")
    ActivityType = apps.get_model("activities", "ActivityType")
    Activity = apps.get_model("activities", "Activity")

    label_by_value = dict(LEGACY_TYPES)

    for organization in Organization.objects.all():
        # Seed this org's starting set. get_or_create rather than
        # bulk_create so re-running against a database that somehow
        # already has some of these (a partially-migrated copy, a
        # hand-fixed instance) doesn't trip the uniqueness constraint.
        types_by_name = {}
        for order, (_value, label) in enumerate(LEGACY_TYPES):
            row, _ = ActivityType.objects.get_or_create(
                organization=organization, name=label, defaults={"order": order}
            )
            types_by_name[label] = row

        activities = Activity.objects.filter(organization=organization)
        for activity in activities.only("id", "activity_type"):
            stored = (activity.activity_type or "").strip()
            # A value that isn't one of the eight can only come from a
            # direct database/Django-admin write, but dropping such an
            # activity's type on the floor would silently rewrite real
            # data — so give it a row of its own instead, named from
            # whatever was stored.
            label = label_by_value.get(stored) or stored.replace("_", " ").title() or "Other"
            row = types_by_name.get(label)
            if row is None:
                row, _ = ActivityType.objects.get_or_create(
                    organization=organization,
                    name=label,
                    defaults={"order": len(types_by_name)},
                )
                types_by_name[label] = row
            Activity.objects.filter(pk=activity.pk).update(activity_type_ref=row)


def unbackfill_activity_types(apps, schema_editor):
    """Write the org-defined name back into the string column.

    Only the data half is reversible: a name an org invented after this
    migration has no enum value to go back to, so it round-trips as its
    own lowercased slug rather than being lost. (Reversing the schema half
    — re-adding a non-null column with no default — needs a hand-written
    default anyway; this is here so the data step isn't the thing that
    blocks it.)
    """
    Activity = apps.get_model("activities", "Activity")
    value_by_label = {label: value for value, label in LEGACY_TYPES}

    for activity in Activity.objects.select_related("activity_type_ref"):
        if activity.activity_type_ref is None:
            continue
        name = activity.activity_type_ref.name
        value = value_by_label.get(name) or name.lower().replace(" ", "_")[:20]
        Activity.objects.filter(pk=activity.pk).update(activity_type=value)


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0012_organization_custom_html_allowed"),
        ("activities", "0002_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="ActivityType",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=100)),
                ("order", models.PositiveIntegerField(default=0)),
                (
                    "organization",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="activity_types",
                        to="accounts.organization",
                    ),
                ),
            ],
            options={"ordering": ["organization_id", "order", "name"]},
        ),
        migrations.AddConstraint(
            model_name="activitytype",
            constraint=models.UniqueConstraint(
                fields=("organization", "name"), name="unique_activity_type_per_organization"
            ),
        ),
        migrations.AddField(
            model_name="activity",
            name="activity_type_ref",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="activities",
                to="activities.activitytype",
            ),
        ),
        migrations.RunPython(backfill_activity_types, unbackfill_activity_types),
        migrations.RemoveField(model_name="activity", name="activity_type"),
        migrations.RenameField(
            model_name="activity", old_name="activity_type_ref", new_name="activity_type"
        ),
        migrations.AlterField(
            model_name="activity",
            name="activity_type",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name="activities",
                to="activities.activitytype",
            ),
        ),
    ]
