from app.extensions import db
from app.models.base import AuditMixin


class Product(AuditMixin, db.Model):
    __tablename__ = "products"

    id = db.Column(db.Integer, primary_key=True)
    sku = db.Column(db.String(30), unique=True, nullable=False, index=True)
    description = db.Column(db.String(120), nullable=False)
    unit = db.Column(db.String(10), nullable=False, default="ea")
    bin_location = db.Column(db.String(20), nullable=False)
    on_hand = db.Column(db.Integer, nullable=False, default=0)
    unit_cost = db.Column(db.Float, nullable=False, default=0)
    lead_time_days = db.Column(db.Integer, nullable=False, default=7)
    min_order_qty = db.Column(db.Integer, nullable=False, default=1)
    pack_size = db.Column(db.Integer, nullable=False, default=1)

    # numbers the supply chain model needs (EOQ, safety stock, reorder point)
    daily_demand = db.Column(db.Float, nullable=False, default=0)
    daily_demand_std = db.Column(db.Float, nullable=False, default=0)
    annual_demand = db.Column(db.Float, nullable=False, default=0)
    order_cost = db.Column(db.Float, nullable=False, default=0)
    holding_cost = db.Column(db.Float, nullable=False, default=0)

    __table_args__ = (
        db.CheckConstraint("on_hand >= 0", name="ck_products_on_hand"),
    )