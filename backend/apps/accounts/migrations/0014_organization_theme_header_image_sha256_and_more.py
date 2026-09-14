"""Add the theme-banner digest column on Organization and Property (D33),
and backfill both.

See apps/activities/migrations/0005 for why the hash is computed in
Postgres rather than in Python, and why schema and data share one
migration.

`theme_header_image` is nullable here (unlike a photo's `image`), so the
`IS NOT NULL` guard is doing real work: an org that has never set a banner
keeps a blank digest, which is right — there is nothing to validate
against, and the serving view 404s on the content-type column before it
ever looks at this one.
"""

from django.db import migrations, models


def _backfill(table):
    return f"""
        UPDATE {table}
           SET theme_header_image_sha256 = encode(sha256(theme_header_image), 'hex')
         WHERE theme_header_image IS NOT NULL
           AND theme_header_image_sha256 = '';
    """


def _unfill(table):
    return f"UPDATE {table} SET theme_header_image_sha256 = '';"


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0013_alter_membership_options"),
    ]

    operations = [
        migrations.AddField(
            model_name="organization",
            name="theme_header_image_sha256",
            field=models.CharField(blank=True, max_length=64),
        ),
        migrations.AddField(
            model_name="property",
            name="theme_header_image_sha256",
            field=models.CharField(blank=True, max_length=64),
        ),
        migrations.RunSQL(
            _backfill("accounts_organization"),
            reverse_sql=_unfill("accounts_organization"),
        ),
        migrations.RunSQL(
            _backfill("accounts_property"),
            reverse_sql=_unfill("accounts_property"),
        ),
    ]
