from rest_framework import serializers
from .models.data import OrderBase, OrderCountSummary, PrivateOrderbookDepth, PublicOrderbookDepth, DepositBase, WithdrawBase, DepositBaseJoinAssetMaster, WithdrawBaseJoinAssetMaster


class OrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderBase
        fields = '__all__'


class OrderCountSummarySerializer(serializers.ModelSerializer):
    buy_percentage = serializers.ReadOnlyField()
    sell_percentage = serializers.ReadOnlyField()
    algo_percentage = serializers.ReadOnlyField()
    non_algo_percentage = serializers.ReadOnlyField()

    class Meta:
        model = OrderCountSummary
        fields = [
            'id', 'order_date', 'asset_id', 'currency_id', 'customer_code',
            'total_orders', 'buy_orders', 'sell_orders', 'algo_orders', 'non_algo_orders',
            'buy_percentage', 'sell_percentage', 'algo_percentage', 'non_algo_percentage',
            'created_at', 'updated_at'
        ]


class PrivateOrderbookDepthSerializer(serializers.ModelSerializer):
    orderbook_timestamp = serializers.ReadOnlyField()
    
    class Meta:
        model = PrivateOrderbookDepth
        fields = '__all__'


class PublicOrderbookDepthSerializer(serializers.ModelSerializer):
    orderbook_timestamp = serializers.ReadOnlyField()
    
    class Meta:
        model = PublicOrderbookDepth
        fields = '__all__'


class DepositVolumeSerializer(serializers.ModelSerializer):
    date = serializers.DateField(read_only=True, source='Target_date')
    ticker = serializers.CharField(read_only=True, source='assetmaster__currency_ticker')
    volume = serializers.DecimalField( read_only=True, max_digits=38, decimal_places=20, source='volume_sum')
    class Meta:
        model = DepositBaseJoinAssetMaster
        fields = ['date', 'ticker', 'volume']


class WithdrawVolumeSerializer(serializers.ModelSerializer):
    date = serializers.DateField(read_only=True, source='Target_date')
    ticker = serializers.CharField(read_only=True, source='assetmaster__currency_ticker')
    volume = serializers.DecimalField( read_only=True, max_digits=38, decimal_places=20, source='volume_sum')
    class Meta:
        model = WithdrawBaseJoinAssetMaster
        fields = ['date', 'ticker', 'volume']


class LPEvaluationComparisonSerializer(serializers.Serializer):
    """Serializer for LP evaluation comparison data."""
    period = serializers.CharField(help_text="Month (YYYY-MM) or Date (YYYY-MM-DD)")
    liquidity_provider = serializers.CharField(help_text="LP name or 'All LPs'")
    market = serializers.CharField(help_text="Market symbol (e.g., IDR-USDT)")
    bp_range = serializers.CharField(help_text="Basis point range (e.g., 0~12.5bp)")
    public_ask = serializers.FloatField(help_text="Public orderbook ask volume")
    lp_ask = serializers.FloatField(help_text="LP ask volume")
    ask_percentage = serializers.FloatField(help_text="LP ask volume as % of public")
    public_bid = serializers.FloatField(help_text="Public orderbook bid volume")
    lp_bid = serializers.FloatField(help_text="LP bid volume")
    bid_percentage = serializers.FloatField(help_text="LP bid volume as % of public")
    
    # Fiat value fields
    public_ask_fiat_value = serializers.FloatField(help_text="Public ask volume in fiat value")
    lp_ask_fiat_value = serializers.FloatField(help_text="LP ask volume in fiat value")
    public_bid_fiat_value = serializers.FloatField(help_text="Public bid volume in fiat value")
    lp_bid_fiat_value = serializers.FloatField(help_text="LP bid volume in fiat value")
