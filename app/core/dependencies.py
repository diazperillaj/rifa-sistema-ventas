from fastapi import Depends, Request
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import password_fingerprint
from app.models import User

SESSION_USER_KEY = "user_id"
SESSION_FINGERPRINT_KEY = "fp"


class NotAuthenticated(Exception):
    pass


class Forbidden(Exception):
    pass


def get_current_user(request: Request, db: Session = Depends(get_db)) -> User:
    user_id = request.session.get(SESSION_USER_KEY)
    user = db.get(User, user_id) if isinstance(user_id, int) else None

    valid = (
        user is not None
        and user.is_active
        and request.session.get(SESSION_FINGERPRINT_KEY) == password_fingerprint(user.password_hash)
    )
    if not valid:
        request.session.pop(SESSION_USER_KEY, None)
        request.session.pop(SESSION_FINGERPRINT_KEY, None)
        raise NotAuthenticated

    request.state.user = user
    return user


def require_admin(user: User = Depends(get_current_user)) -> User:
    if not user.is_admin:
        raise Forbidden
    return user
