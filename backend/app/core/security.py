from datetime import date, datetime

from cryptography.fernet import Fernet, InvalidToken

from app.core.config import settings


def encrypt(text: str) -> str:
    key = settings.encryption_key
    if not key:
        return text
    try:
        f = Fernet(key.encode() if isinstance(key, str) else key)
        return f.encrypt(text.encode()).decode()
    except Exception:
        return text


def decrypt(text: str) -> str:
    key = settings.encryption_key
    if not key:
        return text
    try:
        f = Fernet(key.encode() if isinstance(key, str) else key)
        return f.decrypt(text.encode()).decode()
    except (InvalidToken, Exception):
        return text


def parse_billing_month(issue_date_str: str | None, due_date_str: str | None = None) -> str:
    target = issue_date_str or due_date_str
    if not target:
        return date.today().replace(day=1).isoformat()
    for fmt in ("%d %b %y", "%d-%m-%Y", "%Y-%m-%d", "%d/%m/%Y"):
        try:
            d = datetime.strptime(target, fmt).date()
            return d.replace(day=1).isoformat()
        except ValueError:
            continue
    return date.today().replace(day=1).isoformat()
