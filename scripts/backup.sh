#!/usr/bin/env bash
# Backup de la base de datos de la rifa. Se ejecuta en el servidor (host), no dentro del contenedor.
#
# Uso:
#   ./scripts/backup.sh
#
# Cron diario a las 3:00 am (crontab -e):
#   0 3 * * * /ruta/al/proyecto/scripts/backup.sh >> /ruta/al/proyecto/backups/backup.log 2>&1
#
# Restaurar:
#   gunzip -c backups/rifa_AAAA-MM-DD_HHMM.sql.gz | docker exec -i rifa-db sh -c 'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB"'

set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
BACKUP_DIR="${BACKUP_DIR:-$PROJECT_DIR/backups}"
KEEP_DAYS="${KEEP_DAYS:-14}"

mkdir -p "$BACKUP_DIR"
FILE="$BACKUP_DIR/rifa_$(date +%F_%H%M).sql.gz"

# --clean: al restaurar, borra y recrea las tablas
docker exec rifa-db sh -c 'pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" --clean --if-exists' | gzip > "$FILE.tmp"
mv "$FILE.tmp" "$FILE"

find "$BACKUP_DIR" -name 'rifa_*.sql.gz' -mtime +"$KEEP_DAYS" -delete

echo "$(date '+%F %T') backup creado: $FILE ($(du -h "$FILE" | cut -f1))"
