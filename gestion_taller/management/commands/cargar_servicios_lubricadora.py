"""
Comando Django para poblar tanto los Servicios del Catálogo como los Repuestos/Insumos
típicos de una Lubricadora / Centro de Lubricación Automotriz, vinculando automáticamente
los productos requeridos a cada servicio.
Uso: python manage.py cargar_servicios_lubricadora
"""

from django.core.management.base import BaseCommand
from gestion_taller.models import Cliente, ServicioCatalogo, Repuesto
from decimal import Decimal

# Catálogo completo de insumos y repuestos de lubricadora
REPUESTOS_LUBRICADORA = [
    # Aceites de Motor
    {
        'codigo': 'ACE-5W30-SN',
        'nombre': 'Aceite de Motor 5W-30 Sintético (Galón)',
        'descripcion': 'Aceite 100% sintético para motores a gasolina modernos con tecnología de protección contra desgaste.',
        'precio_compra': Decimal('22.00'),
        'precio_venta': Decimal('32.00'),
        'stock': 25,
        'stock_minimo': 5,
        'proveedor': 'Castrol / Motul / Mobil',
    },
    {
        'codigo': 'ACE-10W40-SM',
        'nombre': 'Aceite de Motor 10W-40 Semisintético (Galón)',
        'descripcion': 'Lubricante semisintético multigrado de alto rendimiento para motores a gasolina y diésel ligero.',
        'precio_compra': Decimal('17.50'),
        'precio_venta': Decimal('26.00'),
        'stock': 30,
        'stock_minimo': 6,
        'proveedor': 'Valvoline / Havoline',
    },
    {
        'codigo': 'ACE-20W50-SL',
        'nombre': 'Aceite de Motor 20W-50 Mineral (Galón)',
        'descripcion': 'Aceite mineral de alta viscosidad para motores con alto kilometraje o trabajo exigente.',
        'precio_compra': Decimal('14.00'),
        'precio_venta': Decimal('21.00'),
        'stock': 20,
        'stock_minimo': 5,
        'proveedor': 'Mobil / Gulf / Shell',
    },
    # Filtros
    {
        'codigo': 'FLT-ACE-STD',
        'nombre': 'Filtro de Aceite Blindado Multimarca',
        'descripcion': 'Elemento filtrante de alta eficiencia para retención de partículas metálicas y carbón en el motor.',
        'precio_compra': Decimal('3.50'),
        'precio_venta': Decimal('6.50'),
        'stock': 40,
        'stock_minimo': 10,
        'proveedor': 'Mann Filter / Bosch / Fram',
    },
    {
        'codigo': 'FLT-AIR-STD',
        'nombre': 'Filtro de Aire de Motor Premium',
        'descripcion': 'Filtro de celulosa y microfibra para entrada de aire limpio al múltiple de admisión.',
        'precio_compra': Decimal('5.00'),
        'precio_venta': Decimal('9.50'),
        'stock': 30,
        'stock_minimo': 8,
        'proveedor': 'Bosch / Wix / Web',
    },
    {
        'codigo': 'FLT-CAB-POL',
        'nombre': 'Filtro de Cabina / A/C Antipolen',
        'descripcion': 'Filtro de habitáculo con capa de carbón activo para purificación del aire acondicionado.',
        'precio_compra': Decimal('6.00'),
        'precio_venta': Decimal('11.00'),
        'stock': 20,
        'stock_minimo': 5,
        'proveedor': 'Mann / Filtron',
    },
    {
        'codigo': 'FLT-COMB-GAS',
        'nombre': 'Filtro de Combustible en Línea',
        'descripcion': 'Filtro sellado para conductos de inyección electrónica a gasolina de alta presión.',
        'precio_compra': Decimal('4.50'),
        'precio_venta': Decimal('8.50'),
        'stock': 25,
        'stock_minimo': 5,
        'proveedor': 'Bosch / Fram',
    },
    # Transmisión y Diferenciales
    {
        'codigo': 'VAL-75W90-GL5',
        'nombre': 'Aceite para Transmisión Manual 75W-90 GL-5 (Cuarto)',
        'descripcion': 'Valvulina sintética para cajas mecánicas de cambios y diferenciales sometidos a extrema presión.',
        'precio_compra': Decimal('8.00'),
        'precio_venta': Decimal('13.00'),
        'stock': 20,
        'stock_minimo': 4,
        'proveedor': 'Motul / Liqui Moly',
    },
    {
        'codigo': 'ATF-VI-SYN',
        'nombre': 'Fluido de Transmisión Automática ATF Dexron VI / Mercon (Cuarto)',
        'descripcion': 'Fluido hidráulico 100% sintético de baja viscosidad para cajas automáticas modernas.',
        'precio_compra': Decimal('9.50'),
        'precio_venta': Decimal('15.50'),
        'stock': 25,
        'stock_minimo': 6,
        'proveedor': 'Valvoline / Mobil 1',
    },
    {
        'codigo': 'VAL-85W140-DIF',
        'nombre': 'Aceite de Diferencial y Corona 85W-140 EP (Cuarto)',
        'descripcion': 'Aceite mineral pesado de extrema presión para diferenciales de carga y camionetas 4x4.',
        'precio_compra': Decimal('7.00'),
        'precio_venta': Decimal('11.50'),
        'stock': 15,
        'stock_minimo': 4,
        'proveedor': 'Gulf / Chevron',
    },
    # Enfriamiento y Frenos
    {
        'codigo': 'REF-COOL-50',
        'nombre': 'Refrigerante / Anticongelante Orgánico 50/50 (Galón)',
        'descripcion': 'Coolant orgánico de larga duración (OAT) protección contra corrosión y sobrecalentamiento.',
        'precio_compra': Decimal('7.50'),
        'precio_venta': Decimal('13.00'),
        'stock': 25,
        'stock_minimo': 5,
        'proveedor': 'Prestone / Peak',
    },
    {
        'codigo': 'LIQ-FREN-DOT4',
        'nombre': 'Líquido de Frenos DOT 4 de Alto Punto de Ebullición (500ml)',
        'descripcion': 'Fluido sintético para sistemas de frenos hidráulicos con tecnología ABS y control de estabilidad.',
        'precio_compra': Decimal('4.00'),
        'precio_venta': Decimal('7.50'),
        'stock': 30,
        'stock_minimo': 6,
        'proveedor': 'Wagner / Bosch / ATE',
    },
    # Insumos y Grasa
    {
        'codigo': 'GRA-CHAS-EP2',
        'nombre': 'Grasa Litio Multipropósito EP-2 (Libra)',
        'descripcion': 'Grasa para engrase de terminales, rótulas, rodamientos y componentes de chasis.',
        'precio_compra': Decimal('3.00'),
        'precio_venta': Decimal('5.50'),
        'stock': 35,
        'stock_minimo': 8,
        'proveedor': 'Castrol / SKF',
    },
    {
        'codigo': 'DES-MOT-BIO',
        'nombre': 'Desengrasante Biodegradable Concentrado de Motor (Litro)',
        'descripcion': 'Agente espumante biodegradable para limpieza y remoción de grasa profunda en motor.',
        'precio_compra': Decimal('3.50'),
        'precio_venta': Decimal('6.50'),
        'stock': 20,
        'stock_minimo': 4,
        'proveedor': 'Simoniz / Meguiar’s',
    },
    {
        'codigo': 'PROT-CHAS-GRAF',
        'nombre': 'Solución Grafito Protectora de Chasis (Litro)',
        'descripcion': 'Fórmula lubricante e hidrofóbica grafitada para amortiguadores, hojas de ballesta y partes bajas.',
        'precio_compra': Decimal('4.00'),
        'precio_venta': Decimal('7.00'),
        'stock': 20,
        'stock_minimo': 5,
        'proveedor': 'Grafix / ABRO',
    },
    {
        'codigo': 'ARA-CARTER-UNI',
        'nombre': 'Arandela / Golilla de Cárter de Cobre (Unidad)',
        'descripcion': 'Sello de cobre maleable para tapón de drenaje de cárter de aceite.',
        'precio_compra': Decimal('0.30'),
        'precio_venta': Decimal('1.00'),
        'stock': 100,
        'stock_minimo': 20,
        'proveedor': 'Universal OEM',
    }
]

