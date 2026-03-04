def test_login(client):
    res = client.post("/api/auth/login", json={"email": "admin@test.com", "password": "123456"})
    assert res.status_code == 200
    assert "access_token" in res.get_json()


def test_open_run_and_start_segment(client, auth_header):
    run = client.post("/api/runs/open", headers=auth_header, json={"machine_id": 1, "shift_id": 1, "op_code": "OP-1"})
    assert run.status_code == 200
    seg = client.post(
        "/api/segments/start",
        headers=auth_header,
        json={"run_id": run.get_json()["id"], "product_id": 1},
    )
    assert seg.status_code == 201


def test_downtime_updates_machine_state(client, auth_header):
    run = client.post(
        "/api/runs/open",
        headers=auth_header,
        json={"machine_id": 1, "shift_id": 1, "op_code": "OP-2"},
    ).get_json()
    client.post("/api/segments/start", headers=auth_header, json={"run_id": run["id"], "product_id": 1})
    start = client.post("/api/downtime/start", headers=auth_header, json={"run_id": run["id"], "reason_id": 1})
    assert start.status_code == 201
    stop = client.post("/api/downtime/stop", headers=auth_header, json={"run_id": run["id"]})
    assert stop.status_code == 200
    state = client.get("/api/status/machines/1", headers=auth_header).get_json()
    assert state["state"]["status"] == "IDLE"
