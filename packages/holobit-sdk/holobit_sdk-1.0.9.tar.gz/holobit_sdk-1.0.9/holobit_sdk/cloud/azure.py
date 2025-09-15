"""Backend de Azure para ejecutar trabajos Holobit."""

from __future__ import annotations

import logging
import os
from typing import Any, Optional

from .base import BaseCloudBackend
from .credentials import CredentialsProvider


class AzureBackend(BaseCloudBackend):
    """Cliente para Azure basado en ``azure``.

    Utiliza las variables de entorno ``AZURE_CLIENT_ID``,
    ``AZURE_TENANT_ID`` y ``AZURE_CLIENT_SECRET`` para autenticarse.
    El cliente creado debe disponer de métodos ``submit_job`` y
    ``execute_job``.  En las pruebas se usan mocks de los SDK oficiales.
    """

    def __init__(self, provider: Optional[CredentialsProvider] = None) -> None:
        self.client = self._authenticate(provider)

    def _authenticate(self, provider: Optional[CredentialsProvider] = None) -> Any:
        """Autentica contra Azure usando ``azure.identity``.

        Si se proporciona ``provider`` se utilizará para obtener las
        credenciales antes de leer las variables de entorno.
        """
        from azure.identity import ClientSecretCredential
        from azure.mgmt.batch import BatchManagementClient

        logger = logging.getLogger(__name__)
        creds = {}
        if provider is not None:
            try:
                creds = provider.get_credentials()
            except Exception as exc:  # pragma: no cover - log de error
                logger.error("Error obteniendo credenciales de Azure: %s", exc)
        client_id = creds.get("AZURE_CLIENT_ID") or os.environ.get("AZURE_CLIENT_ID")
        tenant_id = creds.get("AZURE_TENANT_ID") or os.environ.get("AZURE_TENANT_ID")
        secret = creds.get("AZURE_CLIENT_SECRET") or os.environ.get(
            "AZURE_CLIENT_SECRET"
        )
        subscription = creds.get("AZURE_SUBSCRIPTION_ID") or os.environ.get(
            "AZURE_SUBSCRIPTION_ID",
            "default",
        )
        if not (client_id and tenant_id and secret):
            logger.error("Faltan credenciales de Azure")
            raise EnvironmentError("Faltan credenciales de Azure")

        credential = ClientSecretCredential(
            tenant_id=tenant_id, client_id=client_id, client_secret=secret
        )
        return BatchManagementClient(credential, subscription)

    def submit_job(self, job_data: Any) -> Any:
        """Envía un trabajo a Azure."""
        return self.client.submit_job(job_data)

    def execute_job(self, job_id: str) -> Any:
        """Ejecuta un trabajo previamente enviado."""
        return self.client.execute_job(job_id)
