# Detener y eliminar el contenedor si ya existe
Write-Host "--- Limpiando contenedores antiguos ---" -ForegroundColor Cyan
docker rm -f mi-proyecto-contenedor

# Construir la imagen (opcional, puedes comentarlo si no cambias librerías)
Write-Host "--- Construyendo imagen de Docker ---" -ForegroundColor Cyan
docker build -t gestion-proyectos-app .

# Lanzar el contenedor con volumen para persistencia de base de datos
Write-Host "--- Lanzando proyecto en http://localhost:8080/docs ---" -ForegroundColor Cyan
docker run -d -p 8080:80 -v "${PWD}:/code" --name mi-proyecto-contenedor gestion-proyectos-app

# Esperar un par de segundos y mostrar el estado
Start-Sleep -Seconds 2
docker ps