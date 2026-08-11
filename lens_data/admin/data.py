import csv
from datetime import datetime, timedelta

from django.conf import settings
from django.contrib import admin
from django.core.paginator import Paginator
from django.http import HttpResponse
from django.utils.functional import cached_property
from rangefilter.filters import DateRangeFilter
from lens_data.admin.filter import *
from lens_data.models.data import *


class NoCountPaginator(Paginator):
    """
    Paginator that does not count the rows in the table.
    """
    @cached_property
    def count(self):
        return 9999999999


class LimitCountPaginator(Paginator):
    LIMIT = 2000000

    @cached_property
    def count(self):
        """
        Returns the total number of objects, across all pages.
        """
        try:
            limit = self.LIMIT
            total = self.object_list.order_by()[:limit].count()
            # ^-- User order_by() to remove any ordering and
            # count objects as quickly as possible. (Shouldn't
            # SQL optimize the query regardless of ordering?)
            return total if total < limit else IntPlus(total)
        except (AttributeError, TypeError):
            # AttributeError if object_list has no count() method.
            # TypeError if object_list.count() requires arguments
            # (i.e. is of type list).
            return len(self.object_list)


class IntPlus(int):
    def __str__(self):
        return '{}+'.format(int.__str__(self))


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

@admin.register(TradeBase)
class TradeBaseAdmin(admin.ModelAdmin, ExportCsvMixin):
    list_display = (
        'trade_no',        
        'trade_date',
        'trade_time',
        'execution_price',
        'execution_quantity',
        'execution_value',
        'b_customer_code',
        'b_is_algorithmic',
        's_customer_code',
        's_is_algorithmic',
        'b_fee',
        's_fee',
        'currency_id',
        'asset_id',
        'asset_name_enum',
        's_id',
        'b_id',
        's_ip',
        'b_ip',
        'fiat_amount',
        's_order_date',
        's_order_time',
        'b_order_date',
        'b_order_time',
        'fiat_fee',
    )
    list_filter = (
        ('trade_date', DateRangeFilter),
        # BCustomerCodeFilter,
        # SCustomerCodeFilter,
        'b_customer_code',
        's_customer_code'
    )

    search_fields = [
        'b_customer_code',
        's_customer_code',
    ]

    actions = ['export_as_csv']
    paginator = LimitCountPaginator
    show_full_result_count = False

    def has_add_permission(self, request):
        return False


    def has_delete_permission(self, request, obj=None):
        return False
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        b_code = request.GET.get('b_customer_code')
        s_code = request.GET.get('s_customer_code')

        if b_code:
            qs = qs.filter(b_customer_code__icontains=b_code)
        if s_code:
            qs = qs.filter(s_customer_code__icontains=s_code)

        return qs
@admin.register(UserInfo)
class UserInfoAdmin(admin.ModelAdmin, ExportCsvMixin):
    list_display = (
        'member_id',        
        'member_uuid',
        'security_level',
        'member_state',
        'member_type',
        'birthday',
        'age',
        'nationality',
        'country_location',
        'country_of_birth',
        'mip_state',
        'created_at_jkt',
    )
    # list_filter = (('age', NumericRangeFilterBuilder),)
    search_fields = [
        'member_id',
        'member_uuid',
    ]
    actions = ['export_as_csv']

    def has_add_permission(self, request):
        return False
    def has_delete_permission(self, request, obj=None):
        return False
    def created_at_jkt(self, obj):
        return obj.created_at + timedelta(hours=settings.LOCAL_TIME_DELTA)
    created_at_jkt.short_description = 'Created At (JKT)'
