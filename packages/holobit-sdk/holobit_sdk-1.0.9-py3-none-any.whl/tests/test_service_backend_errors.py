import importlib.util
from pathlib import Path

import bcrypt
import pytest
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
    return module, user, password


class FailingBackend:
    def __init__(self, *, submit=False, execute=False):
        self._submit = submit
        self._execute = execute

    def submit_job(self, *_args, **_kwargs):  # pragma: no cover - simple
        if self._submit:
            raise RuntimeError("fail submit")
        return "job"

    def execute_job(self, *_args, **_kwargs):  # pragma: no cover - simple
        if self._execute:
            raise RuntimeError("fail exec")
        return "ok"


def test_compile_handles_backend_errors(monkeypatch):
    service, user, password = _load_service(monkeypatch)
    service.backend = FailingBackend(submit=True)
    client = TestClient(service.app)
    resp = client.post("/compile", json={"code": "print(1)"}, auth=(user, password))
    assert resp.status_code == 502
    assert resp.json()["detail"] == "Error en el backend"


def test_execute_handles_backend_errors(monkeypatch):
    service, user, password = _load_service(monkeypatch)
    service.backend = FailingBackend(execute=True)
    client = TestClient(service.app)
    resp = client.post("/execute", json={"job_id": "abc"}, auth=(user, password))
    assert resp.status_code == 502
    assert resp.json()["detail"] == "Error en el backend"


def test_execute_validates_job_id_type(monkeypatch):
    service, user, password = _load_service(monkeypatch)
    service.backend = FailingBackend()
    client = TestClient(service.app)
    resp = client.post("/execute", json={"job_id": 123}, auth=(user, password))
    assert resp.status_code == 400
    assert resp.json()["detail"] == "El campo 'job_id' debe ser una cadena"
