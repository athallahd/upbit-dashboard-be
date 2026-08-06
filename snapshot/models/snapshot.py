from django.db import models
from lens.celeryconfig import beat_schedule



class AccountVersionSnapshot(models.Model):
    id = models.BigAutoField(primary_key=True)
    target_date = models.DateField()
    currency = models.CharField(max_length=32)
    member_id = models.BigIntegerField()
    member_uuid = models.CharField(max_length=191, blank=True, null=True)
    amount =  models.DecimalField(max_digits=32, decimal_places=20, blank=True, null=True)
    btc_amount =  models.DecimalField(max_digits=32, decimal_places=20, blank=True, null=True)
    value_btc_market =  models.DecimalField(max_digits=32, decimal_places=20, blank=True, null=True)
    value_fiat_market =  models.DecimalField(max_digits=32, decimal_places=20, blank=True, null=True)
    tag = models.CharField(unique=True, max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = False
        db_table = 'account_version_snapshot2'



STATUS_CHOICES = [
    ("p", "Pending"),
    ("c", "Checked"),
    ("f", "Failed"),
]

class NIDCheckLog(models.Model):
    id = models.BigAutoField(primary_key=True)
    # input = models.TextField(blank=True, null=True) # TODO: Depricate
    input_file = models.FileField(upload_to="nid_check", blank=True, null=True)
    # output = models.TextField() # TODO: Depricate
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=1, choices=STATUS_CHOICES, default='p')
    is_trigger = models.BooleanField(default=False)
    

    class Meta:
        managed = False
        db_table = 'nid_check_log'


class DukcapilCheckLog(models.Model):
    id = models.BigAutoField(primary_key=True)
    input_file = models.FileField(upload_to="dukcapil")
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=1, choices=STATUS_CHOICES, default='p')
    created_by = models.CharField(max_length=100)
    is_trigger = models.BooleanField(default=False)

    class Meta:
        managed = False
        db_table = 'dukcapil_check_log'

class AccountSnapshotLp(models.Model):
    id = models.BigAutoField(primary_key=True)
    member_id = models.IntegerField(blank=True, null=True)
    currency = models.IntegerField(blank=True, null=True)
    out = models.DecimalField(max_digits=32, decimal_places=20, blank=True, null=True)
    balance = models.DecimalField(max_digits=40, decimal_places=20, blank=True, null=True)
    locked = models.DecimalField(max_digits=40, decimal_places=20, blank=True, null=True)
    default_withdraw_fund_source_id = models.IntegerField(blank=True, null=True)
    default_deposit_fund_source_id = models.IntegerField(blank=True, null=True)
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()
    passbook_id = models.BigIntegerField()
    imported_at = models.DateTimeField(auto_now_add=True)
    fiat_value =  models.DecimalField(max_digits=32, decimal_places=20, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'account_snapshot_lp'


class PublicOrderbookSnapshot(models.Model):
    id = models.BigAutoField(primary_key=True)
    market = models.CharField(max_length=20)
    orderbook_timestamp_unix = models.BigIntegerField()
    total_ask_size = models.DecimalField(max_digits=38, decimal_places=20)
    total_bid_size = models.DecimalField(max_digits=38, decimal_places=20)
    orderbook_units = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = False
        db_table = 'public_orderbook_snapshot'

class AssetSnapshot(models.Model):
    id = models.BigAutoField(primary_key=True)
    target_date = models.DateField()
    file_name = models.CharField(max_length=255)
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        managed = False
        db_table = 'asset_snapshot'