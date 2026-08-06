# views.py
import calendar
import logging
from collections import defaultdict
from datetime import date, datetime, timedelta

import pandas as pd
import pytz
from dateutil.relativedelta import relativedelta
from django.conf import settings
from django.db.models import Avg, Count, Sum
from django.db.models.functions import (TruncDay, TruncMonth, TruncWeek,
                                        TruncYear)
from django_filters import DateFilter, DateFromToRangeFilter, FilterSet
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, generics, status
from rest_framework.decorators import api_view
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.response import Response
from rest_framework.views import APIView

from lens_data.models.data import (DepositBase, WithdrawBase,
                                   OrderBase, OrderCountSummary,
                                   PrivateOrderbookDepth, PublicOrderbookDepth,
                                   UserInfo, 
                                   DepositBaseJoinAssetMaster, WithdrawBaseJoinAssetMaster)
from lens_data.serializers import (DepositVolumeSerializer,
                                   LPEvaluationComparisonSerializer,
                                   OrderCountSummarySerializer,
                                   OrderSerializer,
                                   PrivateOrderbookDepthSerializer,
                                   PublicOrderbookDepthSerializer,
                                   WithdrawVolumeSerializer)
from .serializers import DepositVolumeSerializer, WithdrawVolumeSerializer
from lens_monitoring.views import all_ticker_chach
from masterdata.models.sec import LpMaster, MarketCategory
from lens.simple_query import *


# BP levels in order (for interval calculations)
BP_LEVELS = ['12_5', '25', '37_5', '50', '100', '200', '400', '800']

logger = logging.getLogger(__name__)

# Range names matching the levels
RANGE_NAMES = [
    'sum_0_12.5',
    'sum_12.5_25', 
    'sum_25_37.5',
    'sum_37.5_50',
    'sum_50_100',
    'sum_100_200',
    'sum_200_400',
    'sum_400_800',
]

# Mapping from LpMaster target fields to interval ranges
TARGET_FIELD_MAPPING = {
    'sum_0_12.5': 'target_25bp',
    'sum_12.5_25': 'target_50bp',
    'sum_25_37.5': 'target_75bp',
    'sum_37.5_50': 'target_100bp',
    'sum_50_100': 'target_200bp',
    'sum_100_200': 'target_400bp',
    'sum_200_400': 'target_800bp',
    'sum_400_800': 'target_1600bp',
}


class OrderFilter(FilterSet):
    order_date = DateFilter(field_name='order_date')
    order_date_from = DateFilter(field_name='order_date', lookup_expr='gte')
    order_date_to = DateFilter(field_name='order_date', lookup_expr='lte')
    order_date_range = DateFromToRangeFilter(field_name='order_date')
    
    class Meta:
        model = OrderBase
        fields = ['order_date', 'customer_code', 'is_buy', 'order_status', 'currency_id', 'asset_id']


class OrderListAPIView(generics.ListAPIView):
    queryset = OrderBase.objects.all()
    serializer_class = OrderSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_class = OrderFilter
    ordering_fields = ['order_date', 'order_datetime', 'order_price']
    ordering = ['-order_date']


class OrderCountSummaryListView(generics.ListAPIView):
    queryset = OrderCountSummary.objects.all()
    serializer_class = OrderCountSummarySerializer
    filter_backends = [DjangoFilterBackend, OrderingFilter, SearchFilter]
    filterset_fields = ['asset_id', 'currency_id', 'customer_code']
    search_fields = ['asset_id', 'currency_id', 'customer_code']
    ordering_fields = ['order_date', 'total_orders', 'buy_orders', 'sell_orders']
    ordering = ['-order_date']

    def get_queryset(self):
        queryset = OrderCountSummary.objects.all()
        
        # Date range filtering with current date as default end_date
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        
        if start_date:
            try:
                start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
                queryset = queryset.filter(order_date__gte=start_date)
            except ValueError:
                pass
        
        if end_date:
            try:
                end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
                queryset = queryset.filter(order_date__lte=end_date)
            except ValueError:
                pass
        else:
            # Default to current date if no end_date provided
            from datetime import date
            queryset = queryset.filter(order_date__lte=date.today())

        return queryset


class OrderCountSummaryDetailView(generics.RetrieveAPIView):
    queryset = OrderCountSummary.objects.all()
    serializer_class = OrderCountSummarySerializer


@api_view(['GET'])
def order_summary_by_period(request):
    """Get order summaries aggregated by period"""
    customer_code = request.query_params.get('customer_code')
    period = request.query_params.get('period', 'daily')  # daily, weekly, monthly, annual
    limit = int(request.query_params.get('limit', 0))  # 0 = no limit, 90 = last 90 points
    start_date = request.query_params.get('start_date')
    end_date = request.query_params.get('end_date')
    asset_id = request.query_params.get('asset_id')
    currency_id = request.query_params.get('currency_id')
    
    if not customer_code:
        return Response({'error': 'customer_code is required'}, status=400)
    
    # First check if customer exists
    customer_exists = OrderCountSummary.objects.filter(customer_code=customer_code).exists()
    if not customer_exists:
        return Response([])
    
    queryset = OrderCountSummary.objects.filter(customer_code=customer_code)
    
    # Apply date filtering
    if start_date:
        try:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
            queryset = queryset.filter(order_date__gte=start_date)
        except ValueError:
            return Response({
                'error': 'Invalid start_date format. Use YYYY-MM-DD',
                'code': 'invalid_date_format'
            }, status=400)
    
    if end_date:
        try:
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
            queryset = queryset.filter(order_date__lte=end_date)
        except ValueError:
            return Response({
                'error': 'Invalid end_date format. Use YYYY-MM-DD',
                'code': 'invalid_date_format'
            }, status=400)
    else:
        # Default to current date if no end_date provided
        queryset = queryset.filter(order_date__lte=date.today())

    if asset_id:
        asset_id_list = asset_id.split(",")
        queryset = queryset.filter(asset_id__in=asset_id_list)
    
    if currency_id:
        currency_id_list = currency_id.split(",")
        queryset = queryset.filter(currency_id__in=currency_id_list)

    # Define date format for all periods
    date_format = {
        'daily': "DATE_FORMAT(order_date, '%%Y-%%m-%%d')",
        'weekly': "DATE_FORMAT(DATE_SUB(order_date, INTERVAL WEEKDAY(order_date) DAY), '%%Y-%%m-%%d')",  # Start of week (Monday)
        'monthly': "DATE_FORMAT(order_date, '%%Y-%%m')",
        'annual': "DATE_FORMAT(order_date, '%%Y')"
    }.get(period)
    
    if not date_format:
        return Response({
            'error': f'Invalid period: {period}. Must be one of: daily, weekly, monthly, annual',
            'code': 'invalid_period'
        }, status=400)
    
    # Perform the aggregation for all periods including daily
    aggregated_data = queryset.extra(
        select={'period': date_format}
    ).values('period', 'asset_id', 'currency_id').annotate(
        total_orders=Sum('total_orders'),
        buy_orders=Sum('buy_orders'),
        sell_orders=Sum('sell_orders'),
        algo_orders=Sum('algo_orders'),
        non_algo_orders=Sum('non_algo_orders')
    ).order_by('period')  # Order by period descending
    
    # Apply limit if specified
    if limit > 0:
        aggregated_data = aggregated_data[:limit]
    
    # Convert to list and calculate percentages
    data = list(aggregated_data)
    
    # Add calculated percentages and week end date for weekly period
    for item in data:
        if item['total_orders'] > 0:
            item['buy_percentage'] = round((item['buy_orders'] * 100.0) / item['total_orders'], 2)
            item['sell_percentage'] = round((item['sell_orders'] * 100.0) / item['total_orders'], 2)
            item['algo_percentage'] = round((item['algo_orders'] * 100.0) / item['total_orders'], 2)
            item['non_algo_percentage'] = round((item['non_algo_orders'] * 100.0) / item['total_orders'], 2)
        
        # Add week end date for weekly period
        if period == 'weekly':
            start_date = datetime.strptime(item['period'], '%Y-%m-%d').date()
            item['week_end'] = (start_date + timedelta(days=6)).strftime('%Y-%m-%d')
            item['period_label'] = f"{item['period']} to {item['week_end']}"
    
    # # Sort by period ascending for final output
    # data.sort(key=lambda x: x['period'])
    
    return Response(data)


@api_view(['GET'])
def order_summary_stats(request):
    """Get aggregated statistics for order summaries"""
    queryset = OrderCountSummary.objects.all()
    
    # Apply date filtering with current date as default end_date
    start_date = request.query_params.get('start_date')
    end_date = request.query_params.get('end_date')
    
    if start_date:
        try:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
            queryset = queryset.filter(order_date__gte=start_date)
        except ValueError:
            pass
    
    if end_date:
        try:
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
            queryset = queryset.filter(order_date__lte=end_date)
        except ValueError:
            pass
    else:
        # Default to current date if no end_date provided
        queryset = queryset.filter(order_date__lte=date.today())

    stats = queryset.aggregate(
        total_records=Count('id'),
        total_orders_sum=Sum('total_orders'),
        total_buy_orders=Sum('buy_orders'),
        total_sell_orders=Sum('sell_orders'),
        total_algo_orders=Sum('algo_orders'),
        total_non_algo_orders=Sum('non_algo_orders'),
        avg_orders_per_record=Avg('total_orders'),
    )
    
    # Add percentages
    if stats['total_orders_sum']:
        stats['overall_buy_percentage'] = round((stats['total_buy_orders'] * 100.0) / stats['total_orders_sum'], 2)
        stats['overall_sell_percentage'] = round((stats['total_sell_orders'] * 100.0) / stats['total_orders_sum'], 2)
        stats['overall_algo_percentage'] = round((stats['total_algo_orders'] * 100.0) / stats['total_orders_sum'], 2)
        stats['overall_non_algo_percentage'] = round((stats['total_non_algo_orders'] * 100.0) / stats['total_orders_sum'], 2)
    
    return Response(stats)


@api_view(['GET'])
def get_lp_flag_members(request):
    """
    API endpoint to return list of member_ids where flag_lp is True
    """
    try:
        # Query users where flag_lp is True and get only member_id values
        member_ids = UserInfo.objects.filter(flag_lp=True).values_list('member_id', flat=True)
        
        # Convert to list for JSON serialization
        member_ids_list = list(member_ids)
        
        return Response({
            'success': True,
            'count': len(member_ids_list),
            'member_ids': member_ids_list
        }, status=status.HTTP_200_OK)
    
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



