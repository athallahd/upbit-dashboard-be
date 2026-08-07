from datetime import date
from decimal import Decimal
from types import SimpleNamespace

from django.test import SimpleTestCase

from executive_dashboard.serializers import DashboardDailySerializer


def summary(**overrides):
    values = {
        "target_date": date(2026, 8, 6),
        "inbound_users": 100,
        "approved_users": 60,
        "first_deposit_users": 30,
        "repeat_deposit_users": 10,
        "first_trade_users": 20,
        "repeat_trade_users": 5,
        "dormant_users": 2,
        "trade_count": 25,
        "trading_users": 20,
        "total_volume_idr": Decimal("123.45"),
        "revenue_idr": Decimal("6.78"),
    }
    values.update(overrides)
    return SimpleNamespace(**values)


class DashboardDailySerializerTests(SimpleTestCase):
    def test_serializes_camel_case_metrics_and_conversions(self):
        data = DashboardDailySerializer(
            SimpleNamespace(summary=summary(), previous_summary=summary()),
        ).data

        self.assertEqual(data["target_date"], "2026-08-06")
        self.assertEqual(data["inboundUsers"], 100)
        self.assertEqual(data["repeatTrade"], 5)
        self.assertEqual(data["totalVolumeIdr"], "123.45")
        self.assertEqual(data["conversion"]["approvalRate"], 60.0)
        self.assertEqual(data["conversion"]["depositRate"], 50.0)
        self.assertEqual(data["change"]["firstTrade"], 0.0)

    def test_returns_null_change_when_previous_value_is_zero(self):
        current = summary(inbound_users=10)
        previous = summary(inbound_users=0)
        data = DashboardDailySerializer(
            SimpleNamespace(summary=current, previous_summary=previous),
        ).data

        self.assertIsNone(data["change"]["inboundUsers"])

    def test_conversion_uses_zero_for_empty_funnel_stage(self):
        data = DashboardDailySerializer(
            SimpleNamespace(
                summary=summary(approved_users=0, first_deposit_users=0),
                previous_summary=None,
            ),
        ).data

        self.assertEqual(data["conversion"]["depositRate"], 0.0)
