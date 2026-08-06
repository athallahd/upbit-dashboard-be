from django.urls import path
from .views import *

urlpatterns = [
    path('api/order-base/', OrderListAPIView.as_view(), name='order-list'),
    path('api/order-count/', OrderCountSummaryListView.as_view(), name='order-summary-list'),
    path('api/order-count/<int:pk>/', OrderCountSummaryDetailView.as_view(), name='order-summary-detail'),
    path('api/order-count/by-period/', order_summary_by_period, name='order-summary-by-period'),
    path('api/order-count/stats/', order_summary_stats, name='order-summary-stats'),
    path('api/lp-flag-members/', get_lp_flag_members, name='lp_flag_members'),
    path('api/private-orderbook-depth/', PrivateOrderbookDepthListView.as_view(), name='private-orderbook-depth'),
    path('api/public-orderbook-depth/', PublicOrderbookDepthListView.as_view(), name='public-orderbook-depth'),
    path('api/deposit_withdraw_volumes/', deposit_withdraw_volumes, name='deposit-withdraw-volumes'),
    path('api/currency_list/', deposit_withdraw_currency_list, name='deposit-withdraw-currency-list'),
    path('api/public-orderbook-depth/daily-agg/', PublicOrderbookDepthDailyAggregateView.as_view(), name='public-orderbook-depth-daily-agg'),
    path('api/private-orderbook-depth/daily-agg/', PrivateOrderbookDepthDailyAggregateView.as_view(), name='private-orderbook-depth-daily-agg'),
    path('api/public-orderbook-depth/monthly-agg/', PublicOrderbookDepthMonthlyAggregateView.as_view(), name='public-orderbook-depth-monthly-agg'),
    path('api/private-orderbook-depth/monthly-agg/', PrivateOrderbookDepthMonthlyAggregateView.as_view(), name='private-orderbook-depth-monthly-agg'),
    path('api/lp-evaluation/comparison/', LPEvaluationComparisonView.as_view(), name='lp-evaluation-comparison'),
    path('api/lp-performance/summary/', LPPerformanceSummaryView.as_view(), name='lp-performance-summary'),
    path('api/uptime-performance-summary/', UptimePerformanceSummaryView.as_view(), name='uptime-performance-summary'),
    path('api/uptime-performance-summary2/', UptimePerformanceSummaryView2.as_view(), name='uptime-performance-summary2'),
    path('api/lp-evaluation/comparison2/', LPEvaluationComparisonView2.as_view(), name='lp-evaluation-comparison2'),
]
