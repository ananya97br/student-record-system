#!/usr/bin/env sh
set -eu
OUT_DIR="${1:-backups}"
mkdir -p "$OUT_DIR"
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
if [ "${DATABASE_URL:-}" = "" ] || printf '%s' "${DATABASE_URL:-}" | grep -q '^sqlite'; then
  DB_PATH="${SQLITE_PATH:-db.sqlite3}"
  cp "$DB_PATH" "$OUT_DIR/student-records-$STAMP.sqlite3"
else
  mysqldump --single-transaction --no-tablespaces --routines --triggers -h "${MYSQL_HOST:-db}" -P "${MYSQL_PORT:-3306}" -u "${MYSQL_USER:-student}" -p"${MYSQL_PASSWORD:-student_password}" "${MYSQL_DATABASE:-student_records}" > "$OUT_DIR/student-records-$STAMP.sql"
fi
echo "Backup written to $OUT_DIR"
