import importlib.util
from pathlib import Path

import bcrypt
import pytest
from fastapi import HTTPException
from fastapi.security import HTTPBasicCredentials

SERVICE_FILE = Path(__file__).resolve().parents[1] / "holobit_sdk" / "api" / "service.py"


def _load_service():
    spec = importlib.util.spec_from_file_location("service", SERVICE_FILE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)  # type: ignore[attr-defined]
    return module


def test_service_requires_credentials(monkeypatch):
    monkeypatch.delenv("HOLOBIT_USER", raising=False)
    monkeypatch.delenv("HOLOBIT_PASSWORD_HASH", raising=False)
    spec = importlib.util.spec_from_file_location("service", SERVICE_FILE)
    module = importlib.util.module_from_spec(spec)
    with pytest.raises(RuntimeError):
        spec.loader.exec_module(module)  # type: ignore[attr-defined]


def test_password_hash_verification(monkeypatch):
    password = "secreto"
    user = "usuario"
    hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    monkeypatch.setenv("HOLOBIT_USER", user)
    monkeypatch.setenv("HOLOBIT_PASSWORD_HASH", hashed)
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "x")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "y")
    import types, sys
    dummy = types.SimpleNamespace(
        session=types.SimpleNamespace(
            Session=lambda *a, **k: types.SimpleNamespace(client=lambda *a, **k: types.SimpleNamespace())
        )
    )
    monkeypatch.setitem(sys.modules, "boto3", dummy)
    service = _load_service()

    creds = HTTPBasicCredentials(username=user, password=password)
    assert service._authenticate(creds) == user

    wrong = HTTPBasicCredentials(username=user, password="otra")
    with pytest.raises(HTTPException):
        service._authenticate(wrong)
