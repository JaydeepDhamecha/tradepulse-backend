from django.urls import path

from .views import IntradaySignalView, TopDeliveryView, VolumeSpikeView

app_name = 'stocks'

urlpatterns = [
    path('top-delivery/', TopDeliveryView.as_view(), name='top-delivery'),
    path('volume-spike/', VolumeSpikeView.as_view(), name='volume-spike'),
    path('intraday-signals/', IntradaySignalView.as_view(), name='intraday-signals'),
]