# Django admin does not support models with composite primary keys.
# DepositBase remains available through application queries and APIs.
class DepositBaseAdmin(admin.ModelAdmin, ExportCsvMixin):
    list_display = (
        'deposit_id',        
        'target_date',
        'target_time',
        'member_uuid',
        'member_id',
        'currency_id',
        'currency_name',
        'amount',
        'fiat_amount',
        'type',
        'ip',
        'txid',
        'fee',
        'fiat_fee',
        'settlement_date',
        'settlement_time',
    )
    list_filter = (
        ('target_date', DateRangeFilter),
    )
    search_fields = [
        'member_id',
    ]
    actions = ['export_as_csv']

    def has_add_permission(self, request):
        return False
    def has_delete_permission(self, request, obj=None):
        return False
# Django admin does not support models with composite primary keys.
# WithdrawBase remains available through application queries and APIs.
class WithdrawBaseAdmin(admin.ModelAdmin, ExportCsvMixin):
    list_display = (
        'withdraw_id',        
        'target_date',
        'target_time',
        'member_uuid',
        'member_id',
        'currency_id',
        'currency_name',
        'amount',
        'fiat_amount',
        'type',
        'ip',
        'txid',
        'fee',
        'fiat_fee',
        'settlement_date',
        'settlement_time',
    )
    list_filter = (
        ('target_date', DateRangeFilter),
    )
    search_fields = [
        'member_id',
    ]
    actions = ['export_as_csv']

    def has_add_permission(self, request):
        return False
    def has_delete_permission(self, request, obj=None):
        return False
@admin.register(GlobalDailyRateBTC)
class GlobalDailyRatesBTCAdmin(admin.ModelAdmin, ExportCsvMixin):
    list_display = (
        'id',
        'target_date',
        'target_time',        
        'trading_pair',
        'currency_code',
        'btc_price',
        'created_at',
    )
    actions = ['export_as_csv']

    def has_add_permission(self, request):
        return False


    def has_delete_permission(self, request, obj=None):
        return False
@admin.register(LocalDailyRate)
class LocalDailyRatesAdmin(admin.ModelAdmin, ExportCsvMixin):
    list_display = (
        'id',
        'target_date',
        'target_time',        
        'currency_code',
        'price',
        'created_at',
    )
    actions = ['export_as_csv']

    def has_add_permission(self, request):
        return False


    def has_delete_permission(self, request, obj=None):
        return False

@admin.register(IPAddressCache)
class IPAddressCacheAdmin(admin.ModelAdmin, ExportCsvMixin):
    list_display = (
        'ip',
        'country_name',
        'country_code',
    )

    search_fields = [
        'ip',
        'country_name',
        'country_code',
    ]

    def has_add_permission(self, request):
        return False


    def has_delete_permission(self, request, obj=None):
        return False
@admin.register(LoginHistory)
class LoginHistoryAdmin(admin.ModelAdmin, ExportCsvMixin):
    list_display = (
        'id',
        'member_uuid',
        # 'member_id',
        'target_date',
        'login_date',
        'ip',
    )
    list_filter = ('target_date',)
    search_fields = [
        # 'member_id',
        'member_uuid',
    ]
    actions = ['export_as_csv']

    def has_add_permission(self, request):
        return False
    def has_delete_permission(self, request, obj=None):
        return False


# Django admin does not support models with composite primary keys.
# InvestmentEventBase remains available through application queries and APIs.
class InvestmentEventBaseAdmin(admin.ModelAdmin, ExportCsvMixin):
    list_display = (
        'investment_event_id',
        'event_date',
        'event_time',
        'event_type',
        'market',
        'currency',
        'volume',
        'price',
        'amount',
        'fee',
        'settlement_amount',
        'fiat_unit_price',
        'fiat_amount',
        'fiat_fee',
        'fiat_settlement_amount',
        'event_type_id',
        'member_id',
        'member_uuid',
    )
    list_filter = (
        ('event_date', DateRangeFilter),
    )
    search_fields = [
        'investment_event_id',
        'event_type_id',
        'member_id',
        'member_uuid',
    ]

    paginator = LimitCountPaginator
    show_full_result_count = False
    actions = ['export_as_csv']


    def has_add_permission(self, request):
        return False