class PrivateOrderbookDepthListView(generics.ListAPIView):
    """
    API endpoint to filter private orderbook depth by date.
    
    Query Parameters:
    - date: Date in YYYY-MM-DD format (e.g., 2024-11-12)
    - market: Optional market filter
    - member_id: Optional member filter
    
    Example:
    /api/private-orderbook-depth/?date=2024-11-12
    /api/private-orderbook-depth/?date=2024-11-12&market=BTC-USDT&member_id=123
    """
    serializer_class = PrivateOrderbookDepthSerializer
    
    def get_queryset(self):
        queryset = PrivateOrderbookDepth.objects.all()
        
        # Filter by date
        date_str = self.request.query_params.get('date', None)
        if date_str:
            try:
                # Parse the date string
                date_obj = datetime.strptime(date_str, '%Y-%m-%d')
                sgt = pytz.timezone(settings.LOCAL_TIMEZONE)
                start_of_day_sgt = sgt.localize(datetime.combine(date_obj.date(), datetime.min.time()))
                end_of_day_sgt = sgt.localize(datetime.combine(date_obj.date(), datetime.max.time()))
                
                # Convert to unix timestamp range (milliseconds)
                start_of_day = int(start_of_day_sgt.timestamp() * 1000)
                end_of_day = int(end_of_day_sgt.timestamp() * 1000)
                
                queryset = queryset.filter(
                    orderbook_timestamp_unix__gte=start_of_day,
                    orderbook_timestamp_unix__lte=end_of_day
                )
            except ValueError:
                # Invalid date format, return empty queryset
                return queryset.none()
        
        # Optional filters
        market = self.request.query_params.get('market', None)
        if market:
            queryset = queryset.filter(market__iexact=market)
        
        member_id = self.request.query_params.get('member_id', None)
        if member_id:
            queryset = queryset.filter(member_id=member_id)
        
        return queryset.order_by('-orderbook_timestamp_unix')


class PublicOrderbookDepthListView(generics.ListAPIView):
    """
    API endpoint to filter public orderbook depth by date.
    
    Query Parameters:
    - date: Date in YYYY-MM-DD format (e.g., 2024-11-12)
    - market: Optional market filter
    
    Example:
    /api/public-orderbook-depth/?date=2024-11-12
    /api/public-orderbook-depth/?date=2024-11-12&market=BTC-USDT
    """
    serializer_class = PublicOrderbookDepthSerializer
    
    def get_queryset(self):
        queryset = PublicOrderbookDepth.objects.all()
        
        # Filter by date
        date_str = self.request.query_params.get('date', None)
        if date_str:
            try:
                # Parse the date string
                date_obj = datetime.strptime(date_str, '%Y-%m-%d')
                sgt = pytz.timezone(settings.LOCAL_TIMEZONE)
                start_of_day_sgt = sgt.localize(datetime.combine(date_obj.date(), datetime.min.time()))
                end_of_day_sgt = sgt.localize(datetime.combine(date_obj.date(), datetime.max.time()))
                
                # Convert to unix timestamp range (milliseconds)
                start_of_day = int(start_of_day_sgt.timestamp() * 1000)
                end_of_day = int(end_of_day_sgt.timestamp() * 1000)
                
                queryset = queryset.filter(
                    orderbook_timestamp_unix__gte=start_of_day,
                    orderbook_timestamp_unix__lte=end_of_day
                )
            except ValueError:
                # Invalid date format, return empty queryset
                return queryset.none()
        
        # Optional filter
        market = self.request.query_params.get('market', None)
        if market:
            queryset = queryset.filter(market__iexact=market)
        
        return queryset.order_by('-orderbook_timestamp_unix')


@api_view(['GET'])
def deposit_withdraw_currency_list(request):

    type = request.query_params.get('type') # deposit or withdraw
    if type != 'deposit' and type != 'withdraw' :
        return Response({'error': 'Invalid type parameter'}, status=400)
    
    allTickerChach = all_ticker_chach()
    allTickerChach.append('IDR')
    
    if (type == "deposit") : # 
        currencies = DepositBaseJoinAssetMaster.objects.filter(assetmaster__currency_ticker__in=allTickerChach).values_list('assetmaster__currency_ticker', flat=True).distinct().order_by('assetmaster__currency_ticker')
    elif type == 'withdraw' : 
        currencies = WithdrawBaseJoinAssetMaster.objects.filter(assetmaster__currency_ticker__in=allTickerChach).values_list('assetmaster__currency_ticker', flat=True).distinct().order_by('assetmaster__currency_ticker')

    # print(currencies.query)
    unique_currencies = [c for c in currencies if c is not None]
    return Response(unique_currencies)


# API for retrieving data for the 'Trading Volume Dashboard.'
@api_view(['GET'])
def deposit_withdraw_volumes(request):
        
    period = request.query_params.get('period', 'daily')
    period_end = request.query_params.get('period_end')  # YYYY-MM 
    type = request.query_params.get('type') # deposit or withdraw

    if type != 'deposit' and type != 'withdraw' :
        return Response({'error': 'Invalid type parameter'}, status=400)

    allTickerChach = all_ticker_chach()
    allTickerChach.append('IDR')

    trunc_func_map = {
        'daily': TruncDay,
        'weekly': TruncWeek,
        'monthly': TruncMonth,
        'annual': TruncYear,
    }
    
    trunc_func = trunc_func_map.get(period)
    if trunc_func is None:
        return Response({'error': 'Invalid period parameter'}, status=400)
    

    today = date.today()

    if period_end:
        try:
            end_date_dt = datetime.strptime(period_end, '%Y-%m')
            year = end_date_dt.year
            month = end_date_dt.month

            # Judging by this month
            if year == today.year and month == today.month:
                # This month, today's date is set as end_date
                end_date = today - timedelta(days=1)
            else:
                # If it is a past month, calculate the last day of that month
                last_day = calendar.monthrange(year, month)[1]
                end_date = date(year, month, last_day)
        except ValueError:
            return Response({'error': 'Invalid period_end format. Expected YYYY-MM.'}, status=400)
    else:
        end_date = today

    # Calculate start date
    if period == 'daily':
        # if year == today.year and month == today.month:
            start_date = end_date - relativedelta(days=30)
        # else : 
        #     start_date = date(year, month, 1)
    elif period == 'weekly':
        start_date = end_date - timedelta(weeks=30)
    elif period == 'monthly':
        start_date = end_date - relativedelta(months=30)
    else:
        start_date = None  # yearly or no limit

    if type == 'deposit' : 
        queryset = DepositBaseJoinAssetMaster.objects.annotate(Target_date=trunc_func('target_date'))
    elif type == 'withdraw' : 
        queryset = WithdrawBaseJoinAssetMaster.objects.annotate(Target_date=trunc_func('target_date'))

    if start_date:
        queryset = queryset.filter(assetmaster__currency_ticker__in=allTickerChach, target_date__gte=start_date, target_date__lte=end_date)
    else : 
        queryset = queryset.filter(assetmaster__currency_ticker__in=allTickerChach)

    queryset = queryset.values('Target_date', 'assetmaster__currency_ticker').annotate(volume_sum=Sum('fiat_amount')).order_by('Target_date')

    # print(queryset.query)


    if type == 'deposit' : 
        serializer = DepositVolumeSerializer(queryset, many=True)
    elif type == 'withdraw' : 
        serializer = WithdrawVolumeSerializer(queryset, many=True)

    return Response(serializer.data)


class PublicOrderbookDepthMonthlyAggregateView(generics.ListAPIView):
    """
    API endpoint to get daily averaged orderbook depth for a month.
    
    Query Parameters:
    - month: Month in YYYY-MM format (e.g., 2024-11)
    - market: Required market filter
    
    Returns daily aggregated data where each bp range value is the average
    of all records for that day.
    
    Example:
    /api/public-orderbook-depth/monthly/?month=2024-11&market=BTC-USDT
    """

    queryset = PublicOrderbookDepth.objects.none()
    
    
    def list(self, request, *args, **kwargs):
        month_str = request.query_params.get('month', None)
        market = request.query_params.get('market', None)
        
        # Validate required parameters
        if not month_str:
            return Response(
                {"error": "month parameter is required (format: YYYY-MM)"},
                status=400
            )
        
        if not market:
            return Response(
                {"error": "market parameter is required"},
                status=400
            )
        
        try:
            # Parse the month string
            date_obj = datetime.strptime(month_str, '%Y-%m')
            year = date_obj.year
            month = date_obj.month
            
            # Get timezone
            sgt = pytz.timezone(settings.LOCAL_TIMEZONE)
            
            # Get first and last day of the month
            first_day = sgt.localize(datetime(year, month, 1, 0, 0, 0))
            last_day_num = calendar.monthrange(year, month)[1]
            last_day = sgt.localize(datetime(year, month, last_day_num, 23, 59, 59, 999999))
            
            # Convert to unix timestamp (milliseconds)
            start_timestamp = int(first_day.timestamp() * 1000)
            end_timestamp = int(last_day.timestamp() * 1000)
            
            # Query and aggregate by day
            queryset = PublicOrderbookDepth.objects.filter(
                market__iexact=market,
                orderbook_timestamp_unix__gte=start_timestamp,
                orderbook_timestamp_unix__lte=end_timestamp
            )
            
            # Group by day and calculate averages
            daily_aggregates = []
            
            for day in range(1, last_day_num + 1):
                day_start = sgt.localize(datetime(year, month, day, 0, 0, 0))
                day_end = sgt.localize(datetime(year, month, day, 23, 59, 59, 999999))
                
                day_start_unix = int(day_start.timestamp() * 1000)
                day_end_unix = int(day_end.timestamp() * 1000)
                
                # Filter records for this specific day
                day_records = queryset.filter(
                    orderbook_timestamp_unix__gte=day_start_unix,
                    orderbook_timestamp_unix__lte=day_end_unix
                )
                
                # Calculate aggregates
                aggregates = day_records.aggregate(
                    count=Count('id'),
                    ask_vol_12_5bp=Avg('ask_vol_12_5bp'),
                    bid_vol_12_5bp=Avg('bid_vol_12_5bp'),
                    ask_vol_25bp=Avg('ask_vol_25bp'),
                    bid_vol_25bp=Avg('bid_vol_25bp'),
                    ask_vol_37_5bp=Avg('ask_vol_37_5bp'),
                    bid_vol_37_5bp=Avg('bid_vol_37_5bp'),
                    ask_vol_50bp=Avg('ask_vol_50bp'),
                    bid_vol_50bp=Avg('bid_vol_50bp'),
                    ask_vol_100bp=Avg('ask_vol_100bp'),
                    bid_vol_100bp=Avg('bid_vol_100bp'),
                    ask_vol_200bp=Avg('ask_vol_200bp'),
                    bid_vol_200bp=Avg('bid_vol_200bp'),
                    ask_vol_400bp=Avg('ask_vol_400bp'),
                    bid_vol_400bp=Avg('bid_vol_400bp'),
                    ask_vol_800bp=Avg('ask_vol_800bp'),
                    bid_vol_800bp=Avg('bid_vol_800bp'),
                )
                
                # Only include days that have data
                if aggregates['count'] > 0:
                    daily_aggregates.append({
                        'date': day_start.strftime('%Y-%m-%d'),
                        'market': market,
                        'orderbook_timestamp_unix': day_start_unix,
                        'record_count': aggregates['count'],
                        'ask_vol_12_5bp': aggregates['ask_vol_12_5bp'],
                        'bid_vol_12_5bp': aggregates['bid_vol_12_5bp'],
                        'ask_vol_25bp': aggregates['ask_vol_25bp'],
                        'bid_vol_25bp': aggregates['bid_vol_25bp'],
                        'ask_vol_37_5bp': aggregates['ask_vol_37_5bp'],
                        'bid_vol_37_5bp': aggregates['bid_vol_37_5bp'],
                        'ask_vol_50bp': aggregates['ask_vol_50bp'],
                        'bid_vol_50bp': aggregates['bid_vol_50bp'],
                        'ask_vol_100bp': aggregates['ask_vol_100bp'],
                        'bid_vol_100bp': aggregates['bid_vol_100bp'],
                        'ask_vol_200bp': aggregates['ask_vol_200bp'],
                        'bid_vol_200bp': aggregates['bid_vol_200bp'],
                        'ask_vol_400bp': aggregates['ask_vol_400bp'],
                        'bid_vol_400bp': aggregates['bid_vol_400bp'],
                        'ask_vol_800bp': aggregates['ask_vol_800bp'],
                        'bid_vol_800bp': aggregates['bid_vol_800bp'],
                    })
            
            return Response(daily_aggregates)
            
        except ValueError:
            return Response(
                {"error": "Invalid month format. Use YYYY-MM (e.g., 2024-11)"},
                status=400
            )


