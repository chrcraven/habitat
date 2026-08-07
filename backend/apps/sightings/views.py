from apps.accounts.org_scoping import OrganizationScopedViewSet

from .models import Sighting
from .serializers import SightingSerializer


class SightingViewSet(OrganizationScopedViewSet):
    queryset = Sighting.objects.select_related("species", "property")
    serializer_class = SightingSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        property_id = self.request.query_params.get("property")
        if property_id:
            qs = qs.filter(property_id=property_id)
        return qs

    def perform_create(self, serializer):
        serializer.save(
            organization=self.get_organization(), created_by=self.request.user
        )
