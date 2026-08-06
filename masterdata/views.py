# views.py
import pandas as pd
from django.conf import settings
from rest_framework import generics, status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.views import APIView

from .models.sec import (AssetMaster, DashboardAlertMaster,
                         DashboardRulesetMaster, LpMaster, MarketMaster)
from .serializers import (AssetMasterSerializer,
                          DashboardAlertMasterSerializer, LpMasterSerializer)


class AssetListAPIView(generics.ListAPIView):
    queryset = AssetMaster.objects.all()
    serializer_class = AssetMasterSerializer
    
    def get_queryset(self):
        """
        Optionally filter assets by currency_ticker
        """
        queryset = AssetMaster.objects.all()
        currency = self.request.query_params.get('currency_ticker', None)
        if currency is not None:
            queryset = queryset.filter(currency_ticker=currency)
        return queryset.order_by('enum_value')


@api_view(['GET'])
def listed_asset_symbols(request):
    df = pd.read_json("https://id-crix-static.upbit.com/crix_master_id")
    symbols = df[(df['marketState'] == "ACTIVE") & (df['exchange'] == "UPBIT")]['baseCurrencyCode'].drop_duplicates().to_list()

    return Response(symbols)


@api_view(['GET'])
def local_fiat(request):

    return Response({"code": settings.CURRENCY_CODE, "symbol": "Rp"})


class LpMasterListAPIView(generics.ListAPIView):
    queryset = LpMaster.objects.all()
    serializer_class = LpMasterSerializer

@api_view(['GET'])
def market_list(request):
    markets = MarketMaster.objects.values_list('market_name', flat=True)
    result = list(markets)
    return Response(result)


class DashboardAlertView(APIView):
    def get(self, request):
        alert_name = request.query_params.get('alert_name')
        
        if not alert_name:
            return Response(
                {'error': 'alert_name parameter required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        alerts = DashboardAlertMaster.objects.filter(alert_name=alert_name)
        serializer = DashboardAlertMasterSerializer(alerts, many=True)
        return Response(serializer.data)


class ActiveRulesetListView(APIView):
    def get(self, request):
        rulesets = DashboardRulesetMaster.objects.filter(is_active=True).values(
            'ruleset_name',
            'display_name'
        )
        return Response(list(rulesets))
