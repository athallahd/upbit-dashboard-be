from datetime import date
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import patch

from django.test import SimpleTestCase
from rest_framework.test import APIRequestFactory, force_authenticate

from executive_dashboard.views import DashboardDailyView
from executive_dashboard.services import DashboardDataNotReady


class DashboardDailyViewTests(SimpleTestCase):
    def test_returns_daily_dashboard_payload(self):
        summary = SimpleNamespace(
            target_date=date(2026, 8, 6),
            inbound_users=1,
            approved_users=1,
            first_deposit_users=1,
            repeat_deposit_users=0,
            first_trade_users=1,
            repeat_trade_users=0,
            dormant_users=0,
            trade_count=1,
            trading_users=1,
            total_volume_idr=Decimal("10"),
            revenue_idr=Decimal("1"),
        )
        request = APIRequestFactory().get("/api/dashboard/daily/")
        force_authenticate(request, user=SimpleNamespace(is_authenticated=True))

        with patch(
            "executive_dashboard.views.get_daily_dashboard",
            return_value=SimpleNamespace(summary=summary, previous_summary=None),
        ):
            response = DashboardDailyView.as_view()(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["target_date"], "2026-08-06")
        self.assertEqual(response.data["inboundUsers"], 1)

    def test_returns_not_found_until_the_summary_is_refreshed(self):
        request = APIRequestFactory().get("/api/dashboard/daily/")
        force_authenticate(request, user=SimpleNamespace(is_authenticated=True))

        with patch(
            "executive_dashboard.views.get_daily_dashboard",
            side_effect=DashboardDataNotReady(date(2026, 8, 6)),
        ):
            response = DashboardDailyView.as_view()(request)

        self.assertEqual(response.status_code, 404)
        self.assertIn("refresh_dashboard", response.data["detail"])
