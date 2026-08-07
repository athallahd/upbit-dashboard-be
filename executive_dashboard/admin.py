from django.contrib import admin

from .models import DashboardDaily


@admin.register(DashboardDaily)
class DashboardDailyAdmin(admin.ModelAdmin):
    """Read-only admin view for SQL-owned dashboard summaries."""

    list_display = (
        "target_date",
        "inbound_users",
        "approved_users",
        "first_deposit_users",
        "first_trade_users",
        "revenue_idr",
        "updated_at",
    )
    list_filter = ("target_date",)
    ordering = ("-target_date",)

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
