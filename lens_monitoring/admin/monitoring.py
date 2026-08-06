import csv
import datetime

from django.conf import settings
from django.contrib import admin
from django.http import HttpResponse
from rangefilter.filters import DateRangeFilter

from lens_monitoring.models.monitoring import *


class ExportCsvMixin:
    def export_as_csv(self, request, queryset):

        meta = self.model._meta
        field_names = [field.name for field in meta.fields]

        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename={}.csv'.format(meta)
        writer = csv.writer(response)

        writer.writerow(field_names)
        for obj in queryset:
            writer.writerow([getattr(obj, field) for field in field_names])

        return response

    export_as_csv.short_description = "Export Selected"


# ----- APAC Rulesets
@admin.register(LensWashTradeApac)
class LensWashTradeApacAdmin(admin.ModelAdmin, ExportCsvMixin):
    list_display = (
        'id',
        'trade_date',
        'asset_name',
        'pair_id',
        '_n_tx',
        '_n_tx_pct',
        'simul_count',
        '_vol_IDR',
        '_total_vol_IDR',
        '_vol',
        '_vol_pct',
        'level',
        'p1_lv1_ratio',
        'p2_lv2_ratio',
        'p3_lv3_ratio',
        'p4_simul_entry',
        '_p5_trade_vol',
        'params_tag',
        'created_at_jkt',
        'updated_at_jkt',
    )

    list_filter = (('trade_date', DateRangeFilter),)

    actions = ['export_as_csv']


    def has_add_permission(self, request):
        return False


    def has_delete_permission(self, request, obj=None):
        return False
    

    def _n_tx(self, obj):
        return str(int(obj.n_tx)).replace(",", "")


    def _n_tx_pct(self, obj):
        return "%.2f" % obj.n_tx_pct
    

    def _vol(self, obj):
        return "%.4f" % obj.vol


    def _vol_IDR(self, obj):
        return "%.2f" % obj.vol_IDR
    

    def _total_vol_IDR(self, obj):
        return "%.2f" % obj.total_vol_IDR


    def _vol_pct(self, obj):
        return "%.2f" % obj.vol_pct
    

    def _p5_trade_vol(self, obj):
        return str(int(obj.p5_trade_vol)).replace(",", "")
    

    def created_at_jkt(self, obj):
        return obj.created_at + datetime.timedelta(hours=settings.LOCAL_TIME_DELTA)
    created_at_jkt.short_description = 'Created at (JKT)'


    def updated_at_jkt(self, obj):
        return obj.updated_at + datetime.timedelta(hours=settings.LOCAL_TIME_DELTA)
    updated_at_jkt.short_description = 'Updated at (JKT)'


@admin.register(LensFATFMonitoringApac)
class LensFATFMonitoringApacAdmin(admin.ModelAdmin, ExportCsvMixin):
    list_display = (
        'id',
        'member_uuid',
        'ip',
        'target_date',
        'country_name',
        'country_code',
        'action_type',
        'action_count',
        'fatf_level',
        'p1_fatf_countries_list',
        'params_tag',
        'created_at_jkt',
        'updated_at_jkt',
    )

    list_filter = (('target_date', DateRangeFilter), 'fatf_level')
    search_fields = [
        'country_code',
        'country_name',
    ]

    actions = ['export_as_csv']


    def has_add_permission(self, request):
        return False


    def has_delete_permission(self, request, obj=None):
        return False
    

    def created_at_jkt(self, obj):
        return obj.created_at + datetime.timedelta(hours=settings.LOCAL_TIME_DELTA)
    created_at_jkt.short_description = 'Created at (JKT)'


    def updated_at_jkt(self, obj):
        return obj.updated_at + datetime.timedelta(hours=settings.LOCAL_TIME_DELTA)
    updated_at_jkt.short_description = 'Updated at (JKT)'

