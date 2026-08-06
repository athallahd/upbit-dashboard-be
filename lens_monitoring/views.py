import calendar
from datetime import date, datetime, timedelta

import pandas as pd
import requests
from dateutil.relativedelta import relativedelta
from django.db.models import (Count, ExpressionWrapper, F, FloatField, Sum,
                              Value)
from django.db.models.functions import (TruncDay, TruncMonth, TruncWeek,
                                        TruncYear)
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.views import APIView

from masterdata.models.sec import DashboardRulesetMaster, MarketMaster
from masterdata.registry import MODEL_REGISTRY

from .models.monitoring import (FeeVolumeJoinAssetMaster, TradingVolume,
                                TradingVolumeJoinAssetMaster)
from .serializers import (MarketTradingVolumListSerializer,
                          TradingVolumeSerializer, TradingVolumListSerializer)

__marketListChache =[] # ['SGD', 'USDT', ...]
def markets_chache () :
    global __marketListChache 
    if __marketListChache is None or len(__marketListChache) == 0:
        markets = MarketMaster.objects.values_list('market_name', flat=True)
        __marketListChache = list(markets)
    return __marketListChache

__tickerListByMarketChache ={} # { "SGD": ["USDT", "SOL", "BTC", "XRP", "ETH", ...], "USDT": [...], ...}
def market_ticker_chache():
    global __tickerListByMarketChache
    if __tickerListByMarketChache is not None and len(__tickerListByMarketChache) > 0:
        return __tickerListByMarketChache
    
    marketListChache = markets_chache()
    joined_currencies = ",".join(marketListChache)
    
    url = f"https://id-api.upbit.com/v1/ticker/all?quote_currencies={joined_currencies}"
    response = requests.get(url)
    if response.status_code != 200:
        return Response({'error': 'Failed to fetch ticker data'}, status=500)
    data = response.json()

    result = {}
    for qc in marketListChache:
        # Take only the symbols after the hyphen (-) and make them into a list.
        filtered = [
            item['market'].split('-', 1)[1] 
            for item in data 
            if item['market'].startswith(qc + "-")
        ]
        result[qc] = filtered
    __tickerListByMarketChache = result
    # global allTickerChach
    # allTickerChach = list({t for v in tickerListByMarketChache.values() for t in v})
    return __tickerListByMarketChache

__allTickerChach=[]
def all_ticker_chach() : 
    global __allTickerChach
    if __allTickerChach is not None and len(__allTickerChach) > 0:
        return __allTickerChach
    
    tickerListByMarketChache = market_ticker_chache()
    
    __allTickerChach = list({t for v in tickerListByMarketChache.values() for t in v})
    return __allTickerChach


# API for retrieving data from the 'lens_trading_volume' table.
@api_view(['GET'])
def trading_volume_list (request) :
    items = TradingVolume.objects.all()
    serializer = TradingVolumeSerializer(items, many=True)
    return Response(serializer.data)


@api_view(['GET'])
def trading_volume_currency_list(request):

    market_param = request.query_params.get('market', None)
    marketListChache = markets_chache()
    allTickerChach = all_ticker_chach()
    tickerListByMarketChache = market_ticker_chache()
    
    if (market_param != "ALL") :
        if market_param not in marketListChache:
            return Response({'error': 'Invalid or missing market parameter'}, status=400)

    if (market_param == "ALL") : # All market
        currencies = (TradingVolumeJoinAssetMaster.objects
                      .filter(market__in=marketListChache, assetmaster__currency_ticker__in=allTickerChach)
                      .values_list('assetmaster__currency_ticker', flat=True).distinct().order_by('assetmaster__currency_ticker'))
    else :
        currencies = (TradingVolumeJoinAssetMaster.objects
                      .filter(market=market_param, assetmaster__currency_ticker__in=tickerListByMarketChache[market_param])
                      .values_list('assetmaster__currency_ticker', flat=True).distinct().order_by('assetmaster__currency_ticker'))
    # print(currencies.query)
    unique_currencies = [c for c in currencies if c is not None]
    return Response(unique_currencies)



