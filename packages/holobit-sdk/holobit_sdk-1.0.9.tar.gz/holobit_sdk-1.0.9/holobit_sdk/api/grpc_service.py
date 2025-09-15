from __future__ import annotations

"""Servicio gRPC para compilar y ejecutar Holobits."""

import os
import secrets
from concurrent import futures
from typing import Any
import threading

import grpc
from grpc import ssl_server_credentials

from api import holobit_pb2, holobit_pb2_grpc
from holobit_sdk.cloud import AWSBackend, AzureBackend, GCPBackend, UniversalBackend


def _select_backend() -> Any:
    """Selecciona el backend de nube basado en variables de entorno."""
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


backend = None
_backend_lock = threading.Lock()


def get_backend() -> Any:
    """Obtiene (y cachea) el backend seleccionado.

    El backend se crea de forma lazy y se protege con un ``threading.Lock``
    para asegurar un único instanciamiento incluso en escenarios multihilo.
    """

    global backend
    if backend is None:
        with _backend_lock:
            if backend is None:
                backend = _select_backend()
    return backend


TOKEN_METADATA_KEY = "x-holobit-token"


class TokenAuthInterceptor(grpc.ServerInterceptor):
    """Interceptor que valida un token compartido en la metadata."""

    def __init__(self, token: str) -> None:
        self._token = token

    def intercept_service(self, continuation, handler_call_details):  # type: ignore[override]
        handler = continuation(handler_call_details)
        if handler is None:
            return None

        def _verify_metadata(context: grpc.ServicerContext) -> None:
            metadata = dict(context.invocation_metadata())
            provided = metadata.get(TOKEN_METADATA_KEY)
            if not (provided and secrets.compare_digest(provided, self._token)):
                context.abort(grpc.StatusCode.UNAUTHENTICATED, "Token inválido")

        if handler.unary_unary:
            def unary_unary(request, context):
                _verify_metadata(context)
                return handler.unary_unary(request, context)

            return grpc.unary_unary_rpc_method_handler(
                unary_unary,
                request_deserializer=handler.request_deserializer,
                response_serializer=handler.response_serializer,
            )

        if handler.unary_stream:
            def unary_stream(request, context):
                _verify_metadata(context)
                return handler.unary_stream(request, context)

            return grpc.unary_stream_rpc_method_handler(
                unary_stream,
                request_deserializer=handler.request_deserializer,
                response_serializer=handler.response_serializer,
            )

        if handler.stream_unary:
            def stream_unary(request_iterator, context):
                _verify_metadata(context)
                return handler.stream_unary(request_iterator, context)

            return grpc.stream_unary_rpc_method_handler(
                stream_unary,
                request_deserializer=handler.request_deserializer,
                response_serializer=handler.response_serializer,
            )

        if handler.stream_stream:
            def stream_stream(request_iterator, context):
                _verify_metadata(context)
                return handler.stream_stream(request_iterator, context)

            return grpc.stream_stream_rpc_method_handler(
                stream_stream,
                request_deserializer=handler.request_deserializer,
                response_serializer=handler.response_serializer,
            )

        return handler


class HolobitService(holobit_pb2_grpc.HolobitServiceServicer):
    """Implementación del servicio gRPC."""

    def Compile(self, request: holobit_pb2.CodeRequest, context: grpc.ServicerContext) -> holobit_pb2.JobReply:  # noqa: N802
        if not request.code:
            context.abort(grpc.StatusCode.INVALID_ARGUMENT, "Falta el campo 'code'")
        job_id = get_backend().submit_job({"code": request.code})
        return holobit_pb2.JobReply(job_id=job_id)

    def Execute(self, request: holobit_pb2.JobRequest, context: grpc.ServicerContext) -> holobit_pb2.ResultReply:  # noqa: N802
        if not request.job_id:
            context.abort(grpc.StatusCode.INVALID_ARGUMENT, "Falta el campo 'job_id'")
        result = get_backend().execute_job(request.job_id)
        return holobit_pb2.ResultReply(result=str(result))


def serve() -> None:
    """Arranca el servidor gRPC."""
    token = os.getenv("HOLOBIT_GRPC_TOKEN")
    if not token:
        raise RuntimeError("HOLOBIT_GRPC_TOKEN debe estar configurado")

    server = grpc.server(
        futures.ThreadPoolExecutor(max_workers=10),
        interceptors=(TokenAuthInterceptor(token),),
    )
    holobit_pb2_grpc.add_HolobitServiceServicer_to_server(HolobitService(), server)
    port = int(os.getenv("HOLOBIT_PORT", "50051"))

    cert_path = os.getenv("HOLOBIT_TLS_CERT")
    key_path = os.getenv("HOLOBIT_TLS_KEY")
    if cert_path and key_path:
        with open(key_path, "rb") as key_file, open(cert_path, "rb") as cert_file:
            private_key = key_file.read()
            certificate = cert_file.read()
        credentials = ssl_server_credentials(((private_key, certificate),))
        server.add_secure_port(f"[::]:{port}", credentials)
    else:
        print(
            "Iniciando gRPC sin TLS: la comunicación no estará cifrada; "
            "uso solo recomendado en entornos de desarrollo"
        )
        server.add_insecure_port(f"[::]:{port}")
    server.start()
    server.wait_for_termination()


if __name__ == "__main__":
    serve()
