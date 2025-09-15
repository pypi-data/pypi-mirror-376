"""Servicio FastAPI para compilar y ejecutar Holobits.

La configuración se realiza mediante variables de entorno:

* ``HOLOBIT_PORT``: puerto del servidor (por defecto 8000).
* ``HOLOBIT_BACKEND``: backend de cloud a utilizar (``aws``, ``azure``, ``gcp`` o ``universal``).
* ``HOLOBIT_USER`` y ``HOLOBIT_PASSWORD_HASH``: usuario y hash ``bcrypt`` de la contraseña.
* ``HOLOBIT_MAX_AUTH_ATTEMPTS``: número de intentos fallidos permitidos antes de bloquear.
* ``HOLOBIT_LOCK_SECONDS``: tiempo de bloqueo tras exceder los intentos.
"""

from __future__ import annotations

import logging
import os
import re
import secrets
import time
from typing import Any, Dict, Tuple

import bcrypt

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.security import HTTPBasic, HTTPBasicCredentials

from holobit_sdk.cloud import (
    AWSBackend,
    AzureBackend,
    GCPBackend,
    UniversalBackend,
)

app = FastAPI(title="Holobit SDK API")

security = HTTPBasic()


# Intentos fallidos de autenticación por IP/usuario
_FAILED_ATTEMPTS: Dict[str, Tuple[int, float]] = {}
_MAX_ATTEMPTS = int(os.getenv("HOLOBIT_MAX_AUTH_ATTEMPTS", "3"))
_LOCK_SECONDS = int(os.getenv("HOLOBIT_LOCK_SECONDS", "60"))

# Configuración opcional de TLS
_TLS_CERT = os.getenv("HOLOBIT_TLS_CERT")
_TLS_KEY = os.getenv("HOLOBIT_TLS_KEY")
if _TLS_CERT and _TLS_KEY:
    if not (os.path.isfile(_TLS_CERT) and os.path.isfile(_TLS_KEY)):
        logging.warning(
            "Los archivos TLS especificados no existen; la API debe desplegarse detrás de un proxy HTTPS"
        )
        _TLS_CERT = _TLS_KEY = None
else:
    logging.warning(
        "No se configuraron HOLOBIT_TLS_CERT y HOLOBIT_TLS_KEY; la API debe desplegarse detrás de un proxy HTTPS"
    )


def _select_backend() -> Any:
    """Selecciona el backend de cloud según la variable de entorno."""
    backend = os.getenv("HOLOBIT_BACKEND", "aws").lower()
    if backend == "aws":
        return AWSBackend()
    if backend == "azure":
        return AzureBackend()
    if backend == "gcp":
        return GCPBackend()
    if backend == "universal":
        provider = os.getenv("HOLOBIT_PROVIDER")
        return UniversalBackend(provider)
    raise ValueError(f"Backend desconocido: {backend}")


 # Credenciales obligatorias en el entorno
_USER = os.getenv("HOLOBIT_USER")
_PASS_HASH = os.getenv("HOLOBIT_PASSWORD_HASH")
if not (_USER and _PASS_HASH):
    raise RuntimeError(
        "HOLOBIT_USER y HOLOBIT_PASSWORD_HASH deben estar configuradas"
    )
_PASS_HASH_BYTES = _PASS_HASH.encode()

backend = _select_backend()


_VALID_TEXT = re.compile(r"^[\x20-\x7E\r\n\t]*$")


def _validate_ascii(value: str, field: str) -> None:
    if not _VALID_TEXT.fullmatch(value):
        raise HTTPException(
            status_code=400,
            detail=f"El campo '{field}' contiene caracteres inválidos",
        )


def _authenticate(
    credentials: HTTPBasicCredentials = Depends(security),
    request: Request = None,
) -> str:
    """Valida credenciales básicas usando hash ``bcrypt``.

    Implementa un contador de intentos fallidos por IP o usuario que bloquea
    temporalmente el acceso tras varios errores consecutivos.
    """
    key = (
        request.client.host if request and request.client else credentials.username
    )
    now = time.time()
    count, lock_until = _FAILED_ATTEMPTS.get(key, (0, 0.0))
    if lock_until and now < lock_until:
        raise HTTPException(
            status_code=429,
            detail="Demasiados intentos, inténtelo más tarde",
        )
    if lock_until and now >= lock_until:
        count = 0
        lock_until = 0.0

    correct_user = secrets.compare_digest(credentials.username, _USER)
    try:
        correct_pass = bcrypt.checkpw(
            credentials.password.encode(), _PASS_HASH_BYTES
        )
    except ValueError:
        correct_pass = False

    if not (correct_user and correct_pass):
        count += 1
        if count >= _MAX_ATTEMPTS:
            lock_until = now + _LOCK_SECONDS
            _FAILED_ATTEMPTS[key] = (count, lock_until)
            raise HTTPException(
                status_code=429,
                detail="Demasiados intentos, inténtelo más tarde",
            )
        _FAILED_ATTEMPTS[key] = (count, lock_until)
        raise HTTPException(status_code=401, detail="Credenciales inválidas")

    if key in _FAILED_ATTEMPTS:
        del _FAILED_ATTEMPTS[key]
    return credentials.username


@app.post("/compile")
async def compile_holobit(data: Dict[str, Any], _: str = Depends(_authenticate)) -> Dict[str, Any]:
    """Envía código Holobit al backend para su compilación."""
    code = data.get("code")
    if code is None:
        raise HTTPException(status_code=400, detail="Falta el campo 'code'")
    if not isinstance(code, str):
        raise HTTPException(
            status_code=400, detail="El campo 'code' debe ser una cadena"
        )
    if len(code) > 10_000:
        raise HTTPException(
            status_code=413, detail="El campo 'code' excede el tamaño máximo"
        )
    if not code:
        raise HTTPException(status_code=400, detail="Falta el campo 'code'")
    _validate_ascii(code, "code")
    try:
        job_id = backend.submit_job({"code": code})
    except Exception as exc:  # pragma: no cover - defensive
        raise HTTPException(status_code=502, detail="Error en el backend") from exc
    return {"job_id": job_id}


@app.post("/execute")
async def execute_holobit(data: Dict[str, Any], _: str = Depends(_authenticate)) -> Dict[str, Any]:
    """Ejecuta un trabajo previamente compilado.

    El ``job_id`` debe ser una cadena ASCII de hasta 256 caracteres.
    """
    job_id = data.get("job_id")
    if not job_id:
        raise HTTPException(status_code=400, detail="Falta el campo 'job_id'")
    if not isinstance(job_id, str):
        raise HTTPException(
            status_code=400, detail="El campo 'job_id' debe ser una cadena"
        )
    if len(job_id) > 256:
        raise HTTPException(
            status_code=413, detail="El campo 'job_id' excede el tamaño máximo"
        )
    _validate_ascii(job_id, "job_id")
    try:
        result = backend.execute_job(job_id)
    except Exception as exc:  # pragma: no cover - defensive
        raise HTTPException(status_code=502, detail="Error en el backend") from exc
    return {"result": result}


if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("HOLOBIT_PORT", "8000"))
    uvicorn.run(
        "holobit_sdk.api.service:app",
        host="0.0.0.0",
        port=port,
        ssl_certfile=_TLS_CERT,
        ssl_keyfile=_TLS_KEY,
    )
