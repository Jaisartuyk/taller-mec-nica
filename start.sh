#!/bin/bash

echo "==> Sincronizando migraciones de base de datos..."
# 1. Solo si 0027 no está registrada aún (pero sus columnas ya existen), marcarla como aplicada sin retroceder migraciones futuras
python manage.py shell -c "from django.db.migrations.recorder import MigrationRecorder; import subprocess; applied = MigrationRecorder.Migration.objects.filter(app='gestion_taller', name='0027_saas_planes_meta_ia').exists(); subprocess.run(['python', 'manage.py', 'migrate', 'gestion_taller', '0027', '--fake', '--noinput']) if not applied else None" || true

# 2. Aplicar todas las migraciones pendientes normalmente (0028 en adelante)
python manage.py migrate --noinput || true

echo "==> Creando superusuario administrador inicial..."
python manage.py crear_superusuario_inicial || true

echo "==> Cargando servicios de catalogo de lubricadora..."
python manage.py cargar_servicios_lubricadora || true

echo "==> Recopilando archivos estáticos..."
python manage.py collectstatic --noinput

echo "==> Iniciando servidor Gunicorn en puerto ${PORT:-8000}..."
exec gunicorn --bind 0.0.0.0:${PORT:-8000} taller_mecanica.wsgi:application
