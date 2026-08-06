from django.db import models
from lens.models.base_timestamped import TimeStampedModel
from masterdata.models.sec import AssetMaster


# --- New APAC Rulesets
class LensFATFMonitoringApac(models.Model):
    DATE_FIELD = 'target_date'

    id = models.BigAutoField(primary_key=True)
    member_uuid = models.CharField(max_length=191, blank=True, null=True)
    ip = models.CharField(max_length=30, blank=True, null=True)
    target_date = models.DateField(db_index=True) 
    country_name = models.CharField(max_length=191, blank=True, null=True)
    country_code = models.CharField(max_length=10, blank=True, null=True)
    action_type = models.CharField(max_length=30, blank=True, null=True)
    action_count = models.IntegerField(blank=True, null=True)
    fatf_level = models.CharField(max_length=30, blank=True, null=True)
    p1_fatf_countries_list = models.CharField(max_length=191, blank=True, null=True)
    params_tag = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = False
        db_table = 'lens_fatf_monitoring_apac'


class LensWashTradeApac(models.Model):
    DATE_FIELD = 'target_date'

    id = models.BigAutoField(primary_key=True)
    trade_date = models.DateField(db_index=True) 
    asset_name = models.CharField( max_length=20, blank=True, null=True)
    pair_id = models.CharField(max_length=20, blank=True, null=True)
    n_tx = models.IntegerField(blank=True, null=True)
    n_tx_pct = models.DecimalField(max_digits=38, decimal_places=20, null=True)
    simul_count = models.IntegerField(blank=True, null=True)
    vol_IDR = models.DecimalField(max_digits=38, decimal_places=20, null=True)
    total_vol_IDR = models.DecimalField(max_digits=38, decimal_places=20, null=True)
    vol = models.DecimalField(max_digits=38, decimal_places=20, null=True)
    vol_pct = models.DecimalField(max_digits=38, decimal_places=20, null=True)
    level = models.IntegerField(blank=True, null=True)
    p1_lv1_ratio = models.IntegerField(blank=True, null=True)
    p2_lv2_ratio = models.IntegerField(blank=True, null=True)
    p3_lv3_ratio = models.IntegerField(blank=True, null=True)
    p4_simul_entry = models.IntegerField(blank=True, null=True)
    p5_trade_vol = models.IntegerField(blank=True, null=True)
    params_tag = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = False
        db_table = 'lens_wash_trade_apac'

class LensEmployeeAccountApac(TimeStampedModel):
    DATE_FIELD = 'trade_date'

    id = models.BigAutoField(primary_key=True)
    trade_no = models.BigIntegerField(null=True)
    trade_date = models.DateField(db_index=True)
    trade_time = models.TimeField()
    member_uuid = models.CharField(max_length=191, blank=True, null=True)
    asset_name = models.CharField(max_length=20, null=True)
    currency_id = models.CharField(max_length=20, null=True)
    quantity = models.DecimalField(max_digits=38, decimal_places=20, null=True)
    fiat_value = models.DecimalField(max_digits=38, decimal_places=20, null=True)
    action_type = models.CharField(max_length=40, null=True)
    p1_observation_period = models.IntegerField(blank=True, null=True)
    p2_trade_threshold = models.DecimalField(max_digits=38, decimal_places=20, null=True)
    params_tag = models.CharField(max_length=100)

    class Meta:
        managed = False
        db_table = 'lens_employee_account_apac'


class LensInsiderTradingApac(TimeStampedModel):
    DATE_FIELD = 'trade_date'

    id = models.BigAutoField(primary_key=True)
    trade_no = models.BigIntegerField(null=True)
    trade_date = models.DateField(db_index=True)
    trade_time = models.TimeField()
    member_uuid = models.CharField(max_length=191, blank=True, null=True)
    asset_name = models.CharField(max_length=20, null=True)
    currency_id = models.CharField(max_length=20, null=True)
    quantity = models.DecimalField(max_digits=38, decimal_places=20, null=True)
    fiat_value = models.DecimalField(max_digits=38, decimal_places=20, null=True)
    action_type = models.CharField(max_length=40, null=True)
    p1_suspended_period = models.IntegerField(blank=True, null=True)
    params_tag = models.CharField(max_length=100)

    class Meta:
        managed = False
        db_table = 'lens_insider_trading_apac'


class TradingVolume(models.Model):
    id = models.BigAutoField(primary_key=True)
    trade_date = models.DateField()
    asset_name = models.CharField(max_length=20)
    vol_asset = models.DecimalField(max_digits=38, decimal_places=8, null=True)
    vol_local_currency = models.DecimalField(max_digits=38, decimal_places=8, null=True)
    fiat_vol= models.DecimalField(max_digits=38, decimal_places=8, null=True)
    btc_vol= models.DecimalField(max_digits=38, decimal_places=8, null=True)
    usdt_vol= models.DecimalField(max_digits=38, decimal_places=8, null=True)
    max_price = models.DecimalField(max_digits=38, decimal_places=8, null=True)
    min_price = models.DecimalField(max_digits=38, decimal_places=8, null=True)
    dif_price = models.DecimalField(max_digits=38, decimal_places=8, null=True)
    avg_price = models.DecimalField(max_digits=38, decimal_places=8, null=True)
    market = models.CharField(max_length=20)
    enum_value = models.CharField(max_length=20, null=False)

    class Meta:
        managed = False
        db_table = 'lens_trading_volume'

