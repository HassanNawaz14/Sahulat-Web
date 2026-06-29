"""Background job runners. Each function is called by APScheduler on its cron schedule."""

import asyncio
import calendar
import random
import time
from datetime import date, datetime

from app.core.security import decrypt, parse_billing_month
from app.core.supabase import supabase
from app.scrapers.electricity.loadshedding_pdf import DISCO_PDF_URLS
from app.scrapers.registry import get_scraper
from app.services import compute_confidence
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


# Providers to parse loadshedding PDFs for (start with LESCO only, expand in V2)
LOADSHEDDING_PROVIDERS = ["lesco"]


async def fetch_loadshedding_pdfs():
    """Download and parse DISCO loadshedding PDFs, upsert into outage_schedules.

    Returns dict with status and result details.
    Runs Monday 09:00 PKT. Only processes LESCO in V1.
    """
    from app.scrapers.electricity.loadshedding_pdf import (
        parse_loadshedding_pdf,
        normalize_schedule_row,
        upsert_outage_schedules,
    )

    start = time.monotonic()
    total_upserted = 0
    total_failed = 0
    errors: list[str] = []

    for provider_code in LOADSHEDDING_PROVIDERS:
        try:
            entries = await parse_loadshedding_pdf(provider_code)
            if not entries:
                await log_run(provider_code, "loadshedding_pdf", "missing",
                              target_id="no_entries")
                errors.append(f"{provider_code}: no entries parsed from PDF")
                continue

            pdf_url = DISCO_PDF_URLS.get(provider_code, "")

            all_rows = []
            for entry in entries:
                rows = normalize_schedule_row(entry, provider_code, pdf_url=pdf_url)
                all_rows.extend(rows)

            if all_rows:
                count = upsert_outage_schedules(all_rows, source_url=pdf_url)
                total_upserted += count
            else:
                errors.append(f"{provider_code}: {len(entries)} entries produced 0 normalized rows")

            await log_run(provider_code, "loadshedding_pdf", "success",
                          target_id=f"upserted={len(all_rows)}",
                          duration_ms=int((time.monotonic() - start) * 1000))

        except Exception as e:
            total_failed += 1
            errors.append(f"{provider_code}: {e}")
            await log_run(provider_code, "loadshedding_pdf", "failed",
                          error_message=str(e),
                          duration_ms=int((time.monotonic() - start) * 1000))

    if total_failed == 0 and not errors:
        await log_run("system", "loadshedding_pdf_batch", "success",
                       target_id=f"total_upserted={total_upserted}",
                       duration_ms=int((time.monotonic() - start) * 1000))
        return {"status": "ok", "total_upserted": total_upserted}
    elif total_upserted > 0:
        await log_run("system", "loadshedding_pdf_batch", "partial",
                       target_id=f"upserted={total_upserted},failed={total_failed}",
                       duration_ms=int((time.monotonic() - start) * 1000))
        return {"status": "ok", "total_upserted": total_upserted, "warnings": errors}
    else:
        await log_run("system", "loadshedding_pdf_batch", "failed",
                       target_id=f"upserted=0",
                       error_message="; ".join(errors),
                       duration_ms=int((time.monotonic() - start) * 1000))
        return {"status": "error", "error": "; ".join(errors)}


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
    """Sync production data for all solar installations with API credentials. Runs every 30 min."""
    start = time.monotonic()
    installations = (
        supabase.table("solar_installations")
        .select("*")
        .is_("api_username_encrypted", "not", None)
        .is_("api_password_encrypted", "not", None)
        .execute()
    ).data or []

    if not installations:
        return {"status": "ok", "synced": 0}

    today = date.today()
    synced = 0
    errors = []

    for inst in installations:
        try:
            username = decrypt(inst.get("api_username_encrypted", ""))
            password = decrypt(inst.get("api_password_encrypted", ""))
            if not username or not password:
                continue

            brand = inst.get("inverter_brand", "").lower()
            if brand == "growatt":
                from app.services.solar.growatt import GrowattAdapter
                from app.services.solar.base import SolarCredentials
                adapter = GrowattAdapter()
                credentials = SolarCredentials(username=username, password=password, plant_id=inst.get("api_token_encrypted"))
                auth = await adapter.authenticate(credentials)
                if not auth.success:
                    continue

                production = await adapter.fetch_daily_production(inst, today)
                payload = {
                    "solar_installation_id": inst["id"],
                    "reading_date": production.date.isoformat() if hasattr(production.date, "isoformat") else str(production.date),
                    "energy_produced_kwh": production.production_kwh,
                    "energy_consumed_kwh": production.self_consumed_kwh,
                    "energy_exported_kwh": production.exported_kwh,
                    "energy_imported_kwh": production.imported_kwh,
                    "peak_power_kw": production.peak_power_kw,
                }
                supabase.table("solar_production_readings").upsert(payload, on_conflict="solar_installation_id, reading_date").execute()
                supabase.table("solar_installations").update({"last_synced_at": datetime.utcnow().isoformat()}).eq("id", inst["id"]).execute()
                synced += 1
            elif brand in ("solis", "huawei"):
                continue
        except Exception as e:
            errors.append(f"{inst.get('id', 'unknown')}: {str(e)}")
            continue

    duration = int((time.monotonic() - start) * 1000)
    await log_run("solar", "solar_data_sync", "success" if not errors else "partial",
                  target_id=f"synced={synced}", error_message="; ".join(errors) if errors else None,
                  duration_ms=duration)
    return {"status": "ok" if not errors else "partial", "synced": synced, "errors": errors}


