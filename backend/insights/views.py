from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import Insight
from .serializers import InsightSerializer


class DailyInsightView(generics.GenericAPIView):
    """
    GET /api/insights/daily/?date=YYYY-MM-DD
    Returns the insight for a specific date, or the most recent one.
    """
    serializer_class = InsightSerializer
    permission_classes = (IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        date_str = request.query_params.get('date')

        if date_str:
            try:
                insight = Insight.objects.get(date=date_str)
            except (Insight.DoesNotExist, ValueError):
                return Response(
                    {'detail': 'No insight for the requested date.'},
                    status=404,
                )
        else:
            insight = Insight.objects.order_by('-date').first()
            if insight is None:
                return Response(
                    {'detail': 'No insights available.'},
                    status=404,
                )

        return Response(self.get_serializer(insight).data)
