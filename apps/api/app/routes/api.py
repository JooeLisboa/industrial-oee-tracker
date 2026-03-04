from datetime import date, datetime, timedelta

from app import db
from app.models import (
    AuditLog,
    DailyPlanItem,
    DowntimeEvent,
    DowntimeReason,
    Line,
    Machine,
    MachineState,
    MachineStatus,
    PlanStatus,
    Product,
    ProductionOrder,
    ProductionRun,
    Role,
    RunSegment,
    Setting,
    Shift,
    User,
    calc_shift_window,
    serialize,
)
from app.services.oee import calculate_oee
from app.utils.auth import require_roles
from flask import Blueprint, request
from flask_jwt_extended import create_access_token, get_jwt_identity, jwt_required

api_bp = Blueprint("api", __name__)


def _items(payload):
    return {"items": payload}


def _now():
    return datetime.utcnow()


def _ensure_machine_state(machine_id):
    state = MachineState.query.get(machine_id)
    if not state:
        state = MachineState(machine_id=machine_id, status=MachineStatus.IDLE, since_at=_now())
        db.session.add(state)
        db.session.commit()
    return state


def _open_segment(run_id):
    return RunSegment.query.filter_by(run_id=run_id, end_at=None).first()


def _open_downtime(run_id):
    return DowntimeEvent.query.filter_by(run_id=run_id, end_at=None).first()


@api_bp.get("/health")
def api_health():
    return {"status": "ok", "service": "api"}


@api_bp.post("/auth/login")
def login():
    data = request.get_json() or {}
    user = User.query.filter_by(email=data.get("email")).first()
    if not user or not user.check_password(data.get("password", "")):
        return {"message": "Invalid credentials"}, 401
    token = create_access_token(identity=str(user.id), additional_claims={"role": user.role.value})
    return {"access_token": token, "user": serialize(user)}


@api_bp.get("/auth/me")
@jwt_required()
def me():
    user = User.query.get_or_404(int(get_jwt_identity()))
    return {"user": serialize(user)}


def register_crud(model, path, roles):
    @api_bp.get(path, endpoint=f"{model.__name__.lower()}_list")
    @require_roles(*roles)
    def list_items(model=model):
        return _items([serialize(x) for x in model.query.all()])

    @api_bp.post(path, endpoint=f"{model.__name__.lower()}_create")
    @require_roles(*roles)
    def create_item(model=model):
        item = model(**(request.get_json() or {}))
        db.session.add(item)
        db.session.commit()
        return serialize(item), 201

    @api_bp.patch(f"{path}/<int:item_id>", endpoint=f"{model.__name__.lower()}_patch")
    @require_roles(*roles)
    def patch_item(item_id, model=model):
        item = model.query.get_or_404(item_id)
        for k, v in (request.get_json() or {}).items():
            setattr(item, k, v)
        db.session.commit()
        return serialize(item)

    @api_bp.delete(f"{path}/<int:item_id>", endpoint=f"{model.__name__.lower()}_delete")
    @require_roles(*roles)
    def delete_item(item_id, model=model):
        item = model.query.get_or_404(item_id)
        db.session.delete(item)
        db.session.commit()
        return "", 204


register_crud(Line, "/lines", (Role.ADMIN,))
register_crud(Machine, "/machines", (Role.ADMIN,))
register_crud(Shift, "/shifts", (Role.ADMIN,))
register_crud(Product, "/products", (Role.ADMIN,))
register_crud(DowntimeReason, "/downtime-reasons", (Role.ADMIN,))


@api_bp.get("/daily-plan")
@require_roles(Role.ADMIN, Role.LEADER, Role.VIEWER)
def plan_list():
    day = request.args.get("date")
    q = DailyPlanItem.query
    if day:
        q = q.filter_by(plan_date=date.fromisoformat(day))
    return _items([serialize(x) for x in q.order_by(DailyPlanItem.priority.asc()).all()])


