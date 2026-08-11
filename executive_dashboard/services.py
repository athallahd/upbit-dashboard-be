"""Business logic for Executive Dashboard operational metrics."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Any, Iterable, Literal
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


def _empty_metrics() -> Metrics:
    """Return a complete zero-value metric payload."""

    return {
        "inbound_users": 0,
        "approved_users": 0,
        "first_deposit_users": 0,
        "repeat_deposit_users": 0,
        "first_trade_users": 0,
        "repeat_trade_users": 0,
        "dormant_users": 0,
        "trading_users": 0,
        "trade_count": 0,
        "total_volume_idr": ZERO,
        "revenue_idr": ZERO,
    }


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


def _iter_dates(period: DashboardPeriod) -> Iterable[date]:
    current = period.start
    while current <= period.end:
        yield current
        current += timedelta(days=1)


def _load_daily_summaries(
    periods: Iterable[DashboardPeriod],
    db_alias: str,
) -> dict[date, DashboardDaily]:
    """Load all daily snapshots needed for a response in one query."""

    period_list = tuple(periods)
    if not period_list:
        return {}

    start_date = min(period.start for period in period_list)
    end_date = max(period.end for period in period_list)
    summaries = DashboardDaily.objects.using(db_alias).filter(
        target_date__gte=start_date,
        target_date__lte=end_date,
    )
    return {summary.target_date: summary for summary in summaries}


def _period_has_complete_daily_coverage(
    period: DashboardPeriod,
    summaries_by_date: dict[date, DashboardDaily],
) -> bool:
    """A completed period is ready only when every daily snapshot exists."""

    return all(target_date in summaries_by_date for target_date in _iter_dates(period))


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


def _build_period_cte(
    periods: Iterable[DashboardPeriod],
) -> tuple[tuple[DashboardPeriod, ...], str, list[Any]]:
    """Build a parameterized MySQL CTE containing dashboard date ranges."""

    period_list = tuple(periods)
    if not period_list:
        return (), "", []

    rows = []
    parameters: list[Any] = []
    dormant_days = int(getattr(settings, "DASHBOARD_DORMANT_DAYS", 180))
    for key, period in enumerate(period_list):
        inbound_start, inbound_end = _local_period_as_utc_range(
            period.start,
            period.end,
        )
        approval_start = datetime.combine(period.start, datetime.min.time())
        approval_end = datetime.combine(
            period.end + timedelta(days=1),
            datetime.min.time(),
        )
        rows.append(
            "SELECT %s AS period_key, %s AS period_start, %s AS period_end, "
            "%s AS inbound_start, %s AS inbound_end, %s AS approval_start, "
            "%s AS approval_end, %s AS dormant_cutoff"
        )
        parameters.extend(
            [
                key,
                period.start,
                period.end,
                inbound_start,
                inbound_end,
                approval_start,
                approval_end,
                period.end - timedelta(days=dormant_days),
            ]
        )

    return period_list, f"WITH periods AS ({' UNION ALL '.join(rows)})", parameters


def _calculate_period_metrics_batch(
    periods: Iterable[DashboardPeriod],
    db_alias: str,
) -> dict[DashboardPeriod, Metrics]:
    """Calculate source-backed periods in five batched aggregation queries.

    Weekly and monthly metrics cannot be derived by summing daily distinct-user
    rows. This helper therefore keeps the source-of-truth definitions while
    avoiding one full set of queries per requested period.
    """

    period_list, period_cte, cte_parameters = _build_period_cte(periods)
    results = {period: _empty_metrics() for period in period_list}
    if not period_list:
        return results

    period_by_key = dict(enumerate(period_list))
    approval_state = getattr(settings, "DASHBOARD_APPROVED_STATE", "accept")
    revenue_field = _get_revenue_field()

    inbound_sql = f"""
        {period_cte}
        SELECT p.period_key, COUNT(DISTINCT u.member_id)
        FROM periods AS p
        LEFT JOIN user_info AS u
          ON u.created_at >= p.inbound_start
         AND u.created_at < p.inbound_end
        GROUP BY p.period_key
        ORDER BY p.period_key
    """
    approved_sql = f"""
        {period_cte}
        SELECT p.period_key, COUNT(DISTINCT k.member_uuid)
        FROM periods AS p
        LEFT JOIN member_additional_info AS k
          ON k.state = %s
         AND k.member_uuid IS NOT NULL
         AND k.member_uuid <> ''
         AND k.updated_at >= p.approval_start
         AND k.updated_at < p.approval_end
        GROUP BY p.period_key
        ORDER BY p.period_key
    """
    deposit_sql = f"""
        {period_cte}, first_deposits AS (
            SELECT member_id, MIN(target_date) AS first_deposit_date
            FROM deposit_base
            WHERE member_id IS NOT NULL
            GROUP BY member_id
        )
        SELECT
            p.period_key,
            COUNT(DISTINCT CASE
                WHEN fd.first_deposit_date >= p.period_start THEN d.member_id
            END),
            COUNT(DISTINCT CASE
                WHEN fd.first_deposit_date < p.period_start THEN d.member_id
            END)
        FROM periods AS p
        LEFT JOIN deposit_base AS d
          ON d.target_date >= p.period_start
         AND d.target_date <= p.period_end
        LEFT JOIN first_deposits AS fd ON fd.member_id = d.member_id
        GROUP BY p.period_key
        ORDER BY p.period_key
    """
    participant_sql = f"""
        {period_cte}, participant_trades AS (
            SELECT b_customer_code AS participant_id, trade_date
            FROM trade_base
            WHERE b_customer_code IS NOT NULL
            UNION ALL
            SELECT s_customer_code AS participant_id, trade_date
            FROM trade_base
            WHERE s_customer_code IS NOT NULL
        ), participant_first_trades AS (
            SELECT participant_id, MIN(trade_date) AS first_trade_date
            FROM participant_trades
            GROUP BY participant_id
        ), period_participant_history AS (
            SELECT
                p.period_key,
                p.period_start,
                p.dormant_cutoff,
                pt.participant_id,
                MAX(pt.trade_date) AS last_trade_date,
                MAX(CASE
                    WHEN pt.trade_date >= p.period_start THEN 1 ELSE 0
                END) AS traded_in_period
            FROM periods AS p
            JOIN participant_trades AS pt ON pt.trade_date <= p.period_end
            GROUP BY p.period_key, p.period_start, p.dormant_cutoff, pt.participant_id
        )
        SELECT
            h.period_key,
            COALESCE(SUM(CASE WHEN h.traded_in_period = 1 THEN 1 ELSE 0 END), 0),
            COALESCE(SUM(CASE
                WHEN h.traded_in_period = 1
                 AND f.first_trade_date >= h.period_start
                THEN 1 ELSE 0
            END), 0),
            COALESCE(SUM(CASE
                WHEN h.traded_in_period = 1
                 AND f.first_trade_date < h.period_start
                THEN 1 ELSE 0
            END), 0),
            COALESCE(SUM(CASE
                WHEN h.last_trade_date < h.dormant_cutoff THEN 1 ELSE 0
            END), 0)
        FROM period_participant_history AS h
        JOIN participant_first_trades AS f ON f.participant_id = h.participant_id
        GROUP BY h.period_key
        ORDER BY h.period_key
    """
    trade_sql = f"""
        {period_cte}
        SELECT
            p.period_key,
            COUNT(t.trade_no),
            COALESCE(SUM(t.fiat_amount), 0),
            COALESCE(SUM(t.{revenue_field}), 0)
        FROM periods AS p
        LEFT JOIN trade_base AS t
          ON t.trade_date >= p.period_start
         AND t.trade_date <= p.period_end
        GROUP BY p.period_key
        ORDER BY p.period_key
    """

    with connections[db_alias].cursor() as cursor:
        cursor.execute(inbound_sql, cte_parameters)
        for period_key, inbound_users in cursor.fetchall():
            results[period_by_key[period_key]]["inbound_users"] = int(inbound_users or 0)

        cursor.execute(approved_sql, [*cte_parameters, approval_state])
        for period_key, approved_users in cursor.fetchall():
            results[period_by_key[period_key]]["approved_users"] = int(approved_users or 0)

        cursor.execute(deposit_sql, cte_parameters)
        for period_key, first_deposit_users, repeat_deposit_users in cursor.fetchall():
            metrics = results[period_by_key[period_key]]
            metrics["first_deposit_users"] = int(first_deposit_users or 0)
            metrics["repeat_deposit_users"] = int(repeat_deposit_users or 0)

        cursor.execute(participant_sql, cte_parameters)
        for (
            period_key,
            trading_users,
            first_trade_users,
            repeat_trade_users,
            dormant_users,
        ) in cursor.fetchall():
            metrics = results[period_by_key[period_key]]
            metrics["trading_users"] = int(trading_users or 0)
            metrics["first_trade_users"] = int(first_trade_users or 0)
            metrics["repeat_trade_users"] = int(repeat_trade_users or 0)
            metrics["dormant_users"] = int(dormant_users or 0)

        cursor.execute(trade_sql, cte_parameters)
        for period_key, trade_count, total_volume_idr, revenue_idr in cursor.fetchall():
            metrics = results[period_by_key[period_key]]
            metrics["trade_count"] = int(trade_count or 0)
            metrics["total_volume_idr"] = total_volume_idr or ZERO
            metrics["revenue_idr"] = revenue_idr or ZERO

    return results


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


def _snapshot_from_loaded_data(
    period: DashboardPeriod,
    summaries_by_date: dict[date, DashboardDaily],
    source_metrics_by_period: dict[DashboardPeriod, Metrics],
) -> DashboardPeriodSnapshot:
    """Build a snapshot without issuing one query per chart period."""

    if not _period_has_complete_daily_coverage(period, summaries_by_date):
        return DashboardPeriodSnapshot(period=period, metrics=None)

    if period.granularity == "daily":
        return DashboardPeriodSnapshot(
            period=period,
            metrics=_metrics_from_summary(summaries_by_date[period.start]),
        )

    return DashboardPeriodSnapshot(
        period=period,
        metrics=source_metrics_by_period[period],
    )


def get_operational_dashboard(
    granularity: DashboardGranularity = "daily",
    periods: int = 30,
    reference_date: date | None = None,
) -> OperationalDashboard:
    """Return chart history and latest completed operational dashboard period."""

    db_alias = get_dashboard_db_alias()
    period_ranges = build_period_ranges(granularity, periods, reference_date)
    comparison_period = get_previous_period(period_ranges[-1])
    required_periods = (*period_ranges, comparison_period)
    summaries_by_date = _load_daily_summaries(required_periods, db_alias)
    ready_source_periods = tuple(
        period
        for period in dict.fromkeys(required_periods)
        if period.granularity != "daily"
        and _period_has_complete_daily_coverage(period, summaries_by_date)
    )
    source_metrics_by_period = _calculate_period_metrics_batch(
        ready_source_periods,
        db_alias,
    )
    snapshots_by_period = {
        period: _snapshot_from_loaded_data(
            period,
            summaries_by_date,
            source_metrics_by_period,
        )
        for period in dict.fromkeys(required_periods)
    }
    series = tuple(snapshots_by_period[period] for period in period_ranges)
    current = series[-1]
    if current.metrics is None:
        raise DashboardDataNotReady(current.period.end)

    previous = snapshots_by_period[comparison_period]
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
