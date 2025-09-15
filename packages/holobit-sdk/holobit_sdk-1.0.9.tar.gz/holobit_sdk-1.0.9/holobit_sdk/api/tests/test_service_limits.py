import importlib.util
import types
from pathlib import Path

import bcrypt
from fastapi.testclient import TestClient


SERVICE_FILE = Path(__file__).resolve().parents[1] / "service.py"


def _load_service(monkeypatch):
    password = "secret"
    user = "user"
    hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    monkeypatch.setenv("HOLOBIT_USER", user)
    monkeypatch.setenv("HOLOBIT_PASSWORD_HASH", hashed)
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "x")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "y")

    import sys

    dummy = types.SimpleNamespace(
        session=types.SimpleNamespace(
            Session=lambda *a, **k: types.SimpleNamespace(
                client=lambda *a, **k: types.SimpleNamespace()
            )
        )
    )
    monkeypatch.setitem(sys.modules, "boto3", dummy)

    spec = importlib.util.spec_from_file_location("service", SERVICE_FILE)
    service = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(service)  # type: ignore[attr-defined]
    service.backend = types.SimpleNamespace(
        submit_job=lambda _data: "job", execute_job=lambda _id: "ok"
    )
    return service, user, password


def test_compile_rejects_oversized_code(monkeypatch):
    service, user, password = _load_service(monkeypatch)
    client = TestClient(service.app)
    long_code = "x" * 10_001
    resp = client.post("/compile", json={"code": long_code}, auth=(user, password))
    assert resp.status_code == 413
    assert resp.json()["detail"] == "El campo 'code' excede el tamaño máximo"


def test_execute_rejects_oversized_job_id(monkeypatch):
    service, user, password = _load_service(monkeypatch)
    client = TestClient(service.app)
    long_id = "a" * 257
    resp = client.post("/execute", json={"job_id": long_id}, auth=(user, password))
    assert resp.status_code == 413
    assert resp.json()["detail"] == "El campo 'job_id' excede el tamaño máximo"

