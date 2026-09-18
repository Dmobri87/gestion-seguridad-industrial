# Checklist Produccion

## Seguridad y secretos

- [ ] Cambiar `DOMAIN` y dominios reales en `nginx/nginx.prod.conf`.
- [ ] Confirmar `DEBUG=False` en `.env.production`.
- [ ] Confirmar `SECRET_KEY` fuerte y unica.
- [ ] Confirmar `POSTGRES_PASSWORD` fuerte y unica.
- [ ] Confirmar `REDIS_PASSWORD` fuerte y unica.
- [ ] Configurar SMTP real (`SMTP_HOST`, `SMTP_USER`, `SMTP_PASSWORD`, `SMTP_FROM`).
- [ ] Verificar `ALLOWED_HOSTS` y `CORS_ORIGINS` con dominios reales.
- [ ] Asegurar que `.env` no este versionado ni compartido.

## Base de datos

- [ ] Crear backup previo.
- [ ] Ejecutar migraciones Alembic antes de levantar backend (produccion no usa `create_all`).
- [ ] Verificar conectividad con `DATABASE_URL`.

## Despliegue

- [ ] Instalar Docker Desktop y validar:
  - `docker --version`
  - `docker compose version`
- [ ] Levantar stack:
  - `docker compose up -d --force-recreate`
- [ ] Ver estado:
  - `docker compose ps`
  - `docker compose logs --tail=200 backend frontend`

## Validaciones funcionales

- [ ] `GET /health` responde 200.
- [ ] Login 2FA funciona con correo real.
- [ ] Descarga de evidencias funciona via URL firmada temporal.
- [ ] Accesos entre organizaciones bloqueados correctamente.
- [ ] Flujo de aprobacion (Supervisor/Coordinador/Admin) validado.

## Operacion continua

- [ ] Programar backup diario de BD.
- [ ] Definir retencion de logs.
- [ ] Activar monitoreo y alertas (CPU, RAM, error rate).
- [ ] Documentar procedimiento de rotacion trimestral de secretos.

