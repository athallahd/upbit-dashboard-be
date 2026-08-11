from datetime import date, datetime, timedelta
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import MagicMock, call, patch

from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import SimpleTestCase

from executive_dashboard.services import (
    DashboardPeriod,
    DashboardPeriodSnapshot,
    DashboardDataNotReady,
    _calculate_period_metrics_batch,
    _count_approved_users_for_period,
    _count_deposit_metrics_for_period,
    _trade_participant_metrics_for_period,
    build_period_ranges,
    get_operational_dashboard,
    get_latest_completed_period,
    get_previous_period,
    get_target_date,
)


def metric_values(**overrides):
    values = {
        "inbound_users": 0,
        "approved_users": 0,
        "first_deposit_users": 0,
        "repeat_deposit_users": 0,
        "first_trade_users": 0,
        "repeat_trade_users": 0,
        "dormant_users": 0,
        "trading_users": 0,
        "trade_count": 0,
        "total_volume_idr": Decimal("0"),
        "revenue_idr": Decimal("0"),
    }
    values.update(overrides)
    return values


def summaries_for_periods(*periods, missing_dates=()):
    missing = set(missing_dates)
    summaries = {}
    for period in periods:
        current = period.start
        while current <= period.end:
            if current not in missing:
                summaries[current] = SimpleNamespace(
                    target_date=current,
                    **metric_values(),
                )
            current += timedelta(days=1)
    return summaries


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


class BatchedPeriodMetricTests(SimpleTestCase):
    def test_batch_calculation_uses_five_queries_for_all_requested_periods(self):
        cursor = MagicMock()
        cursor.fetchall.side_effect = [
            [(0, 1)],
            [(0, 2)],
            [(0, 3, 4)],
            [(0, 5, 6, 7, 8)],
            [(0, 9, Decimal("10.5"), Decimal("0.5"))],
        ]
        connection = MagicMock()
        connection.cursor.return_value.__enter__.return_value = cursor
        connections = MagicMock()
        connections.__getitem__.return_value = connection
        period = DashboardPeriod("weekly", date(2026, 8, 3), date(2026, 8, 9))

        with patch("executive_dashboard.services.connections", connections):
            result = _calculate_period_metrics_batch((period,), "reporter")

        self.assertEqual(cursor.execute.call_count, 5)
        self.assertEqual(
            result[period],
            metric_values(
                inbound_users=1,
                approved_users=2,
                first_deposit_users=3,
                repeat_deposit_users=4,
                trading_users=5,
                first_trade_users=6,
                repeat_trade_users=7,
                dormant_users=8,
                trade_count=9,
                total_volume_idr=Decimal("10.5"),
                revenue_idr=Decimal("0.5"),
            ),
        )

        executed_sql = [call.args[0] for call in cursor.execute.call_args_list]
        self.assertIn("first_deposits", executed_sql[2])
        self.assertIn("participant_first_trades", executed_sql[3])


class DashboardReadinessTests(SimpleTestCase):
    reference_date = date(2026, 8, 10)

    @patch("executive_dashboard.services._calculate_period_metrics_batch")
    @patch("executive_dashboard.services._load_daily_summaries")
    def test_daily_missing_snapshot_is_a_chart_gap_not_zero(
        self,
        load_summaries,
        calculate_batch,
    ):
        current = DashboardPeriod("daily", date(2026, 8, 9), date(2026, 8, 9))
        load_summaries.return_value = summaries_for_periods(current)
        calculate_batch.return_value = {}

        dashboard = get_operational_dashboard("daily", 2, self.reference_date)

        self.assertFalse(dashboard.series[0].data_available)
        self.assertIsNone(dashboard.series[0].metrics)
        self.assertTrue(dashboard.current.data_available)
        self.assertFalse(dashboard.previous.data_available)
        calculate_batch.assert_called_once_with((), "reporter")

    @patch("executive_dashboard.services._calculate_period_metrics_batch")
    @patch("executive_dashboard.services._load_daily_summaries")
    def test_weekly_missing_day_is_a_gap_while_current_week_remains_available(
        self,
        load_summaries,
        calculate_batch,
    ):
        previous = DashboardPeriod("weekly", date(2026, 7, 27), date(2026, 8, 2))
        current = DashboardPeriod("weekly", date(2026, 8, 3), date(2026, 8, 9))
        load_summaries.return_value = summaries_for_periods(
            previous,
            current,
            missing_dates=(date(2026, 7, 28),),
        )
        calculate_batch.return_value = {current: metric_values(inbound_users=4)}

        dashboard = get_operational_dashboard("weekly", 2, self.reference_date)

        self.assertFalse(dashboard.series[0].data_available)
        self.assertTrue(dashboard.current.data_available)
        self.assertEqual(dashboard.current.metrics["inbound_users"], 4)
        self.assertFalse(dashboard.previous.data_available)
        calculate_batch.assert_called_once_with((current,), "reporter")

    @patch("executive_dashboard.services._calculate_period_metrics_batch")
    @patch("executive_dashboard.services._load_daily_summaries")
    def test_incomplete_latest_month_raises_data_not_ready(
        self,
        load_summaries,
        calculate_batch,
    ):
        previous = DashboardPeriod("monthly", date(2026, 6, 1), date(2026, 6, 30))
        current = DashboardPeriod("monthly", date(2026, 7, 1), date(2026, 7, 31))
        load_summaries.return_value = summaries_for_periods(
            previous,
            current,
            missing_dates=(date(2026, 7, 7),),
        )
        calculate_batch.return_value = {previous: metric_values()}

        with self.assertRaises(DashboardDataNotReady):
            get_operational_dashboard("monthly", 1, self.reference_date)

        calculate_batch.assert_called_once_with((previous,), "reporter")

    @patch("executive_dashboard.services._calculate_period_metrics_batch")
    @patch("executive_dashboard.services._load_daily_summaries")
    def test_complete_zero_activity_period_remains_available(
        self,
        load_summaries,
        calculate_batch,
    ):
        previous = DashboardPeriod("weekly", date(2026, 7, 27), date(2026, 8, 2))
        current = DashboardPeriod("weekly", date(2026, 8, 3), date(2026, 8, 9))
        load_summaries.return_value = summaries_for_periods(previous, current)
        calculate_batch.return_value = {
            previous: metric_values(),
            current: metric_values(),
        }

        dashboard = get_operational_dashboard("weekly", 1, self.reference_date)

        self.assertTrue(dashboard.current.data_available)
        self.assertEqual(dashboard.current.metrics["inbound_users"], 0)
        self.assertEqual(dashboard.current.metrics["total_volume_idr"], Decimal("0"))


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
