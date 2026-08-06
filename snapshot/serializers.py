import pytz
from django.conf import settings
from rest_framework import serializers

from .models.snapshot import AccountSnapshotLp, AccountVersionSnapshot, PublicOrderbookSnapshot


class AccountVersionSnapshotSerializer(serializers.ModelSerializer):
    class Meta:
        model = AccountVersionSnapshot
        fields = '__all__'


class AccountSnapshotLpSerializer(serializers.ModelSerializer):
    imported_at_localtime = serializers.SerializerMethodField()

    class Meta:
        model = AccountSnapshotLp
        fields = '__all__'

    def get_imported_at_localtime(self, obj):
        if obj.imported_at:
            local_tz = pytz.timezone(settings.LOCAL_TIMEZONE)
            local_dt = obj.imported_at.astimezone(local_tz)
            return local_dt.strftime('%Y-%m-%d %H:%M:%S')
        return None


class PublicOrderbookSnapshotSerializer(serializers.ModelSerializer):
    created_at_localtime = serializers.SerializerMethodField()

    class Meta:
        model = PublicOrderbookSnapshot
        fields = '__all__'

    def get_created_at_localtime(self, obj):
        if obj.created_at:
            local_tz = pytz.timezone(settings.LOCAL_TIMEZONE)
            local_dt = obj.created_at.astimezone(local_tz)
            return local_dt.strftime('%Y-%m-%d %H:%M:%S')
        return None
