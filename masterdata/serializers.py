# serializers.py
from rest_framework import serializers
from .models.sec import AssetMaster, LpMaster, DashboardAlertMaster

class AssetMasterSerializer(serializers.ModelSerializer):
    class Meta:
        model = AssetMaster
        fields = ['currency_ticker', 'enum_value']


class LpMasterSerializer(serializers.ModelSerializer):
    class Meta:
        model = LpMaster
        fields = '__all__'


class DashboardAlertMasterSerializer(serializers.ModelSerializer):
    class Meta:
        model = DashboardAlertMaster
        fields = '__all__'
