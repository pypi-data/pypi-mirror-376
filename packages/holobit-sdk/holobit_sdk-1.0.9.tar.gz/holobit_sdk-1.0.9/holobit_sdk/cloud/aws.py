"""Backend de AWS para ejecutar trabajos Holobit."""

from __future__ import annotations

import logging
import os
from typing import Any, Optional

from .base import BaseCloudBackend
from .credentials import CredentialsProvider


class AWSBackend(BaseCloudBackend):
    """Cliente sencillo para AWS basado en ``boto3``.

    La autenticación se realiza leyendo las variables de entorno
    ``AWS_ACCESS_KEY_ID`` y ``AWS_SECRET_ACCESS_KEY``.  Se asume que el
    servicio remoto expone los métodos ``submit_job`` y ``execute_job``.
    En las pruebas se emplean mocks de ``boto3``.
    """

    def __init__(self, provider: Optional[CredentialsProvider] = None) -> None:
        self.client = self._authenticate(provider)

    def _authenticate(self, provider: Optional[CredentialsProvider] = None) -> Any:
        """Crea un cliente de AWS usando ``boto3``.

        Si se proporciona ``provider`` se intentará obtener las credenciales
        desde él antes de leerlas del entorno.
        """
        import boto3  # importación diferida para facilitar los mocks

        logger = logging.getLogger(__name__)
        creds = {}
        if provider is not None:
            try:
                creds = provider.get_credentials()
            except Exception as exc:  # pragma: no cover - log de error
                logger.error("Error obteniendo credenciales de AWS: %s", exc)
        access_key = creds.get("AWS_ACCESS_KEY_ID") or os.environ.get(
            "AWS_ACCESS_KEY_ID"
        )
        secret_key = creds.get("AWS_SECRET_ACCESS_KEY") or os.environ.get(
            "AWS_SECRET_ACCESS_KEY"
        )
        if not (access_key and secret_key):
            logger.error("Faltan credenciales de AWS")
            raise EnvironmentError("Faltan credenciales de AWS")

        session = boto3.session.Session(
            aws_access_key_id=access_key, aws_secret_access_key=secret_key
        )
        return session.client("holobit")

    def submit_job(self, job_data: Any) -> Any:
        """Envía un trabajo al servicio de AWS."""
        return self.client.submit_job(job_data)

    def execute_job(self, job_id: str) -> Any:
        """Ejecuta un trabajo previamente enviado."""
        return self.client.execute_job(job_id)
