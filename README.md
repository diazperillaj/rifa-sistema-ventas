# Sistema de ventas para rifas

Aplicación web para registrar y controlar la venta de números de una rifa de 100 números (00 a 99). El administrador crea las cuentas de los vendedores y cada vendedor registra sus ventas desde el celular o el computador.

## Funcionalidades

**Vendedores**

- Tablero con los números disponibles y vendidos, actualizado periódicamente.
- Registro de ventas con nombre y teléfono del comprador, estado de pago y notas.
- Consulta, edición y eliminación de sus propias ventas.
- Resumen de lo recaudado y lo pendiente por cobrar.

**Administrador**

- Todas las funciones de un vendedor.
- Panel con totales, avance de la rifa, últimos números vendidos y ventas por vendedor.
- Listado de todas las ventas con búsqueda y filtros por vendedor y estado de pago.
- Edición y eliminación de cualquier venta.
- Gestión de usuarios: creación, edición, activación y cambio de contraseña.
- Configuración de la rifa: nombre, valor del número y fecha del sorteo.

La base de datos impide que un mismo número se venda dos veces, incluso si dos vendedores lo registran al mismo tiempo.

## Tecnologías

- Python 3.12, FastAPI y Jinja2
- HTMX
- Tailwind CSS v4
- PostgreSQL 16, SQLAlchemy 2 y Alembic
- Nginx
- Docker Compose

## Estructura

```
├── app/
│   ├── api/v1/           # Módulos: auth, users, raffle, sales, dashboard
│   │   └── <modulo>/
│   │       ├── routes.py
│   │       ├── services.py
│   │       └── schemas.py
│   ├── core/             # Configuración, base de datos, seguridad y plantillas
│   ├── models/           # Modelos SQLAlchemy
│   ├── templates/        # Plantillas Jinja2
│   └── static/
├── docker/               # Dockerfile de la aplicación y configuración de Nginx
├── migrations/           # Migraciones de Alembic
├── scripts/              # Creación de administrador y backups
└── tailwind/             # Hoja de estilos y paleta de colores
```

## Instalación con Docker

### Requisitos

- Docker y Docker Compose

### 1. Clonar el repositorio

```bash
git clone https://github.com/diazperillaj/rifa-sistema-ventas.git
cd rifa-sistema-ventas
```

### 2. Configurar las variables de entorno

```bash
cp .env.example .env
```

Editar `.env` y definir `POSTGRES_PASSWORD` y `SECRET_KEY`. La clave se puede generar con:

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

| Variable | Descripción |
|---|---|
| `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD` | Credenciales de la base de datos |
| `SECRET_KEY` | Clave para firmar las sesiones |
| `ENVIRONMENT` | `production` o `development` |
| `SESSION_MAX_AGE` | Duración de la sesión en segundos (por defecto 86400) |

Con `ENVIRONMENT=production` la cookie de sesión solo se envía por HTTPS, por lo que la aplicación debe publicarse detrás de un proxy inverso con certificado. Para uso local se debe usar `development`.

### 3. Crear la red del proxy

El contenedor de Nginx se conecta a una red externa llamada `proxy`, pensada para compartirse con un proxy inverso. Si no existe:

```bash
docker network create proxy
```

### 4. Levantar los servicios

En producción, detrás de un proxy inverso que apunte a `rifa-web:80`:

```bash
docker compose up -d --build
```

En desarrollo, exponiendo la aplicación en `http://localhost:8090`:

```bash
docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d --build
```

Las migraciones de la base de datos se aplican automáticamente al iniciar el contenedor de la aplicación.

### 5. Crear el administrador

```bash
docker compose exec app python -m scripts.create_admin
```

## Backups

```bash
./scripts/backup.sh
```

Genera un archivo comprimido en `backups/` y elimina los que tengan más de 14 días. Para restaurar:

```bash
gunzip -c backups/<archivo>.sql.gz | docker exec -i rifa-db sh -c 'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB"'
```

## Personalización

Los colores y la tipografía se definen en `tailwind/input.css`. Los cambios se aplican al reconstruir la imagen con `--build`.