async def send_outage_notifications():
    pass


async def expire_community_reports():
    """Mark expired community outage reports as restored (soft delete, runs every 15 min)."""
    supabase.table("community_outage_reports").update({
        "is_restored": True,
        "restored_at": datetime.utcnow().isoformat(),
    }).lt(
        "expires_at", "now()"
    ).execute()


async def compute_report_confidence():
    """Recompute confidence scores for active community outage reports (runs every 5 min).

    Confidence is based on report_count and scheduled outage overlap.
    """
    active = (
        supabase.table("community_outage_reports")
        .select("city, area_slug, utility_type, provider_code")
        .or_("expires_at.is.null,expires_at.gt.now()")
        .eq("is_restored", False)
        .execute()
    )
    if not active.data:
        return

    # Group by city + area_slug + utility_type
    groups: dict[str, dict] = {}
    for r in active.data:
        key = f"{r['city']}|{r['area_slug']}|{r['utility_type']}"
        if key not in groups:
            groups[key] = {"count": 0, "city": r["city"], "area_slug": r["area_slug"], "utility_type": r["utility_type"], "provider_code": r.get("provider_code")}
        groups[key]["count"] += 1

    for key, group in groups.items():
        count = group["count"]
        if count < 3:
            continue

        confidence = compute_confidence(count)
        supabase.table("community_outage_reports").update({
            "confidence_score": confidence,
        }).eq("city", group["city"]).eq("area_slug", group["area_slug"]).eq("utility_type", group["utility_type"]).execute()


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


# ─── P19 Notification Jobs ─────────────────────────────────────────────────────


async def check_bill_due_notifications():
    """Send bill due reminders for bills due in 3 days and today. Runs daily at 08:00 PKT."""
    from app.services.notifications.scheduler import check_and_send_notifications, get_users_with_upcoming_bills, get_users_with_bills_due_today

    # Bills due in 3 days
    upcoming = get_users_with_upcoming_bills(days_ahead=3)
    user_ids_3d = list({b["user_id"] for b in upcoming})

    def kwargs_fn_3d(uid: str) -> dict | None:
        user_bills = [b for b in upcoming if b["user_id"] == uid]
        if not user_bills:
            return None
        bill = user_bills[0]
        return {
            "provider": bill.get("provider_code", "").upper(),
            "amount": str(bill.get("amount_payable", 0)),
            "due_date": bill.get("due_date", ""),
        }

    check_and_send_notifications("bill_due_3_days", user_ids_3d, kwargs_fn_3d, rate_limit_per_day=2)

    # Bills due today
    due_today = get_users_with_bills_due_today()
    user_ids_today = list({b["user_id"] for b in due_today})

    def kwargs_fn_today(uid: str) -> dict | None:
        user_bills = [b for b in due_today if b["user_id"] == uid]
        if not user_bills:
            return None
        bill = user_bills[0]
        return {
            "provider": bill.get("provider_code", "").upper(),
            "amount": str(bill.get("amount_payable", 0)),
        }

    check_and_send_notifications("bill_due_today", user_ids_today, kwargs_fn_today, rate_limit_per_day=2)

    await log_run("system", "bill_due_notifications", "success",
                   target_id=f"due_3d={len(user_ids_3d)},due_today={len(user_ids_today)}")


