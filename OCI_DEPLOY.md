# OCI Deployment (Free Tier) - Secure Guide

This guide deploys the current project to Oracle Cloud (OCI) on a single VM.

## 1) OCI resources to create (manual in OCI Console)

1. Create one Compute instance (`Ampere A1` preferred).
2. Attach a public IP.
3. Network Security List / NSG rules:
   - Allow inbound `22/tcp` from your admin IP.
   - Allow inbound `80/tcp` from `0.0.0.0/0`.
   - Allow inbound `443/tcp` from `0.0.0.0/0`.
4. Keep DB/Redis private (do not open `5432` or `6379`).
5. Point DNS `A` record (`app.yourdomain.com`) to VM public IP.

## 2) Bootstrap VM

SSH to VM as `ubuntu` (or default OCI user), then:

```bash
sudo apt-get update -y
sudo apt-get install -y git
git clone <YOUR_REPO_URL> /opt/gestion_proyectos
cd /opt/gestion_proyectos
sudo bash scripts/oci/bootstrap-vm.sh
```

Logout and login as `deploy`.

## 3) Production env file

Inside VM:

```bash
cd /opt/gestion_proyectos
cp .env.production.template .env
nano .env
```

Set at least:
- `SECRET_KEY` (strong random key, >= 64 chars)
- `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB`
- `DATABASE_URL`
- `REDIS_PASSWORD`, `REDIS_URL`
- `BACKEND_CORS_ORIGINS` to your real domain
- SMTP variables (if using email features)
- `DEBUG=False`

## 4) Deploy app

```bash
cd /opt/gestion_proyectos
bash scripts/oci/deploy.sh
```

This uses:
- `docker-compose.yml`
- `docker-compose.oci.yml` (hides backend public port)

## 5) HTTPS (recommended)

Option A (simpler): terminate TLS at OCI Load Balancer.
Option B (VM certbot): install certbot on VM and terminate at nginx proxy.

If you choose VM certbot with your current project stack, use your existing scripts:

```bash
sudo bash scripts/init-letsencrypt.sh app.yourdomain.com your@email.com
```

## 6) Backups

Enable daily DB backups:

```bash
docker compose -f docker-compose.yml -f docker-compose.backup.yml up -d backup
docker compose -f docker-compose.yml -f docker-compose.backup.yml logs -f backup
```

## 7) Updates

For each release:

```bash
cd /opt/gestion_proyectos
bash scripts/oci/update.sh
```

## 8) Security checklist

- SSH key auth only.
- `ufw` enabled (`22`, `80`, `443` only).
- `fail2ban` running.
- DB/Redis not internet-exposed.
- `DEBUG=False`.
- Strong secrets in `.env`.
- TLS active (`https://`).

