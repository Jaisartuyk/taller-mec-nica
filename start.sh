#!/bin/bash

echo "==> Sincronizando migraciones de base de datos..."
# 1. Si la tabla de Citas ya existe en la BD pero no está registrada la migración 0022, marcarla como aplicada (fake)
python manage.py migrate gestion_taller 0022 --fake --noinput || true

# 2. Correr las demás migraciones normalmente (y continuar si alguna ya fue aplicada)
python manage.py migrate --fake-initial --noinput || true

echo "==> Recopilando archivos estáticos..."
python manage.py collectstatic --noinput

echo "==> Iniciando servidor Gunicorn en puerto ${PORT:-8000}..."
exec gunicorn --bind 0.0.0.0:${PORT:-8000} taller_mecanica.wsgi:application
