"""Background job runners. Each function is called by APScheduler on its cron schedule."""

import time

from app.core.supabase import supabase


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
    pass