@api_bp.post("/daily-plan")
@require_roles(Role.ADMIN, Role.LEADER)
def plan_create():
    data = request.get_json() or {}
    data["created_by"] = int(get_jwt_identity())
    data["plan_date"] = date.fromisoformat(data["plan_date"])
    item = DailyPlanItem(**data)
    db.session.add(item)
    db.session.commit()
    return serialize(item), 201


@api_bp.patch("/daily-plan/<int:item_id>")
@require_roles(Role.ADMIN, Role.LEADER)
def plan_patch(item_id):
    item = DailyPlanItem.query.get_or_404(item_id)
    for k, v in (request.get_json() or {}).items():
        if k == "plan_date":
            v = date.fromisoformat(v)
        setattr(item, k, v)
    db.session.commit()
    return serialize(item)


@api_bp.patch("/daily-plan/<int:item_id>/status")
@require_roles(Role.ADMIN, Role.LEADER)
def plan_patch_status(item_id):
    item = DailyPlanItem.query.get_or_404(item_id)
    item.status = PlanStatus((request.get_json() or {}).get("status", "PENDING"))
    db.session.commit()
    return serialize(item)


@api_bp.delete("/daily-plan/<int:item_id>")
@require_roles(Role.ADMIN)
def plan_delete(item_id):
    item = DailyPlanItem.query.get_or_404(item_id)
    db.session.delete(item)
    db.session.commit()
    return "", 204


@api_bp.post("/runs/open")
@require_roles(Role.ADMIN, Role.LEADER)
def run_open():
    data = request.get_json() or {}
    uid = int(get_jwt_identity())
    machine_id, shift_id = data["machine_id"], data["shift_id"]
    shift = Shift.query.get_or_404(shift_id)
    run_date, start_at, end_at = calc_shift_window(shift)
    if data.get("run_date"):
        run_date = date.fromisoformat(data["run_date"])
        start_at = datetime.combine(run_date, shift.start_time)
        end_at = datetime.combine(
            run_date + (timedelta(days=1) if shift.crosses_midnight else timedelta()),
            shift.end_time,
        )
    run = ProductionRun.query.filter_by(run_date=run_date, shift_id=shift_id, machine_id=machine_id).first()
    if not run:
        op = ProductionOrder.query.filter_by(op_code=data["op_code"]).first()
        if not op:
            op = ProductionOrder(op_code=data["op_code"], description=data.get("description"))
            db.session.add(op)
            db.session.flush()
        run = ProductionRun(
            run_date=run_date,
            shift_id=shift_id,
            machine_id=machine_id,
            op_id=op.id,
            start_at=start_at,
            end_at=end_at,
            created_by=uid,
        )
        db.session.add(run)
        db.session.flush()
    st = _ensure_machine_state(machine_id)
    st.current_run_id = run.id
    st.status = MachineStatus.IDLE
    st.since_at = _now()
    db.session.commit()
    return serialize(run)


@api_bp.post("/segments/start")
@require_roles(Role.ADMIN, Role.LEADER)
def segment_start():
    data = request.get_json() or {}
    run = ProductionRun.query.get_or_404(data["run_id"])
    if _open_segment(run.id):
        return {"message": "Já existe segmento aberto para este run."}, 422
    if _open_downtime(run.id):
        return {"message": "Não é possível iniciar segmento com parada aberta."}, 422
    product = Product.query.get_or_404(data["product_id"])
    seg = RunSegment(
        run_id=run.id,
        product_id=product.id,
        plan_item_id=data.get("plan_item_id"),
        start_at=_now(),
        rate_plates_per_min_snapshot=product.plates_per_min,
        ideal_cycle_time_sec_snapshot=60 / product.plates_per_min,
    )
    db.session.add(seg)
    db.session.flush()
    state = _ensure_machine_state(run.machine_id)
    state.status = MachineStatus.RUNNING
    state.current_segment_id = seg.id
    state.current_run_id = run.id
    state.current_downtime_id = None
    state.since_at = _now()
    db.session.commit()
    return serialize(seg), 201