class TradingVolumeJoinAssetMaster(models.Model):
    id = models.BigAutoField(primary_key=True)
    trade_date = models.DateField()
    asset_name = models.CharField(max_length=20)
    vol_asset = models.DecimalField(max_digits=38, decimal_places=8, null=True)
    vol_local_currency = models.DecimalField(max_digits=38, decimal_places=8, null=True)
    fiat_vol= models.DecimalField(max_digits=38, decimal_places=8, null=True)
    btc_vol= models.DecimalField(max_digits=38, decimal_places=8, null=True)
    usdt_vol= models.DecimalField(max_digits=38, decimal_places=8, null=True)
    max_price = models.DecimalField(max_digits=38, decimal_places=8, null=True)
    min_price = models.DecimalField(max_digits=38, decimal_places=8, null=True)
    dif_price = models.DecimalField(max_digits=38, decimal_places=8, null=True)
    avg_price = models.DecimalField(max_digits=38, decimal_places=8, null=True)
    market = models.CharField(max_length=20)
    enum_value = models.CharField(max_length=20, null=False)

    assetmaster = models.ForeignKey(
        AssetMaster,
        to_field="enum_value",
        db_column="asset_enum",
        on_delete=models.DO_NOTHING,
        related_name="t_vols",
        null=True,
    )

    class Meta:
        managed = False
        db_table = 'lens_trading_volume'
        
class LensMicrostructuringApac(TimeStampedModel):
    DATE_FIELD = 'start_date'
    
    id = models.BigAutoField(primary_key=True)
    member_id = models.IntegerField(blank=True, null=True)
    member_uuid = models.CharField(max_length=191, blank=True, null=True)
    counts = models.IntegerField(blank=True, null=True)
    sum_fiat_amount = models.DecimalField(max_digits=38, decimal_places=20, null=True)
    action_type = models.CharField(max_length=30, blank=True, null=True)
    start_date = models.DateField(db_index=True) 
    end_date = models.DateField(db_index=True) 
    end_date = models.DateField(db_index=True) 
    p1_observation_period = models.IntegerField(blank=True, null=True)
    p2_accumulate_dw = models.DecimalField(max_digits=38, decimal_places=20, null=True)
    p3_counts_dw = models.IntegerField(blank=True, null=True)
    params_tag = models.CharField(max_length=100)
    class Meta:
        managed = False
        db_table = 'lens_microstructuring_apac'

class LensSmurfingId(TimeStampedModel):
    DATE_FIELD = 'start_date'

    id = models.BigAutoField(primary_key=True)
    member_id = models.IntegerField(blank=True, null=True)
    member_uuid = models.CharField(max_length=191, blank=True, null=True)
    counts = models.IntegerField(blank=True, null=True)
    sum_fiat_amount = models.DecimalField(max_digits=38, decimal_places=20, null=True)
    annual_income = models.CharField(max_length=100, blank=True, null=True)
    source_of_funds = models.CharField(blank=True, null=True)
    monthly_income = models.DecimalField(max_digits=30, blank=True, null=True)
    start_date = models.DateField(db_index=True) 
    end_date = models.DateField(db_index=True)
    p1_observation_period = models.IntegerField(blank=True, null=True)
    p2_salary_multiplication_threshold = models.IntegerField(null=True)
    params_tag = models.CharField(max_length=100)
    class Meta:
        managed = False
        db_table = 'lens_smurfing_id'


class LensFiatFeeVolume(models.Model):
    id = models.BigAutoField(primary_key=True)
    target_date = models.DateField()
    asset_enum = models.CharField(max_length=32, null=True)
    ask_fiat_fee= models.DecimalField(max_digits=32, decimal_places=20, null=True)
    bid_fiat_fee= models.DecimalField(max_digits=32, decimal_places=20, null=True)
    withdraw_fiat_fee= models.DecimalField(max_digits=32, decimal_places=20, null=True)
    asset_name = models.CharField(max_length=20, null=True)
    market = models.CharField(max_length=20, null=True)

    class Meta:
        managed = False
        db_table = 'lens_fiat_fee_volume'


class FeeVolumeJoinAssetMaster(models.Model):
    id = models.BigAutoField(primary_key=True)
    target_date = models.DateField()
    # asset_enum = models.CharField(max_length=32, null=True)
    ask_fiat_fee= models.DecimalField(max_digits=32, decimal_places=20, null=True)
    bid_fiat_fee= models.DecimalField(max_digits=32, decimal_places=20, null=True)
    withdraw_fiat_fee= models.DecimalField(max_digits=32, decimal_places=20, null=True)
    enum_value = models.CharField(max_length=20, null=False)
    market = models.CharField(max_length=20, null=True)
    assetmaster = models.ForeignKey(
        AssetMaster,
        to_field="enum_value",
        db_column="asset_enum",
        on_delete=models.DO_NOTHING,
        related_name="fee_currency",
        null=True,
    )

    class Meta:
        managed = False
        db_table = 'lens_fiat_fee_volume'