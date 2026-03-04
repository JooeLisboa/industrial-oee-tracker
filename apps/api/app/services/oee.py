from datetime import datetime

from app.models import DowntimeEvent, DowntimeReason, ProductionRun, RunSegment, StopCategory
from sqlalchemy import func


def _duration_seconds(start, end):
    if not start:
        return 0
    final = end or datetime.utcnow()
    return max(0, int((final - start).total_seconds()))


def calculate_oee(run_id: int):
    run = ProductionRun.query.get_or_404(run_id)
    shift_duration = _duration_seconds(run.start_at, run.end_at)

    planned = (
        DowntimeEvent.query.join(DowntimeReason, DowntimeReason.id == DowntimeEvent.reason_id)
        .filter(DowntimeEvent.run_id == run_id, DowntimeReason.category == StopCategory.PLANNED)
        .all()
    )
    unplanned = (
        DowntimeEvent.query.join(DowntimeReason, DowntimeReason.id == DowntimeEvent.reason_id)
        .filter(DowntimeEvent.run_id == run_id, DowntimeReason.category == StopCategory.UNPLANNED)
        .all()
    )

    planned_sec = sum(_duration_seconds(x.start_at, x.end_at) for x in planned)
    unplanned_sec = sum(_duration_seconds(x.start_at, x.end_at) for x in unplanned)

    nppt = shift_duration - planned_sec
    operating = nppt - unplanned_sec
    availability = (operating / nppt) if nppt > 0 else 0

    segments = RunSegment.query.filter_by(run_id=run_id).all()
    total = sum(s.total_plates for s in segments)
    good = sum(s.good_plates for s in segments)
    quality = (good / total) if total > 0 else 0
    ideal_time = sum(s.total_plates * s.ideal_cycle_time_sec_snapshot for s in segments)
    performance = (ideal_time / operating) if operating > 0 else 0
    oee = availability * performance * quality

    pareto = (
        DowntimeEvent.query.join(DowntimeReason, DowntimeReason.id == DowntimeEvent.reason_id)
        .with_entities(DowntimeReason.name, func.count(DowntimeEvent.id))
        .filter(DowntimeEvent.run_id == run_id)
        .group_by(DowntimeReason.name)
        .all()
    )

    return {
        "run_id": run_id,
        "availability": availability,
        "performance": performance,
        "quality": quality,
        "oee": oee,
        "times": {
            "shift_duration_sec": shift_duration,
            "planned_downtime_sec": planned_sec,
            "unplanned_downtime_sec": unplanned_sec,
            "nppt_sec": nppt,
            "operating_time_sec": operating,
        },
        "pareto": [{"reason": p[0], "count": p[1]} for p in pareto],
    }
