from perma.models import Organization

from ..serializers import OrganizationSerializer
from .base import BaseView


# /organizations
class OrganizationListView(BaseView):
    serializer_class = OrganizationSerializer
    ordering_fields = ('name', 'registrar')

    def get(self, request, format=None):
        """
        List orgs.
        """
        queryset = Organization.objects.accessible_to(request.user).select_related('registrar', 'shared_folder')
        return self.simple_list(request, queryset)


# /organizations/:id
class OrganizationDetailView(BaseView):
    serializer_class = OrganizationSerializer

    def get(self, request, pk, format=None):
        """
        Single org details
        """
        return self.simple_get(request, pk)