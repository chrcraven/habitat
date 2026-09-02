from django.db.models import F, Q
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from apps.accounts.org_scoping import OrganizationScopedViewSet

from .models import Species, bloom_ordinal
from .serializers import SpeciesSerializer


class SpeciesViewSet(OrganizationScopedViewSet):
    queryset = Species.objects.all().order_by("common_name")
    serializer_class = SpeciesSerializer

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