class PrivateOrderbookDepthMonthlyAggregateView(generics.ListAPIView):
    """
    API endpoint to get daily averaged private orderbook depth for a month.
    
    Query Parameters:
    - month: Month in YYYY-MM format (e.g., 2024-11) [Required]
    - market: Market filter (e.g., BTC-USDT) [Required]
    - member_id: Member ID filter [Required]
    
    Returns daily aggregated data where each bp range value is the average
    of all records for that day for the specified member.
    
    Example:
    /api/private-orderbook-depth/monthly/?month=2024-11&market=BTC-USDT&member_id=12345
    """
    
    queryset = PrivateOrderbookDepth.objects.none()
    
    def list(self, request, *args, **kwargs):
        month_str = request.query_params.get('month', None)
        market = request.query_params.get('market', None)
        member_id = request.query_params.get('member_id', None)
        
        # Validate required parameters
        if not month_str:
            return Response(
                {"error": "month parameter is required (format: YYYY-MM)"},
                status=400
            )
        
        if not market:
            return Response(
                {"error": "market parameter is required"},
                status=400
            )
        
        if not member_id:
            return Response(
                {"error": "member_id parameter is required"},
                status=400
            )
        
        try:
            # Validate member_id is an integer
            member_id = int(member_id)
        except ValueError:
            return Response(
                {"error": "member_id must be an integer"},
                status=400
            )
        
        if not PrivateOrderbookDepth.objects.filter(member_id=member_id, market__iexact=market).exists():
            return Response(
                {"error": f"No data found for member_id {member_id} in market {market}"},
                status=404
            )
        
        try:
            # Parse the month string
            date_obj = datetime.strptime(month_str, '%Y-%m')
            year = date_obj.year
            month = date_obj.month
            
            # Get timezone
            sgt = pytz.timezone(settings.LOCAL_TIMEZONE)
            
            # Get first and last day of the month
            first_day = sgt.localize(datetime(year, month, 1, 0, 0, 0))
            last_day_num = calendar.monthrange(year, month)[1]
            last_day = sgt.localize(datetime(year, month, last_day_num, 23, 59, 59, 999999))
            
            # Convert to unix timestamp (milliseconds)
            start_timestamp = int(first_day.timestamp() * 1000)
            end_timestamp = int(last_day.timestamp() * 1000)
            
            # Query and aggregate by day
            queryset = PrivateOrderbookDepth.objects.filter(
                market__iexact=market,
                member_id=member_id,
                orderbook_timestamp_unix__gte=start_timestamp,
                orderbook_timestamp_unix__lte=end_timestamp
            )
            
            # Group by day and calculate averages
            daily_aggregates = []
            
            for day in range(1, last_day_num + 1):
                day_start = sgt.localize(datetime(year, month, day, 0, 0, 0))
                day_end = sgt.localize(datetime(year, month, day, 23, 59, 59, 999999))
                
                day_start_unix = int(day_start.timestamp() * 1000)
                day_end_unix = int(day_end.timestamp() * 1000)
                
                # Filter records for this specific day
                day_records = queryset.filter(
                    orderbook_timestamp_unix__gte=day_start_unix,
                    orderbook_timestamp_unix__lte=day_end_unix
                )
                
                # Calculate aggregates
                aggregates = day_records.aggregate(
                    count=Count('id'),
                    ask_vol_12_5bp=Avg('ask_vol_12_5bp'),
                    bid_vol_12_5bp=Avg('bid_vol_12_5bp'),
                    ask_vol_25bp=Avg('ask_vol_25bp'),
                    bid_vol_25bp=Avg('bid_vol_25bp'),
                    ask_vol_37_5bp=Avg('ask_vol_37_5bp'),
                    bid_vol_37_5bp=Avg('bid_vol_37_5bp'),
                    ask_vol_50bp=Avg('ask_vol_50bp'),
                    bid_vol_50bp=Avg('bid_vol_50bp'),
                    ask_vol_100bp=Avg('ask_vol_100bp'),
                    bid_vol_100bp=Avg('bid_vol_100bp'),
                    ask_vol_200bp=Avg('ask_vol_200bp'),
                    bid_vol_200bp=Avg('bid_vol_200bp'),
                    ask_vol_400bp=Avg('ask_vol_400bp'),
                    bid_vol_400bp=Avg('bid_vol_400bp'),
                    ask_vol_800bp=Avg('ask_vol_800bp'),
                    bid_vol_800bp=Avg('bid_vol_800bp'),
                )
                
                # Only include days that have data
                if aggregates['count'] > 0:
                    daily_aggregates.append({
                        'date': day_start.strftime('%Y-%m-%d'),
                        'market': market,
                        'member_id': member_id,
                        'orderbook_timestamp_unix': day_start_unix,
                        'record_count': aggregates['count'],
                        'ask_vol_12_5bp': aggregates['ask_vol_12_5bp'],
                        'bid_vol_12_5bp': aggregates['bid_vol_12_5bp'],
                        'ask_vol_25bp': aggregates['ask_vol_25bp'],
                        'bid_vol_25bp': aggregates['bid_vol_25bp'],
                        'ask_vol_37_5bp': aggregates['ask_vol_37_5bp'],
                        'bid_vol_37_5bp': aggregates['bid_vol_37_5bp'],
                        'ask_vol_50bp': aggregates['ask_vol_50bp'],
                        'bid_vol_50bp': aggregates['bid_vol_50bp'],
                        'ask_vol_100bp': aggregates['ask_vol_100bp'],
                        'bid_vol_100bp': aggregates['bid_vol_100bp'],
                        'ask_vol_200bp': aggregates['ask_vol_200bp'],
                        'bid_vol_200bp': aggregates['bid_vol_200bp'],
                        'ask_vol_400bp': aggregates['ask_vol_400bp'],
                        'bid_vol_400bp': aggregates['bid_vol_400bp'],
                        'ask_vol_800bp': aggregates['ask_vol_800bp'],
                        'bid_vol_800bp': aggregates['bid_vol_800bp'],
                    })
            
            return Response(daily_aggregates)
            
        except ValueError:
            return Response(
                {"error": "Invalid month format. Use YYYY-MM (e.g., 2024-11)"},
                status=400
            )


class PublicOrderbookDepthDailyAggregateView(generics.ListAPIView):
    """
    API endpoint to get hourly averaged orderbook depth for a specific day.
    
    Query Parameters:
    - date: Date in YYYY-MM-DD format (e.g., 2024-11-15) [Required]
    - market: Market filter (e.g., BTC-USDT) [Required]
    
    Returns hourly aggregated data where each bp range value is the average
    of all records for that hour.
    
    Example:
    /api/public-orderbook-depth/daily-agg/?date=2024-11-15&market=BTC-USDT
    """
    
    queryset = PublicOrderbookDepth.objects.none()
    
    def list(self, request, *args, **kwargs):
        date_str = request.query_params.get('date', None)
        market = request.query_params.get('market', None)
        
        # Validate required parameters
        if not date_str:
            return Response(
                {"error": "date parameter is required (format: YYYY-MM-DD)"},
                status=400
            )
        
        if not market:
            return Response(
                {"error": "market parameter is required"},
                status=400
            )
        
        try:
            # Parse the date string
            date_obj = datetime.strptime(date_str, '%Y-%m-%d')
            
            # Get timezone
            sgt = pytz.timezone(settings.LOCAL_TIMEZONE)
            
            # Get start and end of the day
            day_start = sgt.localize(datetime(date_obj.year, date_obj.month, date_obj.day, 0, 0, 0))
            day_end = sgt.localize(datetime(date_obj.year, date_obj.month, date_obj.day, 23, 59, 59, 999999))
            
            # Convert to unix timestamp (milliseconds)
            start_timestamp = int(day_start.timestamp() * 1000)
            end_timestamp = int(day_end.timestamp() * 1000)
            
            # Query records for the day
            queryset = PublicOrderbookDepth.objects.filter(
                market__iexact=market,
                orderbook_timestamp_unix__gte=start_timestamp,
                orderbook_timestamp_unix__lte=end_timestamp
            )
            
            # Group by hour and calculate averages
            hourly_aggregates = []
            
            for hour in range(24):
                hour_start = sgt.localize(datetime(date_obj.year, date_obj.month, date_obj.day, hour, 0, 0))
                hour_end = sgt.localize(datetime(date_obj.year, date_obj.month, date_obj.day, hour, 59, 59, 999999))
                
                hour_start_unix = int(hour_start.timestamp() * 1000)
                hour_end_unix = int(hour_end.timestamp() * 1000)
                
                # Filter records for this specific hour
                hour_records = queryset.filter(
                    orderbook_timestamp_unix__gte=hour_start_unix,
                    orderbook_timestamp_unix__lte=hour_end_unix
                )
                
                # Calculate aggregates
                aggregates = hour_records.aggregate(
                    count=Count('id'),
                    ask_vol_12_5bp=Avg('ask_vol_12_5bp'),
                    bid_vol_12_5bp=Avg('bid_vol_12_5bp'),
                    ask_vol_25bp=Avg('ask_vol_25bp'),
                    bid_vol_25bp=Avg('bid_vol_25bp'),
                    ask_vol_37_5bp=Avg('ask_vol_37_5bp'),
                    bid_vol_37_5bp=Avg('bid_vol_37_5bp'),
                    ask_vol_50bp=Avg('ask_vol_50bp'),
                    bid_vol_50bp=Avg('bid_vol_50bp'),
                    ask_vol_100bp=Avg('ask_vol_100bp'),
                    bid_vol_100bp=Avg('bid_vol_100bp'),
                    ask_vol_200bp=Avg('ask_vol_200bp'),
                    bid_vol_200bp=Avg('bid_vol_200bp'),
                    ask_vol_400bp=Avg('ask_vol_400bp'),
                    bid_vol_400bp=Avg('bid_vol_400bp'),
                    ask_vol_800bp=Avg('ask_vol_800bp'),
                    bid_vol_800bp=Avg('bid_vol_800bp'),
                )
                
                # Only include hours that have data
                if aggregates['count'] > 0:
                    hourly_aggregates.append({
                        'datetime': hour_start.strftime('%Y-%m-%d %H:%M:%S'),
                        'date': date_str,
                        'hour': hour,
                        'market': market,
                        'orderbook_timestamp_unix': hour_start_unix,
                        'record_count': aggregates['count'],
                        'ask_vol_12_5bp': aggregates['ask_vol_12_5bp'],
                        'bid_vol_12_5bp': aggregates['bid_vol_12_5bp'],
                        'ask_vol_25bp': aggregates['ask_vol_25bp'],
                        'bid_vol_25bp': aggregates['bid_vol_25bp'],
                        'ask_vol_37_5bp': aggregates['ask_vol_37_5bp'],
                        'bid_vol_37_5bp': aggregates['bid_vol_37_5bp'],
                        'ask_vol_50bp': aggregates['ask_vol_50bp'],
                        'bid_vol_50bp': aggregates['bid_vol_50bp'],
                        'ask_vol_100bp': aggregates['ask_vol_100bp'],
                        'bid_vol_100bp': aggregates['bid_vol_100bp'],
                        'ask_vol_200bp': aggregates['ask_vol_200bp'],
                        'bid_vol_200bp': aggregates['bid_vol_200bp'],
                        'ask_vol_400bp': aggregates['ask_vol_400bp'],
                        'bid_vol_400bp': aggregates['bid_vol_400bp'],
                        'ask_vol_800bp': aggregates['ask_vol_800bp'],
                        'bid_vol_800bp': aggregates['bid_vol_800bp'],
                    })
            
            return Response(hourly_aggregates)
            
        except ValueError:
            return Response(
                {"error": "Invalid date format. Use YYYY-MM-DD (e.g., 2024-11-15)"},
                status=400
            )


