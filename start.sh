#!/bin/bash
set -e

echo "==> Ejecutando migraciones de base de datos..."
python manage.py migrate --noinput

echo "==> Recopilando archivos estáticos..."
python manage.py collectstatic --noinput

echo "==> Iniciando servidor Gunicorn en puerto ${PORT:-8000}..."
exec gunicorn --bind 0.0.0.0:${PORT:-8000} taller_mecanica.wsgi:application