@api_view(['GET'])
def trading_volume_asset_percentage(request):

    market_param = request.query_params.get('market', None)
    marketListChache = markets_chache()
    allTickerChach = all_ticker_chach()
    tickerListByMarketChache = market_ticker_chache()


    if (market_param != "ALL") :
        if market_param not in marketListChache:
            return Response({'error': 'Invalid or missing market parameter'}, status=400)

    volume_field_map = {
        'IDR': 'vol_local_currency',
        'BTC': 'btc_vol',
        'USDT': 'usdt_vol',
        'ALL' : 'fiat_vol',
    }
    volume_field = volume_field_map[market_param]
    
    if market_param == "ALL" : # All market
        # Calculate the total volume 
        total_volume_subquery = (TradingVolumeJoinAssetMaster.objects
                                 .filter(market__in=marketListChache, assetmaster__currency_ticker__in=allTickerChach)
                                 .aggregate(total=Sum(volume_field))['total'] or 0)
        # Set a temporary value to handle division when the total is 0
        total_volume = total_volume_subquery if total_volume_subquery != 0 else 1

        # Calculate the sum and percentage of volume by asset_name, sorted by highest first.
        queryset = (
            TradingVolumeJoinAssetMaster.objects
            .filter(market__in=marketListChache, assetmaster__currency_ticker__in=allTickerChach)
            .values(ticker=F('assetmaster__currency_ticker'))
            .annotate(volume_sum=Sum(volume_field))
            .annotate(
                percentage=ExpressionWrapper(
                    F('volume_sum') * 100.0 / Value(total_volume),
                    output_field=FloatField()
                )
            )
            .order_by('-percentage')
        )

    else :
        
        # total_volume_subquery = TradingVolume.objects.filter(market=market_param, asset_name__in=allTickerChach).aggregate(total=Sum(volume_field))['total'] or 0
        total_volume_subquery = (TradingVolumeJoinAssetMaster.objects
                                  .filter(market=market_param, assetmaster__currency_ticker__in=tickerListByMarketChache[market_param])
                                  .aggregate(total=Sum(volume_field))['total'] or 0)
        # Set a temporary value to handle division when the total is 0
        total_volume = total_volume_subquery if total_volume_subquery != 0 else 1

        # Calculate the sum and percentage of volume by asset_name, sorted by highest first.
        queryset = (
            TradingVolumeJoinAssetMaster.objects
            .filter(market=market_param, assetmaster__currency_ticker__in=tickerListByMarketChache[market_param])
            .values(ticker=F('assetmaster__currency_ticker'))
            .annotate(volume_sum=Sum(volume_field))
            .annotate(
                percentage=ExpressionWrapper(
                    F('volume_sum') * 100.0 / Value(total_volume),
                    output_field=FloatField()
                )
            )
            .order_by('-percentage')
        )

    result = list(queryset)

    # If the total is 0, set the percentage to 0 as well.
    if total_volume_subquery == 0:
        total_volume = 0 
        for r in result:
            r['percentage'] = 0.0
    
    # Return response including total_avg_price value separately
    return Response({
        'total_volume': total_volume,
        'data': result
    })


