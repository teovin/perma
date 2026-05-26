from datetime import timedelta

from django.conf import settings
from django.db.models import Count
from django.db.models.functions import TruncDate
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.utils import timezone
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from perma.models import Link

from ..serializers import InternalDailyLinkCountsQuerySerializer


# /api/
class DeveloperDocsView(APIView):
    def get(self, request, format=None):
        """
        reverse to Developer Docs to fetch correct url (view) named as 'dev_docs'.
        Redirect to Dev Docs.
        """
        absolute_url_to_redirect_to = f"{ self.request.scheme }://{ settings.HOST }{ reverse('dev_docs', urlconf='perma.urls') }"
        return HttpResponseRedirect(absolute_url_to_redirect_to)


# /internal/daily_link_counts
class InternalDailyLinkCountsView(APIView):
    """
    Returns the number of public archives created per day over a lookback window.
    Accepts query param lookback_period - number of days to look back (default 30, max 365).
    """
    permission_classes = (IsAuthenticated,)

    def get(self, request, format=None):
        serializer = InternalDailyLinkCountsQuerySerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        lookback_period = serializer.validated_data['lookback_period']
        today = timezone.now().date()
        start_date = today - timedelta(days=lookback_period)
        end_date = today - timedelta(days=1)

        rows = (
            Link.objects.discoverable()
            .filter(
                creation_timestamp__date__gte=start_date,
                creation_timestamp__date__lte=end_date,
            )
            .annotate(day=TruncDate('creation_timestamp'))
            .values('day')
            .annotate(count=Count('guid'))
            .order_by('day')
        )
        data = {
            "lookback_period": lookback_period, 
            "counts": [{row['day'].isoformat(): row['count']} for row in rows]
        }
        return Response(data)
