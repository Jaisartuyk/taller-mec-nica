#!/bin/bash
set -e

echo "==> Ejecutando migraciones de base de datos..."
# --fake-initial permite que si una tabla ya existe en la base de datos (como gestion_taller_cita),
# Django la marque como aplicada sin fallar.
python manage.py migrate --fake-initial --noinput

echo "==> Recopilando archivos estáticos..."
python manage.py collectstatic --noinput

echo "==> Iniciando servidor Gunicorn en puerto ${PORT:-8000}..."
exec gunicorn --bind 0.0.0.0:${PORT:-8000} taller_mecanica.wsgi:application
