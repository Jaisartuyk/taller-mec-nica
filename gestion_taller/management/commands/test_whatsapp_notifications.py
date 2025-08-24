"""
Comando de management para probar las notificaciones automáticas de WhatsApp
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from gestion_taller.models import Conductor, Vehiculo, OrdenServicio, Cliente
from gestion_taller.notification_service import notification_service
from gestion_taller.signals import notificar_diagnostico_adicional_manual
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Prueba las notificaciones automáticas de WhatsApp del taller'

    def add_arguments(self, parser):
        parser.add_argument(
            '--tipo',
            type=str,
            choices=['conductor', 'vehiculo', 'orden', 'diagnostico', 'recordatorio', 'all'],
            default='all',
            help='Tipo de notificación a probar'
        )
        parser.add_argument(
            '--conductor-id',
            type=int,
            help='ID del conductor para pruebas específicas'
        )
        parser.add_argument(
            '--vehiculo-id',
            type=int,
            help='ID del vehículo para pruebas específicas'
        )
        parser.add_argument(
            '--orden-id',
            type=int,
            help='ID de la orden de servicio para pruebas específicas'
        )

    def handle(self, *args, **options):
        tipo = options['tipo']
        
        self.stdout.write(
            self.style.SUCCESS(f'🚀 Iniciando pruebas de notificaciones WhatsApp - Tipo: {tipo}')
        )
        
        if tipo == 'all' or tipo == 'conductor':
            self.test_notificacion_conductor(options.get('conductor_id'))
        
        if tipo == 'all' or tipo == 'vehiculo':
            self.test_notificacion_vehiculo(options.get('vehiculo_id'))
        
        if tipo == 'all' or tipo == 'orden':
            self.test_notificacion_orden(options.get('orden_id'))
        
        if tipo == 'all' or tipo == 'diagnostico':
            self.test_notificacion_diagnostico(options.get('orden_id'))
        
        if tipo == 'all' or tipo == 'recordatorio':
            self.test_recordatorio_mantenimiento(options.get('conductor_id'), options.get('vehiculo_id'))
        
        self.stdout.write(
            self.style.SUCCESS('✅ Pruebas de notificaciones completadas')
        )

    def test_notificacion_conductor(self, conductor_id=None):
        """Prueba la notificación de nuevo conductor"""
        self.stdout.write('📱 Probando notificación de nuevo conductor...')
        
        try:
            if conductor_id:
                conductor = Conductor.objects.get(id=conductor_id)
            else:
                conductor = Conductor.objects.first()
            
            if not conductor:
                self.stdout.write(
                    self.style.WARNING('⚠️ No se encontró ningún conductor para probar')
                )
                return
            
            # Simular notificación de nuevo conductor
            notification_service.notify_nuevo_conductor(
                conductor=conductor,
                send_to_admin=True
            )
            
            self.stdout.write(
                self.style.SUCCESS(f'✅ Notificación de conductor enviada a: {conductor.nombre}')
            )
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Error probando notificación de conductor: {e}')
            )

    def test_notificacion_vehiculo(self, vehiculo_id=None):
        """Prueba la notificación de nuevo vehículo"""
        self.stdout.write('🚗 Probando notificación de nuevo vehículo...')
        
        try:
            if vehiculo_id:
                vehiculo = Vehiculo.objects.get(id=vehiculo_id)
            else:
                vehiculo = Vehiculo.objects.first()
            
            if not vehiculo:
                self.stdout.write(
                    self.style.WARNING('⚠️ No se encontró ningún vehículo para probar')
                )
                return
            
            # Simular notificación de nuevo vehículo
            notification_service.notify_nuevo_vehiculo(vehiculo=vehiculo)
            
            self.stdout.write(
                self.style.SUCCESS(f'✅ Notificación de vehículo enviada: {vehiculo.marca} {vehiculo.modelo} - {vehiculo.placa}')
            )
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Error probando notificación de vehículo: {e}')
            )

    def test_notificacion_orden(self, orden_id=None):
        """Prueba las notificaciones de orden de servicio"""
        self.stdout.write('📝 Probando notificaciones de orden de servicio...')
        
        try:
            if orden_id:
                orden = OrdenServicio.objects.get(id=orden_id)
            else:
                orden = OrdenServicio.objects.first()
            
            if not orden:
                self.stdout.write(
                    self.style.WARNING('⚠️ No se encontró ninguna orden de servicio para probar')
                )
                return
            
            # 1. Simular notificación de orden creada
            servicios_ejemplo = ['Cambio de aceite', 'Revisión de frenos', 'Diagnóstico general']
            notification_service.notify_orden_creada(
                orden_servicio=orden,
                servicios_solicitados=servicios_ejemplo
            )
            
            self.stdout.write(
                self.style.SUCCESS(f'✅ Notificación de orden creada enviada para orden #{getattr(orden, "numero_orden", "N/A")}')
            )
            
            # 2. Simular notificación de orden en progreso
            notification_service.notify_orden_en_progreso(
                orden_servicio=orden,
                tecnico_asignado='Juan Pérez',
                progreso_actual='Iniciando diagnóstico del motor'
            )
            
            self.stdout.write(
                self.style.SUCCESS(f'✅ Notificación de orden en progreso enviada')
            )
            
            # 3. Simular notificación de orden completada
            servicios_realizados = ['Cambio de aceite 15W-40', 'Revisión completa de frenos', 'Diagnóstico computarizado']
            notification_service.notify_orden_completada(
                conductor=orden.vehiculo.conductor,
                vehiculo=orden.vehiculo,
                orden_servicio=orden,
                servicios_realizados=servicios_realizados,
                total=150.00
            )
            
            self.stdout.write(
                self.style.SUCCESS(f'✅ Notificación de orden completada enviada')
            )
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Error probando notificaciones de orden: {e}')
            )

    def test_notificacion_diagnostico(self, orden_id=None):
        """Prueba la notificación de diagnóstico adicional"""
        self.stdout.write('🔍 Probando notificación de diagnóstico adicional...')
        
        try:
            if orden_id:
                orden = OrdenServicio.objects.get(id=orden_id)
            else:
                orden = OrdenServicio.objects.first()
            
            if not orden:
                self.stdout.write(
                    self.style.WARNING('⚠️ No se encontró ninguna orden de servicio para probar')
                )
                return
            
            # Simular diagnóstico adicional
            problema = """Durante la revisión encontramos que las pastillas de freno están muy desgastadas (2mm restantes). 
            
