from datetime import date

from django.test import SimpleTestCase

from executive_dashboard.services import get_target_date


class DashboardDateTests(SimpleTestCase):
    def test_target_date_is_always_the_previous_calendar_day(self):
        self.assertEqual(
            get_target_date(date(2026, 8, 7)),
            date(2026, 8, 6),
        )
