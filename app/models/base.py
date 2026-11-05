from datetime import datetime

from app.extensions import db


class AuditMixin:
    """Adds created_at and updated_at to any table that uses it."""
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow,
                           onupdate=datetime.utcnow, nullable=False)