# API for retrieving data for the 'Market Trading Volume List.'
@api_view(['GET'])
def market_trading_volume_list(request):

    marketListChache = markets_chache()
    allTickerChach = all_ticker_chach()
    # tickerListByMarketChache = market_ticker_chache()
        
    period = request.query_params.get('period', 'daily')
    period_end = request.query_params.get('period_end')  # YYYY-MM 

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

    baseQuerySet = TradingVolumeJoinAssetMaster.objects.annotate(
        Target_date=trunc_func('trade_date')
    )

    if start_date:
        baseQuerySet = baseQuerySet.filter(trade_date__gte=start_date, trade_date__lte=end_date, 
                                       market__in=marketListChache, assetmaster__currency_ticker__in=allTickerChach)
    else : 
        baseQuerySet = baseQuerySet.filter(market__in=marketListChache, assetmaster__currency_ticker__in=allTickerChach)

    # Make ALL Market Datas
    all_market_qs = baseQuerySet.values('Target_date').annotate(volume_sum=Sum('fiat_vol')).order_by('Target_date')
    # print(all_market_qs.query)
    all_market_data = [
        {
            "Target_date": row["Target_date"],
            "market": "Total",
            "volume_sum": row["volume_sum"],
        }
        for row in all_market_qs
    ]

    # Make Per Market Datas
    per_market_qs = baseQuerySet.values('Target_date', 'market').annotate(volume_sum=Sum('fiat_vol')).order_by('Target_date', 'market')
    # print(per_market_qs.query)
    per_market_data = [
        {
            "Target_date": row["Target_date"],
            "market": row["market"],
            "volume_sum": row["volume_sum"],
        }
        for row in per_market_qs
    ]

    result = per_market_data + all_market_data
    result_sorted = sorted(
        result,
        key=lambda x: (x["Target_date"], x["market"])
    )
            
    serializer = MarketTradingVolumListSerializer(result_sorted, many=True)
    return Response(serializer.data)
    


# API for retrieving data for the 'Crypto Trading Volume Dashboard.'
@api_view(['GET'])
def trading_volume_list(request):

    market_param = request.query_params.get('market', None)

    marketListChache = markets_chache()
    allTickerChach = all_ticker_chach()
    tickerListByMarketChache = market_ticker_chache()
    
    if (market_param != "ALL") :
        if market_param not in marketListChache:
            return Response({'error': 'Invalid or missing market parameter'}, status=400)
        
    period = request.query_params.get('period', 'daily')
    period_end = request.query_params.get('period_end')  # YYYY-MM 

    trunc_func_map = {
        'daily': TruncDay,
        'weekly': TruncWeek,
        'monthly': TruncMonth,
        'annual': TruncYear,
    }
    
    trunc_func = trunc_func_map.get(period)
    if trunc_func is None:
        return Response({'error': 'Invalid period parameter'}, status=400)
    
    # DB Colume 
    volume_field_map = {
        'IDR': 'vol_local_currency',
        'BTC': 'btc_vol',
        'USDT': 'usdt_vol',
        'ALL' : 'fiat_vol',
    }
    volume_field = volume_field_map[market_param]

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

    queryset = TradingVolumeJoinAssetMaster.objects.annotate(
        Target_date=trunc_func('trade_date')
    )

    if market_param == "ALL" : 

        if start_date:
            queryset = queryset.filter(trade_date__gte=start_date, trade_date__lte=end_date, 
                                       market__in=marketListChache, assetmaster__currency_ticker__in=allTickerChach)
        else : 
            queryset = queryset.filter(market__in=marketListChache, assetmaster__currency_ticker__in=allTickerChach)

        queryset = queryset.values('Target_date', 'assetmaster__currency_ticker').annotate(
            volume_sum=Sum(volume_field)
        ).order_by('Target_date')

    else :

        if start_date:
            queryset = queryset.filter(trade_date__gte=start_date, trade_date__lte=end_date, 
                                       market=market_param, assetmaster__currency_ticker__in=tickerListByMarketChache[market_param])
        else : 
            queryset = queryset.filter(market=market_param, assetmaster__currency_ticker__in=tickerListByMarketChache[market_param])
            
        queryset = queryset.values('Target_date', 'assetmaster__currency_ticker').annotate(
            volume_sum=Sum(volume_field)
        ).order_by('Target_date')
    # print(queryset.query)
    serializer = TradingVolumListSerializer(queryset, many=True)
    return Response(serializer.data)


@api_view(['GET'])
def fee_volume_currency_list(request):

    allTickerChach = all_ticker_chach()

    currencies = (FeeVolumeJoinAssetMaster.objects
                    .filter(assetmaster__currency_ticker__in=allTickerChach)
                    .values_list('assetmaster__currency_ticker', flat=True)
                    .distinct().order_by('assetmaster__currency_ticker'))

    unique_currencies = [c for c in currencies if c is not None]

    return Response(unique_currencies)


