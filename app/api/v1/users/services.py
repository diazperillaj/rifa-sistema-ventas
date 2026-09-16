from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.v1.users.schemas import UserCreate, UserUpdate
from app.core.forms import FORM_ERROR
from app.core.security import hash_password
from app.models import Sale, User, UserRole


class UserError(Exception):
    def __init__(self, message: str, field: str = FORM_ERROR) -> None:
        super().__init__(message)
        self.field = field
        self.message = message


def list_users_with_sales(db: Session) -> list[tuple[User, int]]:
    stmt = (
        select(User, func.count(Sale.id))
        .outerjoin(Sale, Sale.seller_id == User.id)
        .group_by(User.id)
        .order_by(User.is_active.desc(), User.full_name)
    )
    return [(user, count) for user, count in db.execute(stmt).all()]


def get_user(db: Session, user_id: int) -> User | None:
    return db.get(User, user_id)


def create_user(db: Session, data: UserCreate) -> User:
    user = User(
        full_name=data.full_name,
        username=data.username,
        phone=data.phone,
        role=data.role,
        password_hash=hash_password(data.password),
    )
    db.add(user)
    _commit_unique_username(db)
    db.refresh(user)
    return user


def update_user(db: Session, user: User, data: UserUpdate, acting_user: User) -> User:
    if user.id == acting_user.id and (data.role != UserRole.ADMIN or not data.is_active):
        raise UserError("No puedes quitarte el rol de administrador ni desactivar tu propia cuenta")

    user.full_name = data.full_name
    user.username = data.username
    user.phone = data.phone
    user.role = data.role
    user.is_active = data.is_active
    _commit_unique_username(db)
    return user


def set_password(db: Session, user: User, password: str) -> None:
    # Cambiar el hash invalida las sesiones abiertas de ese usuario
    user.password_hash = hash_password(password)
    db.commit()


def _commit_unique_username(db: Session) -> None:
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        if "uq_users_username" in str(exc.orig):
            raise UserError("Ese nombre de usuario ya existe", field="username") from exc
        raise