@admin.register(LensEmployeeAccountApac)
class LensEmployeeAccountApacAdmin(admin.ModelAdmin, ExportCsvMixin):
    list_display = (
        'id',
        'trade_no',
        'trade_date',
        'trade_time',
        'member_uuid',
        'asset_name',
        'currency_id',
        '_quantity',
        '_fiat_value',
        'action_type',
        'p1_observation_period',
        '_p2_trade_threshold',
        'params_tag',
        'created_at', 
        'updated_at',
    )

    list_filter = (('trade_date', DateRangeFilter),)
    search_fields = [
        'member_uuid',
        'asset_name',
    ]

    actions = ['export_as_csv']

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
    
    def _quantity(self, obj):
        return "%.8f" % obj.quantity
    
    def _fiat_value(self, obj):
        return "%.2f" % obj.fiat_value
    
    def _p2_trade_threshold(self, obj):
        return "%.2f" % obj.p2_trade_threshold

@admin.register(LensInsiderTradingApac)
class LensInsiderTradingApacAdmin(admin.ModelAdmin, ExportCsvMixin):
    list_display = (
        'id',
        'trade_no',
        'trade_date',
        'trade_time',
        'member_uuid',
        'asset_name',
        'currency_id',
        '_quantity',
        '_fiat_value',
        'action_type',
        'p1_suspended_period',
        'params_tag',
        'created_at', 
        'updated_at',
    )

    list_filter = (('trade_date', DateRangeFilter),)
    search_fields = [
        'member_uuid',
        'asset_name',
    ]

    actions = ['export_as_csv']

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
    
    def _quantity(self, obj):
        return "%.8f" % obj.quantity
    
    def _fiat_value(self, obj):
        return "%.2f" % obj.fiat_value
    
@admin.register(TradingVolume)
class TradingVolumeAdmin(admin.ModelAdmin, ExportCsvMixin):
    list_display = (
        'id',        
        'trade_date',
        'asset_name',
        'market',
        'vol_asset',
        '_vol_local_currency',
        'max_price',
        'min_price',
        '_dif_price', ### diff price %
        'avg_price',
    )
    list_filter = (('trade_date', DateRangeFilter),)
    search_fields = [
        'trade_date',
    ]

    actions = ['export_as_csv']
    ordering = ('-trade_date', )


    def has_add_permission(self, request):
        return False


    def has_delete_permission(self, request, obj=None):
        return False

    def _dif_price(self,obj):
        return str(obj.dif_price)+"%"
    
    def _vol_local_currency(self, obj):
        return "%.2f" % obj.vol_local_currency
    
@admin.register(LensMicrostructuringApac)
class LensMicrostructuringApacAdmin(admin.ModelAdmin, ExportCsvMixin):
    list_display = (
        'id',
        'member_id',
        'member_uuid',
        'action_type',
        'counts',
        'sum_fiat_amount',
        'start_date',
        'end_date',
        'p1_observation_period',
        'p2_accumulate_dw',
        'p3_counts_dw',
        'params_tag',
    )

    list_filter = (('start_date', DateRangeFilter),)
    search_fields = [
        'member_uuid',
        'member_id',
    ]

    actions = ['export_as_csv']

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
    
@admin.register(LensSmurfingId)
class LensSmurfingIdAdmin(admin.ModelAdmin, ExportCsvMixin):
    list_display = (
        'id',
        'member_id',
        'member_uuid',
        'counts',
        'sum_fiat_amount',
        'annual_income',
        'source_of_funds',
        'monthly_income',
        'start_date',
        'end_date',
        'p1_observation_period',
        'p2_salary_multiplication_threshold',
        'params_tag',
    )

    list_filter = (('start_date', DateRangeFilter),)
    search_fields = [
        'member_uuid',
        'member_id',
    ]

    actions = ['export_as_csv']

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(LensFiatFeeVolume)
class LensFiatFeeVolumeAdmin(admin.ModelAdmin, ExportCsvMixin):
    list_display = (
        'id',        
        'target_date',
        'asset_enum',
        'asset_name',
        'ask_fiat_fee',
        'bid_fiat_fee',
        'withdraw_fiat_fee',
    )
    list_filter = (('target_date', DateRangeFilter),)
    search_fields = [
        'target_date',
    ]

    actions = ['export_as_csv']
    ordering = ('-target_date', )

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
