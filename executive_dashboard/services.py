"""Business logic for building and reading the Executive Dashboard summary."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Any
from zoneinfo import ZoneInfo

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.db import connections, transaction
from django.db.models import Subquery, Sum

from lens_data.models.data import DepositBase, TradeBase, UserInfo

from .models import DashboardDaily


ZERO = Decimal("0")


class DashboardDataNotReady(Exception):
    """Raised when the requested dashboard summary has not been refreshed."""


@dataclass(frozen=True)
class DashboardSnapshot:
    """Current and previous summaries used to build the API response."""

    summary: DashboardDaily
    previous_summary: DashboardDaily | None


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
    """Convert a local calendar day to an aware UTC range for DateTimeField."""

    local_tz = ZoneInfo(settings.LOCAL_TIMEZONE)
    start_local = datetime.combine(target_date, datetime.min.time(), tzinfo=local_tz)
    end_local = start_local + timedelta(days=1)
    utc_tz = ZoneInfo("UTC")
    return start_local.astimezone(utc_tz), end_local.astimezone(utc_tz)


def _count_inbound_users(target_date: date, db_alias: str) -> int:
    """Count registrations created during the target local calendar day."""

    start_utc, end_utc = _local_day_as_utc_range(target_date)
    return (
        UserInfo.objects.using(db_alias)
        .filter(created_at__gte=start_utc, created_at__lt=end_utc)
        .count()
    )


def _count_approved_users(target_date: date, db_alias: str) -> int:
    """Count distinct KYC members accepted on the target Jakarta date.

    ``member_additional_info`` is the approval-event source. Its timestamps
    are imported as MySQL ``DATETIME`` values representing Jakarta local time,
    so the query deliberately uses local, naive boundaries instead of the UTC
    range used for timezone-aware ``user_info.created_at`` values.
    """

    start_local = datetime.combine(target_date, datetime.min.time())
    end_local = start_local + timedelta(days=1)
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


def _count_deposit_metrics(target_date: date, db_alias: str) -> tuple[int, int]:
    """Return mutually exclusive first- and repeat-deposit user counts.

    A user who makes multiple deposits on their first day is still a first
    depositor. Repeat depositors must have at least one deposit before the
    target date, then deposit again on the target date.
    """

    deposits = DepositBase.objects.using(db_alias)
    target_deposits = deposits.filter(target_date=target_date)
    prior_deposit_members = deposits.filter(
        target_date__lt=target_date,
    ).values("member_id")

    first_deposit_users = (
        target_deposits.exclude(member_id__in=Subquery(prior_deposit_members))
        .values("member_id")
        .distinct()
        .count()
    )
    repeat_deposit_users = (
        target_deposits.filter(member_id__in=Subquery(prior_deposit_members))
        .values("member_id")
        .distinct()
        .count()
    )
    return first_deposit_users, repeat_deposit_users


def _trade_participant_metrics(target_date: date, db_alias: str) -> dict[str, int]:
    """Aggregate trade users across both buyer and seller columns.

    ``trade_base`` stores both sides of an execution in one row. A SQL UNION
    gives each member one participant record per trade, avoiding double
    counting a member who appears on both sides of a row.
    """

    cutoff_date = target_date - timedelta(
        days=int(getattr(settings, "DASHBOARD_DORMANT_DAYS", 180))
    )
    sql = """
        SELECT
            COALESCE(SUM(CASE WHEN traded_on_target = 1 THEN 1 ELSE 0 END), 0),
            COALESCE(SUM(CASE
                WHEN traded_on_target = 1 AND has_prior_trade = 0
                THEN 1 ELSE 0
            END), 0),
            COALESCE(SUM(CASE
                WHEN traded_on_target = 1 AND has_prior_trade = 1
                THEN 1 ELSE 0
            END), 0),
            COALESCE(SUM(
                CASE WHEN last_trade_date < %s THEN 1 ELSE 0 END
            ), 0)
        FROM (
            SELECT
                participant_id,
                MAX(trade_date) AS last_trade_date,
                MAX(CASE WHEN trade_date = %s THEN 1 ELSE 0 END)
                    AS traded_on_target,
                MAX(CASE WHEN trade_date < %s THEN 1 ELSE 0 END)
                    AS has_prior_trade
            FROM (
                SELECT b_customer_code AS participant_id, trade_date, trade_no
                FROM trade_base
                WHERE b_customer_code IS NOT NULL AND trade_date <= %s
                UNION
                SELECT s_customer_code AS participant_id, trade_date, trade_no
                FROM trade_base
                WHERE s_customer_code IS NOT NULL AND trade_date <= %s
            ) AS participant_trades
            GROUP BY participant_id
        ) AS participant_stats
    """

    with connections[db_alias].cursor() as cursor:
        cursor.execute(
            sql,
            [cutoff_date, target_date, target_date, target_date, target_date],
        )
        row = cursor.fetchone()

    trading_users, first_trade_users, repeat_trade_users, dormant_users = row or (0, 0, 0, 0)
    return {
        "trading_users": int(trading_users or 0),
        "first_trade_users": int(first_trade_users or 0),
        "repeat_trade_users": int(repeat_trade_users or 0),
        "dormant_users": int(dormant_users or 0),
    }


def _calculate_metrics(target_date: date, db_alias: str) -> dict[str, Any]:
    """Calculate all persisted metrics for one completed business day."""

    first_deposit_users, repeat_deposit_users = _count_deposit_metrics(
        target_date,
        db_alias,
    )
    trade_metrics = _trade_participant_metrics(target_date, db_alias)

    trade_queryset = TradeBase.objects.using(db_alias).filter(trade_date=target_date)
    volume = trade_queryset.aggregate(total=Sum("fiat_amount"))["total"]
    revenue_field = getattr(settings, "DASHBOARD_REVENUE_FIELD", "fiat_fee")
    if revenue_field not in {"fiat_fee", "b_fee", "s_fee"}:
        raise ImproperlyConfigured(
            "DASHBOARD_REVENUE_FIELD must be one of: fiat_fee, b_fee, s_fee."
        )
    revenue = trade_queryset.aggregate(total=Sum(revenue_field))["total"]

    return {
        "target_date": target_date,
        "inbound_users": _count_inbound_users(target_date, db_alias),
        "approved_users": _count_approved_users(target_date, db_alias),
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


def refresh_dashboard(target_date: date | None = None) -> DashboardDaily:
    """Calculate and upsert a dashboard row for ``target_date``.

    The optional date is intended for backfills and local verification. The
    regular daily flow omits it and refreshes Jakarta T-1.
    """

    target_date = target_date or get_target_date()
    db_alias = get_dashboard_db_alias()
    metrics = _calculate_metrics(target_date, db_alias)
    now = datetime.now(ZoneInfo("UTC"))
    update_values = {key: value for key, value in metrics.items() if key != "target_date"}
    update_values["updated_at"] = now
    create_values = {**update_values, "created_at": now}

    with transaction.atomic(using=db_alias):
        summary, _ = (
            DashboardDaily.objects.using(db_alias)
            .update_or_create(
                target_date=target_date,
                defaults=update_values,
                create_defaults=create_values,
            )
        )
    return summary


def get_daily_dashboard(target_date: date | None = None) -> DashboardSnapshot:
    """Read the cached current and previous daily dashboard summaries."""

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
