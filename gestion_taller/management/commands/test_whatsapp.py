"""
Comando Django para probar el envío de mensajes por WhatsApp
Uso: python manage.py test_whatsapp
"""

from django.core.management.base import BaseCommand
from gestion_taller.whatsapp_service import WhatsAppService
from gestion_taller.taller_config import TallerConfig
from gestion_taller.models import ConfiguracionTaller, Conductor
from gestion_taller.services.multi_taller_messaging import MultiTallerMessagingService
from gestion_taller.whatsapp_service import enviar_recordatorio_whatsapp
import os


class Command(BaseCommand):
    help = 'Prueba el envío de mensajes por WhatsApp usando WASenderAPI'

    def add_arguments(self, parser):
        parser.add_argument(
            '--conductor-id',
            type=int,
            help='ID del conductor para enviar mensaje de prueba'
        )
        parser.add_argument(
            '--telefono',
            type=str,
            help='Número de teléfono para enviar mensaje de prueba (formato: +57xxxxxxxxxx)'
        )
        parser.add_argument(
            '--mensaje',
            type=str,
            default='🔧 Mensaje de prueba desde el sistema del taller mecánico. ¡Todo funciona correctamente! ✅',
            help='Mensaje personalizado para enviar'
        )
        parser.add_argument(
            '--taller-codigo',
            type=str,
            help='Código del taller para usar su configuración específica'
        )
        parser.add_argument(
            '--tipo-mensaje',
            type=str,
            choices=['simple', 'bienvenida', 'recordatorio', 'promocion', 'diagnostico', 'vehiculo_listo'],
            default='simple',
            help='Tipo de mensaje a enviar (usa plantillas predefinidas)'
        )
        parser.add_argument(
            '--cliente-nombre',
            type=str,
            help='Nombre del cliente (dueño del taller) para usar su información'
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('🚀 Iniciando prueba de WhatsApp...'))
        
        # Verificar configuración
        if not self._verificar_configuracion():
            return
        
        # Inicializar servicio multi-taller
        taller_codigo = options.get('taller_codigo')
        cliente_nombre = options.get('cliente_nombre')
        
        # Si se especifica un cliente, buscarlo
        cliente = None
        if cliente_nombre:
            try:
                from gestion_taller.models import Cliente
                cliente = Cliente.objects.get(nombre__icontains=cliente_nombre)
                self.stdout.write(f'👤 Usando cliente: {cliente.nombre}')
            except Cliente.DoesNotExist:
                self.stdout.write(
                    self.style.WARNING(f'⚠️ Cliente "{cliente_nombre}" no encontrado')
                )
            except Cliente.MultipleObjectsReturned:
                self.stdout.write(
                    self.style.WARNING(f'⚠️ Múltiples clientes encontrados con "{cliente_nombre}"')
                )
        
        messaging_service = MultiTallerMessagingService(
            taller_codigo=taller_codigo,
            cliente=cliente
        )
        
        # Mostrar información del taller
        self._mostrar_info_taller(messaging_service)
        
        # Probar según parámetros
        if options['conductor_id']:
            self._probar_con_conductor(options, messaging_service)
        elif options['telefono']:
            self._probar_con_telefono(options, messaging_service)
        else:
            self._probar_configuracion_general(messaging_service)

    def _verificar_configuracion(self):
        """Verifica que las variables de entorno estén configuradas"""
        token = os.environ.get('WASENDER_API_TOKEN')
        instance_id = os.environ.get('WASENDER_INSTANCE_ID')
        
        if not token:
            self.stdout.write(
                self.style.ERROR('❌ WASENDER_API_TOKEN no está configurado en las variables de entorno')
            )
            self.stdout.write('💡 Agrega: WASENDER_API_TOKEN=tu_token_aqui')
            return False
        
        # Instance ID es opcional para algunos proveedores como wasenderapi.com
        if instance_id:
            self.stdout.write(self.style.SUCCESS(f'✅ Configuración completa: Token y Instance ID'))
        else:
            self.stdout.write(self.style.SUCCESS(f'✅ Configuración básica: Solo Token (compatible con wasenderapi.com)'))
            
        return True

    def _mostrar_info_taller(self, messaging_service):
        """Muestra información del taller seleccionado"""
        taller_info = messaging_service.get_taller_info()
        
        self.stdout.write(self.style.SUCCESS('\n=== INFORMACIÓN DEL TALLER ==='))
        self.stdout.write(f'🏢 Nombre: {taller_info["nombre"]}')
        self.stdout.write(f'📞 Teléfono: {taller_info["telefono"]}')
        self.stdout.write(f'📧 Email: {taller_info["email"]}')
        self.stdout.write(f'📍 Dirección: {taller_info["direccion"]}')
        self.stdout.write(f'⏰ Horarios: {taller_info["horarios"]}')
        
        # Mostrar número de WhatsApp
        whatsapp_num = messaging_service.get_whatsapp_number()
        self.stdout.write(f'📱 WhatsApp: {whatsapp_num}')
        
        if messaging_service.taller_config:
            self.stdout.write(f'🌐 Código: {messaging_service.taller_config.codigo}')
        
        if messaging_service.cliente:
            self.stdout.write(f'👤 Dueño: {messaging_service.cliente.nombre}')
        
        self.stdout.write('')

    def _probar_con_conductor(self, options, messaging_service):
        """Prueba envío con un conductor específico"""
        conductor_id = options['conductor_id']
        tipo_mensaje = options['tipo_mensaje']
        
        try:
            conductor = Conductor.objects.get(id=conductor_id)
            self.stdout.write(f'📱 Enviando mensaje a conductor: {conductor.nombre}')
            
            if not conductor.telefono:
                self.stdout.write(
                    self.style.WARNING(f'⚠️ El conductor {conductor.nombre} no tiene teléfono registrado')
                )
                return
            
            # Preparar datos para el mensaje
            datos_mensaje = {
                'nombre_cliente': conductor.nombre,
                'vehiculo': 'Vehículo de prueba',
                'placa': 'ABC-123',
                'servicio': 'Mantenimiento general',
                'fecha': 'Hoy'
            }
            
            # Usar servicio multi-taller
            if tipo_mensaje == 'simple':
                mensaje = options.get('mensaje', 'Mensaje de prueba')
                resultado = messaging_service.enviar_mensaje(
                    conductor.telefono, 'generico', 
                    {'mensaje': mensaje}, 'whatsapp'
                )
            else:
                resultado = messaging_service.enviar_mensaje(
                    conductor.telefono, tipo_mensaje, 
                    datos_mensaje, 'whatsapp'
                )
            
            if resultado['whatsapp'].get('success'):
                self.stdout.write(
                    self.style.SUCCESS(f'✅ Mensaje enviado exitosamente a {conductor.nombre} ({conductor.telefono})')
                )
            else:
                self.stdout.write(
                    self.style.ERROR(f'❌ Error enviando mensaje: {resultado["whatsapp"].get("error")}')
                )
                
        except Conductor.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f'❌ No se encontró conductor con ID: {conductor_id}')
            )

    def _probar_con_telefono(self, options, messaging_service):
        """Prueba envío con un número de teléfono específico"""
        telefono = options['telefono']
        tipo_mensaje = options['tipo_mensaje']
        
        self.stdout.write(f'📱 Enviando mensaje a teléfono: {telefono}')
        
        # Preparar datos para el mensaje
        datos_mensaje = {
            'nombre_cliente': 'Cliente de prueba',
            'vehiculo': 'Toyota Corolla 2020',
            'placa': 'XYZ-789',
            'servicio': 'Cambio de aceite',
            'fecha': 'Hoy',
            'costo_total': '45.00'
        }
        
        # Usar servicio multi-taller
        if tipo_mensaje == 'simple':
            mensaje = options.get('mensaje', 'Mensaje de prueba')
            resultado = messaging_service.enviar_mensaje(
                telefono, 'generico', 
                {'mensaje': mensaje}, 'whatsapp'
            )
        else:
            resultado = messaging_service.enviar_mensaje(
                telefono, tipo_mensaje, 
                datos_mensaje, 'whatsapp'
            )
        
        if resultado['whatsapp'].get('success'):
            self.stdout.write(
                self.style.SUCCESS(f'✅ Mensaje enviado exitosamente a {telefono}')
            )
        else:
            self.stdout.write(
                self.style.ERROR(f'❌ Error enviando mensaje: {resultado["whatsapp"].get("error")}')
            )

    def _probar_configuracion_general(self, messaging_service):
        """Muestra información general y talleres disponibles"""
        self.stdout.write(self.style.SUCCESS('📋 Información del sistema:'))
        
        # Mostrar clientes (dueños de taller) disponibles
        from gestion_taller.models import Cliente
        clientes = Cliente.objects.all()
        
        if clientes.exists():
            self.stdout.write('\n👤 Clientes/Dueños de taller:')
            for cliente in clientes:
                config_info = ''
                if hasattr(cliente, 'configuracion_taller') and cliente.configuracion_taller:
                    config = cliente.configuracion_taller
                    principal = ' 🌟 PRINCIPAL' if config.es_principal else ''
                    config_info = f' (Config: {config.codigo}){principal}'
                
                self.stdout.write(f'  - {cliente.nombre}{config_info}')
                self.stdout.write(f'    Teléfono: {cliente.telefono or "No registrado"}')
                self.stdout.write(f'    Email: {cliente.correo or "No registrado"}')
        else:
            self.stdout.write(self.style.WARNING('⚠️ No hay clientes registrados'))
        
        # Mostrar configuraciones de taller adicionales
        talleres_config = ConfiguracionTaller.objects.filter(activo=True)
        if talleres_config.exists():
            self.stdout.write('\n🏢 Configuraciones de taller:')
            for taller in talleres_config:
                principal = ' 🌟 PRINCIPAL' if taller.es_principal else ''
                self.stdout.write(f'  - {taller.nombre} ({taller.codigo}){principal}')
                self.stdout.write(f'    WhatsApp: {taller.get_telefono_whatsapp()}')
        
        # Mostrar conductores con teléfono
        conductores_con_telefono = Conductor.objects.exclude(telefono__isnull=True).exclude(telefono='')
        
        if conductores_con_telefono.exists():
            self.stdout.write('\n📞 Conductores con teléfono registrado:')
            for conductor in conductores_con_telefono:
                self.stdout.write(f'  • ID: {conductor.id} | {conductor.nombre} | {conductor.telefono}')
            
            self.stdout.write('\n💡 Para probar con un conductor específico:')
            self.stdout.write('   python manage.py test_whatsapp --conductor-id 1')
        else:
            self.stdout.write('⚠️ No hay conductores con teléfono registrado')
        
        self.stdout.write('\n💡 Para probar con un número específico:')
        self.stdout.write('   python manage.py test_whatsapp --telefono "+573001234567"')
        
        self.stdout.write('\n💡 Para mensaje personalizado:')
        self.stdout.write('   python manage.py test_whatsapp --telefono "+573001234567" --mensaje "Hola desde el taller"')
        
        self.stdout.write('\n🔧 Estado del servicio WhatsApp:')
        
        # Verificar directamente si el servicio está habilitado
        if messaging_service._is_whatsapp_enabled():
            self.stdout.write('   ✅ WhatsApp habilitado y configurado')
            
            # Mostrar información del taller activo
            taller_info = messaging_service.get_taller_info()
            self.stdout.write(f'   🏢 Taller activo: {taller_info["nombre"]}')
            self.stdout.write(f'   📱 Número WhatsApp: {messaging_service.get_whatsapp_number()}')
            
            # Verificar token
            from django.conf import settings
            import os
            token = getattr(settings, 'WASENDER_API_TOKEN', None) or os.environ.get('WASENDER_API_TOKEN')
            if token:
                self.stdout.write('   ✅ Token API configurado')
            else:
                self.stdout.write('   ❌ Token API no encontrado')
        else:
            self.stdout.write('   ❌ Servicio WhatsApp no habilitado')
