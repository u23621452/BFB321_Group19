from app.extensions import db
from app.models.base import AuditMixin

JOB_STATUSES = ("reserved", "shortage", "kitting", "issued")


class Job(AuditMixin, db.Model):
    __tablename__ = "jobs"

    id = db.Column(db.Integer, primary_key=True)
    job_number = db.Column(db.String(20), unique=True, nullable=False)
    customer = db.Column(db.String(80), nullable=False)
    description = db.Column(db.String(100), nullable=False)
    start_date = db.Column(db.Date, nullable=False)
    priority = db.Column(db.String(10), nullable=False, default="Normal")
    status = db.Column(db.String(10), nullable=False, default="reserved")
    created_by = db.Column(db.Integer, db.ForeignKey("users.id"))

    lines = db.relationship("JobLine", back_populates="job",
                            cascade="all, delete-orphan")

    # the storeroom queue filters by status and start date a lot
    __table_args__ = (
        db.Index("ix_jobs_status_start", "status", "start_date"),
    )


class JobLine(AuditMixin, db.Model):
    """One row of a job's Bill of Materials."""
    __tablename__ = "job_lines"

    id = db.Column(db.Integer, primary_key=True)
    job_id = db.Column(db.Integer, db.ForeignKey("jobs.id"), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey("products.id"), nullable=False)
    qty = db.Column(db.Integer, nullable=False)
    picked_qty = db.Column(db.Integer, nullable=False, default=0)

    job = db.relationship("Job", back_populates="lines")
    product = db.relationship("Product")

    __table_args__ = (
        db.UniqueConstraint("job_id", "product_id", name="uq_job_product"),
        db.CheckConstraint("qty > 0", name="ck_job_lines_qty"),
    )