"""Crea un usuario administrador.

Uso (en el servidor):
    docker compose exec app python -m scripts.create_admin
"""

import argparse
import getpass
import sys

from app.api.v1.users import services
from app.api.v1.users.schemas import UserCreate
from app.core.database import SessionLocal
from app.core.forms import validate_form
from app.models import UserRole


def ask(label: str, default: str | None = None) -> str:
    return default if default is not None else input(f"{label}: ").strip()


def ask_password() -> str:
    while True:
        password = getpass.getpass("Contraseña (mín. 8 caracteres): ")
        if password == getpass.getpass("Repite la contraseña: "):
            return password
        print("Las contraseñas no coinciden, inténtalo de nuevo.\n")


def main() -> int:
    parser = argparse.ArgumentParser(description="Crea un usuario administrador")
    parser.add_argument("--username")
    parser.add_argument("--full-name")
    parser.add_argument("--phone", default="")
    args = parser.parse_args()

    values = {
        "username": ask("Usuario", args.username),
        "full_name": ask("Nombre completo", args.full_name),
        "phone": args.phone,
        "role": UserRole.ADMIN.value,
        # Sin terminal interactiva (pipe), la contraseña se lee de stdin
        "password": sys.stdin.readline().rstrip("\n") if not sys.stdin.isatty() else ask_password(),
    }

    data, errors = validate_form(UserCreate, values)
    if data is None:
        for field, message in errors.items():
            print(f"  {field}: {message}", file=sys.stderr)
        return 1

    with SessionLocal() as db:
        try:
            user = services.create_user(db, data)
        except services.UserError as exc:
            print(f"Error: {exc.message}", file=sys.stderr)
            return 1

    print(f"Administrador '{user.username}' creado.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
