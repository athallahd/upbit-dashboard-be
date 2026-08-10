from django.db import models


class MemberAdditionalInfo(models.Model):
    """Historical KYC state records imported into the reporting database."""

    id = models.BigIntegerField(primary_key=True)
    member_uuid = models.CharField(max_length=36, blank=True, null=True)
    uuid = models.CharField(max_length=36, blank=True, null=True)
    laser_number = models.CharField(max_length=191, blank=True, null=True)
    education_level = models.CharField(max_length=191, blank=True, null=True)
    marital_status = models.CharField(max_length=191, blank=True, null=True)
    objective = models.CharField(max_length=255, blank=True, null=True)
    occupation = models.CharField(max_length=255, blank=True, null=True)
    position = models.CharField(max_length=191, blank=True, null=True)
    range_of_income = models.CharField(max_length=191, blank=True, null=True)
    job_type = models.CharField(max_length=191, blank=True, null=True)
    source_of_funds = models.CharField(max_length=255, blank=True, null=True)
    company_name = models.CharField(max_length=255, blank=True, null=True)
    company_address = models.CharField(max_length=512, blank=True, null=True)
    w9_form_id = models.CharField(max_length=191, blank=True, null=True)
    w8ben_form_id = models.CharField(max_length=191, blank=True, null=True)
    supported_document_1_id = models.CharField(
        max_length=191,
        blank=True,
        null=True,
    )
    supported_document_2_id = models.CharField(
        max_length=191,
        blank=True,
        null=True,
    )
    suitability_test_score = models.DecimalField(
        max_digits=10,
        decimal_places=4,
        blank=True,
        null=True,
    )
    knowledge_test_passed = models.PositiveSmallIntegerField(
        blank=True,
        null=True,
    )
    phone_number = models.CharField(max_length=32, blank=True, null=True)
    state = models.CharField(max_length=32, blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)
    npwp_number = models.CharField(max_length=64, blank=True, null=True)
    mother_name = models.CharField(max_length=255, blank=True, null=True)
    suitability_test_at = models.DateTimeField(blank=True, null=True)
    occupation_detail = models.CharField(max_length=255, blank=True, null=True)
    company_phone_number = models.CharField(max_length=32, blank=True, null=True)
    other_information = models.TextField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = "member_additional_info"


class DashboardDaily(models.Model):
    """One completed business day of Executive Dashboard metrics.
    """

    target_date = models.DateField(primary_key=True)
    inbound_users = models.PositiveIntegerField(default=0)
    approved_users = models.PositiveIntegerField(default=0)
    first_deposit_users = models.PositiveIntegerField(default=0)
    repeat_deposit_users = models.PositiveIntegerField(default=0)
    first_trade_users = models.PositiveIntegerField(default=0)
    repeat_trade_users = models.PositiveIntegerField(default=0)
    dormant_users = models.PositiveIntegerField(default=0)
    trade_count = models.PositiveIntegerField(default=0)
    trading_users = models.PositiveIntegerField(default=0)
    total_volume_idr = models.DecimalField(
        max_digits=38,
        decimal_places=20,
        default=0,
    )
    revenue_idr = models.DecimalField(
        max_digits=38,
        decimal_places=20,
        default=0,
    )
    created_at = models.DateTimeField(editable=False)
    updated_at = models.DateTimeField(editable=False)

    class Meta:
        managed = False
        db_table = "dashboard_daily_summary"

    def __str__(self) -> str:
        return f"Dashboard summary for {self.target_date.isoformat()}"
