from apps.accounts.org_scoping import OrganizationScopedViewSet

from .models import Species
from .serializers import SpeciesSerializer


class SpeciesViewSet(OrganizationScopedViewSet):
    queryset = Species.objects.all().order_by("common_name")
    serializer_class = SpeciesSerializer
