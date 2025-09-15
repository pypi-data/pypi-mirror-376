import sys
import types

import pytest

from holobit_sdk.cloud import AWSBackend, AzureBackend, CredentialsProvider


class DummyAWSProvider(CredentialsProvider):
    def get_credentials(self):
        return {
            "AWS_ACCESS_KEY_ID": "id",
            "AWS_SECRET_ACCESS_KEY": "secret",
        }


class DummyAzureProvider(CredentialsProvider):
    def get_credentials(self):
        return {
            "AZURE_CLIENT_ID": "cid",
            "AZURE_TENANT_ID": "tid",
            "AZURE_CLIENT_SECRET": "sec",
            "AZURE_SUBSCRIPTION_ID": "sub",
        }


def test_aws_backend_uses_provider(monkeypatch):
    monkeypatch.delenv("AWS_ACCESS_KEY_ID", raising=False)
    monkeypatch.delenv("AWS_SECRET_ACCESS_KEY", raising=False)

    captured = {}

    class DummySession:
        def __init__(self, aws_access_key_id, aws_secret_access_key):
            captured["id"] = aws_access_key_id
            captured["secret"] = aws_secret_access_key

        def client(self, name):
            return "client"

    dummy_boto3 = types.SimpleNamespace(session=types.SimpleNamespace(Session=DummySession))
    monkeypatch.setitem(sys.modules, "boto3", dummy_boto3)

    backend = AWSBackend(provider=DummyAWSProvider())
    assert backend.client == "client"
    assert captured == {"id": "id", "secret": "secret"}


def test_aws_backend_provider_error(monkeypatch, caplog):
    class FailingProvider:
        def get_credentials(self):
            raise RuntimeError("fallo")

    monkeypatch.setitem(sys.modules, "boto3", types.SimpleNamespace(session=types.SimpleNamespace(Session=lambda **k: types.SimpleNamespace(client=lambda name: None))))
    caplog.set_level("ERROR")
    with pytest.raises(EnvironmentError):
        AWSBackend(provider=FailingProvider())
    assert "Error obteniendo credenciales de AWS" in caplog.text


def test_azure_backend_uses_provider(monkeypatch):
    monkeypatch.delenv("AZURE_CLIENT_ID", raising=False)
    monkeypatch.delenv("AZURE_TENANT_ID", raising=False)
    monkeypatch.delenv("AZURE_CLIENT_SECRET", raising=False)
    monkeypatch.delenv("AZURE_SUBSCRIPTION_ID", raising=False)

    captured = {}

    class DummyCredential:
        def __init__(self, tenant_id, client_id, client_secret):
            captured.update({"tid": tenant_id, "cid": client_id, "sec": client_secret})

    class DummyBatchClient:
        def __init__(self, credential, subscription):
            captured["sub"] = subscription

        def client(self, name):
            return "client"

    monkeypatch.setitem(
        sys.modules,
        "azure.identity",
        types.SimpleNamespace(ClientSecretCredential=DummyCredential),
    )
    monkeypatch.setitem(
        sys.modules,
        "azure.mgmt.batch",
        types.SimpleNamespace(BatchManagementClient=DummyBatchClient),
    )

    backend = AzureBackend(provider=DummyAzureProvider())
    assert captured == {"tid": "tid", "cid": "cid", "sec": "sec", "sub": "sub"}


def test_azure_backend_provider_error(monkeypatch, caplog):
    class FailingProvider:
        def get_credentials(self):
            raise RuntimeError("sin servicio")

    monkeypatch.setitem(
        sys.modules,
        "azure.identity",
        types.SimpleNamespace(ClientSecretCredential=lambda *a, **k: None),
    )
    monkeypatch.setitem(
        sys.modules,
        "azure.mgmt.batch",
        types.SimpleNamespace(BatchManagementClient=lambda *a, **k: None),
    )
    caplog.set_level("ERROR")
    with pytest.raises(EnvironmentError):
        AzureBackend(provider=FailingProvider())
    assert "Error obteniendo credenciales de Azure" in caplog.text
