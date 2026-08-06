from django.urls import path
from .views import *

urlpatterns = [
    path('api/account-version-snapshot-list/', AccountVersionSnapshotListAPIView.as_view(), name='account-version-snapshot-list'),
    path('api/account-version-snapshot/by-period/', balance_snapshot_by_period, name='account-version-snapshot-by-period'),
    path('api/accounts-snapshot-lp-list/', AccountSnapshotLpListView.as_view(), name='accounts-snapshot-lp-list'),
    path('api/public-orderbook-list/', PublicOrderbookSnapshotListView.as_view(), name='public-orderbook-list'),
]
