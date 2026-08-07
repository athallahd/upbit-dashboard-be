from django.db import models


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
