"""
Comando de Django para verificar recordatorios de mantenimiento
Puede ejecutarse manualmente o programarse con cron/scheduler
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from gestion_taller.ai_predictor import verificar_recordatorios_pendientes, entrenar_modelo_cliente
from gestion_taller.models import Cliente

class Command(BaseCommand):
    help = 'Verifica recordatorios de mantenimiento pendientes y envía notificaciones'

    def add_arguments(self, parser):
        parser.add_argument(
            '--entrenar-ia',
            action='store_true',
            help='También entrena los modelos de IA para todos los clientes',
        )
        parser.add_argument(
            '--cliente-id',
            type=int,
            help='ID del cliente específico para procesar (opcional)',
        )
        parser.add_argument(
            '--canal',
            choices=['telegram', 'whatsapp', 'ambos'],
            default='ambos',
            help='Canal de notificación: telegram, whatsapp o ambos (por defecto: ambos)'
        )

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS(f'Iniciando verificación de recordatorios - {timezone.now()}')
        )

        try:
            # Entrenar modelos de IA si se solicita
            if options['entrenar_ia']:
                self.stdout.write('Entrenando modelos de IA...')
                
                if options['cliente_id']:
                    clientes = Cliente.objects.filter(id=options['cliente_id'])
                else:
                    clientes = Cliente.objects.all()
                
                for cliente in clientes:
                    try:
                        exito = entrenar_modelo_cliente(cliente)
                        if exito:
                            self.stdout.write(
                                self.style.SUCCESS(f'✅ Modelo entrenado para {cliente.nombre}')
                            )
                        else:
                            self.stdout.write(
                                self.style.WARNING(f'⚠️ No hay suficientes datos para entrenar modelo de {cliente.nombre}')
                            )
                    except Exception as e:
                        self.stdout.write(
                            self.style.ERROR(f'❌ Error entrenando modelo para {cliente.nombre}: {e}')
                        )

            # Verificar recordatorios pendientes
            canal = options['canal']
            self.stdout.write(f'Verificando recordatorios pendientes (canal: {canal})...')
            
            # Importar la función con el parámetro de canal
            from gestion_taller.ai_predictor import verificar_recordatorios_pendientes_con_canal
            
            try:
                notificaciones_enviadas = verificar_recordatorios_pendientes_con_canal(canal)
            except ImportError:
                # Fallback a la función original si no existe la nueva
                notificaciones_enviadas = verificar_recordatorios_pendientes()
            
            if notificaciones_enviadas:
                self.stdout.write(
                    self.style.SUCCESS(f'✅ Se enviaron {len(notificaciones_enviadas)} notificaciones')
                )
                
                for recordatorio in notificaciones_enviadas:
                    vehiculo = recordatorio.vehiculo
                    conductor = vehiculo.conductor.nombre if vehiculo.conductor else 'Sin conductor'
                    self.stdout.write(f'  📧 {vehiculo.placa} ({conductor}) - {recordatorio.tipo}')
            else:
                self.stdout.write(
                    self.style.SUCCESS('ℹ️ No hay recordatorios pendientes para notificar')
                )

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Error durante la verificación: {e}')
            )
            raise

        self.stdout.write(
            self.style.SUCCESS(f'Verificación completada - {timezone.now()}')
        )
