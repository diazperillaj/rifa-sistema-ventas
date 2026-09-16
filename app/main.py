from pathlib import Path

from fastapi import Depends, FastAPI, Request
from fastapi.responses import HTMLResponse, RedirectResponse, Response
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware.sessions import SessionMiddleware

from app.api.v1.router import router as v1_router
from app.core.config import settings
from app.core.dependencies import Forbidden, NotAuthenticated
from app.core.security import CsrfError, csrf_protect
from app.core.templates import templates

BASE_DIR = Path(__file__).resolve().parent

app = FastAPI(
    title="Rifa",
    docs_url=None if settings.is_production else "/docs",
    redoc_url=None,
    openapi_url=None if settings.is_production else "/openapi.json",
    dependencies=[Depends(csrf_protect)],
)

app.add_middleware(
    SessionMiddleware,
    secret_key=settings.secret_key,
    session_cookie="rifa_session",
    max_age=settings.session_max_age,
    same_site="lax",
    https_only=settings.is_production,
)

app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
app.include_router(v1_router)


ERROR_MESSAGES = {
    403: ("Sin permiso", "No tienes acceso a esta página."),
    404: ("Página no encontrada", "La página que buscas no existe o fue movida."),
}


def _error_page(request: Request, status_code: int, title: str | None = None, message: str | None = None) -> HTMLResponse:
    default_title, default_message = ERROR_MESSAGES.get(status_code, ("Algo salió mal", "Inténtalo de nuevo."))
    return templates.TemplateResponse(
        request,
        "errors/error.html",
        {"status_code": status_code, "title": title or default_title, "message": message or default_message},
        status_code=status_code,
    )


@app.exception_handler(NotAuthenticated)
def not_authenticated_handler(request: Request, _: NotAuthenticated) -> Response:
    if request.headers.get("hx-request"):
        return Response(status_code=204, headers={"HX-Redirect": "/login"})
    return RedirectResponse("/login", status_code=303)


@app.exception_handler(Forbidden)
def forbidden_handler(request: Request, _: Forbidden) -> HTMLResponse:
    return _error_page(request, 403)


@app.exception_handler(CsrfError)
def csrf_handler(request: Request, _: CsrfError) -> HTMLResponse:
    return _error_page(request, 403, "La sesión expiró", "Recarga la página e inténtalo de nuevo.")


@app.exception_handler(StarletteHTTPException)
def http_exception_handler(request: Request, exc: StarletteHTTPException) -> HTMLResponse:
    return _error_page(request, exc.status_code)
