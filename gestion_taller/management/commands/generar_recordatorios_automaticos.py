"""
Comando de management para generar recordatorios de mantenimiento automáticos
basado en el kilometraje y fechas de los vehículos
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import datetime, timedelta
from gestion_taller.models import Vehiculo, RecordatorioMantenimiento, OrdenServicio
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Genera recordatorios de mantenimiento automáticos basado en kilometraje y fechas'

    def add_arguments(self, parser):
        parser.add_argument(
            '--cliente-id',
            type=int,
            help='Generar recordatorios solo para un cliente específico'
        )
        parser.add_argument(
            '--vehiculo-id',
            type=int,
            help='Generar recordatorios solo para un vehículo específico'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Simular generación sin crear recordatorios reales'
        )
        parser.add_argument(
            '--forzar',
            action='store_true',
            help='Forzar generación incluso si ya existen recordatorios'
        )

    def handle(self, *args, **options):
        cliente_id = options.get('cliente_id')
        vehiculo_id = options.get('vehiculo_id')
        dry_run = options['dry_run']
        forzar = options['forzar']
        
        self.stdout.write(
            self.style.SUCCESS('🔧 Iniciando generación de recordatorios automáticos')
        )
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING('⚠️ MODO SIMULACIÓN - No se crearán recordatorios reales')
            )
        
        # Obtener vehículos a procesar
        vehiculos = self.obtener_vehiculos(cliente_id, vehiculo_id)
        
        if not vehiculos:
            self.stdout.write(
                self.style.WARNING('⚠️ No se encontraron vehículos para procesar')
            )
            return
        
        self.stdout.write(f'🚗 Procesando {len(vehiculos)} vehículos...')
        
        # Procesar cada vehículo
        recordatorios_creados = 0
        recordatorios_existentes = 0
        errores = 0
        
        for vehiculo in vehiculos:
            try:
                resultado = self.procesar_vehiculo(vehiculo, dry_run, forzar)
                recordatorios_creados += resultado['creados']
                recordatorios_existentes += resultado['existentes']
                
                if resultado['creados'] > 0:
                    self.stdout.write(
                        self.style.SUCCESS(f'  ✅ {vehiculo.placa} - {resultado["creados"]} recordatorios creados')
                    )
                elif resultado['existentes'] > 0:
                    self.stdout.write(
                        f'  ℹ️ {vehiculo.placa} - {resultado["existentes"]} recordatorios ya existían'
                    )
                
            except Exception as e:
                errores += 1
                self.stdout.write(
                    self.style.ERROR(f'  ❌ {vehiculo.placa} - Error: {e}')
                )
        
        # Resumen final
        self.stdout.write('\n📊 RESUMEN DE GENERACIÓN:')
        self.stdout.write(f'  ✅ Recordatorios creados: {recordatorios_creados}')
        self.stdout.write(f'  ℹ️ Ya existían: {recordatorios_existentes}')
        self.stdout.write(f'  ❌ Errores: {errores}')
        self.stdout.write(f'  🚗 Vehículos procesados: {len(vehiculos)}')
        
        if not dry_run and recordatorios_creados > 0:
            self.stdout.write(
                self.style.SUCCESS(f'\n🎯 Recordatorios generados exitosamente')
            )

    def obtener_vehiculos(self, cliente_id, vehiculo_id):
        """Obtiene los vehículos a procesar"""
        
        query = Vehiculo.objects.filter(
            conductor__isnull=False,  # Solo vehículos con conductor
            activo=True  # Solo vehículos activos
        )
        
        if vehiculo_id:
            query = query.filter(id=vehiculo_id)
        elif cliente_id:
            query = query.filter(conductor__cliente_id=cliente_id)
        
        return query.order_by('placa')

    def procesar_vehiculo(self, vehiculo, dry_run, forzar):
        """Procesa un vehículo individual para generar recordatorios"""
        
        resultado = {
            'creados': 0,
            'existentes': 0
        }
        
        # Obtener la última orden de servicio para este vehículo
        ultima_orden = OrdenServicio.objects.filter(
            vehiculo=vehiculo
        ).order_by('-fecha_creacion').first()
        
        # Definir tipos de mantenimiento y sus intervalos
        tipos_mantenimiento = self.obtener_tipos_mantenimiento(vehiculo, ultima_orden)
        
        for tipo_info in tipos_mantenimiento:
            try:
                recordatorio_creado = self.crear_recordatorio_si_necesario(
                    vehiculo=vehiculo,
                    tipo_info=tipo_info,
                    dry_run=dry_run,
                    forzar=forzar
                )
                
                if recordatorio_creado == 'creado':
                    resultado['creados'] += 1
                elif recordatorio_creado == 'existente':
                    resultado['existentes'] += 1
                    
            except Exception as e:
                logger.error(f'Error creando recordatorio {tipo_info["tipo"]} para vehículo {vehiculo.id}: {e}')
                raise
        
        return resultado

    def obtener_tipos_mantenimiento(self, vehiculo, ultima_orden):
        """Define los tipos de mantenimiento y sus intervalos"""
        
        fecha_actual = timezone.now().date()
        
        # Fecha base para cálculos (última orden o fecha de registro del vehículo)
        if ultima_orden:
            fecha_base = ultima_orden.fecha_creacion.date()
            kilometraje_base = getattr(ultima_orden, 'kilometraje_ingreso', vehiculo.kilometraje or 0)
        else:
            fecha_base = vehiculo.fecha_registro.date() if vehiculo.fecha_registro else fecha_actual
            kilometraje_base = vehiculo.kilometraje or 0
        
        tipos = [
            {
                'tipo': 'Cambio de aceite',
                'intervalo_km': 5000,
                'intervalo_meses': 6,
                'prioridad': 'alta',
                'descripcion': 'Cambio de aceite y filtro'
            },
            {
                'tipo': 'Revisión de frenos',
                'intervalo_km': 15000,
                'intervalo_meses': 12,
                'prioridad': 'alta',
                'descripcion': 'Revisión completa del sistema de frenos'
            },
            {
                'tipo': 'Cambio de filtro de aire',
                'intervalo_km': 10000,
                'intervalo_meses': 12,
                'prioridad': 'media',
                'descripcion': 'Cambio de filtro de aire del motor'
            },
            {
                'tipo': 'Revisión de suspensión',
                'intervalo_km': 20000,
                'intervalo_meses': 18,
                'prioridad': 'media',
                'descripcion': 'Revisión de amortiguadores y suspensión'
            },
            {
                'tipo': 'Cambio de bujías',
                'intervalo_km': 30000,
                'intervalo_meses': 24,
                'prioridad': 'media',
                'descripcion': 'Cambio de bujías y cables'
            },
            {
                'tipo': 'Revisión general',
                'intervalo_km': 10000,
                'intervalo_meses': 6,
                'prioridad': 'baja',
                'descripcion': 'Revisión general del vehículo'
            }
        ]
        
        # Calcular fechas y kilometrajes próximos para cada tipo
        for tipo in tipos:
            # Calcular próxima fecha
            fecha_proxima = fecha_base + timedelta(days=tipo['intervalo_meses'] * 30)
            
            # Calcular próximo kilometraje
            km_proximo = kilometraje_base + tipo['intervalo_km']
            
            tipo.update({
                'fecha_base': fecha_base,
                'kilometraje_base': kilometraje_base,
                'fecha_proximo': fecha_proxima,
                'kilometraje_proximo': km_proximo
            })
        
        return tipos

    def crear_recordatorio_si_necesario(self, vehiculo, tipo_info, dry_run, forzar):
        """Crea un recordatorio si es necesario"""
        
        # Verificar si ya existe un recordatorio similar
        if not forzar:
            recordatorio_existente = RecordatorioMantenimiento.objects.filter(
                vehiculo=vehiculo,
                tipo=tipo_info['tipo'],
                notificado=False
            ).first()
            
            if recordatorio_existente:
                return 'existente'
        
        if dry_run:
            self.stdout.write(
                f'    🔍 SIMULACIÓN: Crear recordatorio {tipo_info["tipo"]} para {vehiculo.placa}'
            )
            return 'creado'
        
        # Crear el recordatorio
        recordatorio = RecordatorioMantenimiento.objects.create(
            vehiculo=vehiculo,
            tipo=tipo_info['tipo'],
            descripcion=tipo_info['descripcion'],
            fecha_proximo=tipo_info['fecha_proximo'],
            kilometraje_proximo=tipo_info['kilometraje_proximo'],
            prioridad=tipo_info['prioridad'],
            notificado=False,
            fecha_creacion=timezone.now()
        )
        
        logger.info(f'Recordatorio creado: {vehiculo.placa} - {tipo_info["tipo"]} - {tipo_info["fecha_proximo"]}')
        return 'creado'

    def limpiar_recordatorios_duplicados(self):
        """Limpia recordatorios duplicados"""
        
        self.stdout.write('🧹 Limpiando recordatorios duplicados...')
        
        # Encontrar duplicados
        from django.db.models import Count
        
        duplicados = RecordatorioMantenimiento.objects.values(
            'vehiculo', 'tipo'
        ).annotate(
            count=Count('id')
        ).filter(count__gt=1)
        
        eliminados = 0
        
        for duplicado in duplicados:
            # Mantener solo el más reciente
            recordatorios = RecordatorioMantenimiento.objects.filter(
                vehiculo_id=duplicado['vehiculo'],
                tipo=duplicado['tipo']
            ).order_by('-fecha_creacion')
            
            # Eliminar todos excepto el primero (más reciente)
            for recordatorio in recordatorios[1:]:
                recordatorio.delete()
                eliminados += 1
        
        if eliminados > 0:
            self.stdout.write(
                self.style.SUCCESS(f'✅ Eliminados {eliminados} recordatorios duplicados')
            )
        else:
            self.stdout.write('✅ No se encontraron recordatorios duplicados')

    def mostrar_estadisticas_generacion(self, cliente_id=None):
        """Muestra estadísticas de la generación"""
        
        self.stdout.write('\n📊 ESTADÍSTICAS DE GENERACIÓN:')
        
        try:
            from django.db.models import Count
            
            query_vehiculos = Vehiculo.objects.filter(activo=True, conductor__isnull=False)
            query_recordatorios = RecordatorioMantenimiento.objects.all()
            
            if cliente_id:
                query_vehiculos = query_vehiculos.filter(conductor__cliente_id=cliente_id)
                query_recordatorios = query_recordatorios.filter(vehiculo__conductor__cliente_id=cliente_id)
            
            total_vehiculos = query_vehiculos.count()
            vehiculos_con_recordatorios = query_vehiculos.filter(
                recordatorios__isnull=False
            ).distinct().count()
            
            total_recordatorios = query_recordatorios.count()
            recordatorios_por_tipo = query_recordatorios.values('tipo').annotate(
                count=Count('id')
            ).order_by('-count')
            
            self.stdout.write(f'  🚗 Vehículos activos: {total_vehiculos}')
            self.stdout.write(f'  📋 Vehículos con recordatorios: {vehiculos_con_recordatorios}')
            self.stdout.write(f'  📝 Total recordatorios: {total_recordatorios}')
            
            self.stdout.write('\n📊 Recordatorios por tipo:')
            for item in recordatorios_por_tipo[:5]:  # Top 5
                self.stdout.write(f'  • {item["tipo"]}: {item["count"]}')
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Error obteniendo estadísticas: {e}')
            )