@admin.register(UptimeSummary)
class UptimeSummaryAdmin(admin.ModelAdmin, ExportCsvMixin):
    list_display = (
        'id',
        'member_id',
        'target_date',
        'market',
        'time_stamp_rounding',
        'tier_1',
        'tier_2',
        'tier_3',
        'tier_4',
        'tier_5',
        'tier_6',
        'tier_7',
    )
    list_filter = (
        ('target_date', DateRangeFilter),
    )
    search_fields = [
        'member_id',
        'market',
    ]

    actions = ['export_as_csv']
    paginator = LimitCountPaginator
    show_full_result_count = False

    def has_add_permission(self, request):
        return False
    def has_change_permission(self, request, obj=None):
        return False
    def has_delete_permission(self, request, obj=None):
        return False
    
@admin.register(DailyReconciliation)
class DailyReconciliationAdmin(admin.ModelAdmin, ExportCsvMixin):
    list_display = (
        'id',
        'date',
        'window',
        'volume_idr',
        'volume_non_idr',
        'volume_btc',
        'volume_usdt',
        'deposit_crypto_idr',
        'withdraw_crypto_idr',
        'deposit_fiat_idr',
        'withdraw_fiat_idr',
        'platform_fee_idr',
        'platform_fee_non_idr',
        'withdraw_fiat_fee_idr',
        'withdraw_crypto_fee_idr',
        'count_trades',
        'count_depo_wd_fiat',
        'count_depo_wd_crypto',
        'quote_asset_sell_idr',       
        'quote_asset_buy_idr',
        'created_at_jkt',     
    )
    list_filter = (
        ('date', DateRangeFilter),
    )
    search_fields = [
        'volume_idr',
        'volume_non_idr'
    ]

    paginator = LimitCountPaginator
    show_full_result_count = False
    actions = ['export_as_csv']

    def has_add_permission(self, request):
        return False

    def created_at_jkt(self, obj):
        return obj.created_at + timedelta(hours=settings.LOCAL_TIME_DELTA)
    
    def deposit_crypto_idr(self, obj):
        return obj.deposit_crypto
    
    def withdraw_crypto_idr(self, obj):
        return obj.withdraw_crypto
    
    def deposit_fiat_idr(self, obj):
        return obj.deposit_fiat
    
    def withdraw_fiat_idr(self, obj):
        return obj.withdraw_fiat
    
    def withdraw_fiat_fee_idr(self, obj):
        return obj.withdraw_fiat_fee
    
    def withdraw_crypto_fee_idr(self, obj):
        return obj.withdraw_crypto_fee
    
    def quote_asset_sell_idr(self, obj):
        return obj.quote_asset_sell
    
    def quote_asset_buy_idr(self, obj):
        return obj.quote_asset_buy
    
    def platform_fee_idr(self, obj):
        return obj.trading_fee_idr
    
    def platform_fee_non_idr(self, obj):
        return obj.trading_fee_non_idr
    
    created_at_jkt.short_description = 'Created At (JKT)'
    deposit_crypto_idr.short_description = 'Deposit Crypto (IDR)'
    withdraw_crypto_idr.short_description = 'Withdraw Crypto (IDR)'
    deposit_fiat_idr.short_description = 'Deposit Fiat (IDR)'
    withdraw_fiat_idr.short_description = 'Withdraw Fiat (IDR)'
    withdraw_fiat_fee_idr.short_description = 'Withdraw Fiat Fee (IDR)'
    withdraw_crypto_fee_idr.short_description = 'Withdraw Crypto Fee (IDR)'
    quote_asset_sell_idr.short_description = 'Penjualan Asset (IDR)'
    quote_asset_buy_idr.short_description = 'Pembelian Asset (IDR)'
    platform_fee_idr.short_description = 'Fiat Platform Fee (IDR)'
    platform_fee_non_idr.short_description = 'Crypto Platform Fee (IDR)'
