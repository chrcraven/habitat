"""
Seeds a default activity-status workflow for every new Organization, so a
solo user isn't forced to design a workflow just to log their first
planting. See the WorkflowState docstring in models.py and the task log in
/CLAUDE.md — this is a Phase-1 assumption, not something
/docs/open-questions.md formally resolved; revisit if the default set
proves wrong.
"""

from django.db.models.signals import post_save
from django.dispatch import receiver

from apps.accounts.models import Organization

from .models import WorkflowState

DEFAULT_WORKFLOW_STATES = [
    {"name": "Planned", "is_planned": True, "is_done": False, "order": 0},
    {"name": "In Progress", "is_planned": False, "is_done": False, "order": 1},
    {"name": "Done", "is_planned": False, "is_done": True, "order": 2},
]


@receiver(post_save, sender=Organization)
def seed_default_workflow_states(sender, instance, created, **kwargs):
    if not created:
        return
    WorkflowState.objects.bulk_create(
        WorkflowState(organization=instance, **state) for state in DEFAULT_WORKFLOW_STATES
    )
