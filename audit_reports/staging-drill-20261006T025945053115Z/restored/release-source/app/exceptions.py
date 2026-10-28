"""
Exception Hierarchy & Handlers.
"""
from typing import Any, Dict
from fastapi import Request
from fastapi.responses import JSONResponse


class AppException(Exception):
    """Base exception untuk aplikasi."""
    def __init__(self, message: str, status_code: int = 400, details: Dict[str, Any] = None):
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(message)


class ValidationError(AppException):
    def __init__(self, message: str, field: str = None, details: Dict[str, Any] = None):
        super().__init__(message=message, status_code=422, details={"field": field, **(details or {})})


class NotFoundError(AppException):
    def __init__(self, resource: str, identifier: str):
        super().__init__(
            message=f"{resource} dengan identifier '{identifier}' tidak ditemukan",
            status_code=404,
            details={"resource": resource, "identifier": identifier},
        )


class NotAuthorizedError(AppException):
    def __init__(self, message: str = "Tidak memiliki akses"):
        super().__init__(message=message, status_code=403)


class ConflictError(AppException):
    def __init__(self, message: str, details: Dict[str, Any] = None):
        super().__init__(message=message, status_code=409, details=details)


class InternalError(AppException):
    def __init__(self, message: str = "Terjadi kesalahan internal"):
        super().__init__(message=message, status_code=500)


class ProviderUnavailableError(AppException):
    def __init__(self, provider: str):
        super().__init__(
            message=f"Provider '{provider}' tidak tersedia",
            status_code=503,
            details={"provider": provider},
        )


def register_exception_handlers(app):
    """Register exception handlers."""
    from app.exceptions import (
        AppException, ValidationError, NotFoundError,
        NotAuthorizedError, ConflictError, InternalError, ProviderUnavailableError,
    )

    @app.exception_handler(AppException)
    async def app_exception_handler(request: Request, exc: AppException):
        return JSONResponse(
            status_code=exc.status_code,
            content={"error": True, "message": exc.message, "details": exc.details, "path": str(request.url)}
        )

    @app.exception_handler(ValidationError)
    async def validation_exception_handler(request: Request, exc: ValidationError):
        return JSONResponse(
            status_code=exc.status_code,
            content={"error": True, "message": exc.message, "details": exc.details, "path": str(request.url)}
        )

    @app.exception_handler(NotFoundError)
    async def not_found_exception_handler(request: Request, exc: NotFoundError):
        return JSONResponse(
            status_code=exc.status_code,
            content={"error": True, "message": exc.message, "details": exc.details, "path": str(request.url)}
        )

    @app.exception_handler(NotAuthorizedError)
    async def auth_exception_handler(request: Request, exc: NotAuthorizedError):
        return JSONResponse(
            status_code=exc.status_code,
            content={"error": True, "message": exc.message, "path": str(request.url)}
        )

    @app.exception_handler(ConflictError)
    async def conflict_exception_handler(request: Request, exc: ConflictError):
        return JSONResponse(
            status_code=exc.status_code,
            content={"error": True, "message": exc.message, "details": exc.details, "path": str(request.url)}
        )

    @app.exception_handler(InternalError)
    async def internal_exception_handler(request: Request, exc: InternalError):
        return JSONResponse(
            status_code=exc.status_code,
            content={"error": True, "message": "Terjadi kesalahan internal server", "path": str(request.url)}
        )

    @app.exception_handler(ProviderUnavailableError)
    async def provider_exception_handler(request: Request, exc: ProviderUnavailableError):
        return JSONResponse(
            status_code=exc.status_code,
            content={"error": True, "message": exc.message, "details": exc.details, "path": str(request.url)}
        )

    @app.exception_handler(Exception)
    async def generic_exception_handler(request: Request, exc: Exception):
        return JSONResponse(
            status_code=500,
            content={"error": True, "message": "Terjadi kesalahan tidak diketahui", "path": str(request.url)}
        )
