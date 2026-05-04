from rest_framework.response import Response

from ..serializers import LinkUserSerializer
from ..utils import load_parent
from .base import BaseView


# /user
class LinkUserView(BaseView):
    serializer_class = LinkUserSerializer

    @load_parent
    def get(self, request, format=None):
        """Get current user details."""
        serializer = self.serializer_class(request.user)
        return Response(serializer.data)
