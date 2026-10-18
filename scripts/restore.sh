#!/usr/bin/env sh
set -eu
BACKUP="${1:?Usage: scripts/restore.sh BACKUP_FILE}"
if printf '%s' "$BACKUP" | grep -q '\.sqlite3$'; then
  cp "$BACKUP" "${SQLITE_PATH:-db.sqlite3}"
else
  mysql -h "${MYSQL_HOST:-db}" -P "${MYSQL_PORT:-3306}" -u "${MYSQL_USER:-student}" -p"${MYSQL_PASSWORD:-student_password}" "${MYSQL_DATABASE:-student_records}" < "$BACKUP"
fi
echo "Restore completed from $BACKUP"