@api_bp.post("/segments/switch")
@require_roles(Role.ADMIN, Role.LEADER)
def segment_switch():
    data = request.get_json() or {}
    run = ProductionRun.query.get_or_404(data["run_id"])
    current = _open_segment(run.id)
    if not current:
        return {"message": "Não há segmento aberto para troca."}, 422
    current.end_at = _now()
    db.session.flush()
    product = Product.query.get_or_404(data["product_id"])
    new_seg = RunSegment(
        run_id=run.id,
        product_id=product.id,
        plan_item_id=data.get("plan_item_id"),
        start_at=_now(),
        rate_plates_per_min_snapshot=product.plates_per_min,
        ideal_cycle_time_sec_snapshot=60 / product.plates_per_min,
    )
    db.session.add(new_seg)
    db.session.flush()
    state = _ensure_machine_state(run.machine_id)
    state.current_segment_id = new_seg.id
    state.status = MachineStatus.RUNNING
    state.since_at = _now()
    db.session.commit()
    return serialize(new_seg), 201


@api_bp.post("/downtime/start")
@require_roles(Role.ADMIN, Role.LEADER)
def downtime_start():
    data = request.get_json() or {}
    run = ProductionRun.query.get_or_404(data["run_id"])
    if _open_downtime(run.id):
        return {"message": "Já existe parada aberta."}, 422
    seg = _open_segment(run.id)
    if seg:
        seg.end_at = _now()
    reason = DowntimeReason.query.get_or_404(data["reason_id"])
    ev = DowntimeEvent(
        run_id=run.id,
        reason_id=reason.id,
        start_at=_now(),
        created_by=int(get_jwt_identity()),
        notes=data.get("notes"),
    )
    db.session.add(ev)
    db.session.flush()
    state = _ensure_machine_state(run.machine_id)
    state.status = reason.mapped_status
    state.current_downtime_id = ev.id
    state.current_segment_id = None
    state.since_at = _now()
    db.session.commit()
    return serialize(ev), 201


@api_bp.post("/downtime/stop")
@require_roles(Role.ADMIN, Role.LEADER)
def downtime_stop():
    run = ProductionRun.query.get_or_404((request.get_json() or {})["run_id"])
    ev = _open_downtime(run.id)
    if not ev:
        return {"message": "Não há parada aberta para finalizar."}, 422
    ev.end_at = _now()
    state = _ensure_machine_state(run.machine_id)
    state.status = MachineStatus.IDLE
    state.current_downtime_id = None
    state.since_at = _now()
    db.session.commit()
    return serialize(ev)


@api_bp.post("/runs/close")
@require_roles(Role.ADMIN, Role.LEADER)
def run_close():
    run = ProductionRun.query.get_or_404((request.get_json() or {})["run_id"])
    run.closed_at = _now()
    run.closed_by = int(get_jwt_identity())
    segment = _open_segment(run.id)
    if segment:
        segment.end_at = _now()
    downtime = _open_downtime(run.id)
    if downtime:
        downtime.end_at = _now()
    state = _ensure_machine_state(run.machine_id)
    state.status = MachineStatus.IDLE
    state.current_segment_id = None
    state.current_downtime_id = None
    state.since_at = _now()
    db.session.commit()
    return serialize(run)


def _audit(entity_type, entity_id, before, after, reason):
    item = AuditLog(
        entity_type=entity_type,
        entity_id=entity_id,
        action="UPDATE",
        before_json=before,
        after_json=after,
        reason=reason,
        changed_by=int(get_jwt_identity()),
    )
    db.session.add(item)


@api_bp.patch("/segments/<int:segment_id>")
@require_roles(
    Role.ADMIN,
)
def segment_patch(segment_id):
    seg = RunSegment.query.get_or_404(segment_id)
    data = request.get_json() or {}
    reason = data.pop("reason", None)
    if not reason:
        return {"message": "reason é obrigatório"}, 422
    before = serialize(seg)
    for k, v in data.items():
        if k in ["start_at", "end_at"] and v:
            v = datetime.fromisoformat(v)
        setattr(seg, k, v)
    _audit("run_segment", seg.id, before, serialize(seg), reason)
    db.session.commit()
    return serialize(seg)


