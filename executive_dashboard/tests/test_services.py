from datetime import date, datetime
from types import SimpleNamespace
from unittest.mock import MagicMock, call, patch

from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import SimpleTestCase

from executive_dashboard.services import (
    DashboardPeriod,
    DashboardPeriodSnapshot,
    _count_approved_users_for_period,
    _count_deposit_metrics_for_period,
    _trade_participant_metrics_for_period,
    build_period_ranges,
    get_latest_completed_period,
    get_previous_period,
    get_target_date,
)


class DashboardDateTests(SimpleTestCase):
    def test_target_date_is_the_previous_calendar_day(self):
        self.assertEqual(get_target_date(date(2026, 8, 7)), date(2026, 8, 6))

    def test_daily_latest_period_is_jakarta_t_minus_one(self):
        period = get_latest_completed_period("daily", date(2026, 8, 10))

        self.assertEqual(period.start, date(2026, 8, 9))
        self.assertEqual(period.end, date(2026, 8, 9))

    def test_weekly_latest_period_is_completed_monday_to_sunday(self):
        period = get_latest_completed_period("weekly", date(2026, 8, 10))

        self.assertEqual(period.start, date(2026, 8, 3))
        self.assertEqual(period.end, date(2026, 8, 9))

    def test_monthly_latest_period_is_completed_calendar_month(self):
        period = get_latest_completed_period("monthly", date(2026, 8, 10))

        self.assertEqual(period.start, date(2026, 7, 1))
        self.assertEqual(period.end, date(2026, 7, 31))

    def test_monthly_period_handles_year_rollover(self):
        period = get_latest_completed_period("monthly", date(2026, 1, 7))

        self.assertEqual(period.start, date(2025, 12, 1))
        self.assertEqual(period.end, date(2025, 12, 31))

    def test_monthly_period_handles_leap_year(self):
        period = get_latest_completed_period("monthly", date(2024, 3, 1))

        self.assertEqual(period.start, date(2024, 2, 1))
        self.assertEqual(period.end, date(2024, 2, 29))

    def test_period_ranges_are_chronological(self):
        periods = build_period_ranges("weekly", 3, date(2026, 8, 10))

        self.assertEqual(
            [(period.start, period.end) for period in periods],
            [
                (date(2026, 7, 20), date(2026, 7, 26)),
                (date(2026, 7, 27), date(2026, 8, 2)),
                (date(2026, 8, 3), date(2026, 8, 9)),
            ],
        )
        self.assertEqual(
            get_previous_period(periods[-1]),
            DashboardPeriod("weekly", date(2026, 7, 27), date(2026, 8, 2)),
        )


class ApprovedUserTests(SimpleTestCase):
    def test_counts_distinct_accepted_members_in_the_full_period(self):
        cursor = MagicMock()
        cursor.fetchone.return_value = (2,)
        connection = MagicMock()
        connection.cursor.return_value.__enter__.return_value = cursor
        connections = MagicMock()
        connections.__getitem__.return_value = connection

        with patch("executive_dashboard.services.connections", connections):
            result = _count_approved_users_for_period(
                date(2026, 7, 13),
                date(2026, 7, 19),
                "reporter",
            )

        self.assertEqual(result, 2)
        sql, parameters = cursor.execute.call_args.args
        self.assertIn("COUNT(DISTINCT member_uuid)", sql)
        self.assertEqual(
            parameters,
            [
                "accept",
                datetime(2026, 7, 13, 0, 0),
                datetime(2026, 7, 20, 0, 0),
            ],
        )


class DepositMetricTests(SimpleTestCase):
    def test_first_and_repeat_deposit_are_mutually_exclusive_for_period(self):
        deposits = MagicMock()
        period_deposits = MagicMock()
        prior_deposit_members = MagicMock()
        first_deposit_users = MagicMock()
        repeat_deposit_users = MagicMock()

        deposits.filter.side_effect = [period_deposits, prior_deposit_members]
        period_deposits.exclude.return_value = first_deposit_users
        period_deposits.filter.return_value = repeat_deposit_users
        first_deposit_users.values.return_value.distinct.return_value.count.return_value = 2
        repeat_deposit_users.values.return_value.distinct.return_value.count.return_value = 1

        manager = MagicMock()
        manager.using.return_value = deposits

        with patch("executive_dashboard.services.DepositBase.objects", manager):
            result = _count_deposit_metrics_for_period(
                date(2026, 7, 13),
                date(2026, 7, 19),
                "reporter",
            )

        self.assertEqual(result, (2, 1))
        deposits.filter.assert_has_calls(
            [
                call(target_date__gte=date(2026, 7, 13), target_date__lte=date(2026, 7, 19)),
                call(target_date__lt=date(2026, 7, 13)),
            ]
        )


class TradeMetricTests(SimpleTestCase):
    def test_trade_period_sql_deduplicates_buyer_and_seller_and_uses_period_start(self):
        cursor = MagicMock()
        cursor.fetchone.return_value = (2, 1, 1, 3)
        connection = MagicMock()
        connection.cursor.return_value.__enter__.return_value = cursor
        connections = MagicMock()
        connections.__getitem__.return_value = connection

        with patch("executive_dashboard.services.connections", connections):
            result = _trade_participant_metrics_for_period(
                date(2026, 7, 13),
                date(2026, 7, 19),
                "reporter",
            )

        self.assertEqual(
            result,
            {
                "trading_users": 2,
                "first_trade_users": 1,
                "repeat_trade_users": 1,
                "dormant_users": 3,
            },
        )
        sql, parameters = cursor.execute.call_args.args
        self.assertIn("UNION ALL", sql)
        self.assertIn("GROUP BY participant_id", sql)
        self.assertIn("trade_date < %s", sql)
        self.assertEqual(
            parameters,
            [
                date(2026, 1, 20),
                date(2026, 7, 13),
                date(2026, 7, 19),
                date(2026, 7, 13),
                date(2026, 7, 19),
                date(2026, 7, 19),
            ],
        )


class DashboardRefreshCommandTests(SimpleTestCase):
    @patch("executive_dashboard.management.commands.refresh_dashboard.refresh_dashboard_range")
    def test_refresh_command_accepts_an_inclusive_date_range(self, refresh_range):
        refresh_range.return_value = [
            SimpleNamespace(target_date=date(2026, 8, 1)),
            SimpleNamespace(target_date=date(2026, 8, 2)),
        ]

        call_command(
            "refresh_dashboard",
            "--start-date",
            "2026-08-01",
            "--end-date",
            "2026-08-02",
        )

        refresh_range.assert_called_once_with(date(2026, 8, 1), date(2026, 8, 2))

    def test_refresh_command_rejects_a_partial_date_range(self):
        with self.assertRaises(CommandError):
            call_command("refresh_dashboard", "--start-date", "2026-08-01")
