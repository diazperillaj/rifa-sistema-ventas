from fastapi import Request
from pydantic import BaseModel, ValidationError

from app.core.security import CSRF_FORM_FIELD

FORM_ERROR = "form"  # clave para errores que no son de un campo


def safe_next(value: str | None, default: str) -> str:
    """Solo permite redirigir a rutas internas (evita redirecciones a otros dominios)."""
    if value and value.startswith("/") and not value.startswith("//") and "\\" not in value:
        return value
    return default


async def form_data(request: Request) -> dict[str, str]:
    """Dependencia: devuelve el formulario como dict (sin el token CSRF)."""
    form = await request.form()
    return {k: v for k, v in form.items() if k != CSRF_FORM_FIELD and isinstance(v, str)}


def validate_form[T: BaseModel](schema: type[T], data: dict) -> tuple[T | None, dict[str, str]]:
    """Valida con Pydantic y devuelve (modelo, {}) o (None, {campo: mensaje en español})."""
    try:
        return schema.model_validate(data), {}
    except ValidationError as exc:
        errors: dict[str, str] = {}
        custom = getattr(schema, "error_messages", {})
        for err in exc.errors():
            field = str(err["loc"][0]) if err["loc"] else FORM_ERROR
            if err.get("input") == "":
                message = "Este campo es obligatorio"
            else:
                message = custom.get(field) or _message(err)
            errors.setdefault(field, message)
        return None, errors


def _message(err: dict) -> str:
    ctx = err.get("ctx") or {}
    match err["type"]:
        case "missing":
            return "Este campo es obligatorio"
        case "string_too_short":
            if ctx.get("min_length") == 1:
                return "Este campo es obligatorio"
            return f"Debe tener al menos {ctx.get('min_length')} caracteres"
        case "string_too_long":
            return f"Debe tener máximo {ctx.get('max_length')} caracteres"
        case "enum" | "literal_error":
            return "Selecciona una opción válida"
        case "value_error":
            return str(ctx.get("error", "Valor no válido"))
        case _:
            return "Valor no válido"
