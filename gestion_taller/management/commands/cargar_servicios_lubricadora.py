"""
Comando Django para poblar los servicios del catálogo típicos de una Lubricadora / Centro de Lubricación Automotriz.
Uso: python manage.py cargar_servicios_lubricadora
"""

from django.core.management.base import BaseCommand
from gestion_taller.models import Cliente, ServicioCatalogo
from decimal import Decimal

SERVICIOS_LUBRICADORA = [
    {
        'nombre': 'Cambio de Aceite de Motor y Filtro',
        'descripcion': 'Drenado de aceite usado, cambio de filtro de aceite de motor, colocacion de arandela nueva y llenado con lubricante segun especificacion del fabricante (mineral, semisintetico o 100% sintetico).',
        'precio_base': Decimal('15.00'),
        'frecuencia_km': 5000,
        'frecuencia_meses': 6,
        'aplicar_iva_servicio': True,
    },
    {
        'nombre': 'Cambio de Filtro de Aire de Motor',
        'descripcion': 'Inspeccion, limpieza de caja porta-filtro y reemplazo del elemento filtrante de aire para optimizar la combustion y consumo de combustible.',
        'precio_base': Decimal('5.00'),
        'frecuencia_km': 10000,
        'frecuencia_meses': 12,
        'aplicar_iva_servicio': True,
    },
    {
        'nombre': 'Cambio de Filtro de Cabina / Aire Acondicionado',
        'descripcion': 'Extraccion del filtro de habitaculo saturado, desinfeccion basica de ductos y reemplazo del filtro de polen y particulas para el confort interior.',
        'precio_base': Decimal('6.00'),
        'frecuencia_km': 15000,
        'frecuencia_meses': 12,
        'aplicar_iva_servicio': True,
    },
    {
        'nombre': 'Cambio de Filtro de Combustible (Gasolina / Diesel)',
        'descripcion': 'Reemplazo del filtro de combustible primario/secundario para proteger inyectores y bomba de alta presion contra impurezas y agua.',
        'precio_base': Decimal('10.00'),
        'frecuencia_km': 20000,
        'frecuencia_meses': 12,
        'aplicar_iva_servicio': True,
    },
    {
        'nombre': 'Cambio de Aceite de Transmision Manual / Caja',
        'descripcion': 'Drenado y reposicion de valvulina / aceite de engranajes para caja de cambios mecanica (75W-90, 80W-90 u homologado).',
        'precio_base': Decimal('12.00'),
        'frecuencia_km': 40000,
        'frecuencia_meses': 24,
        'aplicar_iva_servicio': True,
    },
    {
        'nombre': 'Cambio y Dialisis de Fluido de Transmision Automatica (ATF / CVT)',
        'descripcion': 'Reemplazo de fluido hidraulico para transmisiones automaticas tradicionales, CVT o doble embrague (DSG) con revision de nivel a temperatura de operacion.',
        'precio_base': Decimal('35.00'),
        'frecuencia_km': 40000,
        'frecuencia_meses': 24,
        'aplicar_iva_servicio': True,
    },
    {
        'nombre': 'Cambio de Aceite de Diferencial y Corona',
        'descripcion': 'Vaciado y llenado con lubricante para diferenciales abiertos o de deslizamiento limitado (LSD) en vehiculos 4x4, SUVs y camionetas.',
        'precio_base': Decimal('15.00'),
        'frecuencia_km': 30000,
        'frecuencia_meses': 24,
        'aplicar_iva_servicio': True,
    },
    {
        'nombre': 'Engrase General de Chasis y Articulaciones',
        'descripcion': 'Lubricacion a presion mediante grasera en terminales de direccion, rotulas, crucetas de cardan, munones y puntos moviles de suspension.',
        'precio_base': Decimal('8.00'),
        'frecuencia_km': 10000,
        'frecuencia_meses': 6,
        'aplicar_iva_servicio': True,
    },
    {
        'nombre': 'Lavado y Purga del Sistema de Refrigeracion (Coolant)',
        'descripcion': 'Drenado del refrigerante viejo, enjuague del circuito del radiador y recarga completa con refrigerante/anticorrosivo organico (OAT/HOAT).',
        'precio_base': Decimal('18.00'),
        'frecuencia_km': 40000,
        'frecuencia_meses': 24,
        'aplicar_iva_servicio': True,
    },
    {
        'nombre': 'Cambio y Purga de Liquido de Frenos (DOT 3 / DOT 4)',
        'descripcion': 'Extraccion de liquido degradado con humedad por cada caliper/rueda y purga completa del circuito hidraulico de frenos y embrague.',
        'precio_base': Decimal('20.00'),
        'frecuencia_km': 30000,
        'frecuencia_meses': 24,
        'aplicar_iva_servicio': True,
    },
    {
        'nombre': 'Lavado de Motor y Desengrasado Ecologico',
        'descripcion': 'Aplicacion de espuma desengrasante bio-amigable en vano motor, limpieza minuciosa protegiendo alternador, bobinas y computador, con abrillantador de mangueras.',
        'precio_base': Decimal('12.00'),
        'frecuencia_km': 10000,
        'frecuencia_meses': 6,
        'aplicar_iva_servicio': True,
    },
    {
        'nombre': 'Lavado, Pulverizado de Chasis y Grafito',
        'descripcion': 'Lavado a alta presion por debajo del vehiculo, secado y pulverizado con solucion grafitada o vaselinada para proteccion anticorrosiva y silenciamiento de articulaciones.',
        'precio_base': Decimal('15.00'),
        'frecuencia_km': 10000,
        'frecuencia_meses': 6,
        'aplicar_iva_servicio': True,
    },
    {
        'nombre': 'Revision y Relleno de Niveles de Seguridad (Chequeo 15 Puntos)',
        'descripcion': 'Inspeccion tecnica de liquido de frenos, direccion hidraulica, coolant, liquido limpiaparabrisas, estado de bateria, presion de llantas y fugas inferiores.',
        'precio_base': Decimal('0.00'),
        'frecuencia_km': 5000,
        'frecuencia_meses': 3,
        'aplicar_iva_servicio': False,
    }
]


