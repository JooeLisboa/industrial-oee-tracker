from datetime import date, datetime, time, timedelta
from enum import Enum

from sqlalchemy import Enum as SAEnum
from sqlalchemy import UniqueConstraint
from werkzeug.security import check_password_hash, generate_password_hash

from app import db


class Role(str, Enum):
    ADMIN = "ADMIN"
    LEADER = "LEADER"
    VIEWER = "VIEWER"


class StopCategory(str, Enum):
    PLANNED = "PLANNED"
    UNPLANNED = "UNPLANNED"


class MachineStatus(str, Enum):
    IDLE = "IDLE"
    RUNNING = "RUNNING"
    MAINTENANCE = "MAINTENANCE"
    PLANNED_STOP = "PLANNED_STOP"
    UNPLANNED_STOP = "UNPLANNED_STOP"
    SETUP = "SETUP"


class PlanStatus(str, Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    DONE = "DONE"
    SKIPPED = "SKIPPED"


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(SAEnum(Role), nullable=False, default=Role.LEADER)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Line(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)


class Machine(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    line_id = db.Column(db.Integer, db.ForeignKey("line.id"), nullable=False)
    name = db.Column(db.String(80), nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)


class Shift(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=False)
    crosses_midnight = db.Column(db.Boolean, default=False, nullable=False)


class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    sku = db.Column(db.String(120), nullable=False)
    plates_per_min = db.Column(db.Float, nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)


class ProductionOrder(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    op_code = db.Column(db.String(80), unique=True, nullable=False)
    description = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)


class ProductionRun(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    run_date = db.Column(db.Date, nullable=False)
    shift_id = db.Column(db.Integer, db.ForeignKey("shift.id"), nullable=False)
    machine_id = db.Column(db.Integer, db.ForeignKey("machine.id"), nullable=False)
    op_id = db.Column(db.Integer, db.ForeignKey("production_order.id"), nullable=False)
    start_at = db.Column(db.DateTime, nullable=False)
    end_at = db.Column(db.DateTime, nullable=True)
    created_by = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    closed_at = db.Column(db.DateTime, nullable=True)
    closed_by = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=True)
    __table_args__ = (UniqueConstraint("run_date", "shift_id", "machine_id", name="uq_run_shift_machine"),)


class RunSegment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    run_id = db.Column(db.Integer, db.ForeignKey("production_run.id"), nullable=False)
    plan_item_id = db.Column(db.Integer, db.ForeignKey("daily_plan_item.id"), nullable=True)
    product_id = db.Column(db.Integer, db.ForeignKey("product.id"), nullable=False)
    start_at = db.Column(db.DateTime, nullable=False)
    end_at = db.Column(db.DateTime, nullable=True)
    rate_plates_per_min_snapshot = db.Column(db.Float, nullable=False)
    ideal_cycle_time_sec_snapshot = db.Column(db.Float, nullable=False)
    total_plates = db.Column(db.Integer, default=0, nullable=False)
    good_plates = db.Column(db.Integer, default=0, nullable=False)
    scrap_plates = db.Column(db.Integer, default=0, nullable=False)
    loss_kg = db.Column(db.Float, default=0, nullable=False)


class DowntimeReason(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    category = db.Column(SAEnum(StopCategory), nullable=False)
    mapped_status = db.Column(SAEnum(MachineStatus), nullable=False)


class DowntimeEvent(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    run_id = db.Column(db.Integer, db.ForeignKey("production_run.id"), nullable=False)
    reason_id = db.Column(db.Integer, db.ForeignKey("downtime_reason.id"), nullable=False)
    start_at = db.Column(db.DateTime, nullable=False)
    end_at = db.Column(db.DateTime, nullable=True)
    created_by = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    notes = db.Column(db.String(255), nullable=True)


class MachineState(db.Model):
    machine_id = db.Column(db.Integer, db.ForeignKey("machine.id"), primary_key=True)
    status = db.Column(SAEnum(MachineStatus), nullable=False, default=MachineStatus.IDLE)
    since_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    current_run_id = db.Column(db.Integer, db.ForeignKey("production_run.id"), nullable=True)
    current_segment_id = db.Column(db.Integer, db.ForeignKey("run_segment.id"), nullable=True)
    current_downtime_id = db.Column(db.Integer, db.ForeignKey("downtime_event.id"), nullable=True)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)


class DailyPlanItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    plan_date = db.Column(db.Date, nullable=False)
    priority = db.Column(db.Integer, nullable=False, default=1)
    line_id = db.Column(db.Integer, db.ForeignKey("line.id"), nullable=True)
    machine_id = db.Column(db.Integer, db.ForeignKey("machine.id"), nullable=True)
    product_id = db.Column(db.Integer, db.ForeignKey("product.id"), nullable=False)
    planned_qty_plates = db.Column(db.Integer, nullable=False)
    status = db.Column(SAEnum(PlanStatus), nullable=False, default=PlanStatus.PENDING)
    created_by = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)


class AuditLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    entity_type = db.Column(db.String(80), nullable=False)
    entity_id = db.Column(db.Integer, nullable=False)
    action = db.Column(db.String(20), nullable=False)
    before_json = db.Column(db.JSON, nullable=True)
    after_json = db.Column(db.JSON, nullable=True)
    reason = db.Column(db.String(255), nullable=True)
    changed_by = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)


class Setting(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    company_name = db.Column(db.String(120), default="OEE Monitor")
    logo_url = db.Column(db.String(255), nullable=True)
    primary_color = db.Column(db.String(30), default="#0f172a")


def calc_shift_window(shift: Shift, ref_dt: datetime | None = None):
    now = ref_dt or datetime.utcnow()
    run_date = now.date()
    start_at = datetime.combine(run_date, shift.start_time)
    if shift.crosses_midnight:
        if now.time() < shift.end_time:
            run_date = run_date - timedelta(days=1)
            start_at = datetime.combine(run_date, shift.start_time)
        end_at = datetime.combine(run_date + timedelta(days=1), shift.end_time)
    else:
        end_at = datetime.combine(run_date, shift.end_time)
    return run_date, start_at, end_at


def serialize(model):
    data = {}
    for c in model.__table__.columns:
        value = getattr(model, c.name)
        if isinstance(value, (datetime, date, time)):
            data[c.name] = value.isoformat()
        elif isinstance(value, Enum):
            data[c.name] = value.value
        else:
            data[c.name] = value
    return data