@api_view(['GET'])
def fee_volume_list(request):

    allTickerChach = all_ticker_chach()

    volume_field, trunc_func, start_date, end_date = set_condition(request)

    queryset = (FeeVolumeJoinAssetMaster.objects
                    .filter(assetmaster__currency_ticker__in=allTickerChach)
                    .annotate(Target_date=trunc_func('target_date'))
                    .values('Target_date', 'assetmaster__currency_ticker'))

    if start_date:
        queryset = queryset.filter(target_date__gte=start_date, target_date__lte=end_date)

    if volume_field == "volume_sum" : 
        volume_field = Sum(F('ask_fiat_fee') + F('bid_fiat_fee') + F('withdraw_fiat_fee'))
    elif volume_field == "trading_fee":
        volume_field = Sum(F('ask_fiat_fee') + F('bid_fiat_fee'))
    else:
        volume_field = Sum(volume_field)

    queryset = queryset.annotate(volume_sum=volume_field).order_by('Target_date')

    df_base = pd.DataFrame.from_records(queryset)
    df_sum = df_base.groupby('Target_date')['volume_sum'].sum().reset_index()
    df_sum.columns = ['Target_date','volume_sum']
    df_sum['assetmaster__currency_ticker'] = 'Total'

    df = pd.concat([df_base, df_sum], ignore_index=True)
    df.sort_values(by='Target_date', ascending=True, inplace=True)
    df = df.reset_index(drop=True)
    df = df.to_dict('records')

    serializer = TradingVolumListSerializer(df, many=True)

    return Response(serializer.data)


@api_view(['GET'])
def fee_volume_total(request):

    allTickerChach = all_ticker_chach()

    volume_field, trunc_func, start_date, end_date = set_condition(request)

    queryset = (FeeVolumeJoinAssetMaster.objects
                    .filter(assetmaster__currency_ticker__in=allTickerChach)
                    .annotate(Target_date=trunc_func('target_date'))
                    .values('Target_date', 'assetmaster__currency_ticker'))

    if start_date:
        queryset = queryset.filter(target_date__gte=start_date, target_date__lte=end_date)

    if volume_field == "volume_sum" : 
        volume_field = Sum(F('ask_fiat_fee') + F('bid_fiat_fee') + F('withdraw_fiat_fee'))
    elif volume_field == "trading_fee":
        volume_field = Sum(F('ask_fiat_fee') + F('bid_fiat_fee'))
    else:
        volume_field = Sum(volume_field)

    queryset = queryset.annotate(volume_sum=volume_field).order_by('Target_date')

    serializer = TradingVolumListSerializer(queryset, many=True)
    
    return Response(serializer.data)


@api_view(['GET'])
def fee_volume_asset_percentage(request):

    allTickerChach = all_ticker_chach()
    event_param = request.query_params.get('event', None)

    volume_field = get_selected_event(event_param)

    total_volume_queryset = FeeVolumeJoinAssetMaster.objects.filter(assetmaster__currency_ticker__in=allTickerChach)
    perc_volume_queryset = total_volume_queryset.values(ticker=F('assetmaster__currency_ticker'))

    if volume_field == "volume_sum" : 
        volume_field = Sum(F('ask_fiat_fee') + F('bid_fiat_fee') + F('withdraw_fiat_fee'))
    elif volume_field == "trading_fee":
        volume_field = Sum(F('ask_fiat_fee') + F('bid_fiat_fee'))
    else:
        volume_field = Sum(volume_field)

    dict_total_volume = total_volume_queryset.aggregate(volume_sum=volume_field)
    perc_volume_queryset = perc_volume_queryset.annotate(volume_sum=volume_field)

    dict_total_volume = dict_total_volume['volume_sum'] or 0
    total_volume = dict_total_volume if dict_total_volume != 0 else 1

    perc_volume_queryset = perc_volume_queryset.annotate(
                                percentage=ExpressionWrapper(
                                    F('volume_sum') * 100.0 / Value(total_volume),
                                    output_field=FloatField()
                                )
                            ).order_by('-percentage')

    result = list(perc_volume_queryset)

    # If the total is 0, set the percentage to 0 as well.
    if dict_total_volume == 0:
        total_volume = 0 
        for r in result:
            r['percentage'] = 0.0
    
    # Return response including total_avg_price value separately
    return Response({
        'total_volume': total_volume,
        'data': result
    })


