from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Any

from rest_framework import serializers

from .services import METRIC_FIELDS, OperationalDashboard, get_latest_completed_period


PERIOD_LIMITS = {
    "daily": 180,
    "weekly": 52,
    "monthly": 24,
}

METRIC_FIELD_NAMES = {
    "inbound_users": "inboundUsers",
    "approved_users": "approvedUsers",
    "first_deposit_users": "firstDeposit",
    "repeat_deposit_users": "repeatDeposit",
    "first_trade_users": "firstTrade",
    "repeat_trade_users": "repeatTrade",
    "dormant_users": "dormantUsers",
    "trading_users": "tradingUsers",
    "trade_count": "tradeCount",
    "total_volume_idr": "totalVolumeIdr",
    "revenue_idr": "revenueIdr",
}

DECIMAL_METRICS = {"total_volume_idr", "revenue_idr"}


def _change_percentage(
    current: int | Decimal,
    previous: int | Decimal | None,
) -> float | None:
    """Return a safe previous-period percentage change."""

    if previous is None:
        return None
    if previous == 0:
        return 0.0 if current == 0 else None
    return round(float((current - previous) * 100 / previous), 2)


def _serialize_metrics(metrics: dict[str, int | Decimal] | None) -> dict[str, Any] | None:
    if metrics is None:
        return None

    return {
        METRIC_FIELD_NAMES[field]: (
            str(metrics[field]) if field in DECIMAL_METRICS else int(metrics[field])
        )
        for field in METRIC_FIELDS
    }


class DashboardQuerySerializer(serializers.Serializer):
    """Validate the timeline parameters accepted by the existing dashboard URL."""

    granularity = serializers.ChoiceField(
        choices=tuple(PERIOD_LIMITS),
        default="daily",
        required=False,
    )
    periods = serializers.IntegerField(min_value=1, required=False)
    end_month = serializers.RegexField(
        regex=r"^\d{4}-(0[1-9]|1[0-2])$",
        required=False,
        help_text="Completed historical month in YYYY-MM format; monthly only.",
    )

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        granularity = attrs.get("granularity", "daily")
        default_periods = {"daily": 30, "weekly": 12, "monthly": 12}
        periods = attrs.get("periods", default_periods[granularity])
        maximum = PERIOD_LIMITS[granularity]
        if periods > maximum:
            raise serializers.ValidationError(
                {"periods": f"{granularity} periods cannot exceed {maximum}."}
            )
        attrs["granularity"] = granularity
        attrs["periods"] = periods

        end_month = attrs.get("end_month")
        if end_month is None:
            return attrs
        if granularity != "monthly":
            raise serializers.ValidationError(
                {"end_month": "end_month is only supported when granularity=monthly."}
            )

        end_month_date = date.fromisoformat(f"{end_month}-01")
        latest_completed_month = get_latest_completed_period("monthly")
        if end_month_date > latest_completed_month.start:
            raise serializers.ValidationError(
                {"end_month": "end_month must be a completed calendar month."}
            )
        attrs["end_month"] = end_month_date
        return attrs


class OperationalDashboardSerializer(serializers.Serializer):
    """Camel-case API schema for the period-based operational dashboard."""

    def to_representation(self, instance: OperationalDashboard) -> dict[str, Any]:
        current_metrics = instance.current.metrics
        previous_metrics = instance.previous.metrics
        if current_metrics is None:
            raise ValueError("Operational dashboard requires current metrics.")

        changes = {
            METRIC_FIELD_NAMES[field]: _change_percentage(
                current_metrics[field],
                previous_metrics[field] if previous_metrics is not None else None,
            )
            for field in METRIC_FIELDS
        }
        comparison_label = {
            "daily": "vs previous day",
            "weekly": "vs previous week",
            "monthly": "vs previous month",
        }[instance.granularity]

        return {
            "schemaVersion": 2,
            "granularity": instance.granularity,
            "periodStart": instance.current.period.start.isoformat(),
            "periodEnd": instance.current.period.end.isoformat(),
            "comparisonLabel": comparison_label,
            "metrics": _serialize_metrics(current_metrics),
            "change": changes,
            "series": [
                {
                    "periodStart": snapshot.period.start.isoformat(),
                    "periodEnd": snapshot.period.end.isoformat(),
                    "dataAvailable": snapshot.data_available,
                    "metrics": _serialize_metrics(snapshot.metrics),
                }
                for snapshot in instance.series
            ],
        }
