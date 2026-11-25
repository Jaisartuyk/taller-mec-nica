"""
Capa central de Herramientas (Function Calling) para el Agente IA de WhatsApp
y el Copiloto IA Interno del taller.

Todas las operaciones están aisladas por tenant (cliente = taller) y respetan
el nivel de permisos según el modo ('whatsapp' vs 'interno').
"""
from datetime import datetime, timedelta
from decimal import Decimal
from django.db.models import Q, F, Sum
from django.utils import timezone


TONOS_DESCRIPCION = {
    'profesional_cercano': 'profesional, cálido y cercano',
    'formal': 'formal, respetuoso y corporativo',
    'amigable': 'amigable, relajado y empático',
    'directo': 'directo, claro y conciso',
}


def construir_contexto_config_taller(cliente) -> str:
    """Construye el bloque de contexto estructurado a partir de ConfiguracionTaller."""
    config = getattr(cliente, 'configuracion', None)
    nombre_taller = (config.nombre if config and config.nombre else cliente.nombre)
    lineas = [f"INFORMACIÓN DEL TALLER '{nombre_taller}':"]

    if config:
        if config.horarios:
            lineas.append(f"- Horario de atención: {config.horarios}")
        if config.direccion:
            lineas.append(f"- Dirección: {config.direccion}")
        if config.telefono_principal:
            lineas.append(f"- Teléfono: {config.telefono_principal}")
        if config.tiempo_aproximado_atencion:
            lineas.append(f"- Tiempo aproximado de atención: {config.tiempo_aproximado_atencion}")
        if config.promociones:
            lineas.append(f"- Promociones vigentes: {config.promociones}")
        if config.politicas_cancelacion:
            lineas.append(f"- Políticas de cancelación: {config.politicas_cancelacion}")
        if config.informacion_adicional:
            lineas.append(f"- Información adicional: {config.informacion_adicional}")
        if config.agente_ia_prompt:
            lineas.append(f"- Notas adicionales: {config.agente_ia_prompt}")

    return "\n".join(lineas)


