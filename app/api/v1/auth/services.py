import time
from collections import defaultdict

from fastapi import Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.dependencies import SESSION_FINGERPRINT_KEY, SESSION_USER_KEY
from app.core.security import password_fingerprint, verify_password
from app.models import User


def authenticate(db: Session, username: str, password: str) -> User | None:
    user = db.scalar(select(User).where(User.username == username))
    if not verify_password(password, user.password_hash if user else None):
        return None
    if not user.is_active:
        return None
    return user


def login(request: Request, user: User) -> None:
    # Se limpia la sesión anterior (evita reutilizar una sesión previa al login)
    request.session.clear()
    request.session[SESSION_USER_KEY] = user.id
    request.session[SESSION_FINGERPRINT_KEY] = password_fingerprint(user.password_hash)


def logout(request: Request) -> None:
    request.session.clear()


class LoginThrottle:
    """Bloquea temporalmente tras varios intentos fallidos (por IP + usuario). En memoria."""

    def __init__(self, max_attempts: int = 5, window_seconds: int = 15 * 60) -> None:
        self.max_attempts = max_attempts
        self.window = window_seconds
        self._failures: dict[str, list[float]] = defaultdict(list)

    def _recent(self, key: str) -> list[float]:
        cutoff = time.monotonic() - self.window
        attempts = [t for t in self._failures[key] if t > cutoff]
        if attempts:
            self._failures[key] = attempts
        else:
            self._failures.pop(key, None)
        return attempts

    def is_blocked(self, key: str) -> bool:
        return len(self._recent(key)) >= self.max_attempts

    def register_failure(self, key: str) -> None:
        self._failures[key].append(time.monotonic())

    def reset(self, key: str) -> None:
        self._failures.pop(key, None)


login_throttle = LoginThrottle()
