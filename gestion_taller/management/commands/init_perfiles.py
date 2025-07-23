from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from gestion_taller.models import Cliente, PerfilUsuario

class Command(BaseCommand):
    help = 'Crea PerfilUsuario para todos los usuarios que no lo tengan, asociándolos automáticamente al primer Cliente.'

    def handle(self, *args, **kwargs):
        cliente = Cliente.objects.first()
        if not cliente:
            self.stdout.write(self.style.ERROR('No hay clientes en la base de datos.'))
            return
        created_count = 0
        for user in User.objects.all():
            if not hasattr(user, 'perfilusuario'):
                PerfilUsuario.objects.create(user=user, cliente=cliente)
                created_count += 1
        if created_count:
            self.stdout.write(self.style.SUCCESS(f'Perfiles creados para {created_count} usuarios.'))
        else:
            self.stdout.write(self.style.WARNING('Todos los usuarios ya tienen perfil.'))
