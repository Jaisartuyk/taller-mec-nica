"""
Comando Django para enviar promociones masivas por WhatsApp y/o Telegram
Uso: python manage.py enviar_promocion --titulo "Promoción Especial" --descuento 20
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import datetime, timedelta
from gestion_taller.models import Conductor
from gestion_taller.whatsapp_service import enviar_promocion_whatsapp
import time


class Command(BaseCommand):
    help = 'Envía promociones masivas a conductores por WhatsApp'

    def add_arguments(self, parser):
        parser.add_argument(
            '--titulo',
            type=str,
            required=True,
            help='Título de la promoción'
        )
        parser.add_argument(
            '--descripcion',
            type=str,
            default='¡Aprovecha esta oferta especial en servicios de mantenimiento!',
            help='Descripción de la promoción'
        )
        parser.add_argument(
            '--descuento',
            type=int,
            required=True,
            help='Porcentaje de descuento (ej: 20 para 20%)'
        )
        parser.add_argument(
            '--vigencia-dias',
            type=int,
            default=30,
            help='Días de vigencia de la promoción (por defecto: 30)'
        )
        parser.add_argument(
            '--canal',
            choices=['telegram', 'whatsapp', 'ambos'],
            default='whatsapp',
            help='Canal de envío (por defecto: whatsapp)'
        )
        parser.add_argument(
            '--limite',
            type=int,
            help='Límite de mensajes a enviar (para pruebas)'
        )
        parser.add_argument(
            '--delay',
            type=float,
            default=1.0,
            help='Delay en segundos entre mensajes (por defecto: 1.0)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Simular envío sin enviar mensajes reales'
        )

    def handle(self, *args, **options):
        titulo = options['titulo']
        descripcion = options['descripcion']
        descuento = options['descuento']
        vigencia_dias = options['vigencia_dias']
        canal = options['canal']
        limite = options['limite']
        delay = options['delay']
        dry_run = options['dry_run']
        
        # Calcular fecha de vigencia
        vigencia = timezone.now().date() + timedelta(days=vigencia_dias)
        
        self.stdout.write(self.style.SUCCESS('🎉 Iniciando envío de promoción...'))
        self.stdout.write(f'📢 Título: {titulo}')
        self.stdout.write(f'💰 Descuento: {descuento}%')
        self.stdout.write(f'📅 Vigencia: {vigencia.strftime("%d/%m/%Y")}')
        self.stdout.write(f'📱 Canal: {canal}')
        
        if dry_run:
            self.stdout.write(self.style.WARNING('🧪 MODO SIMULACIÓN - No se enviarán mensajes reales'))
        
        # Obtener conductores con datos de contacto
        if canal == 'whatsapp':
            conductores = Conductor.objects.exclude(telefono__isnull=True).exclude(telefono='')
        elif canal == 'telegram':
            conductores = Conductor.objects.exclude(telegram_chat_id__isnull=True).exclude(telegram_chat_id='')
        else:  # ambos
            conductores = Conductor.objects.filter(
                models.Q(telefono__isnull=False, telefono__ne='') |
                models.Q(telegram_chat_id__isnull=False, telegram_chat_id__ne='')
            )
        
        if limite:
            conductores = conductores[:limite]
        
        total_conductores = conductores.count()
        
        if total_conductores == 0:
            self.stdout.write(self.style.ERROR('❌ No se encontraron conductores con datos de contacto'))
            return
        
        self.stdout.write(f'👥 Conductores a contactar: {total_conductores}')
        
        if not dry_run:
            confirmacion = input('\n¿Continuar con el envío? (s/N): ')
            if confirmacion.lower() not in ['s', 'si', 'sí', 'y', 'yes']:
                self.stdout.write('❌ Envío cancelado')
                return
        
        # Contadores
        enviados_whatsapp = 0
        enviados_telegram = 0
        errores = 0
        
        self.stdout.write('\n🚀 Iniciando envío...\n')
        
        for i, conductor in enumerate(conductores, 1):
            self.stdout.write(f'[{i}/{total_conductores}] Enviando a {conductor.nombre}...', ending='')
            
            if dry_run:
                self.stdout.write(self.style.SUCCESS(' ✅ SIMULADO'))
                enviados_whatsapp += 1
                continue
            
            try:
                # Enviar por WhatsApp
                if canal in ['whatsapp', 'ambos'] and conductor.telefono:
                    resultado = enviar_promocion_whatsapp(
                        conductor, titulo, descripcion, descuento, vigencia
                    )
                    if resultado.get('success'):
                        enviados_whatsapp += 1
                        self.stdout.write(self.style.SUCCESS(' ✅ WhatsApp'))
                    else:
                        errores += 1
                        self.stdout.write(self.style.ERROR(f' ❌ WhatsApp: {resultado.get("error", "Error desconocido")}'))
                
                # Enviar por Telegram (implementar si es necesario)
                if canal in ['telegram', 'ambos'] and conductor.telegram_chat_id:
                    # TODO: Implementar envío por Telegram
                    self.stdout.write(self.style.WARNING(' ⚠️ Telegram: No implementado'))
                
                # Delay entre mensajes para evitar rate limiting
                if delay > 0:
                    time.sleep(delay)
                    
            except Exception as e:
                errores += 1
                self.stdout.write(self.style.ERROR(f' ❌ Error: {e}'))
        
        # Resumen final
        self.stdout.write('\n' + '='*50)
        self.stdout.write(self.style.SUCCESS('📊 RESUMEN DE ENVÍO'))
        self.stdout.write('='*50)
        
        if not dry_run:
            self.stdout.write(f'✅ Enviados por WhatsApp: {enviados_whatsapp}')
            self.stdout.write(f'✅ Enviados por Telegram: {enviados_telegram}')
            self.stdout.write(f'❌ Errores: {errores}')
            self.stdout.write(f'📊 Tasa de éxito: {((enviados_whatsapp + enviados_telegram) / total_conductores * 100):.1f}%')
        else:
            self.stdout.write(f'🧪 Simulación completada para {total_conductores} conductores')
        
        self.stdout.write('\n🎉 ¡Promoción enviada exitosamente!')
        
        # Consejos adicionales
        self.stdout.write('\n💡 Consejos:')
        self.stdout.write('• Monitorea las respuestas de los clientes')
        self.stdout.write('• Prepara al equipo para el aumento de citas')
        self.stdout.write('• Considera enviar recordatorios antes del vencimiento')
        
        if errores > 0:
            self.stdout.write(f'\n⚠️ Se registraron {errores} errores. Revisa los logs para más detalles.')


# Función auxiliar para importar modelos de Django
def get_django_models():
    """Importa modelos de Django de manera segura"""
    try:
        from django.db import models
        return models
    except ImportError:
        return None