class PrivateOrderbookDepthDailyAggregateView(generics.ListAPIView):
    """
    API endpoint to get hourly averaged private orderbook depth for a specific day.
    
    Query Parameters:
    - date: Date in YYYY-MM-DD format (e.g., 2024-11-15) [Required]
    - market: Market filter (e.g., BTC-USDT) [Required]
    - member_id: Member ID filter [Required]
    
    Returns hourly aggregated data where each bp range value is the average
    of all records for that hour for the specified member.
    
    Example:
    /api/private-orderbook-depth/daily-agg/?date=2024-11-15&market=BTC-USDT&member_id=12345
    """
    
    queryset = PrivateOrderbookDepth.objects.none()
    
    def list(self, request, *args, **kwargs):
        date_str = request.query_params.get('date', None)
        market = request.query_params.get('market', None)
        member_id = request.query_params.get('member_id', None)

        print('member_id')
        print(member_id)
        
        # Validate required parameters
        if not date_str:
            return Response(
                {"error": "date parameter is required (format: YYYY-MM-DD)"},
                status=400
            )
        
        if not market:
            return Response(
                {"error": "market parameter is required"},
                status=400
            )
        
        if not member_id:
            return Response(
                {"error": "member_id parameter is required"},
                status=400
            )
        print("1")

        try:
            # Validate member_id is an integer
            member_id = int(member_id)
        except ValueError:
            return Response(
                {"error": "member_id must be an integer"},
                status=400
            )
        print("2")
        if not PrivateOrderbookDepth.objects.filter(member_id=member_id, market__iexact=market).exists():
            print("3")
            return Response(
                {"error": f"No data found for member_id {member_id} in market {market}"},
                status=404
            )
        
        try:
            # Parse the date string
            date_obj = datetime.strptime(date_str, '%Y-%m-%d')
            print("4")
            print(date_obj)
            
            # Get timezone
            sgt = pytz.timezone(settings.LOCAL_TIMEZONE)
            
            # Get start and end of the day
            day_start = sgt.localize(datetime(date_obj.year, date_obj.month, date_obj.day, 0, 0, 0))
            day_end = sgt.localize(datetime(date_obj.year, date_obj.month, date_obj.day, 23, 59, 59, 999999))
            
            # Convert to unix timestamp (milliseconds)
            start_timestamp = int(day_start.timestamp() * 1000)
            end_timestamp = int(day_end.timestamp() * 1000)
            
            # Query records for the day
            queryset = PrivateOrderbookDepth.objects.filter(
                market__iexact=market,
                member_id=member_id,
                orderbook_timestamp_unix__gte=start_timestamp,
                orderbook_timestamp_unix__lte=end_timestamp
            )
            print(queryset.query)
            
            # Group by hour and calculate averages
            hourly_aggregates = []
            
            for hour in range(24):
                hour_start = sgt.localize(datetime(date_obj.year, date_obj.month, date_obj.day, hour, 0, 0))
                hour_end = sgt.localize(datetime(date_obj.year, date_obj.month, date_obj.day, hour, 59, 59, 999999))
                
                hour_start_unix = int(hour_start.timestamp() * 1000)
                hour_end_unix = int(hour_end.timestamp() * 1000)
                
                # Filter records for this specific hour
                hour_records = queryset.filter(
                    orderbook_timestamp_unix__gte=hour_start_unix,
                    orderbook_timestamp_unix__lte=hour_end_unix
                )
                
                # Calculate aggregates
                aggregates = hour_records.aggregate(
                    count=Count('id'),
                    ask_vol_12_5bp=Avg('ask_vol_12_5bp'),
                    bid_vol_12_5bp=Avg('bid_vol_12_5bp'),
                    ask_vol_25bp=Avg('ask_vol_25bp'),
                    bid_vol_25bp=Avg('bid_vol_25bp'),
                    ask_vol_37_5bp=Avg('ask_vol_37_5bp'),
                    bid_vol_37_5bp=Avg('bid_vol_37_5bp'),
                    ask_vol_50bp=Avg('ask_vol_50bp'),
                    bid_vol_50bp=Avg('bid_vol_50bp'),
                    ask_vol_100bp=Avg('ask_vol_100bp'),
                    bid_vol_100bp=Avg('bid_vol_100bp'),
                    ask_vol_200bp=Avg('ask_vol_200bp'),
                    bid_vol_200bp=Avg('bid_vol_200bp'),
                    ask_vol_400bp=Avg('ask_vol_400bp'),
                    bid_vol_400bp=Avg('bid_vol_400bp'),
                    ask_vol_800bp=Avg('ask_vol_800bp'),
                    bid_vol_800bp=Avg('bid_vol_800bp'),
                )
                
                # Only include hours that have data
                if aggregates['count'] > 0:
                    hourly_aggregates.append({
                        'datetime': hour_start.strftime('%Y-%m-%d %H:%M:%S'),
                        'date': date_str,
                        'hour': hour,
                        'market': market,
                        'member_id': member_id,
                        'orderbook_timestamp_unix': hour_start_unix,
                        'record_count': aggregates['count'],
                        'ask_vol_12_5bp': aggregates['ask_vol_12_5bp'],
                        'bid_vol_12_5bp': aggregates['bid_vol_12_5bp'],
                        'ask_vol_25bp': aggregates['ask_vol_25bp'],
                        'bid_vol_25bp': aggregates['bid_vol_25bp'],
                        'ask_vol_37_5bp': aggregates['ask_vol_37_5bp'],
                        'bid_vol_37_5bp': aggregates['bid_vol_37_5bp'],
                        'ask_vol_50bp': aggregates['ask_vol_50bp'],
                        'bid_vol_50bp': aggregates['bid_vol_50bp'],
                        'ask_vol_100bp': aggregates['ask_vol_100bp'],
                        'bid_vol_100bp': aggregates['bid_vol_100bp'],
                        'ask_vol_200bp': aggregates['ask_vol_200bp'],
                        'bid_vol_200bp': aggregates['bid_vol_200bp'],
                        'ask_vol_400bp': aggregates['ask_vol_400bp'],
                        'bid_vol_400bp': aggregates['bid_vol_400bp'],
                        'ask_vol_800bp': aggregates['ask_vol_800bp'],
                        'bid_vol_800bp': aggregates['bid_vol_800bp'],
                    })

            return Response(hourly_aggregates)
            
        except ValueError:
            return Response(
                {"error": "Invalid date format. Use YYYY-MM-DD (e.g., 2024-11-15)"},
                status=400
            )


