# Lecciones Aprendidas — Gestión GAE

Archivo de patrones de error y sus correcciones. Se actualiza tras cada corrección del usuario.

---

## 2026-04-06

### Deploy frontend en Docker con imágenes no cacheadas
**Error**: `docker build` falla con TLS timeout al intentar `FROM nginx:alpine` cuando la imagen no está en caché local.
**Causa**: Docker Hub no siempre es accesible desde Oracle OCI sin caché previa.
**Corrección**: Construir el bundle localmente (`npm run build`) y copiar el `dist/` directamente al contenedor con `docker cp` + `nginx -s reload`.
**Regla**: Antes de hacer `docker compose build` en el servidor, verificar que las imágenes base estén cacheadas localmente con `docker images`. Si no, usar build local + deploy manual del dist.

### Directorio incorrecto para docker compose
**Error**: `docker compose up -d backend` falla porque el proyecto compose del servidor es `app_gae` en `/home/ubuntu/app_gae/`, no `gestion_proyectos`.
**Causa**: El proyecto fue iniciado originalmente desde un directorio diferente al del repositorio local.
**Corrección**: Verificar con `docker inspect <container> | grep 'com.docker.compose.project'` para conocer el directorio y proyecto correcto antes de cualquier operación compose.
**Regla**: Siempre verificar el label `com.docker.compose.project.working_dir` antes de usar `docker compose` en el servidor.

### Esquema del endpoint de autenticación
**Error**: Login con `{"email":..., "password":...}` falla; verify-otp con `{"otp":...}` falla.
**Causa**: El endpoint `/auth/login` usa OAuth2 form data (`username` + `password`), y `/auth/verify-otp` usa `otp_code` (no `otp`).
**Corrección**: Usar `-d 'username=...&password=...'` para login y `{"email":..., "otp_code":...}` para verify-otp.
**Regla**: Revisar los schemas Pydantic (`OTPVerifyRequest`) antes de probar endpoints de auth vía curl.

### Deploy frontend: SCP al host ≠ dentro del contenedor Docker
**Error**: `docker exec gae_frontend tar -xzf /tmp/file.tar.gz` lee el `/tmp/` DENTRO del contenedor, no el `/tmp/` del host donde SCP subió el archivo.
**Causa**: SCP sube al filesystem del host Ubuntu. Docker exec opera en el namespace del contenedor.
**Corrección**: Secuencia correcta: `scp → host /tmp/` → `docker cp host:/tmp/ → container:/tmp/` → `docker exec tar -xzf`
**Regla**: SIEMPRE usar `docker cp <host_path> <container>:<container_path>` antes de cualquier `docker exec` que lea archivos copiados con SCP.

### Vite build cache genera hash antiguo
**Error**: Después de modificar un archivo, `npm run build` puede generar el mismo hash de chunk si la caché de Vite está activa, resultando en el bundle antiguo en `dist/`.
**Corrección**: Limpiar caché antes del build con `rm -rf node_modules/.vite dist && npm run build`.
**Regla**: Para deploys críticos, SIEMPRE limpiar caché Vite antes de hacer build (`rm -rf node_modules/.vite dist`).
