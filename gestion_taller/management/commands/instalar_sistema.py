"""
Comando Django para instalación completa del sistema de mensajería
Uso: python manage.py instalar_sistema
"""

from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.utils import timezone
import os


class Command(BaseCommand):
    help = 'Instalación completa del sistema de mensajería WhatsApp + Telegram'

    def add_arguments(self, parser):
        parser.add_argument(
            '--skip-migrations',
            action='store_true',
            help='Saltar migraciones de base de datos'
        )
        parser.add_argument(
            '--skip-config',
            action='store_true',
            help='Saltar configuración interactiva'
        )
        parser.add_argument(
            '--test-mode',
            action='store_true',
            help='Modo de prueba (no envía mensajes reales)'
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('🚀 INSTALACIÓN DEL SISTEMA DE MENSAJERÍA'))
        self.stdout.write('='*60)
        
        # Paso 1: Verificar dependencias
        self._check_dependencies()
        
        # Paso 2: Migraciones
        if not options['skip_migrations']:
            self._run_migrations()
        
        # Paso 3: Verificar variables de entorno
        self._check_environment()
        
        # Paso 4: Configuración inicial
        if not options['skip_config']:
            self._initial_configuration()
        
        # Paso 5: Pruebas del sistema
        if options['test_mode']:
            self._run_tests()
        
        # Paso 6: Mostrar resumen
        self._show_summary()
        
        self.stdout.write(self.style.SUCCESS('\n🎉 ¡INSTALACIÓN COMPLETADA!'))

    def _check_dependencies(self):
        """Verifica dependencias del sistema"""
        self.stdout.write('\n📦 VERIFICANDO DEPENDENCIAS')
        self.stdout.write('-'*30)
        
        try:
            import requests
            self.stdout.write('✅ requests: Instalado')
        except ImportError:
            self.stdout.write('❌ requests: No instalado')
            self.stdout.write('💡 Ejecuta: pip install requests>=2.31.0')
        
        try:
            import django
            self.stdout.write(f'✅ Django: {django.get_version()}')
        except ImportError:
            self.stdout.write('❌ Django: No instalado')
        
        # Verificar archivos del sistema
        archivos_requeridos = [
            'gestion_taller/whatsapp_service.py',
            'gestion_taller/message_templates.py',
            'gestion_taller/taller_config.py',
            'gestion_taller/management/commands/test_whatsapp.py',
            'gestion_taller/management/commands/enviar_promocion.py',
            'gestion_taller/management/commands/dashboard_mensajeria.py',
            'gestion_taller/management/commands/configurar_taller.py'
        ]
        
        self.stdout.write('\n📁 Verificando archivos del sistema:')
        for archivo in archivos_requeridos:
            if os.path.exists(archivo):
                self.stdout.write(f'✅ {archivo}')
            else:
                self.stdout.write(f'❌ {archivo} - FALTANTE')

    def _run_migrations(self):
        """Ejecuta migraciones de base de datos"""
        self.stdout.write('\n🗄️ EJECUTANDO MIGRACIONES')
        self.stdout.write('-'*30)
        
        try:
            call_command('makemigrations', verbosity=0)
            call_command('migrate', verbosity=0)
            self.stdout.write('✅ Migraciones completadas')
        except Exception as e:
            self.stdout.write(f'❌ Error en migraciones: {e}')

    def _check_environment(self):
        """Verifica variables de entorno"""
        self.stdout.write('\n🌍 VERIFICANDO VARIABLES DE ENTORNO')
        self.stdout.write('-'*30)
        
        variables_requeridas = {
            'WASENDER_API_TOKEN': 'Token de WASenderAPI',
            'WASENDER_INSTANCE_ID': 'ID de instancia WASenderAPI',
            'TELEGRAM_BOT_TOKEN': 'Token del bot de Telegram'
        }
        
        variables_faltantes = []
        
        for var, descripcion in variables_requeridas.items():
            valor = os.environ.get(var)
            if valor:
                self.stdout.write(f'✅ {var}: Configurado ({valor[:10]}...)')
            else:
                self.stdout.write(f'❌ {var}: No configurado')
                variables_faltantes.append((var, descripcion))
        
        if variables_faltantes:
            self.stdout.write('\n⚠️ VARIABLES FALTANTES:')
            for var, desc in variables_faltantes:
                self.stdout.write(f'   {var}={desc}')
            
            self.stdout.write('\n💡 Crea un archivo .env con estas variables:')
            for var, desc in variables_faltantes:
                self.stdout.write(f'   {var}=tu_{var.lower()}')

    def _initial_configuration(self):
        """Configuración inicial del sistema"""
        self.stdout.write('\n⚙️ CONFIGURACIÓN INICIAL')
        self.stdout.write('-'*30)
        
        respuesta = input('¿Deseas ejecutar configuración interactiva? (s/N): ').strip().lower()
        
        if respuesta in ['s', 'si', 'sí', 'y', 'yes']:
            try:
                call_command('configurar_taller', '--setup')
            except Exception as e:
                self.stdout.write(f'❌ Error en configuración: {e}')
        else:
            self.stdout.write('⏭️ Configuración omitida')
            self.stdout.write('💡 Ejecuta más tarde: python manage.py configurar_taller --setup')

    def _run_tests(self):
        """Ejecuta pruebas del sistema"""
        self.stdout.write('\n🧪 EJECUTANDO PRUEBAS')
        self.stdout.write('-'*30)
        
        # Probar canales
        try:
            call_command('configurar_taller', '--test-channels')
        except Exception as e:
            self.stdout.write(f'❌ Error probando canales: {e}')
        
        # Mostrar dashboard
        try:
            call_command('dashboard_mensajeria')
        except Exception as e:
            self.stdout.write(f'❌ Error en dashboard: {e}')

    def _show_summary(self):
        """Muestra resumen de la instalación"""
        self.stdout.write('\n📋 RESUMEN DE INSTALACIÓN')
        self.stdout.write('='*50)
        
        # Estado de canales
        from gestion_taller.taller_config import taller_config
        
        channels = taller_config.get_available_channels()
        self.stdout.write(f'📱 Canales disponibles: {len(channels)} ({", ".join(channels)})')
        
        # Comandos disponibles
        self.stdout.write('\n🛠️ COMANDOS DISPONIBLES:')
        comandos = [
            ('configurar_taller --setup', 'Configuración inicial del taller'),
            ('dashboard_mensajeria', 'Ver métricas y estado del sistema'),
            ('test_whatsapp --telefono "+573001234567"', 'Probar envío WhatsApp'),
            ('verificar_recordatorios --canal ambos', 'Enviar recordatorios pendientes'),
            ('enviar_promocion --titulo "Oferta" --descuento 20', 'Enviar promoción masiva')
        ]
        
        for comando, descripcion in comandos:
            self.stdout.write(f'  • python manage.py {comando}')
            self.stdout.write(f'    {descripcion}')
        
        # Próximos pasos
        self.stdout.write('\n🎯 PRÓXIMOS PASOS RECOMENDADOS:')
        pasos = [
            'Configura las variables de entorno faltantes',
            'Ejecuta la configuración inicial del taller',
            'Prueba el envío de mensajes con conductores reales',
            'Programa recordatorios automáticos con cron jobs',
            'Monitorea métricas semanalmente con el dashboard'
        ]
        
        for i, paso in enumerate(pasos, 1):
            self.stdout.write(f'  {i}. {paso}')
        
        # Recursos adicionales
        self.stdout.write('\n📚 DOCUMENTACIÓN:')
        self.stdout.write('  • WHATSAPP_INTEGRATION_README.md - Documentación completa')
        self.stdout.write('  • env_example.txt - Ejemplo de variables de entorno')
        
        # Información de soporte
        self.stdout.write('\n💬 SOPORTE:')
        self.stdout.write('  • Revisa los logs en caso de errores')
        self.stdout.write('  • Usa --help en cualquier comando para más información')
        self.stdout.write('  • Verifica la configuración con dashboard_mensajeria')

    def _create_sample_data(self):
        """Crea datos de ejemplo para pruebas"""
        self.stdout.write('\n📊 CREANDO DATOS DE EJEMPLO')
        self.stdout.write('-'*30)
        
        # Aquí podrías crear conductores y vehículos de ejemplo
        # para facilitar las pruebas del sistema
        
        self.stdout.write('💡 Tip: Agrega conductores con teléfonos válidos para pruebas')
        self.stdout.write('💡 Tip: Configura recordatorios de mantenimiento para probar notificaciones')
