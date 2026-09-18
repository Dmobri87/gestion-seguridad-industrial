#!/bin/bash
# =============================================================================
# Database Backup Script
# Sistema de Gestion de Seguridad Industrial y Salud Ocupacional
# =============================================================================
# Supports both PostgreSQL and SQLite backups.
# Detects the database type from the DATABASE_URL environment variable.
#
# Usage:
#   DATABASE_URL=postgresql://user:pass@host:5432/dbname ./backup-db.sh
#   DATABASE_URL=sqlite:///./seguridad_industrial.db ./backup-db.sh
#
# Environment variables:
#   DATABASE_URL       - Required. Connection string for the database.
#   BACKUP_DIR         - Optional. Directory to store backups (default: /backups).
#   BACKUP_RETENTION   - Optional. Number of daily backups to keep (default: 30).
#   BACKUP_LOG         - Optional. Log file path (default: BACKUP_DIR/backup.log).
# =============================================================================

set -euo pipefail

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
BACKUP_DIR="${BACKUP_DIR:-/backups}"
BACKUP_RETENTION="${BACKUP_RETENTION:-30}"
BACKUP_LOG="${BACKUP_LOG:-${BACKUP_DIR}/backup.log}"
TIMESTAMP="$(date +%Y-%m-%d_%H-%M-%S)"

# ---------------------------------------------------------------------------
# Logging helper
# ---------------------------------------------------------------------------
log() {
    local level="$1"
    shift
    local message="$*"
    local entry="[$(date '+%Y-%m-%d %H:%M:%S')] [${level}] ${message}"
    echo "${entry}"
    echo "${entry}" >> "${BACKUP_LOG}"
}

# ---------------------------------------------------------------------------
# Ensure backup directory exists
# ---------------------------------------------------------------------------
mkdir -p "${BACKUP_DIR}"
touch "${BACKUP_LOG}"

# ---------------------------------------------------------------------------
# Validate DATABASE_URL
# ---------------------------------------------------------------------------
if [ -z "${DATABASE_URL:-}" ]; then
    log "ERROR" "DATABASE_URL environment variable is not set."
    exit 1
fi

log "INFO" "Starting database backup at ${TIMESTAMP}"

# ---------------------------------------------------------------------------
# Detect database type and run backup
# ---------------------------------------------------------------------------
if echo "${DATABASE_URL}" | grep -qi "^postgresql\|^postgres"; then
    # -----------------------------------------------------------------------
    # PostgreSQL Backup
    # -----------------------------------------------------------------------
    log "INFO" "Detected PostgreSQL database."

    BACKUP_FILE="${BACKUP_DIR}/db_${TIMESTAMP}.sql.gz"

    # Parse DATABASE_URL components
    # Format: postgresql://user:password@host:port/dbname
    # Remove the scheme prefix
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

    log "INFO" "Backing up PostgreSQL database '${DB_NAME}' on ${DB_HOST}:${DB_PORT}"

    export PGPASSWORD="${DB_PASS}"

    if pg_dump \
        -h "${DB_HOST}" \
        -p "${DB_PORT}" \
        -U "${DB_USER}" \
        -d "${DB_NAME}" \
        --no-owner \
        --no-privileges \
        -F plain \
        | gzip > "${BACKUP_FILE}"; then

        unset PGPASSWORD
        FILESIZE=$(du -h "${BACKUP_FILE}" | cut -f1)
        log "INFO" "PostgreSQL backup completed successfully: ${BACKUP_FILE} (${FILESIZE})"
    else
        unset PGPASSWORD
        log "ERROR" "PostgreSQL backup failed."
        rm -f "${BACKUP_FILE}"
        exit 1
    fi

elif echo "${DATABASE_URL}" | grep -qi "^sqlite"; then
    # -----------------------------------------------------------------------
    # SQLite Backup
    # -----------------------------------------------------------------------
    log "INFO" "Detected SQLite database."

    # Parse SQLite path from DATABASE_URL
    # Formats: sqlite:///./path/to/db.sqlite  or  sqlite:////absolute/path/db.sqlite
    SQLITE_PATH="${DATABASE_URL#sqlite*:///}"

    if [ ! -f "${SQLITE_PATH}" ]; then
        log "ERROR" "SQLite database file not found: ${SQLITE_PATH}"
        exit 1
    fi

    BACKUP_FILE_RAW="${BACKUP_DIR}/db_${TIMESTAMP}.sqlite"
    BACKUP_FILE="${BACKUP_DIR}/db_${TIMESTAMP}.sqlite.gz"

    log "INFO" "Backing up SQLite database '${SQLITE_PATH}'"

    if sqlite3 "${SQLITE_PATH}" ".backup '${BACKUP_FILE_RAW}'"; then
        # Compress the backup
        if gzip "${BACKUP_FILE_RAW}"; then
            FILESIZE=$(du -h "${BACKUP_FILE}" | cut -f1)
            log "INFO" "SQLite backup completed successfully: ${BACKUP_FILE} (${FILESIZE})"
        else
            log "ERROR" "Failed to compress SQLite backup."
            rm -f "${BACKUP_FILE_RAW}" "${BACKUP_FILE}"
            exit 1
        fi
    else
        log "ERROR" "SQLite backup failed."
        rm -f "${BACKUP_FILE_RAW}"
        exit 1
    fi

else
    log "ERROR" "Unsupported database type in DATABASE_URL: ${DATABASE_URL}"
    log "ERROR" "Supported prefixes: postgresql://, postgres://, sqlite:///"
    exit 1
fi

# ---------------------------------------------------------------------------
# Cleanup old backups (keep last BACKUP_RETENTION daily backups)
# ---------------------------------------------------------------------------
log "INFO" "Cleaning up old backups (retaining last ${BACKUP_RETENTION})..."

DELETED_COUNT=0

# List backup files sorted by modification time (oldest first), skip the newest N
BACKUP_FILES=$(ls -1t "${BACKUP_DIR}"/db_*.gz 2>/dev/null || true)
TOTAL_BACKUPS=$(echo "${BACKUP_FILES}" | grep -c . 2>/dev/null || echo 0)

if [ "${TOTAL_BACKUPS}" -gt "${BACKUP_RETENTION}" ]; then
    FILES_TO_DELETE=$(echo "${BACKUP_FILES}" | tail -n +"$((BACKUP_RETENTION + 1))")
    for old_file in ${FILES_TO_DELETE}; do
        rm -f "${old_file}"
        log "INFO" "Deleted old backup: ${old_file}"
        DELETED_COUNT=$((DELETED_COUNT + 1))
    done
fi

log "INFO" "Cleanup complete. Deleted ${DELETED_COUNT} old backup(s). Total backups: $((TOTAL_BACKUPS - DELETED_COUNT))"
log "INFO" "Backup process finished successfully."

exit 0
