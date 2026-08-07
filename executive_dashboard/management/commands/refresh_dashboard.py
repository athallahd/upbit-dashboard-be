from datetime import datetime

from django.core.management.base import BaseCommand, CommandError, CommandParser

from executive_dashboard.services import get_target_date, refresh_dashboard


class Command(BaseCommand):
    help = "Calculate and upsert the Executive Dashboard summary for Jakarta T-1."

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument(
            "--date",
            dest="target_date",
            help="Optional target date in YYYY-MM-DD format for a backfill.",
        )

    def handle(self, *args, **options) -> None:
        target_date = options.get("target_date")
        if target_date:
            try:
                target_date = datetime.strptime(target_date, "%Y-%m-%d").date()
            except ValueError as exc:
                raise CommandError("--date must use YYYY-MM-DD format.") from exc
        else:
            target_date = get_target_date()

        summary = refresh_dashboard(target_date)
        self.stdout.write(
            self.style.SUCCESS(
                "Dashboard summary refreshed for "
                f"{summary.target_date.isoformat()}."
            )
        )
