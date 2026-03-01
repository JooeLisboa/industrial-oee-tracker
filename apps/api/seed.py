import os
from datetime import time
from app import create_app, db
from app.models import User, Role, Shift, DowntimeReason, StopCategory, MachineStatus

app = create_app()

with app.app_context():
    db.create_all()

    if not Shift.query.first():
        db.session.add(Shift(name='Diurno', start_time=time(7, 30), end_time=time(17, 45), crosses_midnight=False))
        db.session.add(Shift(name='Noturno', start_time=time(18, 0), end_time=time(4, 0), crosses_midnight=True))

    defaults = [
        ('Pausa', StopCategory.PLANNED, MachineStatus.PLANNED_STOP),
        ('Almoço', StopCategory.PLANNED, MachineStatus.PLANNED_STOP),
        ('Reunião', StopCategory.PLANNED, MachineStatus.PLANNED_STOP),
        ('Setup', StopCategory.UNPLANNED, MachineStatus.SETUP),
        ('Troca bobina', StopCategory.UNPLANNED, MachineStatus.UNPLANNED_STOP),
        ('Papel empaste', StopCategory.UNPLANNED, MachineStatus.UNPLANNED_STOP),
        ('Aguardando massa', StopCategory.UNPLANNED, MachineStatus.UNPLANNED_STOP),
        ('Falta material', StopCategory.UNPLANNED, MachineStatus.UNPLANNED_STOP),
    ]
    for name, cat, status in defaults:
        if not DowntimeReason.query.filter_by(name=name).first():
            db.session.add(DowntimeReason(name=name, category=cat, mapped_status=status))

    admin = User.query.filter_by(email=os.getenv('ADMIN_EMAIL', 'admin@example.com')).first()
    if not admin:
        admin = User(name='Admin', email=os.getenv('ADMIN_EMAIL', 'admin@example.com'), role=Role.ADMIN)
        admin.set_password(os.getenv('ADMIN_PASSWORD', 'admin123'))
        db.session.add(admin)

    db.session.commit()
    print('Seed concluído')
