"""
Seeds a new Organization's two pieces of org-defined activity reference
data — its status workflow and its activity types — so a solo user isn't
forced to configure anything just to log their first planting. See the
WorkflowState and ActivityType docstrings in models.py and the task log in
/CLAUDE.md; these are working defaults, not decisions
/docs/open-questions.md formally resolved. Revisit if a default set proves
wrong.

Note the seed lists here are the defaults for *new* organizations only.
The equivalent lists that backfilled organizations existing before
activity types became org-defined are frozen inside migration
activities/0003 — deliberately duplicated, since a migration has to keep
describing what it did at the time even after these lists change.
"""

from django.db.models.signals import post_save
from django.dispatch import receiver

from apps.accounts.models import Organization

from .models import ActivityType, WorkflowState

DEFAULT_WORKFLOW_STATES = [
    {"name": "Planned", "is_planned": True, "is_done": False, "order": 0},
    {"name": "In Progress", "is_planned": False, "is_done": False, "order": 1},
    {"name": "Done", "is_planned": False, "is_done": True, "order": 2},
]

# The eight types that were the fixed enum through Phase 1, now just an
# org's starting point — written in the proper Title Case labels the enum
# always carried but never actually exposed to the client.
DEFAULT_ACTIVITY_TYPES = [
    "Seeding",
    "Planting",
    "Treatment",
    "Removal",
    "Monitoring",
    "Maintenance",
    "Intervention (general)",
    "Other",
]


@receiver(post_save, sender=Organization)
def seed_default_workflow_states(sender, instance, created, **kwargs):
    if not created:
        return
    WorkflowState.objects.bulk_create(
        WorkflowState(organization=instance, **state) for state in DEFAULT_WORKFLOW_STATES
    )


@receiver(post_save, sender=Organization)
def seed_default_activity_types(sender, instance, created, **kwargs):
    if not created:
        return
    ActivityType.objects.bulk_create(
        ActivityType(organization=instance, name=name, order=order)
        for order, name in enumerate(DEFAULT_ACTIVITY_TYPES)
    )
