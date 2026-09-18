#!/bin/bash
# =============================================================================
# Database Restore Script
# Sistema de Gestion de Seguridad Industrial y Salud Ocupacional
# =============================================================================
# Restores a database from a backup file created by backup-db.sh.
# Supports both PostgreSQL and SQLite restores.
#
# Usage:
#   DATABASE_URL=postgresql://user:pass@host:5432/dbname ./restore-db.sh db_2025-01-15_10-30-00.sql.gz
#   DATABASE_URL=sqlite:///./seguridad_industrial.db ./restore-db.sh db_2025-01-15_10-30-00.sqlite.gz
#
# Environment variables:
#   DATABASE_URL   - Required. Connection string for the database.
#   BACKUP_DIR     - Optional. Directory where backups are stored (default: /backups).
# =============================================================================

set -euo pipefail

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
BACKUP_DIR="${BACKUP_DIR:-/backups}"

# ---------------------------------------------------------------------------
# Logging helper
# ---------------------------------------------------------------------------
log() {
    local level="$1"
    shift
    local message="$*"
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] [${level}] ${message}"
}

# ---------------------------------------------------------------------------
# Validate arguments
# ---------------------------------------------------------------------------
if [ $# -lt 1 ]; then
    echo "Usage: $0 <backup-filename>"
    echo ""
    echo "Examples:"
    echo "  $0 db_2025-01-15_10-30-00.sql.gz       # PostgreSQL backup"
    echo "  $0 db_2025-01-15_10-30-00.sqlite.gz     # SQLite backup"
    echo ""
    echo "Available backups in ${BACKUP_DIR}:"
    ls -lht "${BACKUP_DIR}"/db_*.gz 2>/dev/null || echo "  (no backups found)"
    exit 1
fi

BACKUP_FILENAME="$1"

# Resolve full path: if the argument is just a filename, prepend BACKUP_DIR
if [ -f "${BACKUP_FILENAME}" ]; then
    BACKUP_FILE="${BACKUP_FILENAME}"
elif [ -f "${BACKUP_DIR}/${BACKUP_FILENAME}" ]; then
    BACKUP_FILE="${BACKUP_DIR}/${BACKUP_FILENAME}"
else
    log "ERROR" "Backup file not found: ${BACKUP_FILENAME}"
    log "ERROR" "Searched in: current directory and ${BACKUP_DIR}/"
    echo ""
    echo "Available backups in ${BACKUP_DIR}:"
    ls -lht "${BACKUP_DIR}"/db_*.gz 2>/dev/null || echo "  (no backups found)"
    exit 1
fi

# ---------------------------------------------------------------------------
# Validate DATABASE_URL
# ---------------------------------------------------------------------------
if [ -z "${DATABASE_URL:-}" ]; then
    log "ERROR" "DATABASE_URL environment variable is not set."
    exit 1
fi

# ---------------------------------------------------------------------------
# Confirmation prompt
# ---------------------------------------------------------------------------
echo "============================================================================="
echo "  WARNING: DATABASE RESTORE"
echo "============================================================================="
echo ""
echo "  This operation will OVERWRITE the current database with the backup."
echo ""
echo "  Backup file : ${BACKUP_FILE}"
echo "  Database URL : ${DATABASE_URL}"
echo ""
echo "  For PostgreSQL: the existing database will be DROPPED and recreated."
echo "  For SQLite:     the existing database file will be REPLACED."
echo ""
echo "  THIS ACTION CANNOT BE UNDONE."
echo ""
echo "============================================================================="
echo ""
read -r -p "Are you sure you want to proceed? Type 'yes' to confirm: " CONFIRMATION

if [ "${CONFIRMATION}" != "yes" ]; then
    log "INFO" "Restore cancelled by user."
    exit 0
fi

log "INFO" "Starting database restore from ${BACKUP_FILE}"

# ---------------------------------------------------------------------------
# Detect database type and run restore
# ---------------------------------------------------------------------------
if echo "${DATABASE_URL}" | grep -qi "^postgresql\|^postgres"; then
    # -----------------------------------------------------------------------
    # PostgreSQL Restore
    # -----------------------------------------------------------------------
    log "INFO" "Detected PostgreSQL database."

    # Parse DATABASE_URL components
    DB_CONN="${DATABASE_URL#*://}"

    # Extract user:password
    DB_USERPASS="${DB_CONN%%@*}"
    DB_USER="${DB_USERPASS%%:*}"
    DB_PASS="${DB_USERPASS#*:}"

    # Extract host:port/dbname
    DB_HOSTPATH="${DB_CONN#*@}"
    DB_HOSTPORT="${DB_HOSTPATH%%/*}"
    DB_NAME="${DB_HOSTPATH#*/}"

    # Remove query params from DB_NAME if any
    DB_NAME="${DB_NAME%%\?*}"

    DB_HOST="${DB_HOSTPORT%%:*}"
    DB_PORT="${DB_HOSTPORT#*:}"

    # If port was not specified, default to 5432
    if [ "${DB_PORT}" = "${DB_HOST}" ]; then
        DB_PORT="5432"
    fi

    export PGPASSWORD="${DB_PASS}"

    log "INFO" "Dropping existing database '${DB_NAME}'..."
    # Terminate active connections before dropping
    psql -h "${DB_HOST}" -p "${DB_PORT}" -U "${DB_USER}" -d postgres -c \
        "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = '${DB_NAME}' AND pid <> pg_backend_pid();" \
        > /dev/null 2>&1 || true

    dropdb -h "${DB_HOST}" -p "${DB_PORT}" -U "${DB_USER}" --if-exists "${DB_NAME}"
    log "INFO" "Database '${DB_NAME}' dropped."

    log "INFO" "Recreating database '${DB_NAME}'..."
    createdb -h "${DB_HOST}" -p "${DB_PORT}" -U "${DB_USER}" -O "${DB_USER}" "${DB_NAME}"
    log "INFO" "Database '${DB_NAME}' recreated."

    log "INFO" "Restoring from backup..."
    if gunzip -c "${BACKUP_FILE}" | psql -h "${DB_HOST}" -p "${DB_PORT}" -U "${DB_USER}" -d "${DB_NAME}" --quiet; then
        unset PGPASSWORD
        log "INFO" "PostgreSQL restore completed successfully."
    else
        unset PGPASSWORD
        log "ERROR" "PostgreSQL restore failed."
        exit 1
    fi

elif echo "${DATABASE_URL}" | grep -qi "^sqlite"; then
    # -----------------------------------------------------------------------
    # SQLite Restore
    # -----------------------------------------------------------------------
    log "INFO" "Detected SQLite database."

    # Parse SQLite path from DATABASE_URL
    SQLITE_PATH="${DATABASE_URL#sqlite*:///}"

    # Create a safety backup of the current database if it exists
    if [ -f "${SQLITE_PATH}" ]; then
        SAFETY_BACKUP="${SQLITE_PATH}.pre-restore.bak"
        log "INFO" "Creating safety backup of current database: ${SAFETY_BACKUP}"
        cp "${SQLITE_PATH}" "${SAFETY_BACKUP}"
    fi

    log "INFO" "Restoring SQLite database to '${SQLITE_PATH}'"

    # Ensure the target directory exists
    TARGET_DIR="$(dirname "${SQLITE_PATH}")"
    mkdir -p "${TARGET_DIR}"

    # Decompress and copy
    if gunzip -c "${BACKUP_FILE}" > "${SQLITE_PATH}"; then
        log "INFO" "SQLite restore completed successfully."

        # Verify the restored file is a valid SQLite database
        if sqlite3 "${SQLITE_PATH}" "PRAGMA integrity_check;" > /dev/null 2>&1; then
            log "INFO" "Integrity check passed."
            # Remove safety backup on success
            rm -f "${SQLITE_PATH}.pre-restore.bak"
        else
            log "ERROR" "Integrity check failed on restored database."
            # Restore from safety backup
            if [ -f "${SQLITE_PATH}.pre-restore.bak" ]; then
                log "INFO" "Rolling back to previous database."
                mv "${SQLITE_PATH}.pre-restore.bak" "${SQLITE_PATH}"
            fi
            exit 1
        fi
    else
        log "ERROR" "SQLite restore failed."
        # Restore from safety backup
        if [ -f "${SQLITE_PATH}.pre-restore.bak" ]; then
            log "INFO" "Rolling back to previous database."
            mv "${SQLITE_PATH}.pre-restore.bak" "${SQLITE_PATH}"
        fi
        exit 1
    fi

else
    log "ERROR" "Unsupported database type in DATABASE_URL: ${DATABASE_URL}"
    log "ERROR" "Supported prefixes: postgresql://, postgres://, sqlite:///"
    exit 1
fi

log "INFO" "Database restore finished successfully."
exit 0
