import calendar

from rest_framework import serializers

from .models import BLOOM_MAX, BLOOM_MIN, Species, bloom_ordinal, bloom_parts


class BloomDateField(serializers.CharField):
    """One end of a bloom period, as `MM-DD`.

    A bloom period repeats every year, so neither end has one — see
    Species.bloom_start. Serving these as `MM-DD` rather than as the MMDD
    integer they're stored as keeps that explicit at the API boundary: a
    client can't mistake `501` for a date and try to do year arithmetic
    with it, and `05-01` reads as what it is.

    February 29 is accepted. It's a real bloom date in a leap year, and
    since the stored value carries no year there's nothing to validate it
    against — so day-of-month validation uses a leap year deliberately.
    """

    #: Any leap year — used only to bound day-of-month, never stored.
    _REFERENCE_LEAP_YEAR = 2000

    def __init__(self, **kwargs):
        kwargs.setdefault("allow_null", True)
        kwargs.setdefault("required", False)
        super().__init__(**kwargs)

    def to_representation(self, value):
        month, day = bloom_parts(value)
        if month is None:
            return None
        return f"{month:02d}-{day:02d}"

    def to_internal_value(self, data):
        if data in (None, ""):
            return None
        text = str(data).strip()
        parts = text.split("-")
        if len(parts) != 2 or not all(p.isdigit() for p in parts):
            raise serializers.ValidationError("Use MM-DD, e.g. 05-01 for May 1.")
        month, day = int(parts[0]), int(parts[1])
        if not 1 <= month <= 12:
            raise serializers.ValidationError("Month must be between 01 and 12.")
        last_day = calendar.monthrange(self._REFERENCE_LEAP_YEAR, month)[1]
        if not 1 <= day <= last_day:
            raise serializers.ValidationError(f"Day must be between 01 and {last_day:02d}.")
        ordinal = bloom_ordinal(month, day)
        if not BLOOM_MIN <= ordinal <= BLOOM_MAX:
            raise serializers.ValidationError("That isn't a valid month/day.")
        return ordinal


class SpeciesSerializer(serializers.ModelSerializer):
    """Note this serializer is served **unauthenticated**: SightingSerializer
    nests it as `species_detail`, and apps/public_site/views.py serves
    public sightings through that. Every field added here reaches the
    public site — which is intended for `description` and the bloom range
    (owner decision, 2026-09-02: species detail shows on a sighting on the
    public property page), but is the reason not to add anything here that
    an org would expect to stay internal."""

    bloom_start = BloomDateField()
    bloom_end = BloomDateField()

    class Meta:
        model = Species
        fields = [
            "id",
            "common_name",
            "scientific_name",
            "description",
            "bloom_start",
            "bloom_end",
            "created_at",
        ]

    def validate_common_name(self, value):
        """Reject a duplicate name with a 400 rather than a 500 (D26).

        The UniqueConstraint is on (organization, common_name) and
        `organization` is supplied by the viewset, never the request body,
        so DRF's auto-generated unique-together validator can't see it and
        isn't built. Nothing else converted the resulting IntegrityError
        either — it subclasses neither APIException nor Django's
        ValidationError, DRF's exception_handler returns None for it, and
        there is no custom EXCEPTION_HANDLER — so adding a species you
        already have reached the user as an unhandled **500**. Measured,
        not assumed: POST {"common_name": "Crabgrass"} twice returns 201
        then 500. Same class and same remedy as the guards on
        WorkflowStateSerializer and ActivityTypeSerializer.

        **This one matches exactly where its two siblings match
        case-insensitively, and that difference is deliberate — don't
        "fix" it for consistency.** Those use `name__iexact`, which is
        itself stricter than their own case-sensitive constraints; the
        mismatch is a recorded, deliberately un-queued item because
        closing it needs a `Lower()` functional constraint *and* a
        decision about existing differently-cased rows (2026-09-10 (3):
        "a product call. Recommendation: not now."). Today
        `Species.objects` accepts "crabgrass" alongside "Crabgrass" —
        verified, 201 — and making this check `iexact` would start
        rejecting that, settling the owner's open question as a side
        effect of a 500 fix. So this converts the error and changes
        nothing else.
        """
        name = value.strip()
        if not name:
            raise serializers.ValidationError("A common name is required.")
        organization = self.context.get("organization")
        if organization is not None:
            clashes = Species.objects.filter(organization=organization, common_name=name)
            if self.instance is not None:
                clashes = clashes.exclude(pk=self.instance.pk)
            if clashes.exists():
                raise serializers.ValidationError("You already have a species with that name.")
        return name

    def validate(self, attrs):
        # A range needs both ends: one alone can't be filtered on and
        # can't be displayed as a period. Merge against the instance so a
        # PATCH that only sends one end is judged on the resulting state,
        # not on the request body alone.
        start = attrs.get("bloom_start", getattr(self.instance, "bloom_start", None))
        end = attrs.get("bloom_end", getattr(self.instance, "bloom_end", None))
        if (start is None) != (end is None):
            raise serializers.ValidationError(
                {"bloom_end": "Give both a start and an end for the bloom period, or neither."}
            )
        # Deliberately no start <= end check — a bloom period may wrap the
        # year (November to February). See Species.bloom_start.
        return attrs
