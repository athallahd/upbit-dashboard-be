# views.py
# views.py
from datetime import datetime, timedelta

import pytz
from django.conf import settings
from django.utils import timezone
from django_filters import DateFilter, FilterSet
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, generics
from rest_framework.decorators import api_view
from rest_framework.response import Response

from snapshot.models.snapshot import AccountSnapshotLp, AccountVersionSnapshot, PublicOrderbookSnapshot
from snapshot.serializers import (AccountSnapshotLpSerializer,
                                  AccountVersionSnapshotSerializer, PublicOrderbookSnapshotSerializer)


class AccountVersionSnapshotFilter(FilterSet):
    target_date = DateFilter(field_name='target_date')
    
    class Meta:
        model = AccountVersionSnapshot
        fields = ['target_date', 'member_id',]


class AccountVersionSnapshotListAPIView(generics.ListAPIView):
    queryset = AccountVersionSnapshot.objects.all()
    serializer_class = AccountVersionSnapshotSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_class = AccountVersionSnapshotFilter
    ordering_fields = ['target_date',]
    ordering = ['-target_date']


@api_view(['GET'])
def balance_snapshot_by_period(request):
    """Get balance snapshots aggregated by period"""
    member_id = request.query_params.get('member_id')
    period = request.query_params.get('period', 'daily')  # daily, weekly, monthly, annual
    limit = int(request.query_params.get('limit', 0))  # 0 = no limit, 90 = last 90 points
    start_date = request.query_params.get('start_date')
    end_date = request.query_params.get('end_date')
    
    if not member_id:
        return Response({'error': 'member_id is required'}, status=400)
    
    # First check if member exists
    member_exists = AccountVersionSnapshot.objects.filter(member_id=member_id).exists()
    if not member_exists:
        return Response({
            'error': f'No data found for member_id: {member_id}',
            'code': 'member_not_found'
        }, status=404)
    
    # Apply date filtering
    if start_date:
        try:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        except ValueError:
            return Response({
                'error': 'Invalid start_date format. Use YYYY-MM-DD',
                'code': 'invalid_date_format'
            }, status=400)
    
    if end_date:
        try:
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
        except ValueError:
            return Response({
                'error': 'Invalid end_date format. Use YYYY-MM-DD',
                'code': 'invalid_date_format'
            }, status=400)
    else:
        # Default to current date if no end_date provided
        from datetime import date
        end_date = date.today()
    
    # Define date format for all periods
    date_format_map = {
        'daily': "DATE_FORMAT(target_date, '%%Y-%%m-%%d')",
        'weekly': "DATE_FORMAT(DATE_SUB(target_date, INTERVAL WEEKDAY(target_date) DAY), '%%Y-%%m-%%d')",  # Start of week (Monday)
        'monthly': "DATE_FORMAT(target_date, '%%Y-%%m')",
        'annual': "DATE_FORMAT(target_date, '%%Y')"
    }
    
    date_format = date_format_map.get(period)
    if not date_format:
        return Response({
            'error': f'Invalid period: {period}. Must be one of: daily, weekly, monthly, annual',
            'code': 'invalid_period'
        }, status=400)
    
    # Use GROUP BY with MAX instead of window function for better performance
    from django.db import connection
    
    with connection.cursor() as cursor:
        sql = f"""
        SELECT 
            ps.period,
            ps.currency,
            avs.amount as total_amount,
            avs.btc_amount as total_btc_amount,
            avs.value_btc_market as total_value_btc_market,
            avs.value_fiat_market as total_value_fiat_market,
            ps.max_date as latest_date
        FROM (
            SELECT 
                {date_format} as period,
                currency,
                MAX(target_date) as max_date
            FROM account_version_snapshot2
            WHERE member_id = %s
        """
        
        params = [member_id]
        
        # Add date filtering to the subquery
        if start_date:
            sql += " AND target_date >= %s"
            params.append(start_date)
        
        sql += " AND target_date <= %s"
        params.append(end_date)
            
        sql += f"""
            GROUP BY {date_format}, currency
        ) ps
        INNER JOIN account_version_snapshot2 avs
            ON avs.member_id = %s
            AND avs.target_date = ps.max_date
            AND avs.currency = ps.currency
        """
        
        # Add member_id again for the JOIN
        params.append(member_id)
        
        # Apply limit if specified
        if limit > 0:
            sql += " ORDER BY ps.period DESC LIMIT {}".format(limit)
        else:
            sql += " ORDER BY ps.period DESC"
        
        cursor.execute(sql, params)
        columns = [col[0] for col in cursor.description]
        data = [dict(zip(columns, row)) for row in cursor.fetchall()]
    
    # Format the data and add week end date for weekly period
    for item in data:
        # Format decimal amounts to strings for JSON serialization
        item['total_amount'] = str(item['total_amount']) if item['total_amount'] else '0'
        item['total_btc_amount'] = str(item['total_btc_amount']) if item['total_btc_amount'] else '0'
        item['total_value_btc_market'] = str(item['total_value_btc_market']) if item['total_value_btc_market'] else '0'
        item['total_value_fiat_market'] = str(item['total_value_fiat_market']) if item['total_value_fiat_market'] else '0'
        item['latest_date'] = item['latest_date'].strftime('%Y-%m-%d') if item['latest_date'] else ''
        
        # Add week end date for weekly period
        if period == 'weekly':
            week_start = datetime.strptime(item['period'], '%Y-%m-%d').date()
            item['week_end'] = (week_start + timedelta(days=6)).strftime('%Y-%m-%d')
            item['period_label'] = f"{item['period']} to {item['week_end']}"
    
    return Response(data)


