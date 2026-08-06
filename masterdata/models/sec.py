from django.db import models
from lens.models.base_timestamped import TimeStampedModel

class AssetMaster(TimeStampedModel):
    sec_asset_id = models.CharField(max_length=32, blank=True, null=True)
    sec_asset_short_name = models.CharField(max_length=32, blank=True, null=True)
    currency_ticker = models.CharField(max_length=32, blank=True, null=True)
    asset_name = models.CharField(max_length=32, blank=True, null=True)
    flag1 = models.IntegerField(blank=True, null=True)
    comments = models.TextField(max_length=4000, blank=True)
    listing_date = models.DateField(blank=True, null=True)
    listing_time = models.TimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now_add=True)
    enum_value = models.IntegerField(max_length=10, primary_key=True)

    def __str__(self):
         return "Asset"

    class Meta:
        managed = False
        db_table = 'asset_master'

class ICEXAssetMaster(TimeStampedModel):
    id = models.BigAutoField(primary_key=True)
    asset_id = models.CharField(max_length=32, primary_key=True)
    asset_code = models.CharField(max_length=32, unique=True)
    asset_name = models.CharField(max_length=32)
    is_whitelisted = models.BooleanField(default=False)

    def __str__(self):
         return "ICEX Asset Master"

    class Meta:
        managed = False
        db_table = 'icex_asset_master'

# Ruleset params
class ParamMaster(TimeStampedModel):
    id = models.BigAutoField(primary_key=True)
    param_key = models.CharField(max_length=50, null=False, blank=False)
    param_field = models.CharField(max_length=50, null=False, blank=False)
    
    def __str__(self):
        return self.param_key+" - "+self.param_field
    
    class Meta:
        managed = False
        db_table = 'param_master'

class ParamValues(TimeStampedModel):
    id = models.BigAutoField(primary_key=True)
    param_master = models.ForeignKey(ParamMaster, on_delete = models.CASCADE)
    param_value = models.CharField(max_length=200)
    created_by = models.CharField(max_length=100)
    params_tag = models.CharField(max_length=100)

    class Meta:
        managed = False
        db_table = 'param_values'

class EmployeeMaster(TimeStampedModel):
    id = models.BigAutoField(primary_key=True)
    member_uuid = models.CharField(max_length=191, blank=True, null=True)
    employee_name = models.CharField(max_length=100, blank=True, null=True)
    
    class Meta:
        managed = False
        db_table = 'employee_master'

class LpMaster(TimeStampedModel):
    member_id = models.BigIntegerField(primary_key=True)
    company_name = models.CharField(max_length=100)
    is_default = models.BooleanField(default=False)
    providing_pairs = models.CharField(max_length=500, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        managed = False
        db_table = 'lp_master'


class DashboardAlertMaster(TimeStampedModel):
    id = models.BigAutoField(primary_key=True)
    alert_name = models.CharField(max_length=100)
    alert_for = models.CharField(max_length=100)
    alert_key = models.CharField(max_length=100)
    alert_type = models.CharField(max_length=100)
    alert_condition = models.CharField(max_length=200)
    alert_threshold = models.CharField(max_length=200)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.CharField(max_length=100)
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.CharField(max_length=100)

    class Meta:
        managed = False
        db_table = 'dashboard_alert_master'

class MarketMaster(TimeStampedModel):
    market_name = models.CharField(max_length=32, primary_key=True)
    flag = models.SmallIntegerField(default=0)
    comments = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        managed = False
        db_table = 'market_master'


class DashboardRulesetMaster(TimeStampedModel):
    id = models.BigAutoField(primary_key=True)
    ruleset_name = models.CharField(max_length=100)
    display_name = models.CharField(max_length=100)
    is_active = models.BooleanField(default=False)
    created_by = models.CharField(max_length=100)
    updated_by = models.CharField(max_length=100)

    class Meta:
        managed = False
        db_table = 'dashboard_ruleset_master'


class MarketCategory(models.Model):
    id = models.BigAutoField(primary_key=True)
    market = models.CharField(max_length=32)
    # enum = models.ForeignKey(CcxEnumValues, db_column='market', to_field="value", on_delete=models.DO_NOTHING)
    category = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.CharField(max_length=100)

    # def __str__(self):
    #     return "Asset"

    class Meta:
        managed = False
        db_table = 'market_category'

class UbidTestAccount(models.Model):
    id          = models.BigAutoField(primary_key=True)
    member_uuid = models.CharField(max_length=100)
    note        = models.CharField(max_length=100, null=True, blank=True)
    created_by  = models.CharField(max_length=100, null=True, blank=True)
    created_at  = models.DateTimeField(auto_now_add=True)
    updated_at  = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "ubid_test_account"

class TaggableMaster(TimeStampedModel):
    member_id = models.IntegerField(max_length=100)
    member_uuid = models.CharField(max_length=100, primary_key=True)
    email = models.CharField(max_length=255, null=True)
    type = models.CharField(max_length=50, null=True)
    nationality = models.CharField(max_length=100, null=True)
    
    def __str__(self):
         return "Taggable Master"

    class Meta:
        managed = False
        db_table = 'taggable_master'