class LPEvaluationComparisonView(generics.GenericAPIView):
    """
    API endpoint to get LP evaluation comparison data.
    
    Query Parameters:
    - market: Market filter (e.g., SGD-USDT) [Required]
    - month: Month in YYYY-MM format (e.g., 2025-01) [Optional - for monthly view]
    - date: Date in YYYY-MM-DD format (e.g., 2025-01-15) [Optional - for daily view]
    - lp: LP member ID or "public" for all LPs [Required]
    
    Examples:
    /api/lp-evaluation/comparison/?month=2025-01&market=SGD-USDT&lp=public
    /api/lp-evaluation/comparison/?month=2025-01&market=SGD-USDT&lp=12345
    /api/lp-evaluation/comparison/?date=2025-01-15&market=SGD-USDT&lp=public
    """
    
    serializer_class = LPEvaluationComparisonSerializer
    
    def get(self, request, *args, **kwargs):
        market = request.query_params.get('market')
        month_str = request.query_params.get('month')
        date_str = request.query_params.get('date')
        lp_id = request.query_params.get('lp')
        
        # Validate required parameters
        if not market:
            return Response({"error": "market parameter is required"}, status=400)
        
        if not lp_id:
            return Response({"error": "lp parameter is required"}, status=400)
        
        if not month_str and not date_str:
            return Response({"error": "Either month or date parameter is required"}, status=400)
        
        if month_str and date_str:
            return Response({"error": "Cannot specify both month and date"}, status=400)
        
        try:
            # Determine LP name
            if lp_id == 'public':
                lp_name = 'All LPs'
            else:
                lp_id = int(lp_id)
                lp_master = LpMaster.objects.filter(member_id=lp_id).first()
                lp_name = lp_master.company_name if lp_master else f'LP {lp_id}'
            
            # Get date range
            if month_str:
                period = month_str
                start_ts, end_ts = self._get_month_range(month_str)
            else:
                period = date_str
                start_ts, end_ts = self._get_day_range(date_str)
            
            # Fetch aggregated data
            public_data = self._fetch_public_data(market, start_ts, end_ts)
            source_data = self._fetch_lp_data(market, start_ts, end_ts, lp_id)
            
            if not public_data:
                return Response({"error": "No public orderbook data found"}, status=404)
            
            if not source_data:
                return Response({"error": f"No LP data found for {lp_name}"}, status=404)
            
            # Generate comparison data
            comparison_data = self._generate_comparison(public_data, source_data, lp_name, market, period)
            
            serializer = self.get_serializer(comparison_data, many=True)
            return Response(serializer.data)
            
        except ValueError:
            logging.warning("Invalid request in LPEvaluationComparisonView.get", exc_info=True)
            return Response({"error": "Invalid request parameters."}, status=400)
        except Exception:
            logging.exception("Unexpected error in LPEvaluationComparisonView.get")
            return Response({"error": "An internal error has occurred."}, status=500)
    
    def _get_month_range(self, month: str) -> tuple:
        """Get start and end timestamps for a month."""
        date_obj = datetime.strptime(month, '%Y-%m')
        year, month_num = date_obj.year, date_obj.month
        
        tz = pytz.timezone(getattr(settings, 'LOCAL_TIMEZONE', 'Asia/Singapore'))
        first_day = tz.localize(datetime(year, month_num, 1, 0, 0, 0))
        last_day_num = calendar.monthrange(year, month_num)[1]
        last_day = tz.localize(datetime(year, month_num, last_day_num, 23, 59, 59, 999999))
        
        return int(first_day.timestamp() * 1000), int(last_day.timestamp() * 1000)
    
    def _get_day_range(self, date: str) -> tuple:
        """Get start and end timestamps for a day."""
        date_obj = datetime.strptime(date, '%Y-%m-%d')
        
        tz = pytz.timezone(getattr(settings, 'LOCAL_TIMEZONE', 'Asia/Singapore'))
        day_start = tz.localize(datetime(date_obj.year, date_obj.month, date_obj.day, 0, 0, 0))
        day_end = tz.localize(datetime(date_obj.year, date_obj.month, date_obj.day, 23, 59, 59, 999999))
        
        return int(day_start.timestamp() * 1000), int(day_end.timestamp() * 1000)
    
    def _build_agg_fields(self) -> dict:
        """Build aggregation fields dynamically."""
        agg_fields = {}
        for level in BP_LEVELS:
            agg_fields[f'ask_vol_{level}bp'] = Avg(f'ask_vol_{level}bp')
            agg_fields[f'bid_vol_{level}bp'] = Avg(f'bid_vol_{level}bp')
            agg_fields[f'ask_fiat_value_{level}bp'] = Avg(f'ask_fiat_value_{level}bp')
            agg_fields[f'bid_fiat_value_{level}bp'] = Avg(f'bid_fiat_value_{level}bp')
        return agg_fields
    
    def _fetch_public_data(self, market: str, start_ts: int, end_ts: int) -> dict:
        """Fetch public orderbook data averaged across entire period."""
        queryset = PublicOrderbookDepth.objects.filter(
            market__iexact=market,
            orderbook_timestamp_unix__gte=start_ts,
            orderbook_timestamp_unix__lte=end_ts
        )

        agg = queryset.aggregate(**self._build_agg_fields(), count=Count('id'))
        
        if agg['count'] == 0:
            return None
        
        result = {}
        for k, v in agg.items():
            if k == 'count':
                continue
            val = float(v) if v is not None else 0.0
            result[k] = val

        return result
    
    def _fetch_lp_data(self, market: str, start_ts: int, end_ts: int, lp_id) -> dict:
        """Fetch LP orderbook data averaged across entire period."""
        
        if lp_id == 'public':
            # Sum averages from all LPs
            lp_masters = LpMaster.objects.all()
            totals = defaultdict(float)
            has_data = False
            
            for lp in lp_masters:
                queryset = PrivateOrderbookDepth.objects.filter(
                    market__iexact=market,
                    member_id=lp.member_id,
                    orderbook_timestamp_unix__gte=start_ts,
                    orderbook_timestamp_unix__lte=end_ts
                )
                
                agg = queryset.aggregate(**self._build_agg_fields(), count=Count('id'))
                
                if agg['count'] > 0:
                    has_data = True
                    for k, v in agg.items():
                        if k != 'count':
                            val = float(v) if v is not None else 0.0
                            totals[k] += val
            
            return dict(totals) if has_data else None
        else:
            # Single LP
            queryset = PrivateOrderbookDepth.objects.filter(
                market__iexact=market,
                member_id=lp_id,
                orderbook_timestamp_unix__gte=start_ts,
                orderbook_timestamp_unix__lte=end_ts
            )
            
            agg = queryset.aggregate(**self._build_agg_fields(), count=Count('id'))
            
            if agg['count'] == 0:
                return None
            
            result = {}
            for k, v in agg.items():
                if k == 'count':
                    continue
                val = float(v) if v is not None else 0.0
                result[k] = val
            
            return result
    
    def _generate_comparison(self, public_data: dict, source_data: dict, 
                             lp_name: str, market: str, period: str) -> list:
        """Generate comparison data."""
        
        # Define BP ranges with their interval calculations
        bp_ranges = [
            ('0~12.5bp', '12_5', None),
            ('12.5~25bp', '25', '12_5'),
            ('25~37.5bp', '37_5', '25'),
            ('37.5~50bp', '50', '37_5'),
            ('50~100bp', '100', '50'),
            ('100~200bp', '200', '100'),
            ('200~400bp', '400', '200'),
            ('400~800bp', '800', '400'),
        ]
        
        comparison_data = []
        
        for range_name, level, prev_level in bp_ranges:
            # Calculate interval values (current - previous)
            if prev_level:
                public_ask = (public_data.get(f'ask_vol_{level}bp', 0) - 
                             public_data.get(f'ask_vol_{prev_level}bp', 0))
                public_bid = (public_data.get(f'bid_vol_{level}bp', 0) - 
                             public_data.get(f'bid_vol_{prev_level}bp', 0))
                source_ask = (source_data.get(f'ask_vol_{level}bp', 0) - 
                             source_data.get(f'ask_vol_{prev_level}bp', 0))
                source_bid = (source_data.get(f'bid_vol_{level}bp', 0) - 
                             source_data.get(f'bid_vol_{prev_level}bp', 0))
                public_ask_fiat = (public_data.get(f'ask_fiat_value_{level}bp', 0) - 
                                   public_data.get(f'ask_fiat_value_{prev_level}bp', 0))
                public_bid_fiat = (public_data.get(f'bid_fiat_value_{level}bp', 0) - 
                                   public_data.get(f'bid_fiat_value_{prev_level}bp', 0))
                source_ask_fiat = (source_data.get(f'ask_fiat_value_{level}bp', 0) - 
                                   source_data.get(f'ask_fiat_value_{prev_level}bp', 0))
                source_bid_fiat = (source_data.get(f'bid_fiat_value_{level}bp', 0) - 
                                   source_data.get(f'bid_fiat_value_{prev_level}bp', 0))
            else:
                # First range (0-12.5bp) - use cumulative value directly
                public_ask = public_data.get(f'ask_vol_{level}bp', 0)
                public_bid = public_data.get(f'bid_vol_{level}bp', 0)
                source_ask = source_data.get(f'ask_vol_{level}bp', 0)
                source_bid = source_data.get(f'bid_vol_{level}bp', 0)
                public_ask_fiat = public_data.get(f'ask_fiat_value_{level}bp', 0)
                public_bid_fiat = public_data.get(f'bid_fiat_value_{level}bp', 0)
                source_ask_fiat = source_data.get(f'ask_fiat_value_{level}bp', 0)
                source_bid_fiat = source_data.get(f'bid_fiat_value_{level}bp', 0)
            
            # Calculate percentages (cap at 100%)
            ask_pct = min((source_ask / public_ask) * 100, 100) if public_ask > 0 else 0
            bid_pct = min((source_bid / public_bid) * 100, 100) if public_bid > 0 else 0
            
            comparison_data.append({
                'period': period,
                'liquidity_provider': lp_name,
                'market': market,
                'bp_range': range_name,
                'public_ask': round(public_ask, 2),
                'lp_ask': round(source_ask, 2),
                'ask_percentage': round(ask_pct, 2),
                'public_bid': round(public_bid, 2),
                'lp_bid': round(source_bid, 2),
                'bid_percentage': round(bid_pct, 2),
                'public_ask_fiat_value': round(public_ask_fiat, 2),
                'lp_ask_fiat_value': round(source_ask_fiat, 2),
                'public_bid_fiat_value': round(public_bid_fiat, 2),
                'lp_bid_fiat_value': round(source_bid_fiat, 2),
            })
        
        return comparison_data