class AccountSnapshotLpFilter(FilterSet):
    imported_at_date = DateFilter(method='filter_by_local_date')
    
    def filter_by_local_date(self, queryset, name, value):
        if value:
            local_tz = pytz.timezone(settings.LOCAL_TIMEZONE)
            # Convert the date to local timezone start/end of day
            local_start = local_tz.localize(timezone.datetime.combine(value, timezone.datetime.min.time()))
            local_end = local_tz.localize(timezone.datetime.combine(value, timezone.datetime.max.time()))
            
            # Convert to UTC for DB query
            utc_start = local_start.astimezone(pytz.UTC)
            utc_end = local_end.astimezone(pytz.UTC)
            
            return queryset.filter(imported_at__range=(utc_start, utc_end))
        return queryset
    
    class Meta:
        model = AccountSnapshotLp
        fields = ['member_id', 'currency']


class AccountSnapshotLpListView(generics.ListAPIView):
    queryset = AccountSnapshotLp.objects.all()
    serializer_class = AccountSnapshotLpSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_class = AccountSnapshotLpFilter
    ordering_fields = ['imported_at', 'member_id']
    ordering = ['-imported_at']


class PublicOrderbookSnapshotFilter(FilterSet):
    created_at_date = DateFilter(method='filter_by_local_date')
    
    def filter_by_local_date(self, queryset, name, value):
        if value:
            local_tz = pytz.timezone(settings.LOCAL_TIMEZONE)
            # Convert the date to local timezone start/end of day
            local_start = local_tz.localize(
                timezone.datetime.combine(value, timezone.datetime.min.time())
            )
            local_end = local_tz.localize(
                timezone.datetime.combine(value, timezone.datetime.max.time())
            )
            # Convert to UTC for DB query
            utc_start = local_start.astimezone(pytz.UTC)
            utc_end = local_end.astimezone(pytz.UTC)
            return queryset.filter(created_at__range=(utc_start, utc_end))
        return queryset
    
    class Meta:
        model = PublicOrderbookSnapshot
        fields = ['created_at_date']


class PublicOrderbookSnapshotListView(generics.ListAPIView):
    queryset = PublicOrderbookSnapshot.objects.all()
    serializer_class = PublicOrderbookSnapshotSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_class = PublicOrderbookSnapshotFilter
    ordering_fields = ['created_at']
    ordering = ['-created_at']
