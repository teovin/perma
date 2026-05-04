from perma.models import CaptureJob

from ..serializers import CaptureJobSerializer
from .base import BaseView


# /capture_jobs
class CaptureJobListView(BaseView):
    serializer_class = CaptureJobSerializer

    def get(self, request, format=None):
        """ List capture_jobs for user. """
        queryset = CaptureJob.objects.select_related('link').filter(link__created_by_id=request.user.pk, status__in=['pending', 'in_progress'])
        return self.simple_list(request, queryset)


# /capture_jobs/:id
# /capture_jobs/:guid
class CaptureJobDetailView(BaseView):
    serializer_class = CaptureJobSerializer

    def get(self, request, pk=None, guid=None, format=None):
        """ Single capture_job details. """
        if guid:
            # We were called as /capture_jobs/:guid
            # Return capture_job for given link_id
            obj = self.get_object_for_user(request.user, CaptureJob.objects.filter(link_id=guid).select_related('link'))
            return self.simple_get(request, obj=obj)
        else:
            # We were called as /capture_jobs/:id
            return self.simple_get(request, pk)


