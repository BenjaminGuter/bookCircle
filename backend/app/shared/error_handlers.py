# Zentrale Übersetzung fachlicher Fehler in HTTP-Antworten.
# Grund: ersetzt drei kopierte try/except-Blöcke im Router (Duplikat, CCD).

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.shared.errors import DomainError, NotFoundError


def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(NotFoundError)
    def not_found(_request: Request, error: NotFoundError) -> JSONResponse:
        return JSONResponse(status_code=404, content={"detail": str(error)})

    @app.exception_handler(DomainError)
    def domain_error(_request: Request, error: DomainError) -> JSONResponse:
        return JSONResponse(status_code=422, content={"detail": str(error)})
