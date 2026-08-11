from datetime import datetime

import pytz
from django.conf import settings
from django.db import models
from masterdata.models.sec import AssetMaster

class CMCDaily(models.Model):
    th = models.DateTimeField(primary_key=True)
    day = models.DateField(db_index=True)
    hour = models.CharField(max_length=2)
    coin_name = models.CharField(max_length=50)
    abbreviations = models.CharField(max_length=10)
    bot_rate = models.DecimalField(max_digits=38, decimal_places=20, null=True)
    usd_price = models.DecimalField(max_digits=38, decimal_places=20, null=True)
    thb_price = models.DecimalField(max_digits=38, decimal_places=20, null=True)

    class Meta:
        managed = False
        db_table = 'cmc_daily'


class CMCHourly(models.Model):
    id = models.BigAutoField(primary_key=True)
    datetime_utc = models.DateTimeField()
    unix_timestamp = models.CharField(max_length=255, blank=True, null=True)
    asset_name = models.CharField(max_length=50)
    ticker = models.CharField(max_length=10)
    usd_price = models.DecimalField(max_digits=38, decimal_places=20, null=True)
    local_currency_price = models.DecimalField(max_digits=38, decimal_places=20, null=True)

    class Meta:
        managed = False
        db_table = 'cmc_hourly'
    unique_together = ('unix_timestamp', 'ticker',)


