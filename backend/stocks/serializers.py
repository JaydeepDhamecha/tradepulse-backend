from rest_framework import serializers

from .models import IntradaySignal, Stock


class StockSerializer(serializers.ModelSerializer):
    class Meta:
        model = Stock
        fields = (
            'id', 'symbol', 'date',
            'open', 'high', 'low', 'close', 'volume',
            'delivery_percentage', 'open_interest', 'oi_change',
            'price_change_percent', 'volume_spike_ratio',
        )
        read_only_fields = fields


class IntradaySignalSerializer(serializers.ModelSerializer):
    symbol = serializers.CharField(source='stock.symbol', read_only=True)

    class Meta:
        model = IntradaySignal
        fields = (
            'id', 'symbol', 'date',
            'signal_type', 'confidence_score', 'reasoning_summary',
            'created_at',
        )
        read_only_fields = fields