class LPPerformanceSummaryView(generics.GenericAPIView):
    """
    API endpoint for LP performance summary and ranges sum.
    
    Query Parameters:
    - member_id: LP member ID [Required]
    - month: Month in YYYY-MM format (e.g., 2025-01) [Optional - for monthly view]
    - date: Date in YYYY-MM-DD format (e.g., 2025-01-15) [Optional - for daily view]
    - markets: Comma-separated list of markets (e.g., SGD-USDT,SGD-BTC) [Optional]
    
    Examples:
    /api/lp-performance/summary/?member_id=223634&month=2025-01
    /api/lp-performance/summary/?member_id=223634&date=2025-01-15
    /api/lp-performance/summary/?member_id=223634&month=2025-01&markets=SGD-USDT,SGD-BTC
    """
    
    def get(self, request, *args, **kwargs):
        # Parse and validate parameters
        member_id = request.query_params.get('member_id')
        month = request.query_params.get('month')
        date = request.query_params.get('date')
        markets_str = request.query_params.get('markets')
        
        # Validation
        if not member_id:
            return Response({"error": "member_id parameter is required"}, status=400)
        
        if not month and not date:
            return Response({"error": "Either month or date parameter is required"}, status=400)
        
        if month and date:
            return Response({"error": "Cannot specify both month and date"}, status=400)
        
        try:
            member_id = int(member_id)
        except ValueError:
            return Response({"error": "member_id must be an integer"}, status=400)
        
        # Fetch LP master data
        lp_master = LpMaster.objects.filter(member_id=member_id).first()
        if not lp_master:
            return Response({"error": f"LP with member_id {member_id} not found"}, status=404)
        
        # Get total_fund and targets from LpMaster
        total_fund = float(lp_master.total_fund) if lp_master.total_fund else 0.0
        targets = self._get_targets_from_lp_master(lp_master)
        
        # Parse markets filter
        markets = None
        if markets_str:
            markets = [m.strip().upper() for m in markets_str.split(',')]
        
        try:
            # Get date range timestamps
            start_timestamp, end_timestamp = self._get_date_range(month, date)
            
            # Calculate ranges sum
            range_sums = self._calculate_ranges_sum(member_id, start_timestamp, end_timestamp, markets)
            
            # Build response
            ranges_sum_result, total_sum = self._build_ranges_sum(range_sums)
            performance_result = self._build_performance_summary(range_sums, targets, total_fund)
            
            return Response({
                'period': month or date,
                'member_id': member_id,
                'lp_name': lp_master.company_name,
                'total_fund': total_fund,
                'markets': markets or 'all',
                'targets': targets,
                'ranges_sum': ranges_sum_result,
                'performance_summary': performance_result
            })
            
        except ValueError as e:
            logger.warning("Invalid request parameters while building LP interval performance response", exc_info=True)
            return Response({"error": "Invalid request parameters"}, status=400)
        except Exception as e:
            logger.exception("Unhandled error while building LP interval performance response")
            return Response({"error": "An internal error has occurred"}, status=500)
    
    def _get_targets_from_lp_master(self, lp_master) -> dict:
        """Get interval targets from LpMaster."""
        targets = {}
        
        for range_name, field_name in TARGET_FIELD_MAPPING.items():
            targets[range_name] = float(getattr(lp_master, field_name) or 0)
        
        return targets
    
    def _get_date_range(self, month: str = None, date: str = None) -> tuple:
        """Get start and end timestamps in milliseconds."""
        tz = pytz.timezone(getattr(settings, 'LOCAL_TIMEZONE', 'Asia/Singapore'))
        
        if month:
            date_obj = datetime.strptime(month, '%Y-%m')
            year, month_num = date_obj.year, date_obj.month
            
            first_day = tz.localize(datetime(year, month_num, 1, 0, 0, 0))
            last_day_num = calendar.monthrange(year, month_num)[1]
            last_day = tz.localize(datetime(year, month_num, last_day_num, 23, 59, 59, 999999))
            
        else:  # date
            date_obj = datetime.strptime(date, '%Y-%m-%d')
            first_day = tz.localize(datetime(date_obj.year, date_obj.month, date_obj.day, 0, 0, 0))
            last_day = tz.localize(datetime(date_obj.year, date_obj.month, date_obj.day, 23, 59, 59, 999999))

        return int(first_day.timestamp() * 1000), int(last_day.timestamp() * 1000)
    
    def _calculate_ranges_sum(self, member_id: int, start_ts: int, end_ts: int, markets: list = None) -> dict:
        """Calculate sum across all markets for each BP range."""
        queryset = PrivateOrderbookDepth.objects.filter(
            member_id=member_id,
            orderbook_timestamp_unix__gte=start_ts,
            orderbook_timestamp_unix__lte=end_ts
        )

        if markets:
            # Case-insensitive market filter
            from django.db.models import Q
            market_filter = Q()
            for m in markets:
                market_filter |= Q(market__iexact=m)
            queryset = queryset.filter(market_filter)
        
        market_list = queryset.values_list('market', flat=True).distinct()
        range_sums = {name: 0.0 for name in RANGE_NAMES}
        
        # Build aggregation fields dynamically
        agg_fields = {}
        for level in BP_LEVELS:
            agg_fields[f'ask_fiat_value_{level}bp'] = Avg(f'ask_fiat_value_{level}bp')
            agg_fields[f'bid_fiat_value_{level}bp'] = Avg(f'bid_fiat_value_{level}bp')
        
        for market in market_list:
            agg = queryset.filter(market=market).aggregate(**agg_fields)
            
            # Calculate intervals from cumulative values
            prev_ask, prev_bid = 0.0, 0.0
            for i, level in enumerate(BP_LEVELS):
                ask = float(agg.get(f'ask_fiat_value_{level}bp') or 0)
                bid = float(agg.get(f'bid_fiat_value_{level}bp') or 0)
                
                range_sums[RANGE_NAMES[i]] += (ask - prev_ask) + (bid - prev_bid)
                prev_ask, prev_bid = ask, bid
        
        return range_sums
    
    def _build_ranges_sum(self, range_sums: dict) -> tuple:
        """Build ranges sum output."""
        result = []
        total = 0.0
        
        for name in RANGE_NAMES:
            sum_val = range_sums[name]
            result.append({'ranges': name, 'sum': round(sum_val, 2)})
            total += sum_val
        
        result.append({'ranges': 'total', 'sum': round(total, 2)})
        return result, total
    
    def _build_performance_summary(self, range_sums: dict, targets: dict, total_fund: float) -> list:
        """Build performance summary output."""
        result = []
        total_target_fund = 0.0
        total_actual = 0.0
        
        for name in RANGE_NAMES:
            target = targets.get(name, 0.0)
            target_fund = total_fund * target
            actual = range_sums[name]
            diff = actual - target_fund
            
            if target_fund > 0:
                score = str(round((actual / target_fund) * 100, 2))
            else:
                score = "100.0" if actual == 0 else "N/A"
            
            result.append({
                'range': name,
                'target': target,
                'target_fund': round(target_fund, 2),
                'actual': round(actual, 2),
                'diff': round(diff, 2),
                'score': score
            })
            
            total_target_fund += target_fund
            total_actual += actual
        
        # Total row
        total_diff = total_actual - total_target_fund
        total_score = round((total_actual / total_target_fund * 100), 2) if total_target_fund > 0 else 100.0
        
        result.append({
            'range': 'total',
            'target': round(sum(targets.values()), 2),
            'target_fund': round(total_target_fund, 2),
            'actual': round(total_actual, 2),
            'diff': round(total_diff, 2),
            'score': str(total_score)
        })

        return result


