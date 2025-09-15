from __future__ import annotations

from typing import Dict, Protocol


class CredentialsProvider(Protocol):
    """Interfaz simple para obtener credenciales desde un proveedor externo."""

    def get_credentials(self) -> Dict[str, str]:
        """Devuelve un diccionario con las credenciales necesarias."""
