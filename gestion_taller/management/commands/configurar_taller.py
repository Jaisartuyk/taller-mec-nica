"""
Comando Django para configurar información del taller
Uso: python manage.py configurar_taller --setup
"""

from django.core.management.base import BaseCommand
from gestion_taller.taller_config import taller_config, get_full_config
import os
import json


class Command(BaseCommand):
    help = 'Configura información básica del taller mecánico'

    def add_arguments(self, parser):
        parser.add_argument(
            '--setup',
            action='store_true',
            help='Configuración inicial interactiva'
        )
        parser.add_argument(
            '--show-config',
            action='store_true',
            help='Mostrar configuración actual'
        )
        parser.add_argument(
            '--test-channels',
            action='store_true',
            help='Probar canales de comunicación'
        )
        parser.add_argument(
            '--export-config',
            type=str,
            help='Exportar configuración a archivo JSON'
        )

    def handle(self, *args, **options):
        if options['setup']:
            self._setup_interactive()
        elif options['show_config']:
            self._show_config()
        elif options['test_channels']:
            self._test_channels()
        elif options['export_config']:
            self._export_config(options['export_config'])
        else:
            self.stdout.write(self.style.WARNING('Usa --help para ver opciones disponibles'))

    def _setup_interactive(self):
        """Configuración inicial interactiva"""
        self.stdout.write(self.style.SUCCESS('🔧 CONFIGURACIÓN INICIAL DEL TALLER'))
        self.stdout.write('='*50)
        
        # Información básica del negocio
        self.stdout.write('\n📋 INFORMACIÓN BÁSICA DEL NEGOCIO')
        self.stdout.write('-'*30)
        
        nombre = input(f'Nombre del taller [{taller_config.BUSINESS_NAME}]: ').strip()
        if nombre:
            taller_config.BUSINESS_NAME = nombre
        
        telefono = input(f'Teléfono [{taller_config.BUSINESS_PHONE}]: ').strip()
        if telefono:
            taller_config.BUSINESS_PHONE = telefono
        
        email = input(f'Email [{taller_config.BUSINESS_EMAIL}]: ').strip()
        if email:
            taller_config.BUSINESS_EMAIL = email
        
        website = input(f'Sitio web [{taller_config.BUSINESS_WEBSITE}]: ').strip()
        if website:
            taller_config.BUSINESS_WEBSITE = website
        
        direccion = input(f'Dirección [{taller_config.BUSINESS_ADDRESS}]: ').strip()
        if direccion:
            taller_config.BUSINESS_ADDRESS = direccion
        
        horario = input(f'Horario [{taller_config.BUSINESS_HOURS}]: ').strip()
        if horario:
            taller_config.BUSINESS_HOURS = horario
        
        # Configuración de canales
        self.stdout.write('\n📱 CONFIGURACIÓN DE CANALES')
        self.stdout.write('-'*30)
        
        # WhatsApp
        self.stdout.write('WhatsApp (WASenderAPI):')
        token_wa = os.environ.get('WASENDER_API_TOKEN', '')
        instance_wa = os.environ.get('WASENDER_INSTANCE_ID', '')
        
        if not token_wa:
            self.stdout.write('⚠️ WASENDER_API_TOKEN no configurado')
            self.stdout.write('💡 Configura en variables de entorno: WASENDER_API_TOKEN=tu_token')
        else:
            self.stdout.write(f'✅ Token configurado: {token_wa[:10]}...')
        
        if not instance_wa:
            self.stdout.write('⚠️ WASENDER_INSTANCE_ID no configurado')
            self.stdout.write('💡 Configura en variables de entorno: WASENDER_INSTANCE_ID=tu_instance')
        else:
            self.stdout.write(f'✅ Instance ID configurado: {instance_wa}')
        
        # Telegram
        self.stdout.write('\nTelegram Bot:')
        token_tg = os.environ.get('TELEGRAM_BOT_TOKEN', '')
        
        if not token_tg:
            self.stdout.write('⚠️ TELEGRAM_BOT_TOKEN no configurado')
            self.stdout.write('💡 Configura en variables de entorno: TELEGRAM_BOT_TOKEN=tu_token')
        else:
            self.stdout.write(f'✅ Token configurado: {token_tg[:10]}...')
        
        # Configuración de notificaciones
        self.stdout.write('\n🔔 CONFIGURACIÓN DE NOTIFICACIONES')
        self.stdout.write('-'*30)
        
        dias_anticipacion = input('Días de anticipación para recordatorios [7]: ').strip()
        if dias_anticipacion and dias_anticipacion.isdigit():
            taller_config.NOTIFICATION_DEFAULTS['recordatorios_dias_anticipacion'] = int(dias_anticipacion)
        
        canal_preferido = input('Canal preferido (telegram/whatsapp/ambos) [ambos]: ').strip().lower()
        if canal_preferido in ['telegram', 'whatsapp', 'ambos']:
            taller_config.NOTIFICATION_DEFAULTS['canal_preferido'] = canal_preferido
        
        # Resumen
        self.stdout.write('\n✅ CONFIGURACIÓN COMPLETADA')
        self.stdout.write('='*50)
        self._show_config()
        
        # Crear archivo de configuración
        self.stdout.write('\n💾 Guardando configuración...')
        self._save_config_to_file()
        
        self.stdout.write(self.style.SUCCESS('\n🎉 ¡Configuración completada exitosamente!'))
        self.stdout.write('\n💡 Próximos pasos:')
        self.stdout.write('1. Configura las variables de entorno para WhatsApp y Telegram')
        self.stdout.write('2. Prueba los canales: python manage.py configurar_taller --test-channels')
        self.stdout.write('3. Envía tu primera promoción: python manage.py enviar_promocion --titulo "Bienvenida" --descuento 10')

    def _show_config(self):
        """Muestra configuración actual"""
        self.stdout.write(self.style.SUCCESS('📋 CONFIGURACIÓN ACTUAL DEL TALLER'))
        self.stdout.write('='*50)
        
        # Información del negocio
        info = taller_config.get_business_info()
        self.stdout.write('\n🏢 INFORMACIÓN DEL NEGOCIO:')
        for key, value in info.items():
            self.stdout.write(f'  {key.capitalize()}: {value}')
        
        # Canales disponibles
        channels = taller_config.get_available_channels()
        self.stdout.write(f'\n📱 CANALES DISPONIBLES: {", ".join(channels) if channels else "Ninguno"}')
        
        # Estado de WhatsApp
        if taller_config.is_whatsapp_enabled():
            self.stdout.write('  ✅ WhatsApp: Configurado')
        else:
            self.stdout.write('  ❌ WhatsApp: No configurado')
        
        # Estado de Telegram
        if taller_config.is_telegram_enabled():
            self.stdout.write('  ✅ Telegram: Configurado')
        else:
            self.stdout.write('  ❌ Telegram: No configurado')
        
        # Configuración de notificaciones
        notif_config = taller_config.get_notification_config()
        self.stdout.write('\n🔔 NOTIFICACIONES:')
        for key, value in notif_config.items():
            self.stdout.write(f'  {key}: {value}')
        
        # Servicios comunes
        self.stdout.write(f'\n🔧 SERVICIOS COMUNES ({len(taller_config.SERVICIOS_COMUNES)}):')
        for servicio in taller_config.SERVICIOS_COMUNES[:5]:  # Mostrar solo primeros 5
            self.stdout.write(f'  • {servicio}')
        if len(taller_config.SERVICIOS_COMUNES) > 5:
            self.stdout.write(f'  ... y {len(taller_config.SERVICIOS_COMUNES) - 5} más')

    def _test_channels(self):
        """Prueba canales de comunicación"""
        self.stdout.write(self.style.SUCCESS('🧪 PROBANDO CANALES DE COMUNICACIÓN'))
        self.stdout.write('='*50)
        
        # Probar WhatsApp
        if taller_config.is_whatsapp_enabled():
            self.stdout.write('\n📱 Probando WhatsApp...')
            try:
                from gestion_taller.whatsapp_service import WhatsAppService
                whatsapp = WhatsAppService()
                self.stdout.write('  ✅ Servicio WhatsApp inicializado correctamente')
                self.stdout.write('  💡 Usa: python manage.py test_whatsapp --telefono "+573001234567"')
            except Exception as e:
                self.stdout.write(f'  ❌ Error en WhatsApp: {e}')
        else:
            self.stdout.write('\n📱 WhatsApp: No configurado')
        
        # Probar Telegram
        if taller_config.is_telegram_enabled():
            self.stdout.write('\n🤖 Probando Telegram...')
            try:
                # Aquí podrías agregar una prueba real del bot
                self.stdout.write('  ✅ Token Telegram configurado')
                self.stdout.write('  💡 Prueba enviando un mensaje al bot')
            except Exception as e:
                self.stdout.write(f'  ❌ Error en Telegram: {e}')
        else:
            self.stdout.write('\n🤖 Telegram: No configurado')
        
        # Resumen
        channels = taller_config.get_available_channels()
        if channels:
            self.stdout.write(f'\n✅ Canales disponibles: {", ".join(channels)}')
        else:
            self.stdout.write('\n❌ No hay canales configurados')
            self.stdout.write('\n💡 Configura al menos un canal para enviar notificaciones')

    def _export_config(self, filename):
        """Exporta configuración a archivo JSON"""
        try:
            config = get_full_config()
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False, default=str)
            
            self.stdout.write(self.style.SUCCESS(f'✅ Configuración exportada a: {filename}'))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Error exportando configuración: {e}'))

    def _save_config_to_file(self):
        """Guarda configuración en archivo local"""
        config_file = 'taller_config.json'
        try:
            config = {
                'business_name': taller_config.BUSINESS_NAME,
                'business_phone': taller_config.BUSINESS_PHONE,
                'business_email': taller_config.BUSINESS_EMAIL,
                'business_website': taller_config.BUSINESS_WEBSITE,
                'business_address': taller_config.BUSINESS_ADDRESS,
                'business_hours': taller_config.BUSINESS_HOURS,
                'notification_defaults': taller_config.NOTIFICATION_DEFAULTS,
                'last_updated': str(timezone.now())
            }
            
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            
            self.stdout.write(f'💾 Configuración guardada en: {config_file}')
            
        except Exception as e:
            self.stdout.write(self.style.WARNING(f'⚠️ No se pudo guardar configuración: {e}'))