class UptimePerformanceSummaryView(APIView):
    """
    API endpoint for Uptime performance summary
    
    Query Parameters:
    - member_id: Required. The member ID to filter by
    - category: Required. Either 'major' (SGD markets) or 'minor' (USDT markets)
    - date: Required. Date in ISO format (e.g., '2024-01-01')
    """
    
    def get(self, request, *args, **kwargs):
        # Validate parameters
        validation_error = self.validate_parameters(request)
        if validation_error:
            return validation_error
        
        # Extract validated parameters
        member_id = int(request.query_params.get('member_id'))
        category = request.query_params.get('category')
        date = request.query_params.get('date')

        
        # Fetch data
        try:
            df = self.fetch_orderbook_data(member_id, category, date)
        except Exception as e:
            return Response(
                {"error": f"Database query failed: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        # Check if data exists
        if df.empty:
            return Response(
                {"error": "No data found for the given parameters"},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Process data
        processed_df = self.calculate_tier_volumes(df)
        grouped_df = self.group_by_timestamp(processed_df)
        
        # Prepare response
        result = self.prepare_response_data(grouped_df, member_id, category)
        
        return Response({
            'success': True,
            'data': result,
            'count': len(result)
        }, status=status.HTTP_200_OK)
    
    def validate_parameters(self, request):
        """Validate request parameters"""
        member_id = request.query_params.get('member_id')
        category = request.query_params.get('category')
        date_str = request.query_params.get('date')
        
        # Validate member_id
        if not member_id:
            return Response(
                {"error": "member_id is required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            int(member_id)
        except ValueError:
            return Response(
                {"error": "member_id must be an integer"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validate category
        if category not in ['major', 'minor']:
            return Response(
                {"error": "category must be either 'major' or 'minor'"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validate date parameter
        if not date_str:
            return Response(
                {"error": "date is required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Parse date string and create start/end datetime for the entire day
        try:
            local_tz = pytz.timezone(settings.LOCAL_TIMEZONE)
            
            # Parse the date
            date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
            
            # Create start datetime (00:00:00 of the given date)
            self.start_datetime = local_tz.localize(
                datetime.combine(date_obj, datetime.min.time())
            )
            
            # Create end datetime (00:00:00 of the next day)
            next_day = date_obj + timedelta(days=1)
            self.end_datetime = local_tz.localize(
                datetime.combine(next_day, datetime.min.time())
            )
            
        except ValueError:
            return Response(
                {"error": "Invalid date format. Use YYYY-MM-DD format (e.g., '2024-01-01')."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        return None

    def fetch_orderbook_data(self, member_id, category, date_str):
        """Fetch orderbook depth data using Django ORM"""
        # Determine market prefix based on category
        market_prefix = settings.CURRENCY_CODE if category == 'major' else 'USDT'

        date_obj = datetime.strptime(date_str, '%Y-%m-%d')
        
        # Get timezone
        sgt = pytz.timezone(settings.LOCAL_TIMEZONE)
        
        # Get start and end of the day
        day_start = sgt.localize(datetime(date_obj.year, date_obj.month, date_obj.day, 0, 0, 0))
        day_end = sgt.localize(datetime(date_obj.year, date_obj.month, date_obj.day, 23, 59, 59, 999999))
        start_timestamp = int(day_start.timestamp() * 1000)
        end_timestamp = int(day_end.timestamp() * 1000)

    
        # Query using Django ORM
        queryset = PrivateOrderbookDepth.objects.filter(
            market__startswith=market_prefix,
            member_id=member_id,
            orderbook_timestamp_unix__gte=start_timestamp,
            orderbook_timestamp_unix__lte=end_timestamp
        ).values(
            'orderbook_timestamp_rounding',
            'member_id',
            'market',
            'ask_fiat_value_12_5bp',
            'bid_fiat_value_12_5bp',
            'ask_fiat_value_25bp',
            'bid_fiat_value_25bp',
            'ask_fiat_value_50bp',
            'bid_fiat_value_50bp',
            'ask_fiat_value_100bp',
            'bid_fiat_value_100bp',
            'ask_fiat_value_200bp',
            'bid_fiat_value_200bp',
            'ask_fiat_value_400bp',
            'bid_fiat_value_400bp',
            'ask_fiat_value_800bp',
            'bid_fiat_value_800bp',
        )

        # Convert to pandas DataFrame
        df = pd.DataFrame(list(queryset))

        return df
    
    def calculate_tier_volumes(self, df):
        """Calculate tier volumes excluding previous tiers"""
        # Convert columns to float for calculations
        decimal_columns = [
            'ask_fiat_value_12_5bp', 'bid_fiat_value_12_5bp',
            'ask_fiat_value_25bp', 'bid_fiat_value_25bp',
            'ask_fiat_value_50bp', 'bid_fiat_value_50bp',
            'ask_fiat_value_100bp', 'bid_fiat_value_100bp',
            'ask_fiat_value_200bp', 'bid_fiat_value_200bp',
            'ask_fiat_value_400bp', 'bid_fiat_value_400bp',
            'ask_fiat_value_800bp', 'bid_fiat_value_800bp',
        ]
        
        for col in decimal_columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        
        # Tier 1: 0-25bp = ask_12.5bp + bid_12.5bp
        df['tier_1_volume'] = (
            df['ask_fiat_value_12_5bp'] + df['bid_fiat_value_12_5bp']
        )
        
        # Tier 2: 25-50bp = (ask_25bp + bid_25bp) - tier_1
        df['tier_2_volume'] = (
            df['ask_fiat_value_25bp'] + df['bid_fiat_value_25bp']
        ) - df['tier_1_volume']
        
        # Tier 3: 50-100bp = (ask_50bp + bid_50bp) - (ask_25bp + bid_25bp)
        df['tier_3_volume'] = (
            df['ask_fiat_value_50bp'] + df['bid_fiat_value_50bp']
        ) - (
            df['ask_fiat_value_25bp'] + df['bid_fiat_value_25bp']
        )
        
        # Tier 4: 100-200bp = (ask_100bp + bid_100bp) - (ask_50bp + bid_50bp)
        df['tier_4_volume'] = (
            df['ask_fiat_value_100bp'] + df['bid_fiat_value_100bp']
        ) - (
            df['ask_fiat_value_50bp'] + df['bid_fiat_value_50bp']
        )
        
        # Tier 5: 200-400bp = (ask_200bp + bid_200bp) - (ask_100bp + bid_100bp)
        df['tier_5_volume'] = (
            df['ask_fiat_value_200bp'] + df['bid_fiat_value_200bp']
        ) - (
            df['ask_fiat_value_100bp'] + df['bid_fiat_value_100bp']
        )
        
        # Tier 6: 400-800bp = (ask_400bp + bid_400bp) - (ask_200bp + bid_200bp)
        df['tier_6_volume'] = (
            df['ask_fiat_value_400bp'] + df['bid_fiat_value_400bp']
        ) - (
            df['ask_fiat_value_200bp'] + df['bid_fiat_value_200bp']
        )
        
        # Tier 7: 800-1600bp = (ask_800bp + bid_800bp) - (ask_400bp + bid_400bp)
        df['tier_7_volume'] = (
            df['ask_fiat_value_800bp'] + df['bid_fiat_value_800bp']
        ) - (
            df['ask_fiat_value_400bp'] + df['bid_fiat_value_400bp']
        )
        
        return df
    
    def group_by_timestamp(self, df):
        """Group data by orderbook_timestamp_rounding"""
        grouped = df.groupby('orderbook_timestamp_rounding').agg({
            'member_id': 'first',
            'tier_1_volume': 'sum',
            'tier_2_volume': 'sum',
            'tier_3_volume': 'sum',
            'tier_4_volume': 'sum',
            'tier_5_volume': 'sum',
            'tier_6_volume': 'sum',
            'tier_7_volume': 'sum',
        }).reset_index()
        
        return grouped
    
    def prepare_response_data(self, grouped_df, member_id, category):
        """Prepare final response data"""
        result = []
        for _, row in grouped_df.iterrows():
            result.append({
                'orderbook_timestamp_rounding': str(row['orderbook_timestamp_rounding']),
                'member_id': int(row['member_id']),
                'category': category,
                'tier_1_volume': round(float(row['tier_1_volume']), 2),
                'tier_2_volume': round(float(row['tier_2_volume']), 2),
                'tier_3_volume': round(float(row['tier_3_volume']), 2),
                'tier_4_volume': round(float(row['tier_4_volume']), 2),
                'tier_5_volume': round(float(row['tier_5_volume']), 2),
                'tier_6_volume': round(float(row['tier_6_volume']), 2),
                'tier_7_volume': round(float(row['tier_7_volume']), 2),
            })
        
        return result


class UptimePerformanceSummaryView2(APIView):
    """
    API endpoint for Uptime performance summary
    
    Query Parameters:
    - member_id: Required. The member ID to filter by
    - category: Required. Either 'major' or 'minor' 
    - date: Required. Date in ISO format (e.g., '2024-01-01')
    """
    
    def get(self, request, *args, **kwargs):
        # Validate parameters
        validation_error = self.validate_parameters(request)
        if validation_error:
            return validation_error
        
        # Extract validated parameters
        member_id = int(request.query_params.get('member_id'))
        category = request.query_params.get('category')
        date = request.query_params.get('date')

        
        # Fetch data
        try:
            df = self.fetch_orderbook_data(member_id, category, date)
        except Exception as e:
            return Response(
                {"error": f"Database query failed: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        # Check if data exists
        if df.empty:
            return Response(
                {"error": "No data found for the given parameters"},
                status=status.HTTP_404_NOT_FOUND
            )

        result = df.to_dict('records')
        
        return Response({
            'success': True,
            'data': result,
            'count': len(result)
        }, status=status.HTTP_200_OK)
    
    def validate_parameters(self, request):
        """Validate request parameters"""
        member_id = request.query_params.get('member_id')
        category = request.query_params.get('category')
        date_str = request.query_params.get('date')
        
        # Validate member_id
        if not member_id:
            return Response(
                {"error": "member_id is required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            int(member_id)
        except ValueError:
            return Response(
                {"error": "member_id must be an integer"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validate category
        if category not in ['major', 'minor']:
            return Response(
                {"error": "category must be either 'major' or 'minor'"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validate date parameter
        if not date_str:
            return Response(
                {"error": "date is required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Parse date string and create start/end datetime for the entire day
        try:
            local_tz = pytz.timezone(settings.LOCAL_TIMEZONE)
            
            # Parse the date
            date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
            
            # Create start datetime (00:00:00 of the given date)
            self.start_datetime = local_tz.localize(
                datetime.combine(date_obj, datetime.min.time())
            )
            
            # Create end datetime (00:00:00 of the next day)
            next_day = date_obj + timedelta(days=1)
            self.end_datetime = local_tz.localize(
                datetime.combine(next_day, datetime.min.time())
            )
            
        except ValueError as e:
            return Response(
                {"error": f"Invalid date format. Use YYYY-MM-DD format (e.g., '2024-01-01'): {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        return None


    def fetch_orderbook_data(self, member_id, category, date_str):
        """Fetch orderbook depth data using Django ORM"""
        # Determine market prefix based on category
        category_value = True if category == 'major' else False

        markets = tuple(MarketCategory.objects.filter(category=category_value).values_list('market', flat=True))

        # Query using Django ORM
        query = f"""
            WITH tier AS(
            SELECT 
                member_id,
                market,
                DATE_FORMAT(CONVERT_TZ(orderbook_timestamp, 'UTC', '{settings.LOCAL_TIMEZONE}'), '%Y-%m-%d') target_date,
                orderbook_timestamp_rounding 'time_stamp_rounding',
                (ask_fiat_value_12_5bp + bid_fiat_value_12_5bp) tier_1,
                (ask_fiat_value_25bp + bid_fiat_value_25bp) - (ask_fiat_value_12_5bp + bid_fiat_value_12_5bp) tier_2,
                (ask_fiat_value_50bp + bid_fiat_value_50bp) - (ask_fiat_value_25bp + bid_fiat_value_25bp) tier_3,
                (ask_fiat_value_100bp + bid_fiat_value_100bp) - (ask_fiat_value_50bp + bid_fiat_value_50bp) tier_4,
                (ask_fiat_value_200bp + bid_fiat_value_200bp) - (ask_fiat_value_100bp + bid_fiat_value_100bp) tier_5,
                (ask_fiat_value_400bp + bid_fiat_value_400bp) - (ask_fiat_value_200bp + bid_fiat_value_200bp) tier_6,
                (ask_fiat_value_800bp + bid_fiat_value_800bp) - (ask_fiat_value_400bp + bid_fiat_value_400bp) tier_7
            FROM private_orderbook_depth
            WHERE DATE_FORMAT(CONVERT_TZ(orderbook_timestamp, 'UTC', '{settings.LOCAL_TIMEZONE}'), '%Y-%m-%d') = '{date_str}'
            AND member_id = {member_id}
            AND market IN {markets}
            )
            SELECT 
                time_stamp_rounding, sum(tier_1) tier_1, sum(tier_2) tier_2, sum(tier_3) tier_3,
                sum(tier_4) tier_4, sum(tier_5) tier_5, sum(tier_6) tier_6, sum(tier_7) tier_7
            FROM tier
            GROUP BY time_stamp_rounding
        """
        print(query)
        
        df = exe_query('django', query)
        return df


    # def fetch_orderbook_data(self, member_id, category, date_str):
    #     """Fetch orderbook depth data using Django ORM"""
    #     # Determine market prefix based on category
    #     category_value = True if category == 'major' else False

    #     markets = MarketCategory.objects.filter(category=category_value).values_list('market', flat=True)

    #     # Query using Django ORM
    #     queryset = UptimeSummary.objects.filter(
    #         market__in=markets,
    #         member_id=member_id,
    #         target_date=date_str
    #     ).values('time_stamp_rounding').annotate(
    #         tier_1=Sum('tier_1'),
    #         tier_2=Sum('tier_2'),
    #         tier_3=Sum('tier_3'),
    #         tier_4=Sum('tier_4'),
    #         tier_5=Sum('tier_5'),
    #         tier_6=Sum('tier_6'),
    #         tier_7=Sum('tier_7'),
    #     )
    #     print(queryset.query)
        
    #     # Convert to pandas DataFrame
    #     df = pd.DataFrame(list(queryset))
    #     return df



class LPEvaluationComparisonView2(APIView):
    
    def get(self, request, *args, **kwargs):
        # Validate parameters
        validation_error = self.validate_parameters(request)
        if validation_error:
            return validation_error
        
        # Extract validated parameters
        member_id = (request.query_params.get('member_id'))
        market = request.query_params.get('market')
        date = request.query_params.get('date')
        
        try:
            df = self.fetch_orderbook_data(member_id, market, date)
        except Exception as e:
            return Response(
                {"error": f"Database query failed: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        # Check if data exists
        if df.empty:
            return Response(
                {"error": "No data found for the given parameters"},
                status=status.HTTP_404_NOT_FOUND
            )

        result = df.to_dict('records')
        
        return Response({
            'success': True,
            'data': result,
            'count': len(result)
        }, status=status.HTTP_200_OK)
    
    def validate_parameters(self, request):
        """Validate request parameters"""
        member_id = request.query_params.get('member_id')
        market = request.query_params.get('market')
        date_str = request.query_params.get('date')
        
        # Validate member_id
        if not member_id:
            return Response(
                {"error": "member_id is required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # try:
        #     int(member_id)
        # except ValueError:
        #     return Response(
        #         {"error": "member_id must be an integer"},
        #         status=status.HTTP_400_BAD_REQUEST
        #     )
        
        # # Validate category
        # if category not in ['major', 'minor']:
        #     return Response(
        #         {"error": "category must be either 'major' or 'minor'"},
        #         status=status.HTTP_400_BAD_REQUEST
        #     )
        
        # Validate date parameter
        if not date_str:
            return Response(
                {"error": "date is required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Parse date string and create start/end datetime for the entire day
        try:
            local_tz = pytz.timezone(settings.LOCAL_TIMEZONE)
            
            # Parse the date
            date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
            
            # Create start datetime (00:00:00 of the given date)
            self.start_datetime = local_tz.localize(
                datetime.combine(date_obj, datetime.min.time())
            )
            
            # Create end datetime (00:00:00 of the next day)
            next_day = date_obj + timedelta(days=1)
            self.end_datetime = local_tz.localize(
                datetime.combine(next_day, datetime.min.time())
            )
            
        except ValueError as e:
            return Response(
                {"error": f"Invalid date format. Use YYYY-MM-DD format (e.g., '2024-01-01'): {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        return None

    def fetch_orderbook_data(self, member_id, market, date_str):

        if member_id == 'public':
            lp_name = 'All LPs'
            lp_id = tuple(list(LpMaster.objects.values_list('member_id', flat=True))+[0])
        else:
            lp_id = tuple(member_id.split(',')+[0])
        
        query = f"""
            with pbl as (
                SELECT 
                    avg(ask_vol_12_5bp) a_12_5, avg(bid_vol_12_5bp) b_12_5, avg(ask_vol_25bp) a_25, avg(bid_vol_25bp) b_25, 
                    avg(ask_vol_37_5bp) a_37_5, avg(bid_vol_37_5bp) b_37_5, avg(ask_vol_50bp) a_50, avg(bid_vol_50bp) b_50, 
                    avg(ask_vol_100bp) a_100, avg(bid_vol_100bp) b_100, avg(ask_vol_200bp) a_200, avg(bid_vol_200bp) b_200, 
                    avg(ask_vol_400bp) a_400, avg(bid_vol_400bp) b_400, avg(ask_vol_800bp) a_800, avg(bid_vol_800bp) b_800, 
                    avg(ask_fiat_value_12_5bp) a_fiat_12_5, avg(bid_fiat_value_12_5bp) b_fiat_12_5, avg(ask_fiat_value_25bp) a_fiat_25, avg(bid_fiat_value_25bp) b_fiat_25, 
                    avg(ask_fiat_value_37_5bp) a_fiat_37_5, avg(bid_fiat_value_37_5bp) b_fiat_37_5, avg(ask_fiat_value_50bp) a_fiat_50, avg(bid_fiat_value_50bp) b_fiat_50, 
                    avg(ask_fiat_value_100bp) a_fiat_100, avg(bid_fiat_value_100bp) b_fiat_100, avg(ask_fiat_value_200bp) a_fiat_200, avg(bid_fiat_value_200bp) b_fiat_200, 
                    avg(ask_fiat_value_400bp) a_fiat_400, avg(bid_fiat_value_400bp) b_fiat_400, avg(ask_fiat_value_800bp) a_fiat_800, avg(bid_fiat_value_800bp) b_fiat_800
                FROM public_orderbook_depth 
                WHERE market = '{market}' 
                AND DATE_FORMAT(CONVERT_TZ(orderbook_timestamp, 'UTC', '{settings.LOCAL_TIMEZONE}'), '%Y-%m-%d') = '{date_str}'
                ),
                pbl_result as(
                select '0~12.5bp' bp_range, a_12_5 public_ask, a_fiat_12_5 public_ask_fiat, b_12_5 public_bid, b_fiat_12_5 public_bid_fiat from pbl union all
                select '12.5~25bp' bp_range, (a_25 - a_12_5) , (a_fiat_25 - a_fiat_12_5) , (b_25 - b_12_5) , (b_fiat_25 - b_fiat_12_5)  from pbl union all
                select '25~37.5bp' bp_range, (a_37_5 - a_25) , (a_fiat_37_5 - a_fiat_25) , (b_37_5 - b_25) , (b_fiat_37_5 - b_fiat_25)  from pbl union all
                select '37.5~50bp' bp_range, (a_50 - a_37_5) , (a_fiat_50 - a_fiat_37_5) , (b_50 - b_37_5) , (b_fiat_50 - b_fiat_37_5)  from pbl union all
                select '50~100bp'  bp_range, (a_100 - a_50)  , (a_fiat_100 - a_fiat_50)  , (b_100 - b_50)  , (b_fiat_100 - b_fiat_50)   from pbl union all
                select '100~200bp' bp_range, (a_200 - a_100) , (a_fiat_200 - a_fiat_100) , (b_200 - b_100) , (b_fiat_200 - b_fiat_100)  from pbl union all
                select '200~400bp' bp_range, (a_400 - a_200) , (a_fiat_400 - a_fiat_200) , (b_400 - b_200) , (b_fiat_400 - b_fiat_200)  from pbl union all
                select '400~800bp' bp_range, (a_800 - a_400) , (a_fiat_800 - a_fiat_400) , (b_800 - b_400) , (b_fiat_800 - b_fiat_400)  from pbl
            ),
            prv as (
                SELECT
                    sum(a_12_5) a_12_5, sum(b_12_5) b_12_5, sum(a_25) a_25, sum(b_25) b_25, 
                    sum(a_37_5) a_37_5, sum(b_37_5) b_37_5, sum(a_50) a_50, sum(b_50) b_50, 
                    sum(a_100) a_100, sum(b_100) b_100, sum(a_200) a_200, sum(b_200) b_200, 
                    sum(a_400) a_400, sum(b_400) b_400, sum(a_800) a_800, sum(b_800) b_800, 
                    sum(a_fiat_12_5) a_fiat_12_5, sum(b_fiat_12_5) b_fiat_12_5, sum(a_fiat_25) a_fiat_25, sum(b_fiat_25) b_fiat_25, 
                    sum(a_fiat_37_5) a_fiat_37_5, sum(b_fiat_37_5) b_fiat_37_5, sum(a_fiat_50) a_fiat_50, sum(b_fiat_50) b_fiat_50, 
                    sum(a_fiat_100) a_fiat_100, sum(b_fiat_100) b_fiat_100, sum(a_fiat_200) a_fiat_200, sum(b_fiat_200) b_fiat_200, 
                    sum(a_fiat_400) a_fiat_400, sum(b_fiat_400) b_fiat_400, sum(a_fiat_800) a_fiat_800, sum(b_fiat_800) b_fiat_800
                FROM (
                    SELECT 
                        member_id,
                        avg(ask_vol_12_5bp) a_12_5, avg(bid_vol_12_5bp) b_12_5, avg(ask_vol_25bp) a_25, avg(bid_vol_25bp) b_25, 
                        avg(ask_vol_37_5bp) a_37_5, avg(bid_vol_37_5bp) b_37_5, avg(ask_vol_50bp) a_50, avg(bid_vol_50bp) b_50, 
                        avg(ask_vol_100bp) a_100, avg(bid_vol_100bp) b_100, avg(ask_vol_200bp) a_200, avg(bid_vol_200bp) b_200, 
                        avg(ask_vol_400bp) a_400, avg(bid_vol_400bp) b_400, avg(ask_vol_800bp) a_800, avg(bid_vol_800bp) b_800, 
                        avg(ask_fiat_value_12_5bp) a_fiat_12_5, avg(bid_fiat_value_12_5bp) b_fiat_12_5, avg(ask_fiat_value_25bp) a_fiat_25, avg(bid_fiat_value_25bp) b_fiat_25, 
                        avg(ask_fiat_value_37_5bp) a_fiat_37_5, avg(bid_fiat_value_37_5bp) b_fiat_37_5, avg(ask_fiat_value_50bp) a_fiat_50, avg(bid_fiat_value_50bp) b_fiat_50, 
                        avg(ask_fiat_value_100bp) a_fiat_100, avg(bid_fiat_value_100bp) b_fiat_100, avg(ask_fiat_value_200bp) a_fiat_200, avg(bid_fiat_value_200bp) b_fiat_200, 
                        avg(ask_fiat_value_400bp) a_fiat_400, avg(bid_fiat_value_400bp) b_fiat_400, avg(ask_fiat_value_800bp) a_fiat_800, avg(bid_fiat_value_800bp) b_fiat_800
                    FROM private_orderbook_depth 
                    WHERE market = '{market}' 
                    AND DATE_FORMAT(CONVERT_TZ(orderbook_timestamp, 'UTC', '{settings.LOCAL_TIMEZONE}'), '%Y-%m-%d') = '{date_str}'
                    AND member_id in {lp_id}
                    group by member_id
                    ) tbl
            ),
            prv_result as(
                select '0~12.5bp' bp_range, a_12_5 private_ask, a_fiat_12_5 private_ask_fiat, b_12_5 private_bid, b_fiat_12_5 private_bid_fiat from prv union all
                select '12.5~25bp' bp_range, (a_25 - a_12_5) , (a_fiat_25 - a_fiat_12_5) , (b_25 - b_12_5) , (b_fiat_25 - b_fiat_12_5)  from prv union all
                select '25~37.5bp' bp_range, (a_37_5 - a_25) , (a_fiat_37_5 - a_fiat_25) , (b_37_5 - b_25) , (b_fiat_37_5 - b_fiat_25)  from prv union all
                select '37.5~50bp' bp_range, (a_50 - a_37_5) , (a_fiat_50 - a_fiat_37_5) , (b_50 - b_37_5) , (b_fiat_50 - b_fiat_37_5)  from prv union all
                select '50~100bp' bp_range, (a_100 - a_50) , (a_fiat_100 - a_fiat_50) , (b_100 - b_50) , (b_fiat_100 - b_fiat_50)  from prv union all
                select '100~200bp' bp_range, (a_200 - a_100) , (a_fiat_200 - a_fiat_100) , (b_200 - b_100) , (b_fiat_200 - b_fiat_100)  from prv union all
                select '200~400bp' bp_range, (a_400 - a_200) , (a_fiat_400 - a_fiat_200) , (b_400 - b_200) , (b_fiat_400 - b_fiat_200)  from prv union all
                select '400~800bp' bp_range, (a_800 - a_400) , (a_fiat_800 - a_fiat_400) , (b_800 - b_400) , (b_fiat_800 - b_fiat_400)  from prv
            )
            select 
                pbl_result.bp_range, 
                public_ask, public_ask_fiat, private_ask, private_ask_fiat, IFNULL((private_ask * 100.0 / public_ask),0) AS ask_pct,
                public_bid, public_bid_fiat, private_bid, private_bid_fiat, IFNULL((private_bid * 100.0 / public_bid),0) AS bid_pct
            from pbl_result, prv_result
            where pbl_result.bp_range = prv_result.bp_range
        """

        # print(query)
        df = exe_query('django', query)
        # print(df)

        return df