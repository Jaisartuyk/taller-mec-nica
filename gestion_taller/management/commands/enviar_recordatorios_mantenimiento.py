"""
Comando de management para enviar recordatorios de mantenimiento automáticos
Este comando debe ejecutarse diariamente via cron job o tarea programada
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import datetime, timedelta
from gestion_taller.models import RecordatorioMantenimiento, Conductor, Vehiculo
from gestion_taller.signals import enviar_recordatorio_mantenimiento_manual
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Envía recordatorios de mantenimiento automáticos via WhatsApp'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dias-adelanto',
            type=int,
            default=7,
            help='Días de adelanto para enviar recordatorios (default: 7)'
        )
        parser.add_argument(
            '--incluir-vencidos',
            action='store_true',
            help='Incluir recordatorios vencidos'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Simular envío sin enviar mensajes reales'
        )
        parser.add_argument(
            '--cliente-id',
            type=int,
            help='Enviar solo recordatorios de un cliente específico'
        )

    def handle(self, *args, **options):
        dias_adelanto = options['dias_adelanto']
        incluir_vencidos = options['incluir_vencidos']
        dry_run = options['dry_run']
        cliente_id = options.get('cliente_id')
        
        self.stdout.write(
            self.style.SUCCESS(f'🔧 Iniciando envío de recordatorios de mantenimiento')
        )
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING('⚠️ MODO SIMULACIÓN - No se enviarán mensajes reales')
            )
        
        # Obtener recordatorios pendientes
        recordatorios = self.obtener_recordatorios_pendientes(
            dias_adelanto=dias_adelanto,
            incluir_vencidos=incluir_vencidos,
            cliente_id=cliente_id
        )
        
        if not recordatorios:
            self.stdout.write(
                self.style.SUCCESS('✅ No hay recordatorios pendientes para enviar')
            )
            return
        
        self.stdout.write(f'📋 Encontrados {len(recordatorios)} recordatorios para enviar')
        
        # Procesar recordatorios
        enviados = 0
        errores = 0
        
        for recordatorio in recordatorios:
            try:
                resultado = self.procesar_recordatorio(recordatorio, dry_run)
                if resultado:
                    enviados += 1
                    self.stdout.write(
                        self.style.SUCCESS(f'  ✅ {recordatorio.vehiculo.placa} - {recordatorio.tipo}')
                    )
                else:
                    errores += 1
                    self.stdout.write(
                        self.style.WARNING(f'  ⚠️ {recordatorio.vehiculo.placa} - {recordatorio.tipo} (sin teléfono)')
                    )
                    
            except Exception as e:
                errores += 1
                self.stdout.write(
                    self.style.ERROR(f'  ❌ {recordatorio.vehiculo.placa} - Error: {e}')
                )
        
        # Resumen final
        self.stdout.write('\n📊 RESUMEN DEL ENVÍO:')
        self.stdout.write(f'  ✅ Enviados exitosamente: {enviados}')
        self.stdout.write(f'  ❌ Errores o sin teléfono: {errores}')
        self.stdout.write(f'  📱 Total procesados: {len(recordatorios)}')
        
        if not dry_run and enviados > 0:
            self.stdout.write(
                self.style.SUCCESS(f'\n🎯 Recordatorios enviados exitosamente via WhatsApp')
            )

    def obtener_recordatorios_pendientes(self, dias_adelanto, incluir_vencidos, cliente_id):
        """Obtiene los recordatorios que deben enviarse"""
        
        fecha_actual = timezone.now().date()
        fecha_limite = fecha_actual + timedelta(days=dias_adelanto)
        
        # Query base
        query = RecordatorioMantenimiento.objects.filter(
            notificado=False,
            vehiculo__isnull=False
        )
        
        # Filtrar por cliente si se especifica
        if cliente_id:
            query = query.filter(vehiculo__conductor__cliente_id=cliente_id)
        
        # Filtrar por fechas
        if incluir_vencidos:
            # Incluir vencidos y próximos
            query = query.filter(fecha_proximo__lte=fecha_limite)
        else:
            # Solo próximos (no vencidos)
            query = query.filter(
                fecha_proximo__gte=fecha_actual,
                fecha_proximo__lte=fecha_limite
            )
        
        # Ordenar por fecha próxima
        recordatorios = query.order_by('fecha_proximo')
        
        return list(recordatorios)

    def procesar_recordatorio(self, recordatorio, dry_run):
        """Procesa un recordatorio individual"""
        
        vehiculo = recordatorio.vehiculo
        conductor = vehiculo.conductor
        
        if not conductor:
            logger.warning(f'Recordatorio {recordatorio.id}: vehículo sin conductor')
            return False
        
        if not conductor.telefono:
            logger.warning(f'Recordatorio {recordatorio.id}: conductor {conductor.nombre} sin teléfono')
            return False
        
        # Calcular días restantes
        fecha_actual = timezone.now().date()
        dias_restantes = (recordatorio.fecha_proximo - fecha_actual).days
        
        if dry_run:
            # Modo simulación
            self.stdout.write(
                f'    🔍 SIMULACIÓN: {conductor.nombre} ({conductor.telefono}) - {recordatorio.tipo} - {dias_restantes} días'
            )
            return True
        
        try:
            # Enviar recordatorio real
            enviar_recordatorio_mantenimiento_manual(
                conductor=conductor,
                vehiculo=vehiculo,
                recordatorio=recordatorio,
                dias_restantes=dias_restantes
            )
            
            # Marcar como notificado
            recordatorio.notificado = True
            recordatorio.fecha_notificacion = timezone.now()
            recordatorio.save()
            
            logger.info(f'Recordatorio enviado: {conductor.nombre} - {vehiculo.placa} - {recordatorio.tipo}')
            return True
            
        except Exception as e:
            logger.error(f'Error enviando recordatorio {recordatorio.id}: {e}')
            raise

    def mostrar_estadisticas_recordatorios(self, cliente_id=None):
        """Muestra estadísticas de recordatorios"""
        
        self.stdout.write('\n📊 ESTADÍSTICAS DE RECORDATORIOS:')
        
        try:
            query_base = RecordatorioMantenimiento.objects.all()
            
            if cliente_id:
                query_base = query_base.filter(vehiculo__conductor__cliente_id=cliente_id)
                self.stdout.write(f'  🏢 Cliente ID: {cliente_id}')
            
            total_recordatorios = query_base.count()
            pendientes = query_base.filter(notificado=False).count()
            notificados = query_base.filter(notificado=True).count()
            
            # Recordatorios vencidos
            fecha_actual = timezone.now().date()
            vencidos = query_base.filter(
                notificado=False,
                fecha_proximo__lt=fecha_actual
            ).count()
            
            # Próximos 7 días
            fecha_limite = fecha_actual + timedelta(days=7)
            proximos_7_dias = query_base.filter(
                notificado=False,
                fecha_proximo__gte=fecha_actual,
                fecha_proximo__lte=fecha_limite
            ).count()
            
            self.stdout.write(f'  📋 Total recordatorios: {total_recordatorios}')
            self.stdout.write(f'  ⏳ Pendientes: {pendientes}')
            self.stdout.write(f'  ✅ Notificados: {notificados}')
            self.stdout.write(f'  🚨 Vencidos: {vencidos}')
            self.stdout.write(f'  📅 Próximos 7 días: {proximos_7_dias}')
            
            if vencidos > 0:
                self.stdout.write(
                    self.style.WARNING(f'  ⚠️ Hay {vencidos} recordatorios vencidos que requieren atención')
                )
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Error obteniendo estadísticas: {e}')
            )

    def limpiar_recordatorios_antiguos(self, dias_antiguedad=90):
        """Limpia recordatorios muy antiguos ya notificados"""
        
        fecha_limite = timezone.now().date() - timedelta(days=dias_antiguedad)
        
        recordatorios_antiguos = RecordatorioMantenimiento.objects.filter(
            notificado=True,
            fecha_notificacion__lt=fecha_limite
        )
        
        cantidad = recordatorios_antiguos.count()
        
        if cantidad > 0:
            self.stdout.write(f'🧹 Limpiando {cantidad} recordatorios antiguos...')
            recordatorios_antiguos.delete()
            self.stdout.write(
                self.style.SUCCESS(f'✅ Recordatorios antiguos eliminados')
            )
        else:
            self.stdout.write('✅ No hay recordatorios antiguos para limpiar')
