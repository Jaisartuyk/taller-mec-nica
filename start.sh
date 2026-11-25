#!/bin/bash

echo "==> Sincronizando migraciones de base de datos..."
# 1. Marcar como aplicadas (fake) hasta la 0026 porque esas tablas/columnas ya existen en Railway
python manage.py migrate gestion_taller 0026 --fake --noinput || true

# 2. Aplicar las nuevas migraciones (0027 en adelante)
python manage.py migrate --fake-initial --noinput || true

echo "==> Creando superusuario administrador inicial..."
python manage.py crear_superusuario_inicial || true

echo "==> Cargando servicios de catalogo de lubricadora..."
python manage.py cargar_servicios_lubricadora || true

echo "==> Recopilando archivos estáticos..."
python manage.py collectstatic --noinput

echo "==> Iniciando servidor Gunicorn en puerto ${PORT:-8000}..."
exec gunicorn --bind 0.0.0.0:${PORT:-8000} taller_mecanica.wsgi:application
