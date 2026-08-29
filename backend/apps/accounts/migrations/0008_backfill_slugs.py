"""Backfill vanity slugs for organizations/properties created before the
slug fields existed. Uses the same slugify + numeric-suffix-on-collision
logic new rows get via Organization.save()/Property.save() (see
apps/accounts/slugs.py), applied against the historical models so a fresh
migrate on existing data ends with every row carrying a unique slug.
"""

from django.db import migrations

from apps.accounts.slugs import RESERVED_ORG_SLUGS, unique_slug


def backfill(apps, schema_editor):
    Organization = apps.get_model("accounts", "Organization")
    Property = apps.get_model("accounts", "Property")

    for org in Organization.objects.filter(slug__isnull=True).order_by("pk"):
        org.slug = unique_slug(
            Organization, org.name, fallback="org",
            exclude_pk=org.pk, reserved=RESERVED_ORG_SLUGS,
        )
        org.save(update_fields=["slug"])

    for prop in Property.objects.filter(slug__isnull=True).order_by("pk"):
        prop.slug = unique_slug(
            Property, prop.name, fallback="property",
            filters={"organization": prop.organization}, exclude_pk=prop.pk,
        )
        prop.save(update_fields=["slug"])


def noop(apps, schema_editor):
    # Reversing just drops the columns (handled by 0007's reverse); nothing
    # to undo here.
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0007_organization_slug_property_slug_and_more"),
    ]

    operations = [
        migrations.RunPython(backfill, noop),
    ]
