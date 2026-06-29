"""Notification templates for P19. Each template returns (title, body, url)."""

NOTIFICATION_TEMPLATES = {
    "bill_due_3_days": {
        "title": "Bill due in 3 days",
        "body": "Your {provider} bill of Rs. {amount} is due on {due_date}.",
        "url": "/bills",
    },
    "bill_due_today": {
        "title": "Bill due today!",
        "body": "Your {provider} bill is due today. Amount: Rs. {amount}",
        "url": "/bills",
    },
    "scheduled_outage_15_min": {
        "title": "Outage in 15 minutes",
        "body": "{feeder_name} scheduled outage: {start_time} to {end_time}.",
        "url": "/outages",
    },
    "slab_boundary": {
        "title": "Approaching higher slab",
        "body": "You've used {units} units. Next {remaining} units will be at Rs. {rate}/unit.",
        "url": "/consumption",
    },
    "budget_80_percent": {
        "title": "Budget warning",
        "body": "You've spent {percent}% of your {category} budget this month.",
        "url": "/budget",
    },
    "budget_exceeded": {
        "title": "Budget exceeded!",
        "body": "Your {category} spending has exceeded the monthly limit.",
        "url": "/budget",
    },
    "nearby_outage_verified": {
        "title": "Outage reported nearby",
        "body": "{count} users report {utility} issue in {area}.",
        "url": "/outages",
    },
    "solar_underperformance": {
        "title": "Solar production low",
        "body": "Your system produced {percent}% less than expected today.",
        "url": "/solar",
    },
    "reading_reminder": {
        "title": "Time to submit reading",
        "body": "Submit your {utility} meter reading for accurate bill projection.",
        "url": "/consumption",
    },
    "complaint_followup": {
        "title": "Complaint update",
        "body": "Your {provider} complaint filed on {date} has status: {status}.",
        "url": "/complaints",
    },
}


def mask_ref_number(ref: str) -> str:
    """Mask all but last 4 digits of a reference number."""
    cleaned = ref.replace("-", "").replace(" ", "")
    if len(cleaned) <= 4:
        return cleaned
    return "X" * (len(cleaned) - 4) + cleaned[-4:]


def render_template(category_code: str, **kwargs) -> dict:
    """Render a notification template with the given context variables.

    ``category_code`` is the template key (e.g. ``"budget_80_percent"``).
    Use ``category`` in ``**kwargs`` when the template body refers to a
    plain‑language category name (e.g. ``"Electricity"``).
    """
    template = NOTIFICATION_TEMPLATES.get(category_code)
    if not template:
        raise ValueError(f"Unknown notification category: {category_code}")
    return {
        "title": template["title"].format(**kwargs),
        "body": template["body"].format(**kwargs),
        "url": template["url"],
    }
