from datetime import date
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import patch

from django.test import SimpleTestCase
from rest_framework.test import APIRequestFactory, force_authenticate

from executive_dashboard.services import (
    DashboardDataNotReady,
    DashboardPeriod,
    DashboardPeriodSnapshot,
    OperationalDashboard,
)
from executive_dashboard.views import DashboardDailyView


def metrics():
    return {
        "inbound_users": 1,
        "approved_users": 1,
        "first_deposit_users": 1,
        "repeat_deposit_users": 0,
        "first_trade_users": 1,
        "repeat_trade_users": 0,
        "dormant_users": 0,
        "trading_users": 1,
        "trade_count": 1,
        "total_volume_idr": Decimal("10"),
        "revenue_idr": Decimal("1"),
    }


def operational_dashboard():
    period = DashboardPeriod("daily", date(2026, 8, 6), date(2026, 8, 6))
    previous = DashboardPeriod("daily", date(2026, 8, 5), date(2026, 8, 5))
    current_snapshot = DashboardPeriodSnapshot(period, metrics())
    previous_snapshot = DashboardPeriodSnapshot(previous, metrics())
    return OperationalDashboard(
        granularity="daily",
        current=current_snapshot,
        previous=previous_snapshot,
        series=(previous_snapshot, current_snapshot),
    )


class DashboardDailyViewTests(SimpleTestCase):
    def test_returns_period_dashboard_payload_from_existing_url(self):
        request = APIRequestFactory().get(
            "/api/dashboard/daily/?granularity=weekly&periods=12"
        )
        force_authenticate(request, user=SimpleNamespace(is_authenticated=True))

        with patch(
            "executive_dashboard.views.get_operational_dashboard",
            return_value=operational_dashboard(),
        ) as dashboard_service:
            response = DashboardDailyView.as_view()(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["schemaVersion"], 2)
        dashboard_service.assert_called_once_with(granularity="weekly", periods=12)

    def test_rejects_invalid_period_parameters(self):
        request = APIRequestFactory().get(
            "/api/dashboard/daily/?granularity=monthly&periods=25"
        )
        force_authenticate(request, user=SimpleNamespace(is_authenticated=True))

        response = DashboardDailyView.as_view()(request)

        self.assertEqual(response.status_code, 400)
        self.assertIn("periods", response.data)

    def test_returns_not_found_when_latest_daily_summary_is_missing(self):
        request = APIRequestFactory().get("/api/dashboard/daily/")
        force_authenticate(request, user=SimpleNamespace(is_authenticated=True))

        with patch(
            "executive_dashboard.views.get_operational_dashboard",
            side_effect=DashboardDataNotReady(date(2026, 8, 6)),
        ):
            response = DashboardDailyView.as_view()(request)

        self.assertEqual(response.status_code, 404)
        self.assertIn("refresh_dashboard", response.data["detail"])