def set_condition(request):
    
    event_param = request.query_params.get('event', None)
    volume_field = get_selected_event(event_param)    

    period = request.query_params.get('period', 'daily')
    period_end = request.query_params.get('period_end')  # YYYY-MM 

    trunc_func = get_selected_period(period)
    if trunc_func is None:
        return Response({'error': 'Invalid period parameter'}, status=400)
    
    start_date, end_date = get_period(period_end, period)

    return volume_field, trunc_func, start_date, end_date

def get_selected_event(event_param):
    volume_field_map = {
        'Ask': 'ask_fiat_fee',
        'Bid': 'bid_fiat_fee',
        'Withdraw': 'withdraw_fiat_fee',
        'ALL' : 'volume_sum',
        'Trading(Ask+Bid)' : 'trading_fee',
    }

    volume_field = volume_field_map[event_param]
    return volume_field


def get_selected_period(period):
    trunc_func_map = {
        'daily': TruncDay,
        'weekly': TruncWeek,
        'monthly': TruncMonth,
        'annual': TruncYear,
    }
    
    trunc_func = trunc_func_map.get(period)
    return trunc_func


def get_period(period_end, period):
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
        start_date = end_date - relativedelta(days=30)
    elif period == 'weekly':
        start_date = end_date - timedelta(weeks=30)
    elif period == 'monthly':
        start_date = end_date - relativedelta(months=30)
    else:
        start_date = None  # yearly or no limit

    return start_date, end_date


@api_view(['GET'])
def market_fee_volume_list(request):

    marketListChache = markets_chache()
    allTickerChach = all_ticker_chach()

    period = request.query_params.get('period', 'daily')
    period_end = request.query_params.get('period_end')  # YYYY-MM 

    trunc_func = get_selected_period(period)

    if trunc_func is None:
        return Response({'error': 'Invalid period parameter'}, status=400)
    
    start_date, end_date = get_period(period_end, period)

    baseQuerySet = FeeVolumeJoinAssetMaster.objects.annotate(
        Target_date=trunc_func('target_date')
    )
    print(baseQuerySet.query)
    
    if start_date:
        baseQuerySet = baseQuerySet.filter(target_date__gte=start_date, target_date__lte=end_date, 
                                    market__in=marketListChache, assetmaster__currency_ticker__in=allTickerChach)
    else : 
        baseQuerySet = baseQuerySet.filter(market__in=marketListChache, assetmaster__currency_ticker__in=allTickerChach)


    volume_field = Sum(F('ask_fiat_fee') + F('bid_fiat_fee'))



    # Make ALL Market Datas
    all_market_qs = baseQuerySet.values('Target_date').annotate(volume_sum=volume_field).order_by('Target_date')
    # print(all_market_qs.query)
    all_market_data = [
        {
            "Target_date": row["Target_date"],
            "market": "Total",
            "volume_sum": row["volume_sum"],
        }
        for row in all_market_qs
    ]

    # Make Per Market Datas
    per_market_qs = baseQuerySet.values('Target_date', 'market').annotate(volume_sum=volume_field).order_by('Target_date', 'market')
    # print(per_market_qs.query)
    per_market_data = [
        {
            "Target_date": row["Target_date"],
            "market": row["market"],
            "volume_sum": row["volume_sum"],
        }
        for row in per_market_qs
    ]

    result = per_market_data + all_market_data
    result_sorted = sorted(
        result,
        key=lambda x: (x["Target_date"], x["market"])
    )

    serializer = MarketTradingVolumListSerializer(result_sorted, many=True)
    return Response(serializer.data)