async def check_budget_alerts():
    """Check all users' budget status and send warnings/exceeded alerts. Runs daily at 21:00 PKT."""
    from app.services.notifications.scheduler import check_and_send_notifications, get_users_at_budget_threshold

    # 80% warning
    warning_users = get_users_at_budget_threshold(0.8)

    def kwargs_fn_80(uid: str) -> dict | None:
        matches = [u for u in warning_users if u["user_id"] == uid]
        if not matches:
            return None
        m = matches[0]
        return {"percent": str(m["percent"]), "category": m["category"]}

    warning_ids = list({u["user_id"] for u in warning_users})
    check_and_send_notifications("budget_80_percent", warning_ids, kwargs_fn_80, rate_limit_per_day=1)

    # 100% exceeded
    exceeded_users = get_users_at_budget_threshold(1.0)

    def kwargs_fn_100(uid: str) -> dict | None:
        matches = [u for u in exceeded_users if u["user_id"] == uid]
        if not matches:
            return None
        m = matches[0]
        return {"category": m["category"]}

    exceeded_ids = list({u["user_id"] for u in exceeded_users})
    check_and_send_notifications("budget_exceeded", exceeded_ids, kwargs_fn_100, rate_limit_per_day=1)

    await log_run("system", "budget_alerts", "success",
                   target_id=f"warning={len(warning_ids)},exceeded={len(exceeded_ids)}")


async def check_slab_boundary_notifications():
    """Send slab boundary warnings. Runs daily at 20:00 PKT."""
    from app.services.notifications.scheduler import check_and_send_notifications

    accounts = (
        supabase.table("consumer_accounts")
        .select("id, user_id, provider_code")
        .eq("is_active", True)
        .eq("utility_type", "electricity")
        .execute()
    )

    slab_candidates: dict[str, dict] = {}
    for account in (accounts.data or []):
        try:
            readings = (
                supabase.table("meter_readings")
                .select("units_since_last")
                .eq("consumer_account_id", account["id"])
                .order("reading_date", desc=True)
                .limit(1)
                .execute()
            )
            if not readings.data:
                continue

            last_reading = readings.data[0]
            units_since_last = float(last_reading.get("units_since_last") or 0)
            if units_since_last < 10:
                continue

            from app.services.tariff import get_active_tariffs, get_current_slab

            slabs = get_active_tariffs(account["provider_code"])
            current_slab = get_current_slab(units_since_last, slabs)
            if current_slab is None or current_slab.get("max") is None:
                continue

            units_to_next = current_slab["max"] - units_since_last + 1
            if 0 < units_to_next <= 10:
                slab_candidates[account["user_id"]] = {
                    "units": str(int(units_since_last)),
                    "remaining": str(int(units_to_next)),
                    "rate": str(current_slab.get("rate", 0)),
                }
        except Exception:
            continue

    def kwargs_fn(uid: str) -> dict | None:
        info = slab_candidates.get(uid)
        if not info:
            return None
        return info

    check_and_send_notifications("slab_boundary", list(slab_candidates.keys()), kwargs_fn, rate_limit_per_day=1)
    await log_run("system", "slab_boundary_notifications", "success",
                   target_id=f"slab_candidates={len(slab_candidates)}")


async def generate_recurring_expenses():
    """Create next month's recurring expense entries. Runs daily at 03:00 PKT."""
    today = date.today()
    _, days_in_month = calendar.monthrange(today.year, today.month)

    # Calculate next month's date range
    if today.month == 12:
        next_year = today.year + 1
        next_month = 1
    else:
        next_year = today.year
        next_month = today.month + 1
    _, next_days = calendar.monthrange(next_year, next_month)

    recurrent = (
        supabase.table("budget_expenses")
        .select("id, user_id, category_id, amount, description, recurrence_day, expense_date")
        .eq("is_recurring", True)
        .execute()
    )

    for exp in (recurrent.data or []):
        try:
            day = exp["recurrence_day"]
            if not day:
                continue
            next_day = min(day, next_days)

            # Check if next month's entry already exists
            next_date = f"{next_year}-{next_month:02d}-{next_day:02d}"
            exists = (
                supabase.table("budget_expenses")
                .select("id")
                .eq("user_id", exp["user_id"])
                .eq("category_id", exp["category_id"])
                .eq("amount", exp["amount"])
                .eq("expense_date", next_date)
                .limit(1)
                .execute()
            )
            if exists.data:
                continue

            supabase.table("budget_expenses").insert({
                "user_id": exp["user_id"],
                "category_id": exp["category_id"],
                "amount": exp["amount"],
                "expense_date": next_date,
                "description": exp.get("description"),
                "is_recurring": True,
                "recurrence_day": day,
            }).execute()
        except Exception:
            continue
