from datetime import datetime

from django.core.management.base import BaseCommand, CommandError, CommandParser

from executive_dashboard.services import (
    get_target_date,
    refresh_dashboard,
    refresh_dashboard_range,
)


class Command(BaseCommand):
    help = "Calculate and upsert the Executive Dashboard summary for Jakarta T-1."

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument(
            "--date",
            dest="target_date",
            help="Optional target date in YYYY-MM-DD format for a backfill.",
        )
        parser.add_argument(
            "--start-date",
            help="Inclusive start date in YYYY-MM-DD format for a range backfill.",
        )
        parser.add_argument(
            "--end-date",
            help="Inclusive end date in YYYY-MM-DD format for a range backfill.",
        )

    @staticmethod
    def _parse_date(value: str, option_name: str):
        try:
            return datetime.strptime(value, "%Y-%m-%d").date()
        except ValueError as exc:
            raise CommandError(f"{option_name} must use YYYY-MM-DD format.") from exc

    def handle(self, *args, **options) -> None:
        target_date = options.get("target_date")
        start_date = options.get("start_date")
        end_date = options.get("end_date")

        if target_date and (start_date or end_date):
            raise CommandError("Use either --date or --start-date with --end-date.")
        if bool(start_date) != bool(end_date):
            raise CommandError("--start-date and --end-date must be provided together.")

        if start_date and end_date:
            start = self._parse_date(start_date, "--start-date")
            end = self._parse_date(end_date, "--end-date")
            if end < start:
                raise CommandError("--end-date must be on or after --start-date.")
            summaries = refresh_dashboard_range(start, end)
            self.stdout.write(
                self.style.SUCCESS(
                    "Dashboard summaries refreshed for "
                    f"{summaries[0].target_date.isoformat()} through "
                    f"{summaries[-1].target_date.isoformat()} "
                    f"({len(summaries)} days)."
                )
            )
            return

        target = (
            self._parse_date(target_date, "--date")
            if target_date
            else get_target_date()
        )

        summary = refresh_dashboard(target)
        self.stdout.write(
            self.style.SUCCESS(
                "Dashboard summary refreshed for "
                f"{summary.target_date.isoformat()}."
            )
        )
