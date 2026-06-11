from types import SimpleNamespace


def _restart_blocker_snapshot(active_streams=0, active_runs=0):
    return {
        "active_streams": active_streams,
        "active_runs": active_runs,
        "blocking_stream_ids": ["stream-1"] if active_streams else [],
        "blocking_run_ids": ["run-1"] if active_runs else [],
        "restart_blocked": bool(active_streams or active_runs),
    }


def test_restart_endpoint_returns_status_and_schedules_restart(monkeypatch):
    import api.routes as routes

    calls = []
    responses = []

    monkeypatch.setattr(
        routes,
        "j",
        lambda handler, payload, status=200, **_: responses.append((status, payload)) or True,
    )
    monkeypatch.setattr(
        routes,
        "_check_csrf",
        lambda handler: True,
    )
    monkeypatch.setattr("api.updates._restart_blocker_snapshot", lambda: _restart_blocker_snapshot())

    def fake_schedule_restart(delay=2.0):
        calls.append(delay)

    monkeypatch.setattr(routes, "_schedule_server_restart", fake_schedule_restart, raising=False)

    handler = SimpleNamespace(headers={}, client_address=("127.0.0.1", 12345), command="POST", path="/api/restart")
    handled = routes.handle_post(handler, SimpleNamespace(path="/api/restart", query=""))

    assert handled is True
    assert calls == [0.3]
    assert responses == [(200, {"status": "restarting"})]


def test_restart_endpoint_blocks_when_chat_stream_is_active(monkeypatch):
    import api.routes as routes

    calls = []
    responses = []

    monkeypatch.setattr(
        routes,
        "j",
        lambda handler, payload, status=200, **_: responses.append((status, payload)) or True,
    )
    monkeypatch.setattr(
        routes,
        "_check_csrf",
        lambda handler: True,
    )
    monkeypatch.setattr("api.updates._restart_blocker_snapshot", lambda: _restart_blocker_snapshot(active_streams=2))
    monkeypatch.setattr(routes, "_schedule_server_restart", lambda delay=2.0: calls.append(delay))

    handler = SimpleNamespace(headers={}, client_address=("127.0.0.1", 12345), command="POST", path="/api/restart")
    handled = routes.handle_post(handler, SimpleNamespace(path="/api/restart", query=""))

    assert handled is True
    assert calls == []
    assert responses[0][0] == 409
    assert responses[0][1]["restart_blocked"] is True
    assert responses[0][1]["active_streams"] == 2


def test_restart_endpoint_blocks_when_agent_run_is_active(monkeypatch):
    import api.routes as routes

    calls = []
    responses = []

    monkeypatch.setattr(
        routes,
        "j",
        lambda handler, payload, status=200, **_: responses.append((status, payload)) or True,
    )
    monkeypatch.setattr(
        routes,
        "_check_csrf",
        lambda handler: True,
    )
    monkeypatch.setattr("api.updates._restart_blocker_snapshot", lambda: _restart_blocker_snapshot(active_runs=1))
    monkeypatch.setattr(routes, "_schedule_server_restart", lambda delay=2.0: calls.append(delay))

    handler = SimpleNamespace(headers={}, client_address=("127.0.0.1", 12345), command="POST", path="/api/restart")
    handled = routes.handle_post(handler, SimpleNamespace(path="/api/restart", query=""))

    assert handled is True
    assert calls == []
    assert responses[0][0] == 409
    assert responses[0][1]["restart_blocked"] is True
    assert responses[0][1]["active_runs"] == 1