@api_bp.patch("/downtime/<int:downtime_id>")
@require_roles(
    Role.ADMIN,
)
def downtime_patch(downtime_id):
    ev = DowntimeEvent.query.get_or_404(downtime_id)
    data = request.get_json() or {}
    reason = data.pop("reason", None)
    if not reason:
        return {"message": "reason é obrigatório"}, 422
    before = serialize(ev)
    for k, v in data.items():
        if k in ["start_at", "end_at"] and v:
            v = datetime.fromisoformat(v)
        setattr(ev, k, v)
    _audit("downtime_event", ev.id, before, serialize(ev), reason)
    db.session.commit()
    return serialize(ev)


@api_bp.get("/audit")
@require_roles(
    Role.ADMIN,
)
def audit_list():
    q = AuditLog.query
    if request.args.get("entity_type"):
        q = q.filter_by(entity_type=request.args["entity_type"])
    if request.args.get("entity_id"):
        q = q.filter_by(entity_id=int(request.args["entity_id"]))
    return _items([serialize(x) for x in q.order_by(AuditLog.id.desc()).all()])


@api_bp.get("/status/overview")
@require_roles(Role.ADMIN, Role.LEADER, Role.VIEWER)
def status_overview():
    lines = []
    for line in Line.query.all():
        machines = []
        for machine in Machine.query.filter_by(line_id=line.id).all():
            state = _ensure_machine_state(machine.id)
            machines.append({"machine": serialize(machine), "state": serialize(state)})
        lines.append({"line": serialize(line), "machines": machines})
    return {"items": lines}


@api_bp.get("/status/machines/<int:machine_id>")
@require_roles(Role.ADMIN, Role.LEADER, Role.VIEWER)
def status_machine(machine_id):
    return {"state": serialize(_ensure_machine_state(machine_id))}


@api_bp.get("/reports/run/<int:run_id>/oee")
@require_roles(Role.ADMIN, Role.LEADER, Role.VIEWER)
def report_run_oee(run_id):
    return calculate_oee(run_id)


@api_bp.get("/reports/machine/<int:machine_id>")
@require_roles(Role.ADMIN, Role.LEADER, Role.VIEWER)
def report_machine(machine_id):
    from_dt = datetime.fromisoformat(request.args["from"])
    to_dt = datetime.fromisoformat(request.args["to"])
    runs = ProductionRun.query.filter(
        ProductionRun.machine_id == machine_id,
        ProductionRun.start_at >= from_dt,
        ProductionRun.start_at <= to_dt,
    ).all()
    return _items([calculate_oee(run.id) for run in runs])


@api_bp.get("/reports/monthly")
@require_roles(Role.ADMIN, Role.LEADER, Role.VIEWER)
def report_monthly():
    year = int(request.args["year"])
    month = int(request.args["month"])
    runs = ProductionRun.query.filter(
        db.extract("year", ProductionRun.run_date) == year,
        db.extract("month", ProductionRun.run_date) == month,
    ).all()
    return {"year": year, "month": month, "items": [calculate_oee(run.id) for run in runs]}


@api_bp.get("/reports/yearly")
@require_roles(Role.ADMIN, Role.LEADER, Role.VIEWER)
def report_yearly():
    year = int(request.args["year"])
    runs = ProductionRun.query.filter(db.extract("year", ProductionRun.run_date) == year).all()
    return {"year": year, "items": [calculate_oee(run.id) for run in runs]}


@api_bp.get("/public/settings")
def settings_public():
    setting = Setting.query.first() or Setting(company_name="OEE Line Monitor")
    if not setting.id:
        db.session.add(setting)
        db.session.commit()
    return serialize(setting)


@api_bp.patch("/settings")
@require_roles(
    Role.ADMIN,
)
def settings_patch():
    setting = Setting.query.first() or Setting()
    if not setting.id:
        db.session.add(setting)
    for key, value in (request.get_json() or {}).items():
        setattr(setting, key, value)
    db.session.commit()
    return serialize(setting)
