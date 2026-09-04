"""Make `Membership.objects.first()` deterministic.

org_scoping.get_active_membership picks a user's active organization with
`user.memberships...first()`. Without an ordering that is whatever row
Postgres hands back first, which can change after any row update — so a
user in two organizations could silently switch orgs between requests.
Options-only: no table rewrite, no data change.
"""

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0012_organization_custom_html_allowed"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="membership",
            options={"ordering": ["created_at", "id"]},
        ),
    ]
