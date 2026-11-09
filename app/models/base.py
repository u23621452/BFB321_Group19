from datetime import datetime, timezone

from app.extensions import db


def now_utc():
    return datetime.now(timezone.utc)


class AuditMixin:
    """Adds created_at and updated_at to any table that uses it."""
    created_at = db.Column(db.DateTime, default=now_utc, nullable=False)
    updated_at = db.Column(db.DateTime, default=now_utc,
                           onupdate=now_utc, nullable=False)