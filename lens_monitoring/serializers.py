from rest_framework import serializers
from .models.monitoring import TradingVolume, TradingVolumeJoinAssetMaster, LensFiatFeeVolume, FeeVolumeJoinAssetMaster

#Serializer for retrieving data from the 'lens_trading_volume' table.
class TradingVolumeSerializer(serializers.ModelSerializer):
    class Meta:
        model = TradingVolume
        fields = '__all__'


class TradingVolumListSerializer(serializers.ModelSerializer):
    date = serializers.DateField(read_only=True, source='Target_date')
    ticker = serializers.CharField(read_only=True, source='assetmaster__currency_ticker')
    # volume = serializers.DecimalField( read_only=True, max_digits=38, decimal_places=8, source='vol_asset')//Trading volume.
    volume = serializers.DecimalField( read_only=True, max_digits=38, decimal_places=8, source='volume_sum') 

    class Meta:
        model = TradingVolumeJoinAssetMaster
        fields = ['date', 'ticker', 'volume']

class MarketTradingVolumListSerializer(serializers.ModelSerializer):
    date = serializers.DateField(read_only=True, source='Target_date')
    # market = serializers.CharField(read_only=True, source='market')
    # volume = serializers.DecimalField( read_only=True, max_digits=38, decimal_places=8, source='vol_asset')//Trading volume.
    volume = serializers.DecimalField( read_only=True, max_digits=38, decimal_places=8, source='volume_sum') 

    class Meta:
        model = TradingVolumeJoinAssetMaster
        fields = ['date', 'market', 'volume']


class FeeVolumeSerializer(serializers.ModelSerializer):
    class Meta:
        model = LensFiatFeeVolume
        fields = '__all__'


# class FeeVolumListSerializer(serializers.ModelSerializer):
#     date = serializers.DateField(read_only=True, source='Target_date')
#     ticker = serializers.CharField(read_only=True, source='assetmaster__currency_ticker')
#     fee = serializers.DecimalField(read_only=True, max_digits=38, decimal_places=8, source='fee_sum') 

#     class Meta:
#         model = FeeVolumeJoinAssetMaster
#         fields = ['date', 'ticker', 'fee']


class MarketFeeVolumListSerializer(serializers.ModelSerializer):
    date = serializers.DateField(read_only=True, source='Target_date')
    # market = serializers.CharField(read_only=True, source='market')
    # volume = serializers.DecimalField( read_only=True, max_digits=38, decimal_places=8, source='vol_asset')//Trading volume.
    volume = serializers.DecimalField( read_only=True, max_digits=38, decimal_places=8, source='volume_sum') 

    class Meta:
        model = FeeVolumeJoinAssetMaster
        fields = ['date', 'market', 'volume']