#!/bin/bash
# =============================================================================
# init-letsencrypt.sh
# SSL Certificate Initialization Script using Let's Encrypt (Certbot)
# Sistema de Gestion de Seguridad Industrial
# =============================================================================
#
# Usage:
#   sudo bash scripts/init-letsencrypt.sh yourdomain.com [email@example.com]
#
# This script:
#   1. Creates required directories
#   2. Generates a temporary self-signed certificate (so nginx can start)
#   3. Requests a real certificate from Let's Encrypt via certbot
#   4. Sets up automatic renewal via cron
#
# =============================================================================

set -euo pipefail

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
DOMAIN="${1:-}"
EMAIL="${2:-}"
WEBROOT="/var/www/certbot"
LETSENCRYPT_DIR="/etc/letsencrypt"
LIVE_DIR="${LETSENCRYPT_DIR}/live/${DOMAIN}"
RSA_KEY_SIZE=4096

# ---------------------------------------------------------------------------
# Color helpers
# ---------------------------------------------------------------------------
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log_info()  { echo -e "${GREEN}[INFO]${NC}  $1"; }
log_warn()  { echo -e "${YELLOW}[WARN]${NC}  $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# ---------------------------------------------------------------------------
# Validate arguments
# ---------------------------------------------------------------------------
if [ -z "${DOMAIN}" ]; then
    log_error "Domain name is required."
    echo ""
    echo "Usage: sudo bash $0 <domain> [email]"
    echo "  domain  - Your domain name (e.g., example.com)"
    echo "  email   - (Optional) Email for Let's Encrypt notifications"
    echo ""
    echo "Examples:"
    echo "  sudo bash $0 seguridad.example.com"
    echo "  sudo bash $0 seguridad.example.com admin@example.com"
    exit 1
fi

# Check for root privileges
if [ "$(id -u)" -ne 0 ]; then
    log_error "This script must be run as root (use sudo)."
    exit 1
fi

log_info "Starting SSL certificate initialization for: ${DOMAIN}"

# ---------------------------------------------------------------------------
# Step 1: Create required directories
# ---------------------------------------------------------------------------
log_info "Creating required directories..."

mkdir -p "${WEBROOT}/.well-known/acme-challenge"
mkdir -p "${LETSENCRYPT_DIR}/live/${DOMAIN}"
mkdir -p "/var/log/letsencrypt"

log_info "Directories created successfully."

# ---------------------------------------------------------------------------
# Step 2: Generate temporary self-signed certificate
# ---------------------------------------------------------------------------
# Nginx requires SSL certificates to exist before it can start.
# We generate a temporary self-signed cert so nginx can boot up and
# serve the ACME challenge for the real certificate request.
# ---------------------------------------------------------------------------
log_info "Generating temporary self-signed certificate..."

if [ ! -f "${LIVE_DIR}/fullchain.pem" ]; then
    openssl req -x509 -nodes -newkey rsa:${RSA_KEY_SIZE} \
        -days 1 \
        -keyout "${LIVE_DIR}/privkey.pem" \
        -out "${LIVE_DIR}/fullchain.pem" \
        -subj "/CN=${DOMAIN}/O=Temp/C=US" \
        2>/dev/null

    # Create a copy as chain.pem for OCSP stapling config
    cp "${LIVE_DIR}/fullchain.pem" "${LIVE_DIR}/chain.pem"

    log_info "Temporary self-signed certificate generated."
else
    log_warn "Certificates already exist at ${LIVE_DIR}. Skipping self-signed generation."
fi

# ---------------------------------------------------------------------------
# Step 3: Ensure nginx is running (to serve ACME challenge)
# ---------------------------------------------------------------------------
log_info "Checking if nginx is running..."

if command -v nginx &>/dev/null; then
    if nginx -t 2>/dev/null; then
        nginx -s reload 2>/dev/null || nginx 2>/dev/null || true
        log_info "Nginx is running and ready to serve ACME challenges."
    else
        log_warn "Nginx config test failed. Attempting to start anyway..."
        nginx 2>/dev/null || true
    fi
else
    log_warn "Nginx not found in PATH. Ensure nginx is running before certbot verification."
fi

# Give nginx a moment to start/reload
sleep 2

# ---------------------------------------------------------------------------
# Step 4: Request real certificate from Let's Encrypt
# ---------------------------------------------------------------------------
log_info "Requesting SSL certificate from Let's Encrypt..."

# Build certbot command
CERTBOT_CMD="certbot certonly --webroot"
CERTBOT_CMD+=" --webroot-path ${WEBROOT}"
CERTBOT_CMD+=" -d ${DOMAIN}"
CERTBOT_CMD+=" -d www.${DOMAIN}"
CERTBOT_CMD+=" --rsa-key-size ${RSA_KEY_SIZE}"
CERTBOT_CMD+=" --agree-tos"
CERTBOT_CMD+=" --non-interactive"
CERTBOT_CMD+=" --force-renewal"

if [ -n "${EMAIL}" ]; then
    CERTBOT_CMD+=" --email ${EMAIL}"
else
    CERTBOT_CMD+=" --register-unsafely-without-email"
    log_warn "No email provided. Registering without email (you won't receive renewal warnings)."
fi

# Execute certbot
if eval "${CERTBOT_CMD}"; then
    log_info "SSL certificate obtained successfully!"
else
    log_error "Failed to obtain SSL certificate from Let's Encrypt."
    log_error "Ensure that:"
    log_error "  1. Your domain (${DOMAIN}) points to this server's IP"
    log_error "  2. Port 80 is open and accessible from the internet"
    log_error "  3. Nginx is running and serving the ACME challenge"
    log_error ""
    log_error "The temporary self-signed certificate is still in place."
    log_error "Nginx will continue to run with the self-signed cert."
    exit 1
fi

# ---------------------------------------------------------------------------
# Step 5: Reload nginx with the real certificate
# ---------------------------------------------------------------------------
log_info "Reloading nginx with the new certificate..."

if nginx -t 2>/dev/null; then
    nginx -s reload
    log_info "Nginx reloaded successfully with the new SSL certificate."
else
    log_error "Nginx configuration test failed after certificate installation."
    exit 1
fi

# ---------------------------------------------------------------------------
# Step 6: Set up automatic renewal via cron
# ---------------------------------------------------------------------------
log_info "Setting up automatic SSL certificate renewal..."

CRON_JOB="0 */12 * * * /usr/bin/certbot renew --quiet --deploy-hook 'nginx -s reload' >> /var/log/letsencrypt/renewal.log 2>&1"
RENEW_SCRIPT="/etc/cron.d/certbot-renew"

# Write the cron job
cat > "${RENEW_SCRIPT}" <<CRON
# Let's Encrypt SSL certificate auto-renewal
# Runs twice daily (every 12 hours) as recommended by Let's Encrypt
SHELL=/bin/bash
PATH=/usr/local/sbin:/usr/local/bin:/sbin:/bin:/usr/sbin:/usr/bin

${CRON_JOB}
CRON

chmod 644 "${RENEW_SCRIPT}"
log_info "Cron job installed at ${RENEW_SCRIPT} (runs twice daily)."

# ---------------------------------------------------------------------------
# Done
# ---------------------------------------------------------------------------
echo ""
log_info "============================================================"
log_info "  SSL certificate setup complete for ${DOMAIN}"
log_info "============================================================"
log_info ""
log_info "  Certificate:  ${LETSENCRYPT_DIR}/live/${DOMAIN}/fullchain.pem"
log_info "  Private Key:  ${LETSENCRYPT_DIR}/live/${DOMAIN}/privkey.pem"
log_info "  Chain:        ${LETSENCRYPT_DIR}/live/${DOMAIN}/chain.pem"
log_info ""
log_info "  Auto-renewal: Enabled (twice daily via cron)"
log_info "  Renewal logs: /var/log/letsencrypt/renewal.log"
log_info ""
log_info "  Your site should now be accessible at:"
log_info "    https://${DOMAIN}"
log_info "============================================================"
