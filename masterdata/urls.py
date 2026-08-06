from django.urls import path
from .views import *

urlpatterns = [
    path('api/assets/', AssetListAPIView.as_view(), name='asset-list'),
    path('api/listed-assets/', listed_asset_symbols, name='listed-assets'),
    path('api/local-fiat/', local_fiat, name='local-fiat'),
    path('api/lp-master/', LpMasterListAPIView.as_view(), name='lp-master'),
    path('api/markets/', market_list, name='market-list'),
    path('api/dashboard-alerts/', DashboardAlertView.as_view(), name='dashboard-alerts'),
    path('api/dashboard-active-rulesets/', ActiveRulesetListView.as_view(), name='dashboard-active-rulesets')
]
