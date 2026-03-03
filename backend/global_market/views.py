from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import GlobalMarket
from .serializers import GlobalMarketSerializer


class LatestGlobalMarketView(generics.GenericAPIView):
    """
    GET /api/global-market/latest/?date=YYYY-MM-DD
    Returns the latest GlobalMarket entry, or a specific date if provided.
    """
    serializer_class = GlobalMarketSerializer
    permission_classes = (IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        date_str = request.query_params.get('date')

        if date_str:
            try:
                gm = GlobalMarket.objects.get(date=date_str)
            except (GlobalMarket.DoesNotExist, ValueError):
                return Response(
                    {'detail': 'No data for the requested date.'},
                    status=404,
                )
        else:
            gm = GlobalMarket.objects.order_by('-date').first()
            if gm is None:
                return Response(
                    {'detail': 'No global market data available.'},
                    status=404,
                )

        return Response(self.get_serializer(gm).data)