# Servicios y los códigos de repuestos que habitualmente requieren
SERVICIOS_LUBRICADORA = [
    {
        'nombre': 'Cambio de Aceite de Motor y Filtro',
        'descripcion': 'Drenado de aceite usado, cambio de filtro de aceite de motor, colocacion de arandela nueva y llenado con lubricante segun especificacion del fabricante (mineral, semisintetico o 100% sintetico).',
        'precio_base': Decimal('15.00'),
        'frecuencia_km': 5000,
        'frecuencia_meses': 6,
        'aplicar_iva_servicio': True,
        'repuestos_asociados': ['ACE-5W30-SN', 'ACE-10W40-SM', 'ACE-20W50-SL', 'FLT-ACE-STD', 'ARA-CARTER-UNI']
    },
    {
        'nombre': 'Cambio de Filtro de Aire de Motor',
        'descripcion': 'Inspeccion, limpieza de caja porta-filtro y reemplazo del elemento filtrante de aire para optimizar la combustion y consumo de combustible.',
        'precio_base': Decimal('5.00'),
        'frecuencia_km': 10000,
        'frecuencia_meses': 12,
        'aplicar_iva_servicio': True,
        'repuestos_asociados': ['FLT-AIR-STD']
    },
    {
        'nombre': 'Cambio de Filtro de Cabina / Aire Acondicionado',
        'descripcion': 'Extraccion del filtro de habitaculo saturado, desinfeccion basica de ductos y reemplazo del filtro de polen y particulas para el confort interior.',
        'precio_base': Decimal('6.00'),
        'frecuencia_km': 15000,
        'frecuencia_meses': 12,
        'aplicar_iva_servicio': True,
        'repuestos_asociados': ['FLT-CAB-POL']
    },
    {
        'nombre': 'Cambio de Filtro de Combustible (Gasolina / Diesel)',
        'descripcion': 'Reemplazo del filtro de combustible primario/secundario para proteger inyectores y bomba de alta presion contra impurezas y agua.',
        'precio_base': Decimal('10.00'),
        'frecuencia_km': 20000,
        'frecuencia_meses': 12,
        'aplicar_iva_servicio': True,
        'repuestos_asociados': ['FLT-COMB-GAS']
    },
    {
        'nombre': 'Cambio de Aceite de Transmision Manual / Caja',
        'descripcion': 'Drenado y reposicion de valvulina / aceite de engranajes para caja de cambios mecanica (75W-90, 80W-90 u homologado).',
        'precio_base': Decimal('12.00'),
        'frecuencia_km': 40000,
        'frecuencia_meses': 24,
        'aplicar_iva_servicio': True,
        'repuestos_asociados': ['VAL-75W90-GL5']
    },
    {
        'nombre': 'Cambio y Dialisis de Fluido de Transmision Automatica (ATF / CVT)',
        'descripcion': 'Reemplazo de fluido hidraulico para transmisiones automaticas tradicionales, CVT o doble embrague (DSG) con revision de nivel a temperatura de operacion.',
        'precio_base': Decimal('35.00'),
        'frecuencia_km': 40000,
        'frecuencia_meses': 24,
        'aplicar_iva_servicio': True,
        'repuestos_asociados': ['ATF-VI-SYN']
    },
    {
        'nombre': 'Cambio de Aceite de Diferencial y Corona',
        'descripcion': 'Vaciado y llenado con lubricante para diferenciales abiertos o de deslizamiento limitado (LSD) en vehiculos 4x4, SUVs y camionetas.',
        'precio_base': Decimal('15.00'),
        'frecuencia_km': 30000,
        'frecuencia_meses': 24,
        'aplicar_iva_servicio': True,
        'repuestos_asociados': ['VAL-85W140-DIF', 'VAL-75W90-GL5']
    },
    {
        'nombre': 'Engrase General de Chasis y Articulaciones',
        'descripcion': 'Lubricacion a presion mediante grasera en terminales de direccion, rotulas, crucetas de cardan, munones y puntos moviles de suspension.',
        'precio_base': Decimal('8.00'),
        'frecuencia_km': 10000,
        'frecuencia_meses': 6,
        'aplicar_iva_servicio': True,
        'repuestos_asociados': ['GRA-CHAS-EP2']
    },
    {
        'nombre': 'Lavado y Purga del Sistema de Refrigeracion (Coolant)',
        'descripcion': 'Drenado del refrigerante viejo, enjuague del circuito del radiador y recarga completa con refrigerante/anticorrosivo organico (OAT/HOAT).',
        'precio_base': Decimal('18.00'),
        'frecuencia_km': 40000,
        'frecuencia_meses': 24,
        'aplicar_iva_servicio': True,
        'repuestos_asociados': ['REF-COOL-50']
    },
    {
        'nombre': 'Cambio y Purga de Liquido de Frenos (DOT 3 / DOT 4)',
        'descripcion': 'Extraccion de liquido degradado con humedad por cada caliper/rueda y purga completa del circuito hidraulico de frenos y embrague.',
        'precio_base': Decimal('20.00'),
        'frecuencia_km': 30000,
        'frecuencia_meses': 24,
        'aplicar_iva_servicio': True,
        'repuestos_asociados': ['LIQ-FREN-DOT4']
    },
    {
        'nombre': 'Lavado de Motor y Desengrasado Ecologico',
        'descripcion': 'Aplicacion de espuma desengrasante bio-amigable en vano motor, limpieza minuciosa protegiendo alternador, bobinas y computador, con abrillantador de mangueras.',
        'precio_base': Decimal('12.00'),
        'frecuencia_km': 10000,
        'frecuencia_meses': 6,
        'aplicar_iva_servicio': True,
        'repuestos_asociados': ['DES-MOT-BIO']
    },
    {
        'nombre': 'Lavado, Pulverizado de Chasis y Grafito',
        'descripcion': 'Lavado a alta presion por debajo del vehiculo, secado y pulverizado con solucion grafitada o vaselinada para proteccion anticorrosiva y silenciamiento de articulaciones.',
        'precio_base': Decimal('15.00'),
        'frecuencia_km': 10000,
        'frecuencia_meses': 6,
        'aplicar_iva_servicio': True,
        'repuestos_asociados': ['PROT-CHAS-GRAF']
    },
    {
        'nombre': 'Revision y Relleno de Niveles de Seguridad (Chequeo 15 Puntos)',
        'descripcion': 'Inspeccion tecnica de liquido de frenos, direccion hidraulica, coolant, liquido limpiaparabrisas, estado de bateria, presion de llantas y fugas inferiores.',
        'precio_base': Decimal('0.00'),
        'frecuencia_km': 5000,
        'frecuencia_meses': 3,
        'aplicar_iva_servicio': False,
        'repuestos_asociados': ['REF-COOL-50', 'LIQ-FREN-DOT4']
    }
]