class TradeBase(models.Model):
    trade_no = models.BigIntegerField(primary_key=True)
    trade_date = models.DateField(db_index=True)
    trade_time = models.TimeField()
    execution_price = models.DecimalField(max_digits=38, decimal_places=20, null=True)
    execution_quantity = models.DecimalField(max_digits=38, decimal_places=20, null=True)
    execution_value = models.DecimalField(max_digits=38, decimal_places=20, null=True)
    b_customer_code = models.IntegerField(null=True)
    b_is_algorithmic = models.CharField(max_length=2, null=True)
    s_customer_code = models.IntegerField(null=True)
    s_is_algorithmic = models.CharField(max_length=2, null=True)
    b_fee = models.DecimalField(max_digits=32, decimal_places=20, null=True)
    s_fee = models.DecimalField(max_digits=32, decimal_places=20, null=True)
    currency_id = models.CharField(max_length=20, null=True)
    asset_id = models.CharField(max_length=20, null=True)
    asset_name_enum = models.CharField(max_length=20, null=True)
    s_id = models.BigIntegerField(blank=True, null=True)
    b_id = models.BigIntegerField(blank=True, null=True)
    s_ip = models.CharField(max_length=191, blank=True, null=True)
    b_ip = models.CharField(max_length=191, blank=True, null=True)
    fiat_amount = models.DecimalField(max_digits=38, decimal_places=20, null=True) 
    s_order_date = models.DateField(db_index=True)
    s_order_time = models.TimeField()
    b_order_date = models.DateField(db_index=True)
    b_order_time = models.TimeField()
    fiat_fee = models.DecimalField(max_digits=40, decimal_places=20, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'trade_base'


class DepositBase(models.Model):
    deposit_id = models.BigIntegerField(primary_key=True)
    target_date = models.DateField(db_index=True)
    target_time = models.TimeField()
    member_uuid = models.CharField(max_length=191, blank=True, null=True)
    member_id = models.BigIntegerField()
    currency_id = models.IntegerField(blank=True, null=True)
    currency_name = models.CharField(max_length=20, null=True)
    amount = models.DecimalField(max_digits=32, decimal_places=20, blank=True, null=True)
    fiat_amount = models.DecimalField(max_digits=32, decimal_places=20, blank=True, null=True)
    type = models.CharField(max_length=191, blank=True, null=True)
    ip = models.CharField(max_length=191, blank=True, null=True)
    txid = models.CharField(max_length=191, blank=True, null=True)
    fee = models.DecimalField(max_digits=40, decimal_places=20, blank=True, null=True)
    fiat_fee = models.DecimalField(max_digits=40, decimal_places=20, blank=True, null=True)
    settlement_date = models.DateField()
    settlement_time = models.TimeField()

    class Meta:
        managed = False
        db_table = 'deposit_base'


class DepositBaseJoinAssetMaster(models.Model):
    deposit_id = models.BigIntegerField(primary_key=True)
    target_date = models.DateField(db_index=True)
    target_time = models.TimeField()
    member_uuid = models.CharField(max_length=191, blank=True, null=True)
    member_id = models.BigIntegerField()
    # currency_id = models.IntegerField(blank=True, null=True)
    currency_name = models.CharField(max_length=20, null=True)
    amount = models.DecimalField(max_digits=32, decimal_places=20, blank=True, null=True)
    fiat_amount = models.DecimalField(max_digits=32, decimal_places=20, blank=True, null=True)
    type = models.CharField(max_length=191, blank=True, null=True)
    ip = models.CharField(max_length=191, blank=True, null=True)
    txid = models.CharField(max_length=191, blank=True, null=True)
    fee = models.DecimalField(max_digits=40, decimal_places=20, blank=True, null=True)
    fiat_fee = models.DecimalField(max_digits=40, decimal_places=20, blank=True, null=True)
    settlement_date = models.DateField()
    settlement_time = models.TimeField()

    assetmaster = models.ForeignKey(
        AssetMaster,
        to_field="enum_value",
        db_column="currency_id",
        on_delete=models.DO_NOTHING,
        related_name="depositbase_assetmaster",
        null=True,
    )

    class Meta:
        managed = False
        db_table = 'deposit_base'


class WithdrawBase(models.Model):
    withdraw_id = models.BigIntegerField(primary_key=True)
    target_date = models.DateField(db_index=True)
    target_time = models.TimeField()
    member_uuid = models.CharField(max_length=191, blank=True, null=True)
    member_id = models.BigIntegerField()
    currency_id = models.IntegerField(blank=True, null=True)
    currency_name = models.CharField(max_length=20, null=True)
    amount = models.DecimalField(max_digits=32, decimal_places=20, blank=True, null=True)
    fiat_amount = models.DecimalField(max_digits=32, decimal_places=20, blank=True, null=True)
    type = models.CharField(max_length=191, blank=True, null=True)
    ip = models.CharField(max_length=191, blank=True, null=True)
    txid = models.CharField(max_length=191, blank=True, null=True)
    fee = models.DecimalField(max_digits=40, decimal_places=20, blank=True, null=True)
    fiat_fee = models.DecimalField(max_digits=40, decimal_places=20, blank=True, null=True)
    settlement_date = models.DateField()
    settlement_time = models.TimeField()

    class Meta:
        managed = False
        db_table = 'withdraw_base'

class WithdrawBaseJoinAssetMaster(models.Model):
    withdraw_id = models.BigIntegerField(primary_key=True)
    target_date = models.DateField(db_index=True)
    target_time = models.TimeField()
    member_uuid = models.CharField(max_length=191, blank=True, null=True)
    member_id = models.BigIntegerField()
    # currency_id = models.IntegerField(blank=True, null=True)
    currency_name = models.CharField(max_length=20, null=True)
    amount = models.DecimalField(max_digits=32, decimal_places=20, blank=True, null=True)
    fiat_amount = models.DecimalField(max_digits=32, decimal_places=20, blank=True, null=True)
    type = models.CharField(max_length=191, blank=True, null=True)
    ip = models.CharField(max_length=191, blank=True, null=True)
    txid = models.CharField(max_length=191, blank=True, null=True)
    fee = models.DecimalField(max_digits=40, decimal_places=20, blank=True, null=True)
    fiat_fee = models.DecimalField(max_digits=40, decimal_places=20, blank=True, null=True)
    settlement_date = models.DateField()
    settlement_time = models.TimeField()

    assetmaster = models.ForeignKey(
        AssetMaster,
        to_field="enum_value",
        db_column="currency_id",
        on_delete=models.DO_NOTHING,
        related_name="withdrawbase_assetmaster",
        null=True,
    )

    class Meta:
        managed = False
        db_table = 'withdraw_base'


class UserInfo(models.Model):
    member_id = models.BigAutoField(primary_key=True)
    member_uuid = models.CharField(unique=True, max_length=191, blank=True, null=True)
    security_level = models.IntegerField(blank=True, null=True)
    member_state = models.CharField(max_length=191, blank=True, null=True)
    member_type = models.CharField(max_length=191, blank=True, null=True)
    birthday = models.CharField(max_length=20)
    age = models.IntegerField(blank=True, null=True)
    nationality = models.CharField(max_length=100)
    country_location = models.CharField(max_length=200, blank=True, null=True)
    country_of_birth = models.CharField(max_length=100)
    mip_state = models.CharField(max_length=10, blank=True, null=True)
    address = models.CharField(max_length=256)
    flag_lp = models.BooleanField(default=False)
    tag = models.CharField(max_length=255, blank=True, null=True)
    properties = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'user_info'

class GlobalDailyRateBTC(models.Model):
    id = models.BigAutoField(primary_key=True)
    target_date = models.DateField(db_index = True)
    target_time = models.TimeField()
    trading_pair = models.CharField(max_length = 30)
    currency_code = models.CharField(max_length=30)
    btc_price = models.DecimalField(max_digits = 38, decimal_places = 20, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = False
        db_table = 'global_daily_rates_btc'

class LocalDailyRate(models.Model):
    id = models.BigAutoField(primary_key=True)
    target_date = models.DateField(db_index = True)
    target_time = models.TimeField()
    currency_code = models.CharField(max_length = 30)
    price = models.DecimalField(max_digits = 38, decimal_places = 20, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = False
        db_table = 'local_daily_rates'


class IPAddressCache(models.Model):
    ip = models.CharField(unique=True, primary_key=True, max_length=191)
    country_name = models.CharField(max_length=191, blank=True, null=True)
    country_code = models.CharField(max_length=10, blank=True, null=True)
    json = models.TextField()

    class Meta:
        managed = False
        db_table = 'ip_address_cache'


class LoginHistory(models.Model):
    id = models.BigAutoField(primary_key=True)
    member_uuid = models.CharField(max_length=191, blank=True, null=True)
    member_id = models.BigIntegerField()
    target_date = models.DateField(db_index=True)
    login_date = models.DateTimeField()
    ip = models.CharField(max_length=191, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'login_action_history'


class InvestmentEventBase(models.Model):
    investment_event_id = models.BigIntegerField(primary_key=True)
    event_date = models.DateField()
    event_time = models.TimeField()
    created_date = models.DateField()
    created_time = models.TimeField()
    event_type = models.CharField(max_length=32, blank=True, null=True)
    base_unit = models.CharField(max_length=32, blank=True, null=True)
    quote_unit = models.CharField(max_length=32, blank=True, null=True)
    market = models.CharField(max_length=32, blank=True, null=True)
    currency = models.CharField(max_length=32, blank=True, null=True)
    volume = models.DecimalField(max_digits=40, decimal_places=20, blank=True, null=True)
    price = models.DecimalField(max_digits=40, decimal_places=20, blank=True, null=True)
    amount = models.DecimalField(max_digits=40, decimal_places=20, blank=True, null=True)
    fee = models.DecimalField(max_digits=40, decimal_places=20, blank=True, null=True)
    settlement_amount = models.DecimalField(max_digits=40, decimal_places=20, blank=True, null=True)
    fiat_unit_price = models.DecimalField(max_digits=40, decimal_places=20, blank=True, null=True)
    fiat_amount = models.DecimalField(max_digits=40, decimal_places=20, blank=True, null=True)
    fiat_fee = models.DecimalField(max_digits=40, decimal_places=20, blank=True, null=True)
    fiat_settlement_amount = models.DecimalField(max_digits=40, decimal_places=20, blank=True, null=True)
    event_type_id = models.BigIntegerField(blank=True, null=True)
    order_id = models.BigIntegerField(blank=True, null=True)
    order_type = models.IntegerField(blank=True, null=True)
    ord_type = models.IntegerField(blank=True, null=True)
    application_id = models.IntegerField(blank=True, null=True)
    transaction_type = models.IntegerField(blank=True, null=True)
    member_id = models.BigIntegerField()
    member_uuid = models.CharField(unique=True, max_length=191, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'investment_event_base'


class OrderBase(models.Model):
    req_id = models.BigIntegerField()
    order_no = models.BigIntegerField(primary_key=True)
    customer_code = models.IntegerField()
    is_algorithmic = models.CharField(max_length=2)
    is_buy = models.CharField(max_length=2)
    order_status = models.IntegerField()
    order_price = models.DecimalField(max_digits=38, decimal_places=20)
    type = models.CharField(max_length=8)
    order_date = models.DateField()
    order_time = models.TimeField()
    currency_id = models.CharField(max_length=20)
    asset_id = models.CharField(max_length=20)
    order_datetime = models.DateTimeField()
    order_type_code = models.CharField(max_length=191, blank=True, null=True)
    quantity = models.DecimalField(max_digits=32, decimal_places=20, blank=True, null=True)
    order_value = models.DecimalField(max_digits=32, decimal_places=20, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'order_base'


class OrderCountSummary(models.Model):
    id = models.AutoField(primary_key=True)
    order_date = models.DateField(db_index=True)
    asset_id = models.CharField(max_length=50, db_index=True)
    currency_id = models.CharField(max_length=10, db_index=True)
    customer_code = models.CharField(max_length=50, db_index=True)
    total_orders = models.IntegerField(default=0)
    buy_orders = models.IntegerField(default=0)
    sell_orders = models.IntegerField(default=0)
    algo_orders = models.IntegerField(default=0)
    non_algo_orders = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'order_count_summary'
        ordering = ['-order_date', 'asset_id', 'currency_id', 'customer_code']
        unique_together = [['order_date', 'asset_id', 'currency_id', 'customer_code']]

    def __str__(self):
        return f"{self.order_date} - {self.asset_id}/{self.currency_id} - {self.customer_code}"

    @property
    def buy_percentage(self):
        return round((self.buy_orders * 100.0) / self.total_orders, 2) if self.total_orders > 0 else 0

    @property
    def sell_percentage(self):
        return round((self.sell_orders * 100.0) / self.total_orders, 2) if self.total_orders > 0 else 0

    @property
    def algo_percentage(self):
        return round((self.algo_orders * 100.0) / self.total_orders, 2) if self.total_orders > 0 else 0

    @property
    def non_algo_percentage(self):
        return round((self.non_algo_orders * 100.0) / self.total_orders, 2) if self.total_orders > 0 else 0


class PrivateOrderbookDepth(models.Model):
    id = models.BigAutoField(primary_key=True)
    market = models.CharField(max_length=20, db_index=True)
    orderbook_timestamp_unix = models.BigIntegerField(
        db_index=True,
        help_text="Unix timestamp in milliseconds"
    )
    member_id = models.IntegerField(db_index=True)
    ask_vol_12_5bp = models.DecimalField(max_digits=38, decimal_places=8, null=True, blank=True)
    bid_vol_12_5bp = models.DecimalField(max_digits=38, decimal_places=8, null=True, blank=True)
    ask_vol_25bp = models.DecimalField(max_digits=38, decimal_places=8, null=True, blank=True)
    bid_vol_25bp = models.DecimalField(max_digits=38, decimal_places=8, null=True, blank=True)
    ask_vol_37_5bp = models.DecimalField(max_digits=38, decimal_places=8, null=True, blank=True)
    bid_vol_37_5bp = models.DecimalField(max_digits=38, decimal_places=8, null=True, blank=True)
    ask_vol_50bp = models.DecimalField(max_digits=38, decimal_places=8, null=True, blank=True)
    bid_vol_50bp = models.DecimalField(max_digits=38, decimal_places=8, null=True, blank=True)
    ask_vol_100bp = models.DecimalField(max_digits=38, decimal_places=8, null=True, blank=True)
    bid_vol_100bp = models.DecimalField(max_digits=38, decimal_places=8, null=True, blank=True)
    ask_vol_200bp = models.DecimalField(max_digits=38, decimal_places=8, null=True, blank=True)
    bid_vol_200bp = models.DecimalField(max_digits=38, decimal_places=8, null=True, blank=True)
    ask_vol_400bp = models.DecimalField(max_digits=38, decimal_places=8, null=True, blank=True)
    bid_vol_400bp = models.DecimalField(max_digits=38, decimal_places=8, null=True, blank=True)
    ask_vol_800bp = models.DecimalField(max_digits=38, decimal_places=8, null=True, blank=True)
    bid_vol_800bp = models.DecimalField(max_digits=38, decimal_places=8, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        managed = False
        db_table = 'private_orderbook_depth'
        indexes = [
            models.Index(fields=['market', 'orderbook_timestamp_unix']),
            models.Index(fields=['member_id', 'orderbook_timestamp_unix']),
        ]
        
    def __str__(self):
        return f"{self.market} - Member {self.member_id} @ {self.orderbook_timestamp_unix}"
    
    @property
    def orderbook_timestamp(self):
        """
        Returns formatted timestamp as YYYY-MM-DD HH:MM
        Replicates the MySQL virtual column
        """
        sgt = pytz.timezone(settings.LOCAL_TIMEZONE)
        dt = datetime.fromtimestamp(self.orderbook_timestamp_unix / 1000, tz=sgt)
        return dt.strftime('%Y-%m-%d %H:%M')
    

class PublicOrderbookDepth(models.Model):
    id = models.BigAutoField(primary_key=True)
    market = models.CharField(max_length=20, db_index=True)
    orderbook_timestamp_unix = models.BigIntegerField(
        db_index=True,
        help_text="Unix timestamp in milliseconds"
    )
    ask_vol_12_5bp = models.DecimalField(max_digits=38, decimal_places=8, null=True, blank=True)
    bid_vol_12_5bp = models.DecimalField(max_digits=38, decimal_places=8, null=True, blank=True)
    ask_vol_25bp = models.DecimalField(max_digits=38, decimal_places=8, null=True, blank=True)
    bid_vol_25bp = models.DecimalField(max_digits=38, decimal_places=8, null=True, blank=True)
    ask_vol_37_5bp = models.DecimalField(max_digits=38, decimal_places=8, null=True, blank=True)
    bid_vol_37_5bp = models.DecimalField(max_digits=38, decimal_places=8, null=True, blank=True)
    ask_vol_50bp = models.DecimalField(max_digits=38, decimal_places=8, null=True, blank=True)
    bid_vol_50bp = models.DecimalField(max_digits=38, decimal_places=8, null=True, blank=True)
    ask_vol_100bp = models.DecimalField(max_digits=38, decimal_places=8, null=True, blank=True)
    bid_vol_100bp = models.DecimalField(max_digits=38, decimal_places=8, null=True, blank=True)
    ask_vol_200bp = models.DecimalField(max_digits=38, decimal_places=8, null=True, blank=True)
    bid_vol_200bp = models.DecimalField(max_digits=38, decimal_places=8, null=True, blank=True)
    ask_vol_400bp = models.DecimalField(max_digits=38, decimal_places=8, null=True, blank=True)
    bid_vol_400bp = models.DecimalField(max_digits=38, decimal_places=8, null=True, blank=True)
    ask_vol_800bp = models.DecimalField(max_digits=38, decimal_places=8, null=True, blank=True)
    bid_vol_800bp = models.DecimalField(max_digits=38, decimal_places=8, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        managed = False
        db_table = 'public_orderbook_depth'
        indexes = [
            models.Index(fields=['market', 'orderbook_timestamp_unix']),
        ]
        
    def __str__(self):
        return f"{self.market} @ {self.orderbook_timestamp_unix}"
    
    @property
    def orderbook_timestamp(self):
        """
        Returns formatted timestamp as YYYY-MM-DD HH:MM
        Replicates the MySQL virtual column
        """
        sgt = pytz.timezone(settings.LOCAL_TIMEZONE)
        dt = datetime.fromtimestamp(self.orderbook_timestamp_unix / 1000, tz=sgt)
        return dt.strftime('%Y-%m-%d %H:%M')



# class PublicOrderEvaluation(models.Model):
#     # id = models.CharField(max_length=191, primary_key=True)
#     # member_id = models.CharField(max_length=10)
#     target_date = models.CharField(max_length=20, primary_key=True)
#     market = models.CharField(max_length=20, primary_key=True)
#     bp_range = models.CharField(max_length=30, primary_key=True)
#     public_ask = models.DecimalField(max_digits=40, decimal_places=20, blank=True, null=True)
#     public_ask_fiat = models.DecimalField(max_digits=40, decimal_places=20, blank=True, null=True)
#     # ask_pct = models.DecimalField(max_digits=3, decimal_places=2, blank=True, null=True)
#     public_bid = models.DecimalField(max_digits=40, decimal_places=20, blank=True, null=True)
#     public_bid_fiat = models.DecimalField(max_digits=40, decimal_places=20, blank=True, null=True)
#     # bid_pct = models.DecimalField(max_digits=3, decimal_places=2, blank=True, null=True)

#     class Meta:
#         managed = False
#         db_table = 'v_pubic_order_evaluation'

# class PrivateOrderEvaluation(models.Model):
#     # id = models.CharField(max_length=191, primary_key=True)
#     member_id = models.CharField(max_length=10, primary_key=True)
#     target_date = models.CharField(max_length=20, primary_key=True)
#     market = models.CharField(max_length=20, primary_key=True)
#     bp_range = models.CharField(max_length=30, primary_key=True)
#     private_ask = models.DecimalField(max_digits=40, decimal_places=20, blank=True, null=True)
#     private_ask_fiat = models.DecimalField(max_digits=40, decimal_places=20, blank=True, null=True)
#     # ask_pct = models.DecimalField(max_digits=3, decimal_places=2, blank=True, null=True)
#     private_bid = models.DecimalField(max_digits=40, decimal_places=20, blank=True, null=True)
#     private_bid_fiat = models.DecimalField(max_digits=40, decimal_places=20, blank=True, null=True)
#     # bid_pct = models.DecimalField(max_digits=3, decimal_places=2, blank=True, null=True)

#     class Meta:
#         managed = False
#         db_table = 'v_private_order_evaluation'


class UptimeSummary(models.Model):
    id = models.CharField(max_length=191, primary_key=True)
    member_id = models.CharField(max_length=10)
    # company_name = models.CharField(max_length=100)
    target_date = models.CharField(max_length=20)
    market = models.CharField(max_length=20)
    time_stamp_rounding = models.CharField(unique=True, max_length=16)
    tier_1 = models.DecimalField(max_digits=40, decimal_places=20, blank=True, null=True)
    tier_2 = models.DecimalField(max_digits=40, decimal_places=20, blank=True, null=True)
    tier_3 = models.DecimalField(max_digits=40, decimal_places=20, blank=True, null=True)
    tier_4 = models.DecimalField(max_digits=40, decimal_places=20, blank=True, null=True)
    tier_5 = models.DecimalField(max_digits=40, decimal_places=20, blank=True, null=True)
    tier_6 = models.DecimalField(max_digits=40, decimal_places=20, blank=True, null=True)
    tier_7 = models.DecimalField(max_digits=40, decimal_places=20, blank=True, null=True)

    # def __str__(self):
    #     return self.lp_master.company_name

    class Meta:
        managed = False
        db_table = 'v_order_uptime_summary'
        # db_table = 'v_order_uptime_summary2'

class DailyReconciliation(models.Model):
    id = models.BigAutoField(primary_key=True)
    date = models.DateField(null=False)
    window = models.CharField(max_length=32, null=False)
    
    volume_idr = models.DecimalField(max_digits=40, decimal_places=8, blank=True, null=True)
    volume_non_idr = models.DecimalField(max_digits=40, decimal_places=8, blank=True, null=True)
    
    volume_btc = models.DecimalField(max_digits=40, decimal_places=8, blank=True, null=True)
    volume_usdt = models.DecimalField(max_digits=40, decimal_places=8, blank=True, null=True)
    
    deposit_crypto = models.DecimalField(max_digits=40, decimal_places=8, blank=True, null=True)
    withdraw_crypto = models.DecimalField(max_digits=40, decimal_places=8, blank=True, null=True)
    
    deposit_fiat = models.DecimalField(max_digits=40, decimal_places=8, blank=True, null=True)
    withdraw_fiat = models.DecimalField(max_digits=40, decimal_places=8, blank=True, null=True)
    
    trading_fee_idr = models.DecimalField(max_digits=40, decimal_places=8, blank=True, null=True)
    trading_fee_non_idr = models.DecimalField(max_digits=40, decimal_places=8, blank=True, null=True)
    withdraw_fiat_fee = models.DecimalField(max_digits=40, decimal_places=8, blank=True, null=True)
    withdraw_crypto_fee = models.DecimalField(max_digits=40, decimal_places=8, blank=True, null=True)

    count_trades = models.IntegerField(null=True)
    count_depo_wd_fiat = models.IntegerField(null=True)
    count_depo_wd_crypto = models.IntegerField(null=True)

    quote_asset_sell = models.DecimalField(max_digits=40, decimal_places=8, blank=True, null=True)
    quote_asset_buy = models.DecimalField(max_digits=40, decimal_places=8, blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)    
    class Meta:
        managed = False
        db_table = 'daily_reconciliation'
