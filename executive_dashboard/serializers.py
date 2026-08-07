from __future__ import annotations

from decimal import Decimal

from rest_framework import serializers

from .services import DashboardSnapshot


def _percentage(numerator: int, denominator: int) -> float:
    if denominator == 0:
        return 0.0
    return round(numerator * 100 / denominator, 2)


def _change_percentage(current: int, previous: int | None) -> float | None:
    if previous is None or previous == 0:
        return 0.0 if current == 0 and previous == 0 else None
    return round((current - previous) * 100 / previous, 2)


def _decimal_as_string(value: Decimal | None) -> str:
    return str(value if value is not None else Decimal("0"))


class DashboardDailySerializer(serializers.Serializer):
    """Public camelCase representation consumed by the Next.js dashboard."""

    target_date = serializers.DateField(source="summary.target_date")
    inboundUsers = serializers.IntegerField(source="summary.inbound_users")
    approvedUsers = serializers.IntegerField(source="summary.approved_users")
    firstDeposit = serializers.IntegerField(source="summary.first_deposit_users")
    repeatDeposit = serializers.IntegerField(source="summary.repeat_deposit_users")
    firstTrade = serializers.IntegerField(source="summary.first_trade_users")
    repeatTrade = serializers.IntegerField(source="summary.repeat_trade_users")
    dormantUsers = serializers.IntegerField(source="summary.dormant_users")
    tradeCount = serializers.IntegerField(source="summary.trade_count")
    tradingUsers = serializers.IntegerField(source="summary.trading_users")
    totalVolumeIdr = serializers.SerializerMethodField()
    revenueIdr = serializers.SerializerMethodField()
    conversion = serializers.SerializerMethodField()
    change = serializers.SerializerMethodField()
    insight = serializers.SerializerMethodField()

    def get_totalVolumeIdr(self, obj: DashboardSnapshot) -> str:
        return _decimal_as_string(obj.summary.total_volume_idr)

    def get_revenueIdr(self, obj: DashboardSnapshot) -> str:
        return _decimal_as_string(obj.summary.revenue_idr)

    def get_conversion(self, obj: DashboardSnapshot) -> dict[str, float]:
        summary = obj.summary
        return {
            "approvalRate": _percentage(summary.approved_users, summary.inbound_users),
            "depositRate": _percentage(summary.first_deposit_users, summary.approved_users),
            "firstTradeRate": _percentage(summary.first_trade_users, summary.first_deposit_users),
            "repeatTradeRate": _percentage(summary.repeat_trade_users, summary.first_trade_users),
        }

    def get_change(self, obj: DashboardSnapshot) -> dict[str, float | None]:
        summary = obj.summary
        previous = obj.previous_summary
        return {
            "inboundUsers": _change_percentage(
                summary.inbound_users,
                previous.inbound_users if previous else None,
            ),
            "approvedUsers": _change_percentage(
                summary.approved_users,
                previous.approved_users if previous else None,
            ),
            "firstDeposit": _change_percentage(
                summary.first_deposit_users,
                previous.first_deposit_users if previous else None,
            ),
            "repeatDeposit": _change_percentage(
                summary.repeat_deposit_users,
                previous.repeat_deposit_users if previous else None,
            ),
            "firstTrade": _change_percentage(
                summary.first_trade_users,
                previous.first_trade_users if previous else None,
            ),
            "repeatTrade": _change_percentage(
                summary.repeat_trade_users,
                previous.repeat_trade_users if previous else None,
            ),
        }

    def get_insight(self, obj: DashboardSnapshot) -> str:
        conversion = self.get_conversion(obj)
        stages = {
            "Inbound → Approved": conversion["approvalRate"],
            "Approved → First Deposit": conversion["depositRate"],
            "First Deposit → First Trade": conversion["firstTradeRate"],
            "First Trade → Repeat Trade": conversion["repeatTradeRate"],
        }
        bottleneck, rate = min(stages.items(), key=lambda item: item[1])
        return f"Main funnel bottleneck: {bottleneck} at {rate:.2f}%."
