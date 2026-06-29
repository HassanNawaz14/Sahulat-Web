SCHEDULED_JOBS = [
    {
        "id": "refresh_all_bills",
        "func": "app.jobs.runner:refresh_all_bills",
        "trigger": "cron",
        "hour": 7,
        "minute": 0,
        "timezone": "Asia/Karachi",
    },
    {
        "id": "mark_overdue_bills",
        "func": "app.jobs.runner:mark_overdue_bills",
        "trigger": "cron",
        "hour": 8,
        "minute": 0,
        "timezone": "Asia/Karachi",
    },
    {
        "id": "auto_paid_from_arrears",
        "func": "app.jobs.runner:auto_paid_from_arrears",
        "trigger": "cron",
        "hour": 8,
        "minute": 30,
        "timezone": "Asia/Karachi",
    },
    {
        "id": "fetch_loadshedding_pdfs",
        "func": "app.jobs.runner:fetch_loadshedding_pdfs",
        "trigger": "cron",
        "day_of_week": "mon",
        "hour": 9,
        "minute": 0,
        "timezone": "Asia/Karachi",
    },
    {
        "id": "fetch_nepra_tariffs",
        "func": "app.jobs.runner:fetch_nepra_tariffs",
        "trigger": "cron",
        "day": 1,
        "hour": 6,
        "minute": 0,
        "timezone": "Asia/Karachi",
    },
    {
        "id": "fetch_ogra_tariffs",
        "func": "app.jobs.runner:fetch_ogra_tariffs",
        "trigger": "cron",
        "day": 1,
        "hour": 6,
        "minute": 0,
        "timezone": "Asia/Karachi",
    },
    {
        "id": "refresh_isp_packages",
        "func": "app.jobs.runner:refresh_isp_packages",
        "trigger": "cron",
        "day_of_week": "sun",
        "hour": 10,
        "minute": 0,
        "timezone": "Asia/Karachi",
    },
    {
        "id": "solar_data_sync",
        "func": "app.jobs.runner:solar_data_sync",
        "trigger": "interval",
        "minutes": 30,
    },
    {
        "id": "send_outage_notifications",
        "func": "app.jobs.runner:send_outage_notifications",
        "trigger": "interval",
        "minutes": 15,
    },
    {
        "id": "expire_community_reports",
        "func": "app.jobs.runner:expire_community_reports",
        "trigger": "interval",
        "minutes": 15,
    },
    {
        "id": "compute_report_confidence",
        "func": "app.jobs.runner:compute_report_confidence",
        "trigger": "interval",
        "minutes": 5,
    },
    {
        "id": "bill_due_date_alerts",
        "func": "app.jobs.runner:bill_due_date_alerts",
        "trigger": "cron",
        "hour": 9,
        "minute": 0,
        "timezone": "Asia/Karachi",
    },
    {
        "id": "slab_boundary_check",
        "func": "app.jobs.runner:slab_boundary_check",
        "trigger": "cron",
        "hour": 8,
        "minute": 0,
        "timezone": "Asia/Karachi",
    },
    {
        "id": "generate_recurring_expenses",
        "func": "app.jobs.runner:generate_recurring_expenses",
        "trigger": "cron",
        "hour": 3,
        "minute": 0,
        "timezone": "Asia/Karachi",
    },
    {
        "id": "check_bill_due_notifications",
        "func": "app.jobs.runner:check_bill_due_notifications",
        "trigger": "cron",
        "hour": 8,
        "minute": 0,
        "timezone": "Asia/Karachi",
    },
    {
        "id": "check_budget_alerts",
        "func": "app.jobs.runner:check_budget_alerts",
        "trigger": "cron",
        "hour": 21,
        "minute": 0,
        "timezone": "Asia/Karachi",
    },
    {
        "id": "check_slab_boundary_notifications",
        "func": "app.jobs.runner:check_slab_boundary_notifications",
        "trigger": "cron",
        "hour": 20,
        "minute": 0,
        "timezone": "Asia/Karachi",
    },
]


def start_scheduler():
    from apscheduler.schedulers.asyncio import AsyncIOScheduler

    scheduler = AsyncIOScheduler(timezone="Asia/Karachi")
    for job_def in SCHEDULED_JOBS:
        scheduler.add_job(
            id=job_def["id"],
            func=job_def["func"],
            trigger=job_def["trigger"],
            **{k: v for k, v in job_def.items() if k not in ("id", "func", "trigger")},
        )
    scheduler.start()
    return scheduler
