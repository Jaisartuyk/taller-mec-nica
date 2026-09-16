"""
Comando Django para crear automáticamente un superusuario administrador inicial en Railway
Uso: python manage.py crear_superusuario_inicial
"""

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from gestion_taller.models import Cliente, PerfilUsuario
import os

class Command(BaseCommand):
    help = 'Crea o actualiza el superusuario inicial para administración del taller'

    def handle(self, *args, **options):
        username = os.environ.get('DJANGO_SUPERUSER_USERNAME', 'admin')
        email = os.environ.get('DJANGO_SUPERUSER_EMAIL', 'admin@taller.com')
        password = os.environ.get('DJANGO_SUPERUSER_PASSWORD', 'admin12345')

        # 1. Asegurar o crear el Cliente/Taller inicial
        cliente, _ = Cliente.objects.get_or_create(
            id=1,
            defaults={
                'nombre': 'Taller Mecánico Principal',
                'telefono': '0999999999',
                'correo': email,
                'direccion': 'Matriz Central'
            }
        )

        # 2. Crear o actualizar el superusuario
        user, created = User.objects.get_or_create(username=username, defaults={'email': email})
        user.email = email
        user.is_staff = True
        user.is_superuser = True
        user.set_password(password)
        user.save()

        # 3. Asegurar su PerfilUsuario como Administrador
        perfil, _ = PerfilUsuario.objects.get_or_create(user=user)
        perfil.cliente = cliente
        perfil.rol = 'admin'
        perfil.save()

        if created:
            self.stdout.write(self.style.SUCCESS(f'✅ Superusuario "{username}" creado exitosamente.'))
        else:
            self.stdout.write(self.style.SUCCESS(f'✅ Superusuario "{username}" actualizado exitosamente.'))
