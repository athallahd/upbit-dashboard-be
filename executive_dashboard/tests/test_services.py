from datetime import date, datetime
from unittest.mock import MagicMock, call, patch

from django.test import SimpleTestCase

from executive_dashboard.services import (
    _count_approved_users,
    _count_deposit_metrics,
    _trade_participant_metrics,
    get_target_date,
)


class DashboardDateTests(SimpleTestCase):
    def test_target_date_is_always_the_previous_calendar_day(self):
        self.assertEqual(
            get_target_date(date(2026, 8, 7)),
            date(2026, 8, 6),
        )


class ApprovedUserTests(SimpleTestCase):
    def test_counts_distinct_accepted_kyc_members_on_local_target_day(self):
        cursor = MagicMock()
        cursor.fetchone.return_value = (2,)
        connection = MagicMock()
        connection.cursor.return_value.__enter__.return_value = cursor
        connections = MagicMock()
        connections.__getitem__.return_value = connection

        with patch(
            "executive_dashboard.services.connections",
            connections,
        ):
            result = _count_approved_users(date(2026, 7, 13), "reporter")

        self.assertEqual(result, 2)
        cursor.execute.assert_called_once()
        self.assertEqual(
            cursor.execute.call_args.args[1],
            [
                "accept",
                datetime(2026, 7, 13, 0, 0),
                datetime(2026, 7, 14, 0, 0),
            ],
        )
        cursor.fetchone.assert_called_once_with()


class DepositMetricTests(SimpleTestCase):
    def test_classifies_same_day_multiple_deposits_as_first_not_repeat(self):
        deposits = MagicMock()
        target_deposits = MagicMock()
        prior_deposit_members = MagicMock()
        first_deposit_users = MagicMock()
        repeat_deposit_users = MagicMock()

        deposits.filter.side_effect = [target_deposits, prior_deposit_members]
        target_deposits.exclude.return_value = first_deposit_users
        target_deposits.filter.return_value = repeat_deposit_users
        first_deposit_users.values.return_value.distinct.return_value.count.return_value = 2
        repeat_deposit_users.values.return_value.distinct.return_value.count.return_value = 0

        manager = MagicMock()
        manager.using.return_value = deposits

        with patch("executive_dashboard.services.DepositBase.objects", manager):
            result = _count_deposit_metrics(date(2026, 7, 13), "reporter")

        self.assertEqual(result, (2, 0))
        deposits.filter.assert_has_calls(
            [
                call(target_date=date(2026, 7, 13)),
                call(target_date__lt=date(2026, 7, 13)),
            ]
        )
        self.assertEqual(target_deposits.exclude.call_count, 1)
        self.assertEqual(target_deposits.filter.call_count, 1)


class TradeMetricTests(SimpleTestCase):
    def test_counts_repeat_trades_only_when_activity_predates_target_day(self):
        cursor = MagicMock()
        cursor.fetchone.return_value = (2, 2, 0, 0)
        connection = MagicMock()
        connection.cursor.return_value.__enter__.return_value = cursor
        connections = MagicMock()
        connections.__getitem__.return_value = connection

        with patch("executive_dashboard.services.connections", connections):
            result = _trade_participant_metrics(date(2026, 7, 13), "reporter")

        self.assertEqual(
            result,
            {
                "trading_users": 2,
                "first_trade_users": 2,
                "repeat_trade_users": 0,
                "dormant_users": 0,
            },
        )
        sql, parameters = cursor.execute.call_args.args
        self.assertIn("has_prior_trade", sql)
        self.assertEqual(
            parameters,
            [
                date(2026, 1, 14),
                date(2026, 7, 13),
                date(2026, 7, 13),
                date(2026, 7, 13),
                date(2026, 7, 13),
            ],
        )
