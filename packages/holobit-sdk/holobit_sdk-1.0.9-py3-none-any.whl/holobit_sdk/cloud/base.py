from __future__ import annotations

"""Clases base para los backends de nube de Holobit."""

from abc import ABC, abstractmethod
from typing import Any


class BaseCloudBackend(ABC):
    """Interface mínima que deben implementar los backends de nube."""

    @abstractmethod
    def submit_job(self, job_data: Any) -> Any:
        """Envía un trabajo al proveedor y devuelve un identificador."""

    @abstractmethod
    def execute_job(self, job_id: str) -> Any:
        """Ejecuta un trabajo previamente enviado."""
