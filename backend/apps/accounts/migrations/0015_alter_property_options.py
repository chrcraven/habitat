"""Give the property list a defined order (D70).

`Property` was the only user-facing list model with no ordering at any
layer — not on the model, not on PropertyViewSet's queryset, and not
client-side. So the list came back in Postgres heap order, and an
ordinary UPDATE (a rename, the landing-page select, a theme save, or a
restore from Recently deleted, which clears `deleted_at`) relocated that
property to the bottom of its owner's own list. Meanwhile the *public*
organization page has ordered the same list by name since it was built.

`["name", "id"]` rather than `["name"]`: there is no name-uniqueness
constraint on this model, so two properties in one org can share a name,
and a tie under a non-total order lets two identical requests disagree.

Options-only: no table rewrite, no data change. Same shape as
accounts/0013 (Membership) and notifications/0002 (Notification).
"""

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0014_organization_theme_header_image_sha256_and_more"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="property",
            options={"ordering": ["name", "id"], "verbose_name_plural": "properties"},
        ),
    ]
