from django.urls import path
from .views import *

urlpatterns = [
    path('trading-volume-list/', trading_volume_list, name='trading-volumes'),
    # path('trading-volume-dashboard-list/', trading_volume_dashboard_list, name='trading-volume-dashboard'),
    path('trading_volume_currency_list/', trading_volume_currency_list, name='trading_volume_currency_list'),
    path('trading_volume_list/', trading_volume_list, name='trading_volume_list'),
    path('market_trading_volume_list/', market_trading_volume_list, name='market_trading_volume_list'),
    path('trading_volume_asset_percentage/', trading_volume_asset_percentage, name='trading_volume_asset_percentage'),

    # path('fee-volume-all/', fee_volume_all, name='all-fee-volumes'),
    # path('trading-volume-dashboard-list/', trading_volume_dashboard_list, name='trading-volume-dashboard'),
    path('fee_volume_currency_list/', fee_volume_currency_list, name='fee_volume_currency_list'),
    path('fee_volume_list/', fee_volume_list, name='fee_volume_list'),
    path('market_fee_volume_list/', market_fee_volume_list, name='market_fee_volume_list'),
    path('fee_volume_asset_percentage/', fee_volume_asset_percentage, name='fee_volume_asset_percentage'),
    path('lens/events-summary/', LensEventsSummaryView.as_view(), name='lens-events-summary'),

]
