import hashlib
import hmac
import secrets

from fastapi import Request
from pwdlib import PasswordHash

from app.core.config import settings

_hasher = PasswordHash.recommended()  # Argon2

# Hash de relleno: se verifica cuando el usuario no existe para que la respuesta
# tarde lo mismo y no revele qué usuarios existen.
DUMMY_HASH = _hasher.hash(secrets.token_urlsafe(16))

CSRF_SESSION_KEY = "csrf"
CSRF_FORM_FIELD = "csrf_token"
CSRF_HEADER = "x-csrf-token"
SAFE_METHODS = {"GET", "HEAD", "OPTIONS"}


class CsrfError(Exception):
    pass


def hash_password(password: str) -> str:
    return _hasher.hash(password)


def verify_password(password: str, password_hash: str | None) -> bool:
    return _hasher.verify(password, password_hash or DUMMY_HASH) and password_hash is not None


def password_fingerprint(password_hash: str) -> str:
    """Huella del hash guardada en la sesión: si la contraseña cambia, la sesión deja de ser válida."""
    digest = hmac.new(settings.secret_key.encode(), password_hash.encode(), hashlib.sha256)
    return digest.hexdigest()[:16]


def get_csrf_token(request: Request) -> str:
    token = request.session.get(CSRF_SESSION_KEY)
    if not token:
        token = secrets.token_urlsafe(32)
        request.session[CSRF_SESSION_KEY] = token
    return token


async def csrf_protect(request: Request) -> None:
    """Dependencia global: valida el token CSRF en toda petición que modifica datos."""
    if request.method in SAFE_METHODS:
        return
    expected = request.session.get(CSRF_SESSION_KEY)
    sent = request.headers.get(CSRF_HEADER)
    if sent is None and "form" in request.headers.get("content-type", ""):
        sent = (await request.form()).get(CSRF_FORM_FIELD)
    if not expected or not isinstance(sent, str) or not secrets.compare_digest(expected, sent):
        raise CsrfError