class Command(BaseCommand):
    help = 'Carga los servicios del catalogo especializados para una Lubricadora'

    def handle(self, *args, **options):
        # Tomar todos los clientes o al menos el inicial
        clientes = Cliente.objects.all()
        if not clientes.exists():
            self.stdout.write(self.style.WARNING('No se encontraron clientes/talleres. Creando taller inicial...'))
            cliente = Cliente.objects.create(
                id=1,
                nombre='Taller Mecanico Principal',
                telefono='0999999999',
                correo='admin@taller.com',
                direccion='Matriz Central'
            )
            clientes = [cliente]

        total_creados = 0
        total_actualizados = 0

        for cliente in clientes:
            self.stdout.write(f'Procesando servicios para taller: {cliente.nombre} (ID: {cliente.id})')
            for item in SERVICIOS_LUBRICADORA:
                servicio, created = ServicioCatalogo.objects.update_or_create(
                    cliente=cliente,
                    nombre=item['nombre'],
                    defaults={
                        'descripcion': item['descripcion'],
                        'precio_base': item['precio_base'],
                        'frecuencia_km': item['frecuencia_km'],
                        'frecuencia_meses': item['frecuencia_meses'],
                        'aplicar_iva_servicio': item['aplicar_iva_servicio'],
                        'activo': True,
                    }
                )
                if created:
                    total_creados += 1
                else:
                    total_actualizados += 1

        self.stdout.write(self.style.SUCCESS(
            f'Servicios de Lubricadora procesados con exito: {total_creados} creados, {total_actualizados} actualizados.'
        ))
