from django.db import models
from django.conf import settings


class Stock(models.Model):
    symbol = models.CharField(max_length=20, db_index=True)
    date = models.DateField(db_index=True)
    open = models.DecimalField(max_digits=12, decimal_places=2)
    high = models.DecimalField(max_digits=12, decimal_places=2)
    low = models.DecimalField(max_digits=12, decimal_places=2)
    close = models.DecimalField(max_digits=12, decimal_places=2)
    volume = models.BigIntegerField()
    delivery_percentage = models.DecimalField(
        max_digits=6, decimal_places=2, null=True, blank=True,
    )
    open_interest = models.BigIntegerField(null=True, blank=True)
    previous_open_interest = models.BigIntegerField(null=True, blank=True)
    oi_change = models.BigIntegerField(null=True, blank=True)
    price_change_percent = models.DecimalField(
        max_digits=8, decimal_places=4, null=True, blank=True,
    )
    volume_spike_ratio = models.DecimalField(
        max_digits=8, decimal_places=4, null=True, blank=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'stocks'
        ordering = ['-date', 'symbol']
        unique_together = [['symbol', 'date']]

    def __str__(self):
        return f"{self.symbol} — {self.date}"


class IntradaySignal(models.Model):
    class SignalType(models.TextChoices):
        BUY = 'BUY', 'Buy'
        SELL = 'SELL', 'Sell'
        HOLD = 'HOLD', 'Hold'

    stock = models.ForeignKey(
        Stock,
        on_delete=models.CASCADE,
        related_name='signals',
    )
    date = models.DateField(db_index=True)
    signal_type = models.CharField(
        max_length=4,
        choices=SignalType.choices,
    )
    confidence_score = models.DecimalField(max_digits=5, decimal_places=2)
    reasoning_summary = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'intraday_signals'
        ordering = ['-date', '-confidence_score']
        unique_together = [['stock', 'date', 'signal_type']]

    def __str__(self):
        return f"{self.stock.symbol} {self.signal_type} ({self.confidence_score}%) — {self.date}"
