from app.extensions import db
from app.models.base import AuditMixin


class StockMovement(AuditMixin, db.Model):
    """The ledger. Every pick writes one row here."""
    __tablename__ = "stock_movements"

    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey("products.id"), nullable=False)
    job_id = db.Column(db.Integer, db.ForeignKey("jobs.id"))
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    qty = db.Column(db.Integer, nullable=False)   # negative = stock taken out
    kind = db.Column(db.String(10), nullable=False, default="pick")

    product = db.relationship("Product")

    __table_args__ = (
        db.Index("ix_movements_product_time", "product_id", "created_at"),
    )


class MaterialRequest(AuditMixin, db.Model):
    """An operator asking the storeroom for extra material."""
    __tablename__ = "material_requests"

    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey("products.id"), nullable=False)
    qty = db.Column(db.Integer, nullable=False)
    note = db.Column(db.String(120))
    status = db.Column(db.String(10), nullable=False, default="open")
    requested_by = db.Column(db.Integer, db.ForeignKey("users.id"))

    product = db.relationship("Product")