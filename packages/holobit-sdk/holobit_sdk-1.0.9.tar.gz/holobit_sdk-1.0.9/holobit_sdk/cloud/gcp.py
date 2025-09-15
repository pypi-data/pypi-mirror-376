"""Backend de Google Cloud Platform para ejecutar trabajos Holobit."""

from __future__ import annotations

import os
from typing import Any

from .base import BaseCloudBackend


class GCPBackend(BaseCloudBackend):
    """Cliente para GCP basado en ``google-cloud``.

    Utiliza la variable de entorno ``GOOGLE_APPLICATION_CREDENTIALS`` que
    apunta al archivo de credenciales del servicio.  Se asume que el
    cliente expone los métodos ``submit_job`` y ``execute_job``.
    """

    def __init__(self) -> None:
        self.client = self._authenticate()

    def _authenticate(self) -> Any:
        """Autentica contra GCP usando ``google.cloud``."""
        from google.cloud import compute_v1
        from google.oauth2 import service_account

        creds = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
        if not creds:
            raise EnvironmentError(
                "Faltan credenciales de GCP en la variable GOOGLE_APPLICATION_CREDENTIALS"
            )
        credentials = service_account.Credentials.from_service_account_file(creds)
        return compute_v1.InstancesClient(credentials=credentials)

    def submit_job(self, job_data: Any) -> Any:
        """Envía un trabajo a GCP."""
        return self.client.submit_job(job_data)

    def execute_job(self, job_id: str) -> Any:
        """Ejecuta un trabajo previamente enviado."""
        return self.client.execute_job(job_id)
