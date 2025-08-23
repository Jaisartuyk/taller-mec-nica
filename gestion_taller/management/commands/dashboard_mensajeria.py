"""
Comando Django para mostrar dashboard de métricas de mensajería
Uso: python manage.py dashboard_mensajeria
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db.models import Count, Q
from datetime import datetime, timedelta
from gestion_taller.models import Conductor, RecordatorioMantenimiento
from gestion_taller.taller_config import taller_config
import os


class Command(BaseCommand):
    help = 'Muestra dashboard con métricas de mensajería del taller'

    def add_arguments(self, parser):
        parser.add_argument(
            '--periodo',
            choices=['hoy', 'semana', 'mes', 'trimestre'],
            default='semana',
            help='Período para mostrar métricas (por defecto: semana)'
        )
        parser.add_argument(
            '--detallado',
            action='store_true',
            help='Mostrar información detallada'
        )
        parser.add_argument(
            '--export',
            type=str,
            help='Exportar métricas a archivo CSV'
        )

    def handle(self, *args, **options):
        periodo = options['periodo']
        detallado = options['detallado']
        export_file = options['export']
        
        self.stdout.write(self.style.SUCCESS('📊 DASHBOARD DE MENSAJERÍA'))
        self.stdout.write('='*60)
        
        # Calcular fechas según período
        fecha_inicio = self._get_fecha_inicio(periodo)
        fecha_fin = timezone.now()
        
        self.stdout.write(f'📅 Período: {fecha_inicio.strftime("%d/%m/%Y")} - {fecha_fin.strftime("%d/%m/%Y")}')
        
        # Mostrar métricas generales
        self._show_general_metrics()
        
        # Mostrar métricas de conductores
        self._show_conductor_metrics()
        
        # Mostrar métricas de recordatorios
        self._show_recordatorio_metrics(fecha_inicio, fecha_fin)
        
        # Mostrar estado de canales
        self._show_channel_status()
        
        # Mostrar recomendaciones
        self._show_recommendations()
        
        if detallado:
            self._show_detailed_info()
        
        if export_file:
            self._export_metrics(export_file, fecha_inicio, fecha_fin)

    def _get_fecha_inicio(self, periodo):
        """Calcula fecha de inicio según período"""
        now = timezone.now()
        
        if periodo == 'hoy':
            return now.replace(hour=0, minute=0, second=0, microsecond=0)
        elif periodo == 'semana':
            return now - timedelta(days=7)
        elif periodo == 'mes':
            return now - timedelta(days=30)
        elif periodo == 'trimestre':
            return now - timedelta(days=90)
        
        return now - timedelta(days=7)

    def _show_general_metrics(self):
        """Muestra métricas generales del sistema"""
        self.stdout.write('\n🎯 MÉTRICAS GENERALES')
        self.stdout.write('-'*30)
        
        # Total de conductores
        total_conductores = Conductor.objects.count()
        conductores_con_telefono = Conductor.objects.exclude(
            Q(telefono__isnull=True) | Q(telefono='')
        ).count()
        conductores_con_telegram = Conductor.objects.exclude(
            Q(telegram_chat_id__isnull=True) | Q(telegram_chat_id='')
        ).count()
        
        self.stdout.write(f'👥 Total conductores: {total_conductores}')
        self.stdout.write(f'📱 Con WhatsApp: {conductores_con_telefono} ({self._percentage(conductores_con_telefono, total_conductores)}%)')
        self.stdout.write(f'🤖 Con Telegram: {conductores_con_telegram} ({self._percentage(conductores_con_telegram, total_conductores)}%)')
        
        # Cobertura dual
        conductores_dual = Conductor.objects.exclude(
            Q(telefono__isnull=True) | Q(telefono='')
        ).exclude(
            Q(telegram_chat_id__isnull=True) | Q(telegram_chat_id='')
        ).count()
        
        self.stdout.write(f'🔄 Con ambos canales: {conductores_dual} ({self._percentage(conductores_dual, total_conductores)}%)')

    def _show_conductor_metrics(self):
        """Muestra métricas de conductores"""
        self.stdout.write('\n👥 ANÁLISIS DE CONDUCTORES')
        self.stdout.write('-'*30)
        
        # Conductores por canal disponible
        solo_whatsapp = Conductor.objects.exclude(
            Q(telefono__isnull=True) | Q(telefono='')
        ).filter(
            Q(telegram_chat_id__isnull=True) | Q(telegram_chat_id='')
        ).count()
        
        solo_telegram = Conductor.objects.exclude(
            Q(telegram_chat_id__isnull=True) | Q(telegram_chat_id='')
        ).filter(
            Q(telefono__isnull=True) | Q(telefono='')
        ).count()
        
        sin_contacto = Conductor.objects.filter(
            Q(telefono__isnull=True) | Q(telefono='')
        ).filter(
            Q(telegram_chat_id__isnull=True) | Q(telegram_chat_id='')
        ).count()
        
        self.stdout.write(f'📱 Solo WhatsApp: {solo_whatsapp}')
        self.stdout.write(f'🤖 Solo Telegram: {solo_telegram}')
        self.stdout.write(f'❌ Sin contacto: {sin_contacto}')
        
        if sin_contacto > 0:
            self.stdout.write(f'⚠️ {sin_contacto} conductores no pueden recibir notificaciones')

    def _show_recordatorio_metrics(self, fecha_inicio, fecha_fin):
        """Muestra métricas de recordatorios"""
        self.stdout.write('\n🔔 RECORDATORIOS DE MANTENIMIENTO')
        self.stdout.write('-'*30)
        
        # Recordatorios en el período
        recordatorios_periodo = RecordatorioMantenimiento.objects.filter(
            fecha_creacion__range=[fecha_inicio, fecha_fin]
        )
        
        total_recordatorios = recordatorios_periodo.count()
        recordatorios_notificados = recordatorios_periodo.filter(notificado=True).count()
        recordatorios_pendientes = recordatorios_periodo.filter(notificado=False).count()
        
        self.stdout.write(f'📋 Total recordatorios: {total_recordatorios}')
        self.stdout.write(f'✅ Notificados: {recordatorios_notificados} ({self._percentage(recordatorios_notificados, total_recordatorios)}%)')
        self.stdout.write(f'⏳ Pendientes: {recordatorios_pendientes}')
        
        # Recordatorios próximos (7 días)
        fecha_limite = timezone.now().date() + timedelta(days=7)
        recordatorios_proximos = RecordatorioMantenimiento.objects.filter(
            fecha_proximo__lte=fecha_limite,
            notificado=False
        ).count()
        
        if recordatorios_proximos > 0:
            self.stdout.write(f'🚨 Recordatorios próximos (7 días): {recordatorios_proximos}')
        
        # Recordatorios urgentes (vencidos)
        recordatorios_urgentes = RecordatorioMantenimiento.objects.filter(
            fecha_proximo__lt=timezone.now().date(),
            notificado=False
        ).count()
        
        if recordatorios_urgentes > 0:
            self.stdout.write(f'🚨 URGENTES (vencidos): {recordatorios_urgentes}')

    def _show_channel_status(self):
        """Muestra estado de canales de comunicación"""
        self.stdout.write('\n📡 ESTADO DE CANALES')
        self.stdout.write('-'*30)
        
        # WhatsApp
        if taller_config.is_whatsapp_enabled():
            self.stdout.write('📱 WhatsApp: ✅ Configurado')
            token = os.environ.get('WASENDER_API_TOKEN', '')
            instance = os.environ.get('WASENDER_INSTANCE_ID', '')
            self.stdout.write(f'   Token: {token[:10]}... (configurado)')
            self.stdout.write(f'   Instance: {instance}')
        else:
            self.stdout.write('📱 WhatsApp: ❌ No configurado')
        
        # Telegram
        if taller_config.is_telegram_enabled():
            self.stdout.write('🤖 Telegram: ✅ Configurado')
            token = os.environ.get('TELEGRAM_BOT_TOKEN', '')
            self.stdout.write(f'   Token: {token[:10]}... (configurado)')
        else:
            self.stdout.write('🤖 Telegram: ❌ No configurado')
        
        # Canales disponibles
        channels = taller_config.get_available_channels()
        self.stdout.write(f'🔄 Canales activos: {len(channels)} ({", ".join(channels)})')

    def _show_recommendations(self):
        """Muestra recomendaciones basadas en métricas"""
        self.stdout.write('\n💡 RECOMENDACIONES')
        self.stdout.write('-'*30)
        
        # Analizar cobertura
        total_conductores = Conductor.objects.count()
        sin_contacto = Conductor.objects.filter(
            Q(telefono__isnull=True) | Q(telefono='')
        ).filter(
            Q(telegram_chat_id__isnull=True) | Q(telegram_chat_id='')
        ).count()
        
        if sin_contacto > 0:
            porcentaje_sin_contacto = self._percentage(sin_contacto, total_conductores)
            self.stdout.write(f'📞 {porcentaje_sin_contacto}% de conductores sin datos de contacto')
            self.stdout.write('   → Actualiza información de contacto en el admin')
        
        # Recordatorios pendientes
        recordatorios_pendientes = RecordatorioMantenimiento.objects.filter(
            notificado=False,
            fecha_proximo__lte=timezone.now().date() + timedelta(days=7)
        ).count()
        
        if recordatorios_pendientes > 0:
            self.stdout.write(f'🔔 {recordatorios_pendientes} recordatorios pendientes de envío')
            self.stdout.write('   → Ejecuta: python manage.py verificar_recordatorios')
        
        # Canales no configurados
        if not taller_config.is_whatsapp_enabled():
            self.stdout.write('📱 WhatsApp no configurado')
            self.stdout.write('   → Configura WASENDER_API_TOKEN y WASENDER_INSTANCE_ID')
        
        if not taller_config.is_telegram_enabled():
            self.stdout.write('🤖 Telegram no configurado')
            self.stdout.write('   → Configura TELEGRAM_BOT_TOKEN')
        
        # Sugerencias generales
        self.stdout.write('\n🚀 SUGERENCIAS DE MEJORA:')
        self.stdout.write('• Programa recordatorios automáticos con cron jobs')
        self.stdout.write('• Usa promociones para aumentar engagement')
        self.stdout.write('• Monitorea métricas semanalmente')
        self.stdout.write('• Mantén actualizados los datos de contacto')

    def _show_detailed_info(self):
        """Muestra información detallada"""
        self.stdout.write('\n📋 INFORMACIÓN DETALLADA')
        self.stdout.write('-'*30)
        
        # Top 5 conductores con más vehículos
        from django.db.models import Count
        top_conductores = Conductor.objects.annotate(
            num_vehiculos=Count('vehiculos')
        ).filter(num_vehiculos__gt=0).order_by('-num_vehiculos')[:5]
        
        if top_conductores:
            self.stdout.write('\n🏆 TOP CONDUCTORES (más vehículos):')
            for i, conductor in enumerate(top_conductores, 1):
                contacto = "📱" if conductor.telefono else ""
                contacto += "🤖" if conductor.telegram_chat_id else ""
                self.stdout.write(f'  {i}. {conductor.nombre} - {conductor.num_vehiculos} vehículos {contacto}')
        
        # Tipos de recordatorios más comunes
        tipos_recordatorios = RecordatorioMantenimiento.objects.values('tipo').annotate(
            count=Count('tipo')
        ).order_by('-count')[:5]
        
        if tipos_recordatorios:
            self.stdout.write('\n🔧 TIPOS DE MANTENIMIENTO MÁS COMUNES:')
            for item in tipos_recordatorios:
                self.stdout.write(f'  • {item["tipo"]}: {item["count"]} recordatorios')

    def _export_metrics(self, filename, fecha_inicio, fecha_fin):
        """Exporta métricas a archivo CSV"""
        try:
            import csv
            
            with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                
                # Headers
                writer.writerow(['Métrica', 'Valor', 'Porcentaje', 'Fecha'])
                
                # Datos básicos
                total_conductores = Conductor.objects.count()
                conductores_whatsapp = Conductor.objects.exclude(
                    Q(telefono__isnull=True) | Q(telefono='')
                ).count()
                conductores_telegram = Conductor.objects.exclude(
                    Q(telegram_chat_id__isnull=True) | Q(telegram_chat_id='')
                ).count()
                
                writer.writerow(['Total Conductores', total_conductores, '100%', timezone.now().strftime('%Y-%m-%d')])
                writer.writerow(['Conductores WhatsApp', conductores_whatsapp, f'{self._percentage(conductores_whatsapp, total_conductores)}%', timezone.now().strftime('%Y-%m-%d')])
                writer.writerow(['Conductores Telegram', conductores_telegram, f'{self._percentage(conductores_telegram, total_conductores)}%', timezone.now().strftime('%Y-%m-%d')])
                
                # Recordatorios
                total_recordatorios = RecordatorioMantenimiento.objects.filter(
                    fecha_creacion__range=[fecha_inicio, fecha_fin]
                ).count()
                recordatorios_notificados = RecordatorioMantenimiento.objects.filter(
                    fecha_creacion__range=[fecha_inicio, fecha_fin],
                    notificado=True
                ).count()
                
                writer.writerow(['Total Recordatorios', total_recordatorios, '100%', timezone.now().strftime('%Y-%m-%d')])
                writer.writerow(['Recordatorios Notificados', recordatorios_notificados, f'{self._percentage(recordatorios_notificados, total_recordatorios)}%', timezone.now().strftime('%Y-%m-%d')])
            
            self.stdout.write(self.style.SUCCESS(f'📊 Métricas exportadas a: {filename}'))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Error exportando métricas: {e}'))

    def _percentage(self, parte, total):
        """Calcula porcentaje"""
        if total == 0:
            return 0
        return round((parte / total) * 100, 1)
