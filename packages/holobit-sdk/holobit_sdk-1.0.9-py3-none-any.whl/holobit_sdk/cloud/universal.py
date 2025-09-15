from __future__ import annotations

"""Backend universal que delega en el proveedor configurado."""

import os
from typing import Any, Dict, Type

from .base import BaseCloudBackend
from .aws import AWSBackend
from .azure import AzureBackend
from .gcp import GCPBackend

BACKENDS: Dict[str, Type[BaseCloudBackend]] = {
    "aws": AWSBackend,
    "azure": AzureBackend,
    "gcp": GCPBackend,
    # Otros proveedores como IBM podrían añadirse aquí
}


class UniversalBackend(BaseCloudBackend):
    """Selecciona dinámicamente el backend a utilizar."""

    def __init__(self, provider: str | None = None) -> None:
        name = provider or os.getenv("HOLOBIT_PROVIDER", "aws")
        backend_cls = BACKENDS.get(name.lower())
        if backend_cls is None:
            raise ValueError(f"Backend desconocido: {name}")
        self.backend = backend_cls()

    def submit_job(self, job_data: Any) -> Any:
        return self.backend.submit_job(job_data)

    def execute_job(self, job_id: str) -> Any:
        return self.backend.execute_job(job_id)
