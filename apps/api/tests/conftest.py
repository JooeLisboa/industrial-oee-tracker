import pytest
from datetime import time
from app import create_app, db
from app.models import User, Role, Shift, Line, Machine, Product, DowntimeReason, StopCategory, MachineStatus


@pytest.fixture
def client():
    app = create_app({'TESTING': True, 'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:', 'JWT_SECRET_KEY': 'test'})
    with app.app_context():
        db.create_all()
        u = User(name='Admin', email='admin@test.com', role=Role.ADMIN)
        u.set_password('123456')
        db.session.add(u)
        shift = Shift(name='Diurno', start_time=time(7, 30), end_time=time(17, 45), crosses_midnight=False)
        line = Line(name='Linha 1')
        db.session.add_all([shift, line])
        db.session.flush()
        machine = Machine(name='M1', line_id=line.id)
        product = Product(name='Produto A', sku='A', plates_per_min=60)
        reason = DowntimeReason(name='Setup', category=StopCategory.UNPLANNED, mapped_status=MachineStatus.SETUP)
        db.session.add_all([machine, product, reason])
        db.session.commit()
    yield app.test_client()


@pytest.fixture
def auth_header(client):
    res = client.post('/api/auth/login', json={'email': 'admin@test.com', 'password': '123456'})
    token = res.get_json()['access_token']
    return {'Authorization': f'Bearer {token}'}
