import importlib.util
from pathlib import Path

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
    module.backend = types.SimpleNamespace(
        submit_job=lambda _data: "job", execute_job=lambda _id: "ok"
    )
    return module, user, password


def test_compile_rejects_invalid_characters(monkeypatch):
    service, user, password = _load_service(monkeypatch)
    client = TestClient(service.app)
    bad_code = "print(1)\x00"
    resp = client.post("/compile", json={"code": bad_code}, auth=(user, password))
    assert resp.status_code == 400
    assert resp.json()["detail"] == "El campo 'code' contiene caracteres inválidos"


def test_execute_rejects_invalid_characters(monkeypatch):
    service, user, password = _load_service(monkeypatch)
    client = TestClient(service.app)
    resp = client.post("/execute", json={"job_id": "abc\x00"}, auth=(user, password))
    assert resp.status_code == 400
    assert resp.json()["detail"] == "El campo 'job_id' contiene caracteres inválidos"