class Command(BaseCommand):
    help = 'Carga repuestos/insumos y servicios del catalogo especializados para una Lubricadora'

    def handle(self, *args, **options):
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

        for cliente in clientes:
            self.stdout.write(f'Procesando taller: {cliente.nombre} (ID: {cliente.id})')
            
            # 1. Crear / actualizar repuestos
            repuestos_map = {}
            for item in REPUESTOS_LUBRICADORA:
                repuesto, _ = Repuesto.objects.update_or_create(
                    cliente=cliente,
                    codigo=f"{item['codigo']}-{cliente.id}",
                    defaults={
                        'nombre': item['nombre'],
                        'descripcion': item['descripcion'],
                        'precio_compra': item['precio_compra'],
                        'precio_venta': item['precio_venta'],
                        'stock': item['stock'],
                        'stock_minimo': item['stock_minimo'],
                        'proveedor': item['proveedor'],
                        'aplicar_iva_producto': True,
                    }
                )
                repuestos_map[item['codigo']] = repuesto

            self.stdout.write(f'  -> {len(repuestos_map)} repuestos/insumos verificados.')

            # 2. Crear / actualizar servicios y asociar productos requeridos
            total_servicios = 0
            for item in SERVICIOS_LUBRICADORA:
                servicio, _ = ServicioCatalogo.objects.update_or_create(
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
                
                # Asociar repuestos correspondientes
                repuestos_a_vincular = [
                    repuestos_map[cod] for cod in item.get('repuestos_asociados', [])
                    if cod in repuestos_map
                ]
                if repuestos_a_vincular:
                    servicio.productos_requeridos.set(repuestos_a_vincular)

                total_servicios += 1

            self.stdout.write(f'  -> {total_servicios} servicios de catalogo con repuestos asociados.')

        self.stdout.write(self.style.SUCCESS(
            'Proceso completado exitosamente: Servicios y Repuestos de Lubricadora sincronizados.'
        ))
