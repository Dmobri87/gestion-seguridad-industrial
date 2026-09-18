#!/bin/bash
# =============================================================================
# renew-ssl.sh
# SSL Certificate Renewal Script
# Sistema de Gestion de Seguridad Industrial
# =============================================================================
#
# Usage:
#   sudo bash scripts/renew-ssl.sh
#
# This script:
#   1. Attempts to renew SSL certificates via certbot
#   2. Tests the nginx configuration
#   3. Reloads nginx if the config is valid
#   4. Logs the result
#
# Designed to be run manually or via cron for certificate maintenance.
# =============================================================================

set -euo pipefail

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
LOG_FILE="/var/log/letsencrypt/renewal.log"
TIMESTAMP="$(date '+%Y-%m-%d %H:%M:%S')"

# ---------------------------------------------------------------------------
# Logging helpers
# ---------------------------------------------------------------------------
log() {
    local message="[${TIMESTAMP}] $1"
    echo "${message}"
    echo "${message}" >> "${LOG_FILE}" 2>/dev/null || true
}

# Ensure log directory exists
mkdir -p "$(dirname "${LOG_FILE}")"

# ---------------------------------------------------------------------------
# Check for root privileges
# ---------------------------------------------------------------------------
if [ "$(id -u)" -ne 0 ]; then
    log "ERROR: This script must be run as root (use sudo)."
    exit 1
fi

# ---------------------------------------------------------------------------
# Step 1: Attempt certificate renewal
# ---------------------------------------------------------------------------
log "Starting SSL certificate renewal..."

if certbot renew --quiet; then
    log "Certificate renewal completed successfully."
else
    CERTBOT_EXIT=$?
    log "WARNING: certbot renew exited with code ${CERTBOT_EXIT}."
    log "This may mean no certificates are due for renewal (which is normal)."
fi

# ---------------------------------------------------------------------------
# Step 2: Test nginx configuration
# ---------------------------------------------------------------------------
log "Testing nginx configuration..."

if nginx -t 2>&1; then
    log "Nginx configuration test passed."
else
    log "ERROR: Nginx configuration test failed. Skipping reload."
    log "ERROR: Please check the nginx configuration manually."
    exit 1
fi

# ---------------------------------------------------------------------------
# Step 3: Reload nginx
# ---------------------------------------------------------------------------
log "Reloading nginx to apply renewed certificates..."

if nginx -s reload; then
    log "Nginx reloaded successfully."
else
    log "ERROR: Failed to reload nginx."
    exit 1
fi

# ---------------------------------------------------------------------------
# Done
# ---------------------------------------------------------------------------
log "SSL certificate renewal process completed successfully."