class TallerAITools:
    """
    Ejecutor de herramientas sobre los modelos Django del taller.
    - modo='whatsapp': restringido a los datos del cliente final (conductor_actual).
    - modo='interno': acceso completo para administrador y empleados del taller.
    """

    HERRAMIENTAS_WHATSAPP = {
        'buscar_cliente',
        'crear_cliente',
        'buscar_vehiculo',
        'crear_vehiculo',
        'listar_servicios',
        'consultar_disponibilidad',
        'crear_cita',
        'reprogramar_cita',
        'cancelar_cita',
        'consultar_orden',
        'consultar_repuesto',
        'transferir_a_humano',
    }

    HERRAMIENTAS_INTERNO = {
        'buscar_cliente',
        'crear_cliente',
        'buscar_vehiculo',
        'crear_vehiculo',
        'listar_servicios',
        'consultar_disponibilidad',
        'crear_cita',
        'reprogramar_cita',
        'cancelar_cita',
        'consultar_orden',
        'consultar_repuesto',
        'crear_orden',
        'consultar_ingresos',
        'consultar_stock_bajo',
    }

    def __init__(self, cliente, modo: str = 'interno', conductor_actual=None, telefono_remitente: str = ''):
        self.cliente = cliente
        self.modo = modo
        self.conductor_actual = conductor_actual
        self.telefono_remitente = (telefono_remitente or '').strip()
        self.transferido_a_humano = False

    def _permitidas(self) -> set:
        if self.modo == 'whatsapp':
            config = getattr(self.cliente, 'configuracion', None)
            permitidas = set(self.HERRAMIENTAS_WHATSAPP)
            if config and not config.agente_ia_transferencia_humano:
                permitidas.discard('transferir_a_humano')
            return permitidas
        return set(self.HERRAMIENTAS_INTERNO)

    def ejecutar(self, nombre_funcion: str, args: dict) -> dict:
        if nombre_funcion not in self._permitidas():
            return {'ok': False, 'error': f"Herramienta '{nombre_funcion}' no permitida en modo {self.modo}."}

        metodo = getattr(self, nombre_funcion, None)
        if not metodo:
            return {'ok': False, 'error': f"Herramienta '{nombre_funcion}' no encontrada."}

        try:
            return metodo(**(args or {}))
        except TypeError as exc:
            return {'ok': False, 'error': f"Parámetros inválidos para {nombre_funcion}: {exc}"}
        except Exception as exc:
            return {'ok': False, 'error': f"Error ejecutando {nombre_funcion}: {exc}"}

    # ------------------------------------------------------------------
    # HERRAMIENTAS DE CLIENTES (Conductor en el modelo Django)
    # ------------------------------------------------------------------
    def buscar_cliente(self, consulta: str = '') -> dict:
        from gestion_taller.models import Conductor

        if self.modo == 'whatsapp':
            cond = self.conductor_actual
            if not cond and self.telefono_remitente:
                digitos = ''.join(c for c in self.telefono_remitente if c.isdigit())[-9:]
                cond = Conductor.objects.filter(cliente=self.cliente, telefono__icontains=digitos).first()
                self.conductor_actual = cond
            if not cond:
                return {'ok': True, 'encontrado': False, 'mensaje': 'Cliente aún no registrado.'}
            return {
                'ok': True,
                'encontrado': True,
                'clientes': [{
                    'id': cond.id,
                    'nombre': cond.nombre,
                    'telefono': cond.telefono,
                    'correo': cond.correo or '',
                }],
            }

        qs = Conductor.objects.filter(cliente=self.cliente)
        if consulta:
            qs = qs.filter(
                Q(nombre__icontains=consulta) |
                Q(telefono__icontains=consulta) |
                Q(correo__icontains=consulta)
            )
        resultados = [
            {'id': c.id, 'nombre': c.nombre, 'telefono': c.telefono, 'correo': c.correo or ''}
            for c in qs.order_by('-fecha_registro')[:10]
        ]
        return {'ok': True, 'encontrado': bool(resultados), 'clientes': resultados}

    def crear_cliente(self, nombre: str, telefono: str = '', correo: str = '', direccion: str = '') -> dict:
        from gestion_taller.models import Conductor

        tel = (telefono or self.telefono_remitente or '').strip()
        if not nombre or not tel:
            return {'ok': False, 'error': 'Se requiere nombre y teléfono para registrar al cliente.'}

        existente = Conductor.objects.filter(cliente=self.cliente, telefono__icontains=tel[-9:]).first()
        if existente:
            self.conductor_actual = existente
            return {
                'ok': True,
                'creado': False,
                'mensaje': 'El cliente ya existía.',
                'cliente': {'id': existente.id, 'nombre': existente.nombre, 'telefono': existente.telefono},
            }

        nuevo = Conductor.objects.create(
            cliente=self.cliente,
            nombre=nombre.strip(),
            telefono=tel,
            correo=(correo or '').strip(),
            direccion=(direccion or '').strip(),
        )
        if self.modo == 'whatsapp':
            self.conductor_actual = nuevo
        return {
            'ok': True,
            'creado': True,
            'cliente': {'id': nuevo.id, 'nombre': nuevo.nombre, 'telefono': nuevo.telefono},
        }

    # ------------------------------------------------------------------
    # HERRAMIENTAS DE VEHÍCULOS
    # ------------------------------------------------------------------
    def buscar_vehiculo(self, placa: str = '', cliente_id: int = None) -> dict:
        from django.db.models import Value
        from django.db.models.functions import Replace
        from gestion_taller.models import Vehiculo

        qs = Vehiculo.objects.filter(cliente=self.cliente, activo=True).select_related('conductor')
        placa_norm = (placa or '').replace('-', '').replace(' ', '').upper().strip()
        if self.modo == 'whatsapp':
            if self.conductor_actual:
                qs = qs.filter(conductor=self.conductor_actual)
            elif placa_norm:
                qs = qs.annotate(
                    placa_limpia=Replace(Replace('placa', Value('-'), Value('')), Value(' '), Value(''))
                ).filter(placa_limpia__icontains=placa_norm)
            else:
                return {'ok': True, 'encontrado': False, 'vehiculos': []}
        else:
            if cliente_id:
                qs = qs.filter(conductor_id=cliente_id)
            if placa_norm:
                qs = qs.annotate(
                    placa_limpia=Replace(Replace('placa', Value('-'), Value('')), Value(' '), Value(''))
                ).filter(placa_limpia__icontains=placa_norm)

        vehiculos = [
            {
                'id': v.id,
                'placa': v.placa,
                'marca': v.marca,
                'modelo': v.modelo,
                'anio': v.anio,
                'kilometraje': v.kilometraje,
                'cliente_id': v.conductor_id,
                'cliente_nombre': v.conductor.nombre if v.conductor else 'Sin asignar',
            }
            for v in qs[:10]
        ]
        return {'ok': True, 'encontrado': bool(vehiculos), 'vehiculos': vehiculos}

    def crear_vehiculo(
        self,
        placa: str,
        marca: str,
        modelo: str,
        anio: int = None,
        kilometraje: int = 0,
        cliente_id: int = None,
    ) -> dict:
        from gestion_taller.models import Vehiculo, Conductor

        placa_limpia = placa.replace(' ', '').upper().strip()
        if not placa_limpia or not marca or not modelo:
            return {'ok': False, 'error': 'Se requiere placa, marca y modelo.'}

        conductor = self.conductor_actual
        if self.modo == 'interno' and cliente_id:
            conductor = Conductor.objects.filter(cliente=self.cliente, id=cliente_id).first()

        existente = Vehiculo.objects.filter(cliente=self.cliente, placa__iexact=placa_limpia).first()
        if existente:
            return {
                'ok': True,
                'creado': False,
                'vehiculo': {
                    'id': existente.id,
                    'placa': existente.placa,
                    'marca': existente.marca,
                    'modelo': existente.modelo,
                },
            }

        nuevo = Vehiculo.objects.create(
            cliente=self.cliente,
            conductor=conductor,
            placa=placa_limpia,
            marca=marca.strip(),
            modelo=modelo.strip(),
            anio=anio or timezone.now().year,
            kilometraje=int(kilometraje or 0),
        )
        return {
            'ok': True,
            'creado': True,
            'vehiculo': {
                'id': nuevo.id,
                'placa': nuevo.placa,
                'marca': nuevo.marca,
                'modelo': nuevo.modelo,
                'anio': nuevo.anio,
            },
        }

    # ------------------------------------------------------------------
    # SERVICIOS Y DISPONIBILIDAD
    # ------------------------------------------------------------------
    def listar_servicios(self, busqueda: str = '') -> dict:
        from gestion_taller.models import ServicioCatalogo

        qs = ServicioCatalogo.objects.filter(cliente=self.cliente, activo=True)
        if busqueda:
            qs = qs.filter(Q(nombre__icontains=busqueda) | Q(descripcion__icontains=busqueda))
        servicios = [
            {
                'id': s.id,
                'nombre': s.nombre,
                'precio_base': float(s.precio_base),
                'descripcion': (s.descripcion or '')[:120],
            }
            for s in qs.order_by('nombre')[:25]
        ]
        return {'ok': True, 'servicios': servicios}

    def consultar_disponibilidad(self, fecha: str) -> dict:
        """
        Consulta horarios disponibles para una fecha YYYY-MM-DD.
        Devuelve bloques horarios reales que no estén ocupados en Cita.
        """
        from gestion_taller.models import Cita

        try:
            fecha_obj = datetime.strptime(fecha.strip(), '%Y-%m-%d').date()
        except ValueError:
            return {'ok': False, 'error': 'Formato de fecha inválido. Usa YYYY-MM-DD.'}

        hoy = timezone.localdate()
        if fecha_obj < hoy:
            return {'ok': False, 'error': 'No se puede consultar disponibilidad en fechas pasadas.'}

        # Bloques estándar del taller (08:30 a 17:00)
        bloques = ['08:30', '09:30', '10:30', '11:30', '14:00', '15:00', '16:00', '17:00']
        citas_dia = Cita.objects.filter(
            cliente=self.cliente,
            fecha_cita__date=fecha_obj,
            estado__in=['pendiente', 'confirmada'],
        )
        ocupados = {timezone.localtime(c.fecha_cita).strftime('%H:%M') for c in citas_dia}

        ahora = timezone.localtime()
        disponibles = []
        for hora in bloques:
            if hora in ocupados:
                continue
            if fecha_obj == hoy:
                h, m = map(int, hora.split(':'))
                if (h, m) <= (ahora.hour, ahora.minute):
                    continue
            disponibles.append(hora)

        return {
            'ok': True,
            'fecha': fecha_obj.strftime('%Y-%m-%d'),
            'horarios_disponibles': disponibles,
            'horarios_ocupados': sorted(list(ocupados)),
        }

    # ------------------------------------------------------------------
    # CITAS (Crear, Reprogramar, Cancelar)
    # ------------------------------------------------------------------
    def _parsear_fecha_hora(self, fecha: str, hora: str):
        dt_naive = datetime.strptime(f"{fecha.strip()} {hora.strip()}", '%Y-%m-%d %H:%M')
        return timezone.make_aware(dt_naive, timezone.get_current_timezone())

    def crear_cita(
        self,
        fecha: str,
        hora: str,
        notas: str = '',
        cliente_id: int = None,
        vehiculo_id: int = None,
    ) -> dict:
        from gestion_taller.models import Cita, Conductor, Vehiculo

        try:
            fecha_dt = self._parsear_fecha_hora(fecha, hora)
        except ValueError:
            return {'ok': False, 'error': 'Usa fecha YYYY-MM-DD y hora HH:MM (24h).'}

        # Validar disponibilidad real en BD antes de guardar
        conflicto = Cita.objects.filter(
            cliente=self.cliente,
            fecha_cita=fecha_dt,
            estado__in=['pendiente', 'confirmada'],
        ).exists()
        if conflicto:
            return {'ok': False, 'error': f'El horario {fecha} {hora} ya fue ocupado. Consulta otro horario.'}

        conductor = self.conductor_actual
        if self.modo == 'interno' and cliente_id:
            conductor = Conductor.objects.filter(cliente=self.cliente, id=cliente_id).first()

        vehiculo = None
        if vehiculo_id:
            vehiculo = Vehiculo.objects.filter(cliente=self.cliente, id=vehiculo_id).first()
        elif conductor:
            vehiculo = Vehiculo.objects.filter(cliente=self.cliente, conductor=conductor, activo=True).first()

        cita = Cita.objects.create(
            cliente=self.cliente,
            conductor=conductor,
            vehiculo=vehiculo,
            fecha_cita=fecha_dt,
            estado='confirmada',
            notas=(notas or '').strip(),
        )
        return {
            'ok': True,
            'cita': {
                'id': cita.id,
                'fecha': timezone.localtime(cita.fecha_cita).strftime('%Y-%m-%d %H:%M'),
                'estado': cita.estado,
                'cliente': conductor.nombre if conductor else 'Sin asignar',
                'vehiculo': vehiculo.placa if vehiculo else 'Sin asignar',
                'notas': cita.notas,
            },
        }

    def reprogramar_cita(self, cita_id: int, nueva_fecha: str, nueva_hora: str) -> dict:
        from gestion_taller.models import Cita

        qs = Cita.objects.filter(cliente=self.cliente, id=cita_id)
        if self.modo == 'whatsapp' and self.conductor_actual:
            qs = qs.filter(conductor=self.conductor_actual)
        cita = qs.first()
        if not cita:
            return {'ok': False, 'error': f'No se encontró la cita #{cita_id}.'}

        try:
            nueva_dt = self._parsear_fecha_hora(nueva_fecha, nueva_hora)
        except ValueError:
            return {'ok': False, 'error': 'Usa nueva_fecha YYYY-MM-DD y nueva_hora HH:MM.'}

        conflicto = Cita.objects.filter(
            cliente=self.cliente,
            fecha_cita=nueva_dt,
            estado__in=['pendiente', 'confirmada'],
        ).exclude(id=cita.id).exists()
        if conflicto:
            return {'ok': False, 'error': f'El horario {nueva_fecha} {nueva_hora} ya está ocupado.'}

        cita.fecha_cita = nueva_dt
        cita.estado = 'confirmada'
        cita.save(update_fields=['fecha_cita', 'estado'])
        return {
            'ok': True,
            'cita_id': cita.id,
            'nueva_fecha': timezone.localtime(cita.fecha_cita).strftime('%Y-%m-%d %H:%M'),
        }

    def cancelar_cita(self, cita_id: int, motivo: str = '') -> dict:
        from gestion_taller.models import Cita

        qs = Cita.objects.filter(cliente=self.cliente, id=cita_id)
        if self.modo == 'whatsapp' and self.conductor_actual:
            qs = qs.filter(conductor=self.conductor_actual)
        cita = qs.first()
        if not cita:
            return {'ok': False, 'error': f'No se encontró la cita #{cita_id}.'}

        cita.estado = 'cancelada'
        if motivo:
            cita.notas = f"{cita.notas} | Cancelada: {motivo}".strip(' |')
        cita.save(update_fields=['estado', 'notas'])
        return {'ok': True, 'cita_id': cita.id, 'estado': 'cancelada'}

    # ------------------------------------------------------------------
    # ÓRDENES DE SERVICIO E INVENTARIO
    # ------------------------------------------------------------------
    def consultar_orden(self, orden_id: int = None, placa: str = '', cliente_id: int = None) -> dict:
        from gestion_taller.models import OrdenServicio

        qs = OrdenServicio.objects.filter(cliente=self.cliente).select_related('vehiculo', 'conductor')
        if self.modo == 'whatsapp':
            if not self.conductor_actual:
                return {'ok': True, 'ordenes': [], 'mensaje': 'No se identificó al cliente.'}
            qs = qs.filter(conductor=self.conductor_actual)
        else:
            if cliente_id:
                qs = qs.filter(conductor_id=cliente_id)

        if orden_id:
            qs = qs.filter(id=orden_id)
        if placa:
            from django.db.models import Value
            from django.db.models.functions import Replace
            placa_norm = placa.replace('-', '').replace(' ', '').upper().strip()
            qs = qs.annotate(
                placa_limpia=Replace(Replace('vehiculo__placa', Value('-'), Value('')), Value(' '), Value(''))
            ).filter(placa_limpia__icontains=placa_norm)

        ordenes = [
            {
                'id': o.id,
                'estado': o.get_estado_display(),
                'total': float(o.total),
                'pagada': o.pagada,
                'fecha': o.fecha_creacion.strftime('%Y-%m-%d'),
                'vehiculo': o.vehiculo.placa if o.vehiculo else 'N/A',
                'cliente': o.conductor.nombre if o.conductor else 'N/A',
            }
            for o in qs.order_by('-fecha_creacion')[:8]
        ]
        return {'ok': True, 'ordenes': ordenes}

    def consultar_repuesto(self, busqueda: str = '') -> dict:
        from gestion_taller.models import Repuesto

        qs = Repuesto.objects.filter(cliente=self.cliente)
        if busqueda:
            qs = qs.filter(Q(nombre__icontains=busqueda) | Q(codigo__icontains=busqueda))

        repuestos = []
        for r in qs.order_by('nombre')[:15]:
            item = {
                'id': r.id,
                'nombre': r.nombre,
                'disponible': r.stock > 0,
                'precio_venta': float(r.precio_venta),
            }
            if self.modo == 'interno':
                item['codigo'] = r.codigo or ''
                item['stock'] = r.stock
                item['stock_minimo'] = r.stock_minimo
            repuestos.append(item)
        return {'ok': True, 'repuestos': repuestos}

    # ------------------------------------------------------------------
    # TRANSFERENCIA A HUMANO (Solo WhatsApp)
    # ------------------------------------------------------------------
    def transferir_a_humano(self, motivo: str = '') -> dict:
        self.transferido_a_humano = True
        if self.conductor_actual:
            self.conductor_actual.bot_pausado = True
            self.conductor_actual.save(update_fields=['bot_pausado'])
        return {
            'ok': True,
            'transferido': True,
            'motivo': motivo or 'Solicitud de atención con un asesor humano.',
        }

    # ------------------------------------------------------------------
    # HERRAMIENTAS EXCLUSIVAS DEL COPILOTO INTERNO (Admin / Empleados)
    # ------------------------------------------------------------------
    def crear_orden(self, vehiculo_id: int, cliente_id: int = None, kilometraje: int = 0) -> dict:
        from gestion_taller.models import OrdenServicio, Vehiculo, Conductor

        vehiculo = Vehiculo.objects.filter(cliente=self.cliente, id=vehiculo_id).select_related('conductor').first()
        if not vehiculo:
            return {'ok': False, 'error': f'No se encontró el vehículo #{vehiculo_id}.'}

        conductor = vehiculo.conductor
        if cliente_id:
            conductor = Conductor.objects.filter(cliente=self.cliente, id=cliente_id).first() or conductor

        orden = OrdenServicio.objects.create(
            cliente=self.cliente,
            vehiculo=vehiculo,
            conductor=conductor,
            kilometraje=int(kilometraje or vehiculo.kilometraje or 0),
            estado='pendiente',
            total=Decimal('0.00'),
        )
        return {
            'ok': True,
            'orden': {
                'id': orden.id,
                'estado': orden.estado,
                'vehiculo': vehiculo.placa,
                'cliente': conductor.nombre if conductor else 'Sin asignar',
            },
        }

    def consultar_ingresos(self, dias: int = 30) -> dict:
        from gestion_taller.models import OrdenServicio

        hoy = timezone.localdate()
        desde = hoy - timedelta(days=max(1, int(dias or 30)))
        ordenes = OrdenServicio.objects.filter(
            cliente=self.cliente,
            estado__in=['completada', 'facturada'],
            fecha_creacion__date__gte=desde,
        )
        total = ordenes.aggregate(t=Sum('total'))['t'] or Decimal('0.00')
        return {
            'ok': True,
            'desde': desde.strftime('%Y-%m-%d'),
            'hasta': hoy.strftime('%Y-%m-%d'),
            'ordenes_completadas': ordenes.count(),
            'ingresos_totales': float(total),
        }

    def consultar_stock_bajo(self) -> dict:
        from gestion_taller.models import Repuesto

        bajos = list(
            Repuesto.objects.filter(cliente=self.cliente, stock__lte=F('stock_minimo'))
            .values('id', 'nombre', 'codigo', 'stock', 'stock_minimo', 'precio_venta')[:20]
        )
        for r in bajos:
            r['precio_venta'] = float(r['precio_venta'])
        return {'ok': True, 'total_bajos': len(bajos), 'repuestos': bajos}

    # ------------------------------------------------------------------
    # DECLARACIONES DE HERRAMIENTAS PARA GEMINI FUNCTION CALLING
    # ------------------------------------------------------------------
    def get_gemini_tool_declarations(self) -> list:
        todas = [
            {
                'name': 'buscar_cliente',
                'description': 'Busca un cliente del taller por nombre, teléfono o correo. En WhatsApp identifica automáticamente al remitente.',
                'parameters': {
                    'type': 'OBJECT',
                    'properties': {
                        'consulta': {'type': 'STRING', 'description': 'Nombre, teléfono o correo a buscar (opcional en WhatsApp).'},
                    },
                },
            },
            {
                'name': 'crear_cliente',
                'description': 'Registra un nuevo cliente en el taller.',
                'parameters': {
                    'type': 'OBJECT',
                    'properties': {
                        'nombre': {'type': 'STRING', 'description': 'Nombre completo del cliente.'},
                        'telefono': {'type': 'STRING', 'description': 'Teléfono con código de país o local.'},
                        'correo': {'type': 'STRING', 'description': 'Correo electrónico (opcional).'},
                        'direccion': {'type': 'STRING', 'description': 'Dirección (opcional).'},
                    },
                    'required': ['nombre'],
                },
            },
            {
                'name': 'buscar_vehiculo',
                'description': 'Busca vehículos registrados por placa o por ID de cliente.',
                'parameters': {
                    'type': 'OBJECT',
                    'properties': {
                        'placa': {'type': 'STRING', 'description': 'Placa del vehículo (ej. ABC1234).'},
                        'cliente_id': {'type': 'INTEGER', 'description': 'ID del cliente propietario.'},
                    },
                },
            },
            {
                'name': 'crear_vehiculo',
                'description': 'Registra un nuevo vehículo en el taller.',
                'parameters': {
                    'type': 'OBJECT',
                    'properties': {
                        'placa': {'type': 'STRING', 'description': 'Placa del vehículo.'},
                        'marca': {'type': 'STRING', 'description': 'Marca (ej. Toyota, Chevrolet).'},
                        'modelo': {'type': 'STRING', 'description': 'Modelo (ej. Corolla, Spark).'},
                        'anio': {'type': 'INTEGER', 'description': 'Año del vehículo.'},
                        'kilometraje': {'type': 'INTEGER', 'description': 'Kilometraje actual.'},
                        'cliente_id': {'type': 'INTEGER', 'description': 'ID del cliente propietario.'},
                    },
                    'required': ['placa', 'marca', 'modelo'],
                },
            },
            {
                'name': 'listar_servicios',
                'description': 'Lista los servicios activos del catálogo del taller con sus precios reales.',
                'parameters': {
                    'type': 'OBJECT',
                    'properties': {
                        'busqueda': {'type': 'STRING', 'description': 'Filtro opcional por nombre de servicio.'},
                    },
                },
            },
            {
                'name': 'consultar_disponibilidad',
                'description': 'Consulta los horarios reales disponibles en la agenda del taller para una fecha.',
                'parameters': {
                    'type': 'OBJECT',
                    'properties': {
                        'fecha': {'type': 'STRING', 'description': 'Fecha en formato YYYY-MM-DD.'},
                    },
                    'required': ['fecha'],
                },
            },
            {
                'name': 'crear_cita',
                'description': 'Agenda una nueva cita en la agenda del taller después de verificar disponibilidad.',
                'parameters': {
                    'type': 'OBJECT',
                    'properties': {
                        'fecha': {'type': 'STRING', 'description': 'Fecha en formato YYYY-MM-DD.'},
                        'hora': {'type': 'STRING', 'description': 'Hora en formato HH:MM (24 horas, ej. 10:30).'},
                        'notas': {'type': 'STRING', 'description': 'Servicio solicitado o detalles.'},
                        'cliente_id': {'type': 'INTEGER', 'description': 'ID del cliente.'},
                        'vehiculo_id': {'type': 'INTEGER', 'description': 'ID del vehículo.'},
                    },
                    'required': ['fecha', 'hora'],
                },
            },
            {
                'name': 'reprogramar_cita',
                'description': 'Cambia la fecha y hora de una cita existente.',
                'parameters': {
                    'type': 'OBJECT',
                    'properties': {
                        'cita_id': {'type': 'INTEGER', 'description': 'ID de la cita.'},
                        'nueva_fecha': {'type': 'STRING', 'description': 'Nueva fecha YYYY-MM-DD.'},
                        'nueva_hora': {'type': 'STRING', 'description': 'Nueva hora HH:MM.'},
                    },
                    'required': ['cita_id', 'nueva_fecha', 'nueva_hora'],
                },
            },
            {
                'name': 'cancelar_cita',
                'description': 'Cancela una cita existente.',
                'parameters': {
                    'type': 'OBJECT',
                    'properties': {
                        'cita_id': {'type': 'INTEGER', 'description': 'ID de la cita a cancelar.'},
                        'motivo': {'type': 'STRING', 'description': 'Motivo de la cancelación.'},
                    },
                    'required': ['cita_id'],
                },
            },
            {
                'name': 'consultar_orden',
                'description': 'Consulta órdenes de servicio por ID, placa o cliente.',
                'parameters': {
                    'type': 'OBJECT',
                    'properties': {
                        'orden_id': {'type': 'INTEGER', 'description': 'ID de la orden.'},
                        'placa': {'type': 'STRING', 'description': 'Placa del vehículo.'},
                        'cliente_id': {'type': 'INTEGER', 'description': 'ID del cliente.'},
                    },
                },
            },
            {
                'name': 'consultar_repuesto',
                'description': 'Consulta disponibilidad, stock y precio de repuestos en inventario.',
                'parameters': {
                    'type': 'OBJECT',
                    'properties': {
                        'busqueda': {'type': 'STRING', 'description': 'Nombre o código del repuesto.'},
                    },
                },
            },
            {
                'name': 'transferir_a_humano',
                'description': 'Pausa el bot y transfiere la conversación a un asesor humano del taller.',
                'parameters': {
                    'type': 'OBJECT',
                    'properties': {
                        'motivo': {'type': 'STRING', 'description': 'Razón de la transferencia.'},
                    },
                },
            },
            {
                'name': 'crear_orden',
                'description': 'Crea una nueva orden de servicio para un vehículo registrado (solo uso interno).',
                'parameters': {
                    'type': 'OBJECT',
                    'properties': {
                        'vehiculo_id': {'type': 'INTEGER', 'description': 'ID del vehículo.'},
                        'cliente_id': {'type': 'INTEGER', 'description': 'ID del cliente (opcional si el vehículo ya tiene propietario).'},
                        'kilometraje': {'type': 'INTEGER', 'description': 'Kilometraje actual del vehículo.'},
                    },
                    'required': ['vehiculo_id'],
                },
            },
            {
                'name': 'consultar_ingresos',
                'description': 'Consulta los ingresos totales de órdenes completadas/facturadas en los últimos N días.',
                'parameters': {
                    'type': 'OBJECT',
                    'properties': {
                        'dias': {'type': 'INTEGER', 'description': 'Cantidad de días hacia atrás (ej. 7 o 30).'},
                    },
                },
            },
            {
                'name': 'consultar_stock_bajo',
                'description': 'Lista los repuestos que están por debajo o igual al stock mínimo.',
            },
        ]
        permitidas = self._permitidas()
        return [d for d in todas if d['name'] in permitidas]
