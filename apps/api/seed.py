import os
from datetime import date, datetime, time, timedelta
from random import Random

from app import create_app, db
from app.models import (
    DowntimeEvent,
    DowntimeReason,
    Line,
    Machine,
    MachineState,
    MachineStatus,
    Product,
    ProductionOrder,
    ProductionRun,
    Role,
    RunSegment,
    Shift,
    StopCategory,
    User,
)

app = create_app()


def get_or_create(model, defaults=None, **lookup):
    instance = model.query.filter_by(**lookup).first()
    created = False
    if not instance:
        params = {**lookup, **(defaults or {})}
        instance = model(**params)
        db.session.add(instance)
        db.session.flush()
        created = True
    return instance, created


def build_demo_days(today: date) -> list[date]:
    days: list[date] = []
    cursor = today
    while cursor.month == today.month and len(days) < 5:
        days.append(cursor)
        cursor = cursor - timedelta(days=1)
    if len(days) < 3:
        for day_number in range(1, 4):
            days.append(date(today.year, today.month, day_number))
    unique_days = sorted(set(days), reverse=True)
    return unique_days[:5]


with app.app_context():
    db.create_all()

    stats = {
        "created": 0,
        "updated": 0,
        "unchanged": 0,
    }

    shifts = [
        {"name": "Diurno", "start_time": time(7, 30), "end_time": time(17, 45), "crosses_midnight": False},
        {"name": "Noturno", "start_time": time(18, 0), "end_time": time(4, 0), "crosses_midnight": True},
    ]
    for shift_payload in shifts:
        shift, created = get_or_create(Shift, defaults=shift_payload, name=shift_payload["name"])
        if created:
            for key, value in shift_payload.items():
                setattr(shift, key, value)
            stats["created"] += 1
        else:
            changed = False
            for key, value in shift_payload.items():
                if getattr(shift, key) != value:
                    setattr(shift, key, value)
                    changed = True
            stats["updated" if changed else "unchanged"] += 1

    reasons = [
        ("Pausa", StopCategory.PLANNED, MachineStatus.PLANNED_STOP),
        ("Almoço", StopCategory.PLANNED, MachineStatus.PLANNED_STOP),
        ("Reunião", StopCategory.PLANNED, MachineStatus.PLANNED_STOP),
        ("Setup", StopCategory.UNPLANNED, MachineStatus.SETUP),
        ("Troca bobina", StopCategory.UNPLANNED, MachineStatus.UNPLANNED_STOP),
        ("Papel empaste", StopCategory.UNPLANNED, MachineStatus.UNPLANNED_STOP),
        ("Aguardando massa", StopCategory.UNPLANNED, MachineStatus.UNPLANNED_STOP),
        ("Falta material", StopCategory.UNPLANNED, MachineStatus.UNPLANNED_STOP),
    ]
    for name, category, mapped_status in reasons:
        reason, created = get_or_create(
            DowntimeReason,
            defaults={"category": category, "mapped_status": mapped_status},
            name=name,
        )
        if created:
            reason.category = category
            reason.mapped_status = mapped_status
            stats["created"] += 1
        elif reason.category != category or reason.mapped_status != mapped_status:
            reason.category = category
            reason.mapped_status = mapped_status
            stats["updated"] += 1
        else:
            stats["unchanged"] += 1

    admin_email = os.getenv("ADMIN_EMAIL", "admin@example.com")
    admin_password = os.getenv("ADMIN_PASSWORD", "admin123")
    admin = User.query.filter_by(email=admin_email).first()
    if not admin:
        admin = User(name="Admin", email=admin_email, role=Role.ADMIN)
        admin.set_password(admin_password)
        db.session.add(admin)
        db.session.flush()
        stats["created"] += 1
    else:
        if admin.role != Role.ADMIN:
            admin.role = Role.ADMIN
            stats["updated"] += 1
        else:
            stats["unchanged"] += 1

    line, created = get_or_create(Line, name="Linha 1", defaults={"is_active": True})
    stats["created" if created else "unchanged"] += 1

    machine, created = get_or_create(
        Machine,
        name="Extrusora 01",
        defaults={"line_id": line.id, "is_active": True},
    )
    if created:
        stats["created"] += 1
    elif machine.line_id != line.id:
        machine.line_id = line.id
        stats["updated"] += 1
    else:
        stats["unchanged"] += 1

    product_payloads = [
        {"sku": "PLA-A", "name": "Placa A", "plates_per_min": 58},
        {"sku": "PLA-B", "name": "Placa B", "plates_per_min": 65},
    ]
    products = []
    for payload in product_payloads:
        product, created = get_or_create(Product, sku=payload["sku"], defaults=payload)
        if created:
            stats["created"] += 1
        else:
            changed = False
            for key, value in payload.items():
                if getattr(product, key) != value:
                    setattr(product, key, value)
                    changed = True
            stats["updated" if changed else "unchanged"] += 1
        products.append(product)

    op, created = get_or_create(
        ProductionOrder,
        op_code="OP-DEMO",
        defaults={"description": "OP de demonstração"},
    )
    stats["created" if created else "unchanged"] += 1

    day_shift = Shift.query.filter_by(name="Diurno").first()
    setup_reason = DowntimeReason.query.filter_by(name="Setup").first()

    for run_day in build_demo_days(date.today()):
        run_start = datetime.combine(run_day, time(7, 30))
        run_end = datetime.combine(run_day, time(17, 45))
        run, created = get_or_create(
            ProductionRun,
            run_date=run_day,
            shift_id=day_shift.id,
            machine_id=machine.id,
            defaults={
                "op_id": op.id,
                "start_at": run_start,
                "end_at": run_end,
                "created_by": admin.id,
                "closed_at": run_end,
                "closed_by": admin.id,
            },
        )
        if created:
            stats["created"] += 1
        else:
            stats["unchanged"] += 1

        if not RunSegment.query.filter_by(run_id=run.id).first():
            rng = Random(int(run_day.strftime("%Y%m%d")))
            p1, p2 = products[0], products[1]
            seg1_total = rng.randint(1000, 1700)
            seg2_total = rng.randint(900, 1400)
            seg1 = RunSegment(
                run_id=run.id,
                product_id=p1.id,
                start_at=run_start,
                end_at=run_start + timedelta(hours=4),
                rate_plates_per_min_snapshot=p1.plates_per_min,
                ideal_cycle_time_sec_snapshot=60 / p1.plates_per_min,
                total_plates=seg1_total,
                good_plates=int(seg1_total * rng.uniform(0.90, 0.97)),
                scrap_plates=max(0, seg1_total - int(seg1_total * rng.uniform(0.90, 0.97))),
                loss_kg=round(rng.uniform(10, 35), 2),
            )
            seg2 = RunSegment(
                run_id=run.id,
                product_id=p2.id,
                start_at=run_start + timedelta(hours=4, minutes=20),
                end_at=run_end,
                rate_plates_per_min_snapshot=p2.plates_per_min,
                ideal_cycle_time_sec_snapshot=60 / p2.plates_per_min,
                total_plates=seg2_total,
                good_plates=int(seg2_total * rng.uniform(0.91, 0.98)),
                scrap_plates=max(0, seg2_total - int(seg2_total * rng.uniform(0.91, 0.98))),
                loss_kg=round(rng.uniform(8, 30), 2),
            )
            db.session.add_all([seg1, seg2])
            stats["created"] += 2
        else:
            stats["unchanged"] += 1

        if not DowntimeEvent.query.filter_by(run_id=run.id).first():
            downtime = DowntimeEvent(
                run_id=run.id,
                reason_id=setup_reason.id,
                start_at=run_start + timedelta(hours=4),
                end_at=run_start + timedelta(hours=4, minutes=20),
                created_by=admin.id,
                notes="Parada de setup demo",
            )
            db.session.add(downtime)
            stats["created"] += 1
        else:
            stats["unchanged"] += 1

    machine_state, created = get_or_create(
        MachineState,
        machine_id=machine.id,
        defaults={"status": MachineStatus.IDLE, "since_at": datetime.utcnow()},
    )
    if created:
        stats["created"] += 1
    elif machine_state.status != MachineStatus.IDLE:
        machine_state.status = MachineStatus.IDLE
        stats["updated"] += 1
    else:
        stats["unchanged"] += 1

    db.session.commit()
    print("Seed concluído | " f"created={stats['created']} updated={stats['updated']} unchanged={stats['unchanged']}")
