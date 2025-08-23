"""
Comando para gestionar múltiples talleres
"""
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from gestion_taller.models import Cliente, ConfiguracionTaller
import json


class Command(BaseCommand):
    help = 'Gestiona la configuración de múltiples talleres'

    def add_arguments(self, parser):
        parser.add_argument(
            '--accion',
            type=str,
            choices=['crear', 'listar', 'actualizar', 'eliminar', 'principal'],
            help='Acción a realizar',
            required=True
        )
        
        parser.add_argument(
            '--codigo',
            type=str,
            help='Código del taller'
        )
        
        parser.add_argument(
            '--nombre',
            type=str,
            help='Nombre del taller'
        )
        
        parser.add_argument(
            '--telefono',
            type=str,
            help='Teléfono principal del taller'
        )
        
        parser.add_argument(
            '--whatsapp',
            type=str,
            help='Número de WhatsApp (opcional)'
        )
        
        parser.add_argument(
            '--email',
            type=str,
            help='Email del taller'
        )
        
        parser.add_argument(
            '--pais',
            type=str,
            default='Ecuador',
            help='País del taller'
        )
        
        parser.add_argument(
            '--cliente-id',
            type=int,
            help='ID del cliente (dueño) para asociar con esta configuración de taller'
        )
        
        parser.add_argument(
            '--direccion',
            type=str,
            help='Dirección del taller'
        )
        
        parser.add_argument(
            '--ciudad',
            type=str,
            help='Ciudad del taller'
        )

    def handle(self, *args, **options):
        accion = options['accion']
        
        if accion == 'listar':
            self.listar_talleres()
        elif accion == 'crear':
            self.crear_taller(options)
        elif accion == 'actualizar':
            self.actualizar_taller(options)
        elif accion == 'eliminar':
            self.eliminar_taller(options)
        elif accion == 'principal':
            self.establecer_principal(options)

    def listar_talleres(self):
        """Lista todos los talleres configurados"""
        talleres = ConfiguracionTaller.objects.all().order_by('nombre')
        
        if not talleres.exists():
            self.stdout.write(
                self.style.WARNING('No hay talleres configurados.')
            )
            return
        
        self.stdout.write(
            self.style.SUCCESS('\n=== TALLERES CONFIGURADOS ===\n')
        )
        
        for taller in talleres:
            estado = "✅ ACTIVO" if taller.activo else "❌ INACTIVO"
            principal = " 🌟 PRINCIPAL" if taller.es_principal else ""
            
            self.stdout.write(f"📍 {taller.nombre} ({taller.codigo}){principal}")
            self.stdout.write(f"   Estado: {estado}")
            self.stdout.write(f"   📞 {taller.telefono_principal}")
            
            if taller.telefono_whatsapp:
                self.stdout.write(f"   💬 WhatsApp: {taller.telefono_whatsapp}")
            
            self.stdout.write(f"   📧 {taller.email}")
            self.stdout.write(f"   📍 {taller.direccion}, {taller.ciudad}")
            self.stdout.write(f"   ⏰ {taller.horarios}")
            
            # Mostrar cliente asociado
            cliente = getattr(taller, 'cliente_taller', None)
            if cliente:
                self.stdout.write(f"   👤 Cliente: {cliente.nombre}")
            
            self.stdout.write("")

    def crear_taller(self, options):
        """Crea un nuevo taller"""
        codigo = options.get('codigo')
        nombre = options.get('nombre')
        telefono = options.get('telefono')
        email = options.get('email')
        direccion = options.get('direccion')
        ciudad = options.get('ciudad', 'Quito')
        cliente_id = options.get('cliente_id')
        
        if not all([codigo, nombre, telefono, email, direccion]):
            raise CommandError(
                'Para crear un taller necesitas: --codigo, --nombre, --telefono, --email, --direccion'
            )
        
        # Verificar que el código no exista
        if ConfiguracionTaller.objects.filter(codigo=codigo).exists():
            raise CommandError(f'Ya existe un taller con el código: {codigo}')
        
        try:
            with transaction.atomic():
                # Crear configuración del taller
                taller = ConfiguracionTaller.objects.create(
                    codigo=codigo,
                    nombre=nombre,
                    telefono_principal=telefono,
                    telefono_whatsapp=options.get('whatsapp', ''),
                    email=email,
                    direccion=direccion,
                    ciudad=ciudad,
                    es_principal=not ConfiguracionTaller.objects.exists()  # Primer taller es principal
                )
                
                # Asociar con cliente si se especifica
                if cliente_id:
                    try:
                        cliente = Cliente.objects.get(id=cliente_id)
                        cliente.configuracion = taller
                        cliente.save()
                        self.stdout.write(
                            self.style.SUCCESS(f'Taller asociado con cliente: {cliente.nombre}')
                        )
                    except Cliente.DoesNotExist:
                        self.stdout.write(
                            self.style.WARNING(f'Cliente con ID {cliente_id} no encontrado')
                        )
                
                self.stdout.write(
                    self.style.SUCCESS(f'✅ Taller "{nombre}" creado exitosamente!')
                )
                
                if taller.es_principal:
                    self.stdout.write(
                        self.style.SUCCESS('🌟 Establecido como taller principal')
                    )
                
        except Exception as e:
            raise CommandError(f'Error creando taller: {str(e)}')

    def actualizar_taller(self, options):
        """Actualiza un taller existente"""
        codigo = options.get('codigo')
        
        if not codigo:
            raise CommandError('Necesitas especificar --codigo del taller a actualizar')
        
        try:
            taller = ConfiguracionTaller.objects.get(codigo=codigo)
        except ConfiguracionTaller.DoesNotExist:
            raise CommandError(f'Taller con código "{codigo}" no encontrado')
        
        # Actualizar campos especificados
        campos_actualizados = []
        
        if options.get('nombre'):
            taller.nombre = options['nombre']
            campos_actualizados.append('nombre')
        
        if options.get('telefono'):
            taller.telefono_principal = options['telefono']
            campos_actualizados.append('teléfono principal')
        
        if options.get('whatsapp'):
            taller.telefono_whatsapp = options['whatsapp']
            campos_actualizados.append('WhatsApp')
        
        if options.get('email'):
            taller.email = options['email']
            campos_actualizados.append('email')
        
        if options.get('direccion'):
            taller.direccion = options['direccion']
            campos_actualizados.append('dirección')
        
        if options.get('ciudad'):
            taller.ciudad = options['ciudad']
            campos_actualizados.append('ciudad')
        
        if campos_actualizados:
            taller.save()
            self.stdout.write(
                self.style.SUCCESS(
                    f'✅ Taller "{taller.nombre}" actualizado: {", ".join(campos_actualizados)}'
                )
            )
        else:
            self.stdout.write(
                self.style.WARNING('No se especificaron campos para actualizar')
            )

    def eliminar_taller(self, options):
        """Elimina un taller"""
        codigo = options.get('codigo')
        
        if not codigo:
            raise CommandError('Necesitas especificar --codigo del taller a eliminar')
        
        try:
            taller = ConfiguracionTaller.objects.get(codigo=codigo)
        except ConfiguracionTaller.DoesNotExist:
            raise CommandError(f'Taller con código "{codigo}" no encontrado')
        
        if taller.es_principal:
            raise CommandError(
                'No puedes eliminar el taller principal. '
                'Primero establece otro taller como principal.'
            )
        
        nombre = taller.nombre
        taller.delete()
        
        self.stdout.write(
            self.style.SUCCESS(f'✅ Taller "{nombre}" eliminado exitosamente')
        )

    def establecer_principal(self, options):
        """Establece un taller como principal"""
        codigo = options.get('codigo')
        
        if not codigo:
            raise CommandError('Necesitas especificar --codigo del taller')
        
        try:
            taller = ConfiguracionTaller.objects.get(codigo=codigo)
        except ConfiguracionTaller.DoesNotExist:
            raise CommandError(f'Taller con código "{codigo}" no encontrado')
        
        # Desmarcar otros talleres como principales
        ConfiguracionTaller.objects.filter(es_principal=True).update(es_principal=False)
        
        # Marcar este como principal
        taller.es_principal = True
        taller.save()
        
        self.stdout.write(
            self.style.SUCCESS(f'🌟 Taller "{taller.nombre}" establecido como principal')
        )
