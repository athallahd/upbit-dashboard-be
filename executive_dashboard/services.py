"""Business logic for Executive Dashboard operational metrics."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Any, Literal
from zoneinfo import ZoneInfo

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.db import connections, transaction
from django.db.models import Subquery, Sum

from lens_data.models.data import DepositBase, TradeBase, UserInfo

from .models import DashboardDaily


ZERO = Decimal("0")
DashboardGranularity = Literal["daily", "weekly", "monthly"]
MetricValue = int | Decimal
Metrics = dict[str, MetricValue]

METRIC_FIELDS = (
    "inbound_users",
    "approved_users",
    "first_deposit_users",
    "repeat_deposit_users",
    "first_trade_users",
    "repeat_trade_users",
    "dormant_users",
    "trading_users",
    "trade_count",
    "total_volume_idr",
    "revenue_idr",
)


class DashboardDataNotReady(Exception):
    """Raised when the requested daily dashboard summary has not been refreshed."""


@dataclass(frozen=True)
class DashboardSnapshot:
    """Legacy current and previous daily summaries."""

    summary: DashboardDaily
    previous_summary: DashboardDaily | None


@dataclass(frozen=True)
class DashboardPeriod:
    """One completed Jakarta business period."""

    granularity: DashboardGranularity
    start: date
    end: date


@dataclass(frozen=True)
class DashboardPeriodSnapshot:
    """Metrics for a period, or ``None`` when a daily cache row is missing."""

    period: DashboardPeriod
    metrics: Metrics | None

    @property
    def data_available(self) -> bool:
        return self.metrics is not None


@dataclass(frozen=True)
class OperationalDashboard:
    """Latest completed period, its predecessor, and chart history."""

    granularity: DashboardGranularity
    current: DashboardPeriodSnapshot
    previous: DashboardPeriodSnapshot
    series: tuple[DashboardPeriodSnapshot, ...]


def get_dashboard_db_alias() -> str:
    """Return the database alias used by source and dashboard tables."""

    return getattr(settings, "DASHBOARD_DB_ALIAS", "reporter")


def get_target_date(reference_date: date | None = None) -> date:
    """Return the completed T-1 date in the configured local timezone."""

    if reference_date is None:
        local_today = datetime.now(ZoneInfo(settings.LOCAL_TIMEZONE)).date()
    else:
        local_today = reference_date
    return local_today - timedelta(days=1)


def _local_day_as_utc_range(target_date: date) -> tuple[datetime, datetime]:
    """Convert a Jakarta-local day to an aware UTC range."""

    return _local_period_as_utc_range(target_date, target_date)


def _local_period_as_utc_range(
    period_start: date,
    period_end: date,
) -> tuple[datetime, datetime]:
    """Convert inclusive Jakarta-local dates to an aware UTC half-open range."""

    local_tz = ZoneInfo(settings.LOCAL_TIMEZONE)
    start_local = datetime.combine(period_start, datetime.min.time(), tzinfo=local_tz)
    end_local = datetime.combine(
        period_end + timedelta(days=1),
        datetime.min.time(),
        tzinfo=local_tz,
    )
    utc_tz = ZoneInfo("UTC")
    return start_local.astimezone(utc_tz), end_local.astimezone(utc_tz)


def _local_today(reference_date: date | None = None) -> date:
    if reference_date is not None:
        return reference_date
    return datetime.now(ZoneInfo(settings.LOCAL_TIMEZONE)).date()


def _first_day_of_month(value: date) -> date:
    return value.replace(day=1)


def get_latest_completed_period(
    granularity: DashboardGranularity,
    reference_date: date | None = None,
) -> DashboardPeriod:
    """Return the latest completed local calendar period.

    Daily means Jakarta T-1. Weekly periods are Monday through Sunday. Monthly
    periods never include a partially completed current month.
    """

    local_today = _local_today(reference_date)
    if granularity == "daily":
        target_date = local_today - timedelta(days=1)
        return DashboardPeriod("daily", target_date, target_date)

    if granularity == "weekly":
        latest_end = local_today - timedelta(days=local_today.weekday() + 1)
        return DashboardPeriod("weekly", latest_end - timedelta(days=6), latest_end)

    if granularity == "monthly":
        current_month_start = _first_day_of_month(local_today)
        latest_end = current_month_start - timedelta(days=1)
        return DashboardPeriod("monthly", _first_day_of_month(latest_end), latest_end)

    raise ValueError(f"Unsupported dashboard granularity: {granularity}")


def get_previous_period(period: DashboardPeriod) -> DashboardPeriod:
    """Return the completed period immediately before ``period``."""

    if period.granularity == "daily":
        previous_date = period.start - timedelta(days=1)
        return DashboardPeriod("daily", previous_date, previous_date)

    if period.granularity == "weekly":
        previous_end = period.start - timedelta(days=1)
        return DashboardPeriod("weekly", previous_end - timedelta(days=6), previous_end)

    previous_end = period.start - timedelta(days=1)
    return DashboardPeriod("monthly", _first_day_of_month(previous_end), previous_end)


def build_period_ranges(
    granularity: DashboardGranularity,
    periods: int,
    reference_date: date | None = None,
) -> tuple[DashboardPeriod, ...]:
    """Build completed periods in chronological order for a chart series."""

    if periods < 1:
        raise ValueError("periods must be at least one")

    current = get_latest_completed_period(granularity, reference_date)
    result = [current]
    for _ in range(periods - 1):
        current = get_previous_period(current)
        result.append(current)
    return tuple(reversed(result))


def _count_inbound_users_for_period(
    period_start: date,
    period_end: date,
    db_alias: str,
) -> int:
    """Count distinct registrations created in an inclusive Jakarta date range."""

    start_utc, end_utc = _local_period_as_utc_range(period_start, period_end)
    return (
        UserInfo.objects.using(db_alias)
        .filter(created_at__gte=start_utc, created_at__lt=end_utc)
        .values("member_id")
        .distinct()
        .count()
    )


def _count_inbound_users(target_date: date, db_alias: str) -> int:
    """Backward-compatible single-day inbound counter."""

    return _count_inbound_users_for_period(target_date, target_date, db_alias)


def _count_approved_users_for_period(
    period_start: date,
    period_end: date,
    db_alias: str,
) -> int:
    """Count distinct members whose KYC state changed to accept in the period."""

    start_local = datetime.combine(period_start, datetime.min.time())
    end_local = datetime.combine(period_end + timedelta(days=1), datetime.min.time())
    approval_state = getattr(settings, "DASHBOARD_APPROVED_STATE", "accept")
    sql = """
        SELECT COUNT(DISTINCT member_uuid)
        FROM member_additional_info
        WHERE state = %s
          AND member_uuid IS NOT NULL
          AND member_uuid <> ''
          AND updated_at >= %s
          AND updated_at < %s
    """

    with connections[db_alias].cursor() as cursor:
        cursor.execute(sql, [approval_state, start_local, end_local])
        row = cursor.fetchone()

    return int((row or (0,))[0] or 0)


def _count_approved_users(target_date: date, db_alias: str) -> int:
    """Backward-compatible single-day KYC approval counter."""

    return _count_approved_users_for_period(target_date, target_date, db_alias)


def _count_deposit_metrics_for_period(
    period_start: date,
    period_end: date,
    db_alias: str,
) -> tuple[int, int]:
    """Return mutually exclusive first- and repeat-deposit users for a period.

    A repeat depositor must already have a deposit before ``period_start``.
    Therefore a member with their first and second deposits in one period is
    classified as first, never both first and repeat.
    """

    deposits = DepositBase.objects.using(db_alias)
    period_deposits = deposits.filter(
        target_date__gte=period_start,
        target_date__lte=period_end,
    )
    prior_deposit_members = deposits.filter(
        target_date__lt=period_start,
    ).values("member_id")

    first_deposit_users = (
        period_deposits.exclude(member_id__in=Subquery(prior_deposit_members))
        .values("member_id")
        .distinct()
        .count()
    )
    repeat_deposit_users = (
        period_deposits.filter(member_id__in=Subquery(prior_deposit_members))
        .values("member_id")
        .distinct()
        .count()
    )
    return first_deposit_users, repeat_deposit_users


def _count_deposit_metrics(target_date: date, db_alias: str) -> tuple[int, int]:
    """Backward-compatible single-day deposit metrics."""

    return _count_deposit_metrics_for_period(target_date, target_date, db_alias)


def _trade_participant_metrics_for_period(
    period_start: date,
    period_end: date,
    db_alias: str,
) -> dict[str, int]:
    """Calculate distinct participant metrics over an inclusive period.

    Buyer and seller records are unioned before grouping so one participant is
    counted once even if they trade on both sides or on many days. A repeat
    participant must have a trade before the period starts. Dormancy is a
    snapshot at ``period_end`` rather than a sum of daily snapshots.
    """

    cutoff_date = period_end - timedelta(
        days=int(getattr(settings, "DASHBOARD_DORMANT_DAYS", 180))
    )
    sql = """
        SELECT
            COALESCE(SUM(CASE WHEN traded_in_period = 1 THEN 1 ELSE 0 END), 0),
            COALESCE(SUM(CASE
                WHEN traded_in_period = 1 AND has_prior_trade = 0
                THEN 1 ELSE 0
            END), 0),
            COALESCE(SUM(CASE
                WHEN traded_in_period = 1 AND has_prior_trade = 1
                THEN 1 ELSE 0
            END), 0),
            COALESCE(SUM(
                CASE WHEN last_trade_date < %s THEN 1 ELSE 0 END
            ), 0)
        FROM (
            SELECT
                participant_id,
                MAX(trade_date) AS last_trade_date,
                MAX(CASE
                    WHEN trade_date >= %s AND trade_date <= %s THEN 1 ELSE 0
                END) AS traded_in_period,
                MAX(CASE WHEN trade_date < %s THEN 1 ELSE 0 END)
                    AS has_prior_trade
            FROM (
                SELECT b_customer_code AS participant_id, trade_date
                FROM trade_base
                WHERE b_customer_code IS NOT NULL AND trade_date <= %s
                UNION ALL
                SELECT s_customer_code AS participant_id, trade_date
                FROM trade_base
                WHERE s_customer_code IS NOT NULL AND trade_date <= %s
            ) AS participant_trades
            GROUP BY participant_id
        ) AS participant_stats
    """

    with connections[db_alias].cursor() as cursor:
        cursor.execute(
            sql,
            [
                cutoff_date,
                period_start,
                period_end,
                period_start,
                period_end,
                period_end,
            ],
        )
        row = cursor.fetchone()

    trading_users, first_trade_users, repeat_trade_users, dormant_users = row or (0, 0, 0, 0)
    return {
        "trading_users": int(trading_users or 0),
        "first_trade_users": int(first_trade_users or 0),
        "repeat_trade_users": int(repeat_trade_users or 0),
        "dormant_users": int(dormant_users or 0),
    }


def _trade_participant_metrics(target_date: date, db_alias: str) -> dict[str, int]:
    """Backward-compatible single-day participant metrics."""

    return _trade_participant_metrics_for_period(target_date, target_date, db_alias)


def _get_revenue_field() -> str:
    revenue_field = getattr(settings, "DASHBOARD_REVENUE_FIELD", "fiat_fee")
    if revenue_field not in {"fiat_fee", "b_fee", "s_fee"}:
        raise ImproperlyConfigured(
            "DASHBOARD_REVENUE_FIELD must be one of: fiat_fee, b_fee, s_fee."
        )
    return revenue_field


def _calculate_period_metrics(
    period_start: date,
    period_end: date,
    db_alias: str,
) -> Metrics:
    """Calculate operational metrics directly from source tables for a period."""

    first_deposit_users, repeat_deposit_users = _count_deposit_metrics_for_period(
        period_start,
        period_end,
        db_alias,
    )
    trade_metrics = _trade_participant_metrics_for_period(
        period_start,
        period_end,
        db_alias,
    )
    trade_queryset = TradeBase.objects.using(db_alias).filter(
        trade_date__gte=period_start,
        trade_date__lte=period_end,
    )
    volume = trade_queryset.aggregate(total=Sum("fiat_amount"))["total"]
    revenue = trade_queryset.aggregate(total=Sum(_get_revenue_field()))["total"]

    return {
        "inbound_users": _count_inbound_users_for_period(period_start, period_end, db_alias),
        "approved_users": _count_approved_users_for_period(period_start, period_end, db_alias),
        "first_deposit_users": first_deposit_users,
        "repeat_deposit_users": repeat_deposit_users,
        "first_trade_users": trade_metrics["first_trade_users"],
        "repeat_trade_users": trade_metrics["repeat_trade_users"],
        "dormant_users": trade_metrics["dormant_users"],
        "trade_count": trade_queryset.count(),
        "trading_users": trade_metrics["trading_users"],
        "total_volume_idr": volume if volume is not None else ZERO,
        "revenue_idr": revenue if revenue is not None else ZERO,
    }


def _calculate_metrics(target_date: date, db_alias: str) -> dict[str, Any]:
    """Calculate all persisted metrics for one completed business day."""

    return {
        "target_date": target_date,
        **_calculate_period_metrics(target_date, target_date, db_alias),
    }


def _metrics_from_summary(summary: DashboardDaily) -> Metrics:
    return {field: getattr(summary, field) for field in METRIC_FIELDS}


def _read_period_snapshot(
    period: DashboardPeriod,
    db_alias: str,
) -> DashboardPeriodSnapshot:
    """Read cached daily data or calculate a larger period from source tables."""

    if period.granularity == "daily":
        summary = DashboardDaily.objects.using(db_alias).filter(
            target_date=period.start
        ).first()
        return DashboardPeriodSnapshot(
            period=period,
            metrics=_metrics_from_summary(summary) if summary else None,
        )

    return DashboardPeriodSnapshot(
        period=period,
        metrics=_calculate_period_metrics(period.start, period.end, db_alias),
    )


def get_operational_dashboard(
    granularity: DashboardGranularity = "daily",
    periods: int = 30,
    reference_date: date | None = None,
) -> OperationalDashboard:
    """Return chart history and latest completed operational dashboard period."""

    db_alias = get_dashboard_db_alias()
    period_ranges = build_period_ranges(granularity, periods, reference_date)
    series = tuple(_read_period_snapshot(period, db_alias) for period in period_ranges)
    current = series[-1]
    if current.metrics is None:
        raise DashboardDataNotReady(current.period.end)

    previous = _read_period_snapshot(get_previous_period(current.period), db_alias)
    return OperationalDashboard(
        granularity=granularity,
        current=current,
        previous=previous,
        series=series,
    )


def refresh_dashboard(target_date: date | None = None) -> DashboardDaily:
    """Calculate and upsert a dashboard row for ``target_date``."""

    target_date = target_date or get_target_date()
    db_alias = get_dashboard_db_alias()
    metrics = _calculate_metrics(target_date, db_alias)
    now = datetime.now(ZoneInfo("UTC"))
    update_values = {key: value for key, value in metrics.items() if key != "target_date"}
    update_values["updated_at"] = now
    create_values = {**update_values, "created_at": now}

    with transaction.atomic(using=db_alias):
        summary, _ = DashboardDaily.objects.using(db_alias).update_or_create(
            target_date=target_date,
            defaults=update_values,
            create_defaults=create_values,
        )
    return summary


def refresh_dashboard_range(start_date: date, end_date: date) -> list[DashboardDaily]:
    """Backfill inclusive daily dashboard summaries in chronological order."""

    if end_date < start_date:
        raise ValueError("end_date must be on or after start_date")

    summaries = []
    current = start_date
    while current <= end_date:
        summaries.append(refresh_dashboard(current))
        current += timedelta(days=1)
    return summaries


def get_daily_dashboard(target_date: date | None = None) -> DashboardSnapshot:
    """Legacy helper retained for internal callers that require daily summaries."""

    target_date = target_date or get_target_date()
    db_alias = get_dashboard_db_alias()
    summaries = DashboardDaily.objects.using(db_alias)
    summary = summaries.filter(target_date=target_date).first()
    if summary is None:
        raise DashboardDataNotReady(target_date)

    previous_summary = summaries.filter(
        target_date=target_date - timedelta(days=1)
    ).first()
    return DashboardSnapshot(summary=summary, previous_summary=previous_summary)