class LensEventsSummaryView(APIView):
    """Get counts for all LENS events aggregated by period"""

    def get_date_format(self, date_field, period):
        return {
            'daily': f"DATE_FORMAT({date_field}, '%%Y-%%m-%%d')",
            'weekly': f"DATE_FORMAT(DATE_SUB({date_field}, INTERVAL WEEKDAY({date_field}) DAY), '%%Y-%%m-%%d')",
            'monthly': f"DATE_FORMAT({date_field}, '%%Y-%%m')"
        }.get(period)

    def validate_period(self, period):
        if period not in ['daily', 'weekly', 'monthly']:
            return False, Response({
                'error': f'Invalid period: {period}. Must be one of: daily, weekly, monthly',
                'code': 'invalid_period'
            }, status=status.HTTP_400_BAD_REQUEST)
        return True, None

    def apply_date_filters(self, queryset, date_field, start_date, end_date):
        if start_date:
            try:
                start_date_parsed = datetime.strptime(start_date, '%Y-%m-%d').date()
                queryset = queryset.filter(**{f'{date_field}__gte': start_date_parsed})
            except ValueError:
                return None, Response({
                    'error': 'Invalid start_date format. Use YYYY-MM-DD',
                    'code': 'invalid_date_format'
                }, status=status.HTTP_400_BAD_REQUEST)

        if end_date:
            try:
                end_date_parsed = datetime.strptime(end_date, '%Y-%m-%d').date()
                queryset = queryset.filter(**{f'{date_field}__lte': end_date_parsed})
            except ValueError:
                return None, Response({
                    'error': 'Invalid end_date format. Use YYYY-MM-DD',
                    'code': 'invalid_date_format'
                }, status=status.HTTP_400_BAD_REQUEST)
        else:
            queryset = queryset.filter(**{f'{date_field}__lte': date.today()})

        return queryset, None

    def get_event_counts(self, model, date_field, period, start_date, end_date):
        queryset = model.objects.all()

        queryset, error = self.apply_date_filters(queryset, date_field, start_date, end_date)
        if error:
            return None, error

        date_format = self.get_date_format(date_field, period)

        aggregated = queryset.extra(
            select={'period': date_format}
        ).values('period').annotate(
            count=Count('id')
        ).order_by('period')

        return {item['period']: item['count'] for item in aggregated}, None

    def add_weekly_labels(self, data, period):
        if period == 'weekly':
            for item in data:
                start = datetime.strptime(item['period'], '%Y-%m-%d').date()
                week_end = (start + timedelta(days=6)).strftime('%Y-%m-%d')
                item['week_end'] = week_end
                item['period_label'] = f"{item['period']} to {week_end}"
        return data

    def get(self, request):
        period = request.query_params.get('period', 'daily')
        limit = int(request.query_params.get('limit', 0))
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')

        is_valid, error_response = self.validate_period(period)
        if not is_valid:
            return error_response

        active_rulesets = DashboardRulesetMaster.objects.filter(is_active=True)

        all_periods = set()
        ruleset_counts = {}
        ruleset_display_names = {}

        for ruleset in active_rulesets:
            model_class = MODEL_REGISTRY.get(ruleset.ruleset_name)
            if not model_class:
                continue

            date_field = getattr(model_class, 'DATE_FIELD', 'target_date')

            counts, error = self.get_event_counts(model_class, date_field, period, start_date, end_date)
            if error:
                return error

            ruleset_counts[ruleset.ruleset_name] = counts
            ruleset_display_names[ruleset.ruleset_name] = ruleset.display_name
            all_periods.update(counts.keys())

        data = []
        for period_key in sorted(all_periods):
            row = {'period': period_key, 'total_count': 0}
            for ruleset_name, counts in ruleset_counts.items():
                count = counts.get(period_key, 0)
                row[ruleset_name] = {
                    'count': count,
                    'name': ruleset_display_names[ruleset_name]
                }
                row['total_count'] += count
            data.append(row)

        if limit > 0:
            data = data[:limit]

        data = self.add_weekly_labels(data, period)
        return Response(data)
