"""Background job runners. Each function is called by APScheduler on its cron schedule."""

import asyncio
import random
import time
from datetime import date, datetime

from app.core.security import decrypt, parse_billing_month
from app.core.supabase import supabase
from app.scrapers.registry import get_scraper
from app.services.tariff import (
    compute_electricity_bill,
    compute_marginal_cost,
    get_active_tariffs,
    get_current_slab,
    get_next_slab,
)


async def log_run(
    provider_code: str,
    job_type: str,
    status: str,
    target_id: str | None = None,
    error_message: str | None = None,
    duration_ms: int | None = None,
):
    supabase.table("scraper_run_log").insert({
        "provider_code": provider_code,
        "job_type": job_type,
        "status": status,
        "target_id": target_id,
        "error_message": error_message,
        "duration_ms": duration_ms,
    }).execute()


async def refresh_all_bills():
    """Re-fetch latest bill for every active consumer account. Daily at 07:00 PKT."""
    start = time.monotonic()
    accounts = (
        supabase.table("consumer_accounts")
        .select("*")
        .eq("is_active", True)
        .order("provider_code")
        .execute()
    )
    rows = accounts.data or []

    by_provider: dict[str, list[dict]] = {}
    for acc in rows:
        by_provider.setdefault(acc["provider_code"], []).append(acc)

    BATCH_LIMIT = 200
    total_fetched = 0
    total_failed = 0

    async def process_account(account: dict):
        nonlocal total_fetched, total_failed
        try:
            scraper = get_scraper(account["provider_code"])
            consumer_number = decrypt(account["consumer_number"])
            bill_data = await scraper.fetch_bill(consumer_number)
        except Exception:
            total_failed += 1
            return

        billing_month = parse_billing_month(bill_data.issue_date, bill_data.due_date)

        existing = (
            supabase.table("bills")
            .select("id")
            .eq("consumer_account_id", account["id"])
            .eq("billing_month", billing_month)
            .execute()
        )

        bill_payload = {
            "consumer_account_id": account["id"],
            "user_id": account["user_id"],
            "billing_month": billing_month,
            "issue_date": bill_data.issue_date,
            "due_date": bill_data.due_date,
            "amount_payable": bill_data.amount_payable,
            "units_consumed": bill_data.units_consumed,
            "previous_reading": bill_data.previous_reading,
            "current_reading": bill_data.current_reading,
            "arrears": bill_data.arrears,
            "taxes": bill_data.taxes,
            "surcharges": bill_data.surcharges,
            "meter_rent": bill_data.meter_rent,
            "fc_surcharge": bill_data.fc_surcharge,
            "tariff_slab": bill_data.tariff_slab,
            "raw_data": bill_data.raw_data,
        }

        if existing.data:
            bill_payload["updated_at"] = datetime.utcnow().isoformat()
            supabase.table("bills").update(bill_payload).eq("id", existing.data[0]["id"]).execute()
        else:
            supabase.table("bills").insert(bill_payload).execute()

        supabase.table("consumer_accounts").update(
            {"last_fetched_at": datetime.utcnow().isoformat()}
        ).eq("id", account["id"]).execute()

        total_fetched += 1

    for provider_code, provider_accounts in by_provider.items():
        batch = provider_accounts[:BATCH_LIMIT]
        for account in batch:
            await process_account(account)
            await asyncio.sleep(random.uniform(2, 5))

    duration = int((time.monotonic() - start) * 1000)
    await log_run("system", "refresh_all_bills", "success",
                   target_id=f"fetched={total_fetched},failed={total_failed}",
                   duration_ms=duration)


async def mark_overdue_bills():
    """Mark unpaid bills past due_date as overdue. Runs daily at 08:00 PKT."""
    today = date.today().isoformat()
    result = (
        supabase.table("bills")
        .update({"status": "overdue", "updated_at": datetime.utcnow().isoformat()})
        .eq("status", "unpaid")
        .lt("due_date", today)
        .execute()
    )
    count = len(result.data or [])
    await log_run("system", "mark_overdue_bills", "success",
                   target_id=f"marked_overdue={count}")


async def auto_paid_from_arrears():
    """If latest bill has arrears=0, mark previous bill as paid."""
    accounts = (
        supabase.table("consumer_accounts")
        .select("id")
        .eq("is_active", True)
        .execute()
    )
    for acc in (accounts.data or []):
        latest = (
            supabase.table("bills")
            .select("id, arrears, billing_month, status")
            .eq("consumer_account_id", acc["id"])
            .order("billing_month", desc=True)
            .limit(1)
            .execute()
        )
        if not latest.data:
            continue
        arrears_val = latest.data[0].get("arrears")
        if arrears_val is None or float(arrears_val) != 0:
            continue
        # Get the bill immediately before the latest one (by billing_month)
        prev = (
            supabase.table("bills")
            .select("id, status")
            .eq("consumer_account_id", acc["id"])
            .order("billing_month", desc=True)
            .limit(1)
            .offset(1)
            .execute()
        )
        if prev.data and prev.data[0].get("status") != "paid":
            supabase.table("bills").update({
                "status": "paid",
                "updated_at": datetime.utcnow().isoformat(),
            }).eq("id", prev.data[0]["id"]).execute()


