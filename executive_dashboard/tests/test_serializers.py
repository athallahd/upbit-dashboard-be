from datetime import date
from decimal import Decimal

from django.test import SimpleTestCase

from executive_dashboard.serializers import (
    DashboardQuerySerializer,
    OperationalDashboardSerializer,
)
from executive_dashboard.services import (
    DashboardPeriod,
    DashboardPeriodSnapshot,
    OperationalDashboard,
)


def metrics(**overrides):
    values = {
        "inbound_users": 100,
        "approved_users": 60,
        "first_deposit_users": 30,
        "repeat_deposit_users": 10,
        "first_trade_users": 20,
        "repeat_trade_users": 5,
        "dormant_users": 2,
        "trading_users": 20,
        "trade_count": 25,
        "total_volume_idr": Decimal("123.45000000000000000000"),
        "revenue_idr": Decimal("6.78000000000000000000"),
    }
    values.update(overrides)
    return values


def dashboard(current_metrics=None, previous_metrics=None):
    current = DashboardPeriodSnapshot(
        DashboardPeriod("weekly", date(2026, 8, 3), date(2026, 8, 9)),
        current_metrics or metrics(),
    )
    previous = DashboardPeriodSnapshot(
        DashboardPeriod("weekly", date(2026, 7, 27), date(2026, 8, 2)),
        previous_metrics,
    )
    return OperationalDashboard(
        granularity="weekly",
        current=current,
        previous=previous,
        series=(previous, current),
    )


class DashboardQuerySerializerTests(SimpleTestCase):
    def test_defaults_to_thirty_daily_periods(self):
        serializer = DashboardQuerySerializer(data={})

        self.assertTrue(serializer.is_valid(), serializer.errors)
        self.assertEqual(serializer.validated_data, {"granularity": "daily", "periods": 30})

    def test_applies_granularity_specific_default(self):
        serializer = DashboardQuerySerializer(data={"granularity": "weekly"})

        self.assertTrue(serializer.is_valid(), serializer.errors)
        self.assertEqual(serializer.validated_data["periods"], 12)

    def test_rejects_periods_over_the_granularity_limit(self):
        serializer = DashboardQuerySerializer(
            data={"granularity": "monthly", "periods": 25}
        )

        self.assertFalse(serializer.is_valid())
        self.assertIn("periods", serializer.errors)


class OperationalDashboardSerializerTests(SimpleTestCase):
    def test_serializes_schema_v2_metrics_changes_and_missing_series_gap(self):
        data = OperationalDashboardSerializer(dashboard(previous_metrics=None)).data

        self.assertEqual(data["schemaVersion"], 2)
        self.assertEqual(data["granularity"], "weekly")
        self.assertEqual(data["periodStart"], "2026-08-03")
        self.assertEqual(data["comparisonLabel"], "vs previous week")
        self.assertEqual(data["metrics"]["inboundUsers"], 100)
        self.assertEqual(data["metrics"]["totalVolumeIdr"], "123.45000000000000000000")
        self.assertIsNone(data["change"]["inboundUsers"])
        self.assertFalse(data["series"][0]["dataAvailable"])
        self.assertIsNone(data["series"][0]["metrics"])

    def test_change_handles_zero_previous_values_without_false_infinity(self):
        data = OperationalDashboardSerializer(
            dashboard(
                current_metrics=metrics(inbound_users=10, approved_users=0),
                previous_metrics=metrics(inbound_users=0, approved_users=0),
            )
        ).data

        self.assertIsNone(data["change"]["inboundUsers"])
        self.assertEqual(data["change"]["approvedUsers"], 0.0)