Por seguridad, recomendamos cambiarlas inmediatamente junto con el líquido de frenos que está contaminado."""
            
            notificar_diagnostico_adicional_manual(
                orden_servicio=orden,
                problema_encontrado=problema,
                costo_adicional=85.00
            )
            
            self.stdout.write(
                self.style.SUCCESS(f'✅ Notificación de diagnóstico adicional enviada')
            )
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Error probando notificación de diagnóstico: {e}')
            )

    def test_recordatorio_mantenimiento(self, conductor_id=None, vehiculo_id=None):
        """Prueba el recordatorio de mantenimiento"""
        self.stdout.write('🔧 Probando recordatorio de mantenimiento...')
        
        try:
            if conductor_id:
                conductor = Conductor.objects.get(id=conductor_id)
            else:
                conductor = Conductor.objects.first()
            
            if vehiculo_id:
                vehiculo = Vehiculo.objects.get(id=vehiculo_id)
            elif conductor:
                vehiculo = conductor.vehiculos.first()
            else:
                vehiculo = Vehiculo.objects.first()
            
            if not conductor or not vehiculo:
                self.stdout.write(
                    self.style.WARNING('⚠️ No se encontró conductor o vehículo para probar recordatorio')
                )
                return
            
            # Crear un recordatorio simulado
            class RecordatorioSimulado:
                def __init__(self):
                    self.tipo = 'Cambio de aceite'
                    self.kilometraje_proximo = vehiculo.kilometraje + 5000
                    self.fecha_proximo = timezone.now().date()
            
            recordatorio = RecordatorioSimulado()
            
            # Probar diferentes escenarios de días restantes
            escenarios = [
                (-5, "VENCIDO"),
                (1, "URGENTE"),
                (7, "PRÓXIMO"),
                (15, "PROGRAMADO")
            ]
            
            for dias_restantes, tipo_urgencia in escenarios:
                self.stdout.write(f'  📅 Probando recordatorio {tipo_urgencia} ({dias_restantes} días)...')
                
                notification_service.notify_recordatorio_mantenimiento(
                    conductor=conductor,
                    vehiculo=vehiculo,
                    recordatorio=recordatorio,
                    dias_restantes=dias_restantes
                )
                
                self.stdout.write(
                    self.style.SUCCESS(f'    ✅ Recordatorio {tipo_urgencia} enviado')
                )
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Error probando recordatorio de mantenimiento: {e}')
            )

    def mostrar_estadisticas(self):
        """Muestra estadísticas del sistema"""
        self.stdout.write('\n📊 ESTADÍSTICAS DEL SISTEMA:')
        
        try:
            total_clientes = Cliente.objects.count()
            total_conductores = Conductor.objects.count()
            total_vehiculos = Vehiculo.objects.count()
            total_ordenes = OrdenServicio.objects.count()
            
            conductores_con_telefono = Conductor.objects.exclude(telefono__isnull=True).exclude(telefono='').count()
            
            self.stdout.write(f'  🏢 Clientes/Talleres: {total_clientes}')
            self.stdout.write(f'  👥 Conductores: {total_conductores}')
            self.stdout.write(f'  📱 Conductores con teléfono: {conductores_con_telefono}')
            self.stdout.write(f'  🚗 Vehículos: {total_vehiculos}')
            self.stdout.write(f'  📝 Órdenes de servicio: {total_ordenes}')
            
            if conductores_con_telefono < total_conductores:
                self.stdout.write(
                    self.style.WARNING(f'  ⚠️ {total_conductores - conductores_con_telefono} conductores sin teléfono no recibirán notificaciones')
                )
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Error obteniendo estadísticas: {e}')
            )