async def fetch_loadshedding_pdfs():
    start = time.monotonic()
    try:
        from app.scrapers.electricity.loadshedding_pdf import parse_loadshedding_pdf

        entries = await parse_loadshedding_pdf("lesco")
        for entry in entries:
            supabase.table("outage_schedules").upsert({
                "provider_code": "lesco",
                "feeder_code": entry.feeder_code,
                "feeder_name": entry.feeder_name,
                "area_tags": [],
                "city": "lahore",
                "schedule_date": entry.schedule_date.isoformat(),
                "slots": entry.slots,
                "week_start": entry.schedule_date.isoformat(),
            }).execute()

        duration = int((time.monotonic() - start) * 1000)
        await log_run("lesco", "loadshedding_pdf", "success", duration_ms=duration)
    except Exception as e:
        duration = int((time.monotonic() - start) * 1000)
        await log_run("lesco", "loadshedding_pdf", "failed", error_message=str(e), duration_ms=duration)


async def fetch_nepra_tariffs():
    from app.scrapers.common.http_client import get_client
    start = time.monotonic()
    try:
        async with get_client() as client:
            resp = await client.get("https://nepra.org.pk/tariff/electricity.php")
            resp.raise_for_status()
        await log_run("nepra", "nepra_tariffs", "success",
                       duration_ms=int((time.monotonic() - start) * 1000))
    except Exception as e:
        await log_run("nepra", "nepra_tariffs", "failed", error_message=str(e),
                       duration_ms=int((time.monotonic() - start) * 1000))


async def fetch_ogra_tariffs():
    start = time.monotonic()
    try:
        await log_run("ogra", "ogra_tariffs", "success",
                       duration_ms=int((time.monotonic() - start) * 1000))
    except Exception as e:
        await log_run("ogra", "ogra_tariffs", "failed", error_message=str(e),
                       duration_ms=int((time.monotonic() - start) * 1000))


async def refresh_isp_packages():
    pass


async def solar_data_sync():
    pass


async def send_outage_notifications():
    pass


async def cleanup_old_reports():
    supabase.table("community_outage_reports").delete().lt(
        "expires_at", "now()"
    ).execute()


async def bill_due_date_alerts():
    pass


async def slab_boundary_check():
    accounts = (
        supabase.table("consumer_accounts")
        .select("*, bills!inner(*)")
        .eq("is_active", True)
        .in_("utility_type", ["electricity", "gas"])
        .execute()
    )
    if not accounts.data:
        return

    for account in accounts.data:
        try:
            readings = (
                supabase.table("meter_readings")
                .select("*")
                .eq("consumer_account_id", account["id"])
                .order("reading_date", desc=True)
                .limit(1)
                .execute()
            )
            if not readings.data:
                continue

            last_bill = None
            bills_data = account.get("bills")
            if isinstance(bills_data, list) and bills_data:
                last_bill = bills_data[0]

            from datetime import date, timedelta
            cycle_start = (date.today().replace(day=1) - timedelta(days=1)).replace(day=1)
            cycle_readings = (
                supabase.table("meter_readings")
                .select("units_since_last")
                .eq("consumer_account_id", account["id"])
                .gte("reading_date", cycle_start.isoformat())
                .execute()
            )
            total_units = sum(
                float(r["units_since_last"] or 0) for r in (cycle_readings.data or [])
            )
            if not readings.data or total_units == 0:
                continue

            slabs = get_active_tariffs(account["provider_code"])
            current_slab = get_current_slab(total_units, slabs)
            if current_slab is None or current_slab["max"] is None:
                continue

            next_slab = get_next_slab(current_slab, slabs)
            if next_slab is None:
                continue

            units_to_next = current_slab["max"] - total_units + 1
            ALERT_THRESHOLDS = [10, 20, 50]
            today = date.today()
            billing_period = today.replace(day=1).isoformat()

            for threshold in ALERT_THRESHOLDS:
                if units_to_next > threshold:
                    continue
                exists = (
                    supabase.table("slab_alerts")
                    .select("id")
                    .eq("consumer_account_id", account["id"])
                    .eq("billing_period", billing_period)
                    .eq("slab_threshold", threshold)
                    .execute()
                )
                if exists.data:
                    continue

                cost = compute_marginal_cost(total_units, slabs)
                supabase.table("slab_alerts").insert({
                    "consumer_account_id": account["id"],
                    "user_id": account["user_id"],
                    "billing_period": billing_period,
                    "slab_threshold": threshold,
                    "units_at_alert": units_to_next,
                    "cost_if_crossed": cost,
                }).execute()
                break
        except Exception:
            continue
