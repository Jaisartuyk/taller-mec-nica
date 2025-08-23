"""
Comando Django para probar el envío de mensajes por WhatsApp
Uso: python manage.py test_whatsapp
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from gestion_taller.models import Conductor
from gestion_taller.whatsapp_service import WhatsAppService, enviar_recordatorio_whatsapp
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

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('🚀 Iniciando prueba de WhatsApp...'))
        
        # Verificar configuración
        if not self._verificar_configuracion():
            return
        
        # Probar servicio básico
        whatsapp = WhatsAppService()
        
        if options['conductor_id']:
            self._probar_con_conductor(options['conductor_id'], options['mensaje'])
        elif options['telefono']:
            self._probar_con_telefono(options['telefono'], options['mensaje'], whatsapp)
        else:
            self._probar_configuracion_general(whatsapp)

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
            
        if not instance_id:
            self.stdout.write(
                self.style.ERROR('❌ WASENDER_INSTANCE_ID no está configurado en las variables de entorno')
            )
            self.stdout.write('💡 Agrega: WASENDER_INSTANCE_ID=tu_instance_id_aqui')
            return False
            
        self.stdout.write(self.style.SUCCESS('✅ Configuración de WhatsApp verificada'))
        return True

    def _probar_con_conductor(self, conductor_id, mensaje):
        """Prueba envío con un conductor específico"""
        try:
            conductor = Conductor.objects.get(id=conductor_id)
            self.stdout.write(f'📱 Enviando mensaje a conductor: {conductor.nombre}')
            
            if not conductor.telefono:
                self.stdout.write(
                    self.style.WARNING(f'⚠️ El conductor {conductor.nombre} no tiene teléfono registrado')
                )
                return
            
            resultado = enviar_recordatorio_whatsapp(conductor, mensaje)
            
            if resultado.get('success'):
                self.stdout.write(
                    self.style.SUCCESS(f'✅ Mensaje enviado exitosamente a {conductor.nombre} ({conductor.telefono})')
                )
            else:
                self.stdout.write(
                    self.style.ERROR(f'❌ Error enviando mensaje: {resultado.get("error")}')
                )
                
        except Conductor.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f'❌ No se encontró conductor con ID: {conductor_id}')
            )

    def _probar_con_telefono(self, telefono, mensaje, whatsapp):
        """Prueba envío con un número de teléfono específico"""
        self.stdout.write(f'📱 Enviando mensaje a teléfono: {telefono}')
        
        resultado = whatsapp.send_message(telefono, mensaje)
        
        if resultado.get('success'):
            self.stdout.write(
                self.style.SUCCESS(f'✅ Mensaje enviado exitosamente a {telefono}')
            )
        else:
            self.stdout.write(
                self.style.ERROR(f'❌ Error enviando mensaje: {resultado.get("error")}')
            )

    def _probar_configuracion_general(self, whatsapp):
        """Muestra información general y conductores disponibles"""
        self.stdout.write(self.style.SUCCESS('📋 Información del sistema:'))
        
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
        if whatsapp.token and whatsapp.instance_id:
            self.stdout.write('   ✅ Token y Instance ID configurados')
        else:
            self.stdout.write('   ❌ Faltan configuraciones')
