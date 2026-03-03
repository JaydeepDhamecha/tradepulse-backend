import logging
from datetime import date, timedelta

from django.utils import timezone
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import GlobalMarket
from .serializers import GlobalMarketSerializer

logger = logging.getLogger(__name__)

# Auto-refresh if data is older than 5 minutes
_REFRESH_INTERVAL = timedelta(minutes=5)


class LatestGlobalMarketView(generics.GenericAPIView):
    """
    GET /api/global-market/latest/?date=YYYY-MM-DD

    - Without ?date → fetches fresh data from Yahoo Finance (cached 5 min)
    - With ?date    → returns stored data for that date from DB
    """
    serializer_class = GlobalMarketSerializer
    permission_classes = (IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        date_str = request.query_params.get('date')

        if date_str:
            # Historical date — serve from DB only
            try:
                gm = GlobalMarket.objects.get(date=date_str)
            except (GlobalMarket.DoesNotExist, ValueError):
                return Response(
                    {'detail': 'No data for the requested date.'},
                    status=404,
                )
            return Response(self.get_serializer(gm).data)

        # Latest — fetch fresh data if stale
        today = date.today()
        gm = GlobalMarket.objects.order_by('-date').first()

        needs_refresh = (
            gm is None
            or (timezone.now() - gm.updated_at) > _REFRESH_INTERVAL
        )

        if needs_refresh:
            gm = self._refresh_global_data(today, gm)

        if gm is None:
            return Response(
                {'detail': 'No global market data available.'},
                status=404,
            )

        return Response(self.get_serializer(gm).data)

    @staticmethod
    def _refresh_global_data(today, existing_gm):
        """Fetch fresh data from Yahoo Finance and recalculate bias."""
        try:
            from global_market.services import (
                fetch_global_market_data,
                calculate_market_bias_for_date,
            )

            target = existing_gm.date if existing_gm else today
            gm = fetch_global_market_data(target)
            calculate_market_bias_for_date(target)
            gm.refresh_from_db()
            logger.info("Auto-refreshed global market data for %s", target)
            return gm
        except Exception as exc:
            logger.warning("Auto-refresh failed: %s", exc)
            return existing_gm
