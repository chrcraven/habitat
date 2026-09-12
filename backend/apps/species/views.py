from django.db import IntegrityError
from django.db.models import F, Q
from django.utils import timezone
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from apps.accounts.org_scoping import OrganizationScopedViewSet
from apps.activities.models import ActivitySpecies

from .models import Species, bloom_ordinal
from .serializers import SpeciesSerializer


class SpeciesViewSet(OrganizationScopedViewSet):
    queryset = Species.objects.all().order_by("common_name")
    serializer_class = SpeciesSerializer

    def get_serializer_context(self):
        # SpeciesSerializer.validate_common_name's duplicate check needs
        # the org, which never comes from the request body — same as
        # ActivityTypeViewSet and WorkflowStateViewSet.
        context = super().get_serializer_context()
        context["organization"] = self.get_organization()
        return context

    def perform_create(self, serializer):
        """The validator above gives the good message; the database is what
        actually enforces uniqueness, and between the two there is a window
        (a stale client list, two tabs, two members adding the same name at
        once). Without this that window is still a 500 — the constraint
        fires, nothing converts it. The check alone would be the D18
        mistake in reverse: a nicer message that leaves the real failure
        mode exactly as loud as it was.
        """
        try:
            super().perform_create(serializer)
        except IntegrityError:
            raise ValidationError({"common_name": "You already have a species with that name."})

    def perform_update(self, serializer):
        """Renaming onto an existing name has the identical window — and
        the identical 500 — so it gets the identical treatment. (Safe to
        catch here because settings.py sets no ATOMIC_REQUESTS, so the
        failed INSERT/UPDATE autocommits on its own rather than poisoning
        a surrounding transaction.)"""
        try:
            super().perform_update(serializer)
        except IntegrityError:
            raise ValidationError({"common_name": "You already have a species with that name."})

    def get_queryset(self):
        """`?blooming_on=MM-DD` (or `?blooming_on=today`) narrows the list
        to species in bloom on that day — the filter the bloom range was
        added for (owner, 2026-09-02).

        The wrap case is the whole reason this isn't a plain BETWEEN: a
        species blooming November to February has `bloom_start` *greater*
        than `bloom_end`, and for those the period is everything from the
        start to year-end plus everything from year-start to the end.
        Species.blooms_on is the same rule in Python; keep the two in step.
        """
        qs = super().get_queryset()
        raw = self.request.query_params.get("blooming_on")
        if not raw:
            return qs
        ordinal = self._parse_blooming_on(raw)
        in_season = Q(bloom_start__lte=ordinal, bloom_end__gte=ordinal)
        wraps_the_year = Q(bloom_start__gt=F("bloom_end")) & (
            Q(bloom_start__lte=ordinal) | Q(bloom_end__gte=ordinal)
        )
        return qs.filter(
            Q(bloom_start__isnull=False, bloom_end__isnull=False)
            & (in_season | wraps_the_year)
        )

    def destroy(self, request, *args, **kwargs):
        """Both FKs into Species are PROTECT — `Sighting.species` and
        `ActivitySpecies.species` — so deleting a species that's in use
        raises ProtectedError. Nothing converts that: it subclasses
        IntegrityError, not APIException, DRF's exception_handler returns
        None for it, and there's no custom EXCEPTION_HANDLER — so it
        reached the user as a 500 from the ordinary Delete button.

        Same guard and same reasoning as WorkflowStateViewSet.destroy and
        ActivityTypeViewSet.destroy (apps/activities/views.py). Species is
        the third per-org reference list and was the only one without it.

        Unlike those two the count spans *two* relations, so the message
        names both — an admin told only "3 records" has to go hunting
        across two different pages to find them.
        """
        instance = self.get_object()

        sightings = instance.sightings.count()
        # Distinct activities, not through-rows. This was originally a
        # workaround: ActivitySpecies had no unique constraint on
        # (activity, species), so a plain row count could overstate how many
        # activities there were to go and fix. D18 (2026-09-10) added the
        # constraint, so the two counts now agree — but `distinct()` stays,
        # because counting *activities* is what this message claims to do,
        # and that shouldn't silently depend on a constraint declared in
        # another app.
        activities = (
            ActivitySpecies.objects.filter(species=instance)
            .values("activity_id")
            .distinct()
            .count()
        )

        if sightings or activities:
            parts = []
            if sightings:
                parts.append(f"{sightings} sighting{'' if sightings == 1 else 's'}")
            if activities:
                parts.append(f"{activities} activit{'y' if activities == 1 else 'ies'}")
            verb = "uses" if sightings + activities == 1 else "use"
            return Response(
                {
                    "detail": (
                        f"{' and '.join(parts)} still {verb} this species. "
                        "Change or remove them first."
                    )
                },
                status=400,
            )
        return super().destroy(request, *args, **kwargs)

    @staticmethod
    def _parse_blooming_on(raw):
        value = raw.strip()
        if value.lower() == "today":
            today = timezone.localdate()
            return bloom_ordinal(today.month, today.day)
        parts = value.split("-")
        if len(parts) != 2 or not all(p.isdigit() for p in parts):
            raise ValidationError({"blooming_on": "Use MM-DD, e.g. 05-01, or 'today'."})
        month, day = int(parts[0]), int(parts[1])
        if not (1 <= month <= 12 and 1 <= day <= 31):
            raise ValidationError({"blooming_on": "That isn't a valid month/day."})
        return bloom_ordinal(month, day)
