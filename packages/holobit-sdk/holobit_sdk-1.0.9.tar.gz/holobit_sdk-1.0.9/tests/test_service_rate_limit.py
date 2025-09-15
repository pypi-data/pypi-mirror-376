import importlib.util
from pathlib import Path
import time

import bcrypt
from fastapi.testclient import TestClient

SERVICE_FILE = Path(__file__).resolve().parents[1] / "holobit_sdk" / "api" / "service.py"


def _load_service(monkeypatch):
    password = "secret"
    user = "user"
    hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    monkeypatch.setenv("HOLOBIT_USER", user)
    monkeypatch.setenv("HOLOBIT_PASSWORD_HASH", hashed)
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "x")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "y")

    import sys, types

    dummy = types.SimpleNamespace(
        session=types.SimpleNamespace(
            Session=lambda *a, **k: types.SimpleNamespace(
                client=lambda *a, **k: types.SimpleNamespace()
            )
        )
    )
    monkeypatch.setitem(sys.modules, "boto3", dummy)

    spec = importlib.util.spec_from_file_location("service", SERVICE_FILE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)  # type: ignore[attr-defined]
    module.backend = types.SimpleNamespace(submit_job=lambda _data: "ok")
    return module, user, password


def test_rate_limit_blocks_after_failures(monkeypatch):
    service, user, password = _load_service(monkeypatch)
    client = TestClient(service.app)
    wrong = (user, "bad")
    for _ in range(service._MAX_ATTEMPTS - 1):
        resp = client.post("/compile", json={"code": "1"}, auth=wrong)
        assert resp.status_code == 401
    resp = client.post("/compile", json={"code": "1"}, auth=wrong)
    assert resp.status_code == 429
    resp = client.post("/compile", json={"code": "1"}, auth=(user, password))
    assert resp.status_code == 429
    future = time.time() + service._LOCK_SECONDS + 1
    monkeypatch.setattr(service.time, "time", lambda: future)
    resp = client.post("/compile", json={"code": "1"}, auth=(user, password))
    assert resp.status_code == 200


def test_rate_limit_respects_env_config(monkeypatch):
    monkeypatch.setenv("HOLOBIT_MAX_AUTH_ATTEMPTS", "1")
    monkeypatch.setenv("HOLOBIT_LOCK_SECONDS", "1")
    service, user, password = _load_service(monkeypatch)
    client = TestClient(service.app)
    wrong = (user, "bad")
    resp = client.post("/compile", json={"code": "1"}, auth=wrong)
    assert resp.status_code == 429
