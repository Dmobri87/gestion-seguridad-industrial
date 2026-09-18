#!/usr/bin/env bash
set -euo pipefail

# Bootstrap base para VM OCI (Ubuntu 22.04/24.04)
# Ejecutar como root:
#   sudo bash scripts/oci/bootstrap-vm.sh

if [[ "${EUID}" -ne 0 ]]; then
  echo "Run as root: sudo bash scripts/oci/bootstrap-vm.sh"
  exit 1
fi

DEPLOY_USER="${DEPLOY_USER:-deploy}"
DEPLOY_HOME="/home/${DEPLOY_USER}"

echo "[1/8] System update"
apt-get update -y
apt-get upgrade -y

echo "[2/8] Base packages"
apt-get install -y \
  ca-certificates \
  curl \
  gnupg \
  lsb-release \
  git \
  ufw \
  fail2ban \
  jq \
  unzip

echo "[3/8] Docker repo"
install -m 0755 -d /etc/apt/keyrings
if [[ ! -f /etc/apt/keyrings/docker.asc ]]; then
  curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
  chmod a+r /etc/apt/keyrings/docker.asc
fi

ARCH="$(dpkg --print-architecture)"
CODENAME="$(. /etc/os-release && echo "${VERSION_CODENAME}")"
echo \
  "deb [arch=${ARCH} signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu ${CODENAME} stable" \
  > /etc/apt/sources.list.d/docker.list

echo "[4/8] Docker install"
apt-get update -y
apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
systemctl enable docker
systemctl start docker

echo "[5/8] Deploy user"
if ! id -u "${DEPLOY_USER}" >/dev/null 2>&1; then
  adduser --disabled-password --gecos "" "${DEPLOY_USER}"
fi
usermod -aG docker "${DEPLOY_USER}"

echo "[6/8] Firewall"
ufw --force default deny incoming
ufw --force default allow outgoing
ufw allow 22/tcp
ufw allow 80/tcp
ufw allow 443/tcp
ufw --force enable

echo "[7/8] Fail2ban"
systemctl enable fail2ban
systemctl restart fail2ban

echo "[8/8] Project folder"
mkdir -p /opt/gestion_proyectos
chown -R "${DEPLOY_USER}:${DEPLOY_USER}" /opt/gestion_proyectos
chown -R "${DEPLOY_USER}:${DEPLOY_USER}" "${DEPLOY_HOME}"

cat <<EOF
Bootstrap complete.
Next steps:
1) SSH as ${DEPLOY_USER}
2) Clone repo into /opt/gestion_proyectos
3) Create .env from .env.production.template
4) Deploy:
   docker compose -f docker-compose.yml -f docker-compose.oci.yml up -d --build
EOF
