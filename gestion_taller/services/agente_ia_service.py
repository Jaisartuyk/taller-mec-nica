import os
import re
import requests
from datetime import timedelta
from decimal import Decimal
from django.db.models import Sum, F
from django.utils import timezone


class AgenteIATallerService:
    """
    Copiloto IA Multi-tenant para el dueño y equipo del taller.
    Consulta exclusivamente los datos del Cliente (taller) autenticado.
    Usa Gemini API si GEMINI_API_KEY está configurada; si no, responde con motor analítico local.
    """

    def __init__(self, cliente):
        self.cliente = cliente
        self.config = getattr(cliente, 'configuracion', None)

    def _recopilar_contexto_taller(self):
        from gestion_taller.models import (
            OrdenServicio, Repuesto, Vehiculo, Cita, ServicioCatalogo, RecordatorioMantenimiento
        )

        hoy = timezone.now().date()
        inicio_mes = hoy.replace(day=1)
        hace_7_dias = hoy - timedelta(days=7)

        ordenes = OrdenServicio.objects.filter(cliente=self.cliente)
        ordenes_pendientes = ordenes.filter(estado='pendiente').count()
        ordenes_progreso = ordenes.filter(estado='en_progreso').count()
        ordenes_completadas_mes = ordenes.filter(
            estado__in=['completada', 'facturada'],
            fecha_creacion__date__gte=inicio_mes
        )
        ingresos_mes = ordenes_completadas_mes.aggregate(t=Sum('total'))['t'] or Decimal('0.00')
        ingresos_semana = ordenes.filter(
            estado__in=['completada', 'facturada'],
            fecha_creacion__date__gte=hace_7_dias
        ).aggregate(t=Sum('total'))['t'] or Decimal('0.00')

        repuestos_bajos = list(
            Repuesto.objects.filter(cliente=self.cliente, stock__lte=F('stock_minimo'))
            .values('nombre', 'stock', 'stock_minimo', 'precio_venta')[:10]
        )
        total_vehiculos = Vehiculo.objects.filter(cliente=self.cliente).count()
        citas_proximas = list(
            Cita.objects.filter(
                cliente=self.cliente,
                fecha_cita__date__gte=hoy,
                estado__in=['pendiente', 'confirmada']
            ).select_related('conductor', 'vehiculo').order_by('fecha_cita')[:8]
        )
        servicios_activos = list(
            ServicioCatalogo.objects.filter(cliente=self.cliente, activo=True)
            .values('nombre', 'precio_base')[:15]
        )
        recordatorios_vencidos = RecordatorioMantenimiento.objects.filter(
            vehiculo__cliente=self.cliente,
            notificado=False,
            fecha_proximo__lt=hoy
        ).count()

        return {
            'hoy': hoy,
            'ordenes_pendientes': ordenes_pendientes,
            'ordenes_progreso': ordenes_progreso,
            'ordenes_completadas_mes': ordenes_completadas_mes.count(),
            'ingresos_mes': ingresos_mes,
            'ingresos_semana': ingresos_semana,
            'repuestos_bajos': repuestos_bajos,
            'total_vehiculos': total_vehiculos,
            'citas_proximas': citas_proximas,
            'servicios_activos': servicios_activos,
            'recordatorios_vencidos': recordatorios_vencidos,
        }

    def _buscar_placa_en_mensaje(self, mensaje):
        from gestion_taller.models import Vehiculo, OrdenServicio
        posibles = re.findall(r'\b[A-Za-z]{2,4}-?\d{3,4}\b', mensaje)
        for token in posibles:
            placa_limpia = token.replace('-', '').upper()
            vehiculo = Vehiculo.objects.filter(
                cliente=self.cliente,
                placa__icontains=placa_limpia
            ).select_related('conductor').first()
            if vehiculo:
                ultimas_ordenes = OrdenServicio.objects.filter(
                    cliente=self.cliente, vehiculo=vehiculo
                ).order_by('-fecha_creacion')[:3]
                return vehiculo, list(ultimas_ordenes)
        return None, []

    def _construir_system_instruction(self, modo: str) -> str:
        from gestion_taller.services.ai_tools import (
            construir_contexto_config_taller,
            TONOS_DESCRIPCION,
        )

        hoy = timezone.localdate().strftime('%Y-%m-%d')
        nombre_agente = (
            self.config.agente_ia_nombre
            if self.config and self.config.agente_ia_nombre
            else ('Asistente Virtual' if modo == 'whatsapp' else 'Copiloto IA')
        )
        tono_key = (self.config.agente_ia_tono if self.config else 'profesional_cercano')
        tono_desc = TONOS_DESCRIPCION.get(tono_key, 'profesional, cálido y cercano')
        contexto_taller = construir_contexto_config_taller(self.cliente)

        if modo == 'whatsapp':
            regla_transferencia = (
                "Si el cliente pide hablar con una persona o hay un caso complejo, usa transferir_a_humano()."
                if (not self.config or self.config.agente_ia_transferencia_humano)
                else "No transfieras a humano; resuelve con la información disponible."
            )
            return (
                f"Eres {nombre_agente}, el agente de atención al cliente del taller '{self.cliente.nombre}'.\n"
                f"Fecha actual: {hoy}.\n"
                f"Tono de atención: {tono_desc}.\n\n"
                f"{contexto_taller}\n\n"
                "REGLAS GENERALES OBLIGATORIAS:\n"
                "1. Responde siempre en español, claro y breve (ideal para WhatsApp).\n"
                "2. NUNCA inventes horarios, precios, órdenes ni stock. Usa SIEMPRE las herramientas disponibles.\n"
                "3. Para agendar una cita: consulta disponibilidad real con consultar_disponibilidad(), ofrece opciones reales y confirma con el cliente antes de llamar a crear_cita().\n"
                "4. Usa listar_servicios() para responder sobre servicios y precios.\n"
                f"5. {regla_transferencia}\n"
            )

        return (
            f"Eres {nombre_agente}, el Copiloto IA interno para el equipo y administrador del taller '{self.cliente.nombre}'.\n"
            f"Fecha actual: {hoy}.\n"
            f"Tono de atención: {tono_desc}.\n\n"
            f"{contexto_taller}\n\n"
            "REGLAS GENERALES OBLIGATORIAS:\n"
            "1. Responde siempre en español, de forma clara, ejecutiva y directa.\n"
            "2. Usa las herramientas disponibles para consultar clientes, vehículos, citas, órdenes, repuestos, stock bajo e ingresos en tiempo real.\n"
            "3. Puedes crear clientes, vehículos, citas y órdenes de servicio cuando el administrador o empleado te lo pida.\n"
            "4. Si falta algún dato obligatorio para crear un registro (ej. placa o fecha), pídelo brevemente antes de ejecutar la acción.\n"
            "5. NUNCA inventes datos que no provengan de las herramientas.\n"
        )

    def _ejecutar_gemini_con_herramientas(
        self,
        api_key: str,
        mensaje_usuario: str,
        modo: str,
        conductor_actual=None,
        telefono_remitente: str = '',
        historial: list = None,
    ):
        from gestion_taller.services.ai_tools import TallerAITools

        tools = TallerAITools(
            self.cliente,
            modo=modo,
            conductor_actual=conductor_actual,
            telefono_remitente=telefono_remitente,
        )
        declarations = tools.get_gemini_tool_declarations()
        system_instruction = self._construir_system_instruction(modo)

        contents = []
        if historial:
            for item in historial[-8:]:
                role = 'model' if item.get('role') in ('model', 'assistant') else 'user'
                texto = (item.get('text') or '').strip()
                if texto:
                    contents.append({'role': role, 'parts': [{'text': texto}]})
        contents.append({'role': 'user', 'parts': [{'text': mensaje_usuario}]})

        modelo_principal = os.environ.get('GEMINI_MODEL', 'gemini-3.8-flash').strip() or 'gemini-3.8-flash'
        modelos_candidatos = []
        for m in (modelo_principal, 'gemini-2.5-flash-lite', 'gemini-flash-latest'):
            if m and m not in modelos_candidatos:
                modelos_candidatos.append(m)

        herramientas_usadas = []
        modelo_activo = modelos_candidatos[0]

        for _ in range(5):
            payload = {
                'system_instruction': {'parts': [{'text': system_instruction}]},
                'contents': contents,
                'tools': [{'functionDeclarations': declarations}],
            }
            data = None
            modelos_a_probar = [modelo_activo] + [m for m in modelos_candidatos if m != modelo_activo]
            for candidato_modelo in modelos_a_probar:
                url = f"https://generativelanguage.googleapis.com/v1beta/models/{candidato_modelo}:generateContent?key={api_key}"
                try:
                    resp = requests.post(url, json=payload, timeout=20)
                    if resp.status_code == 200:
                        modelo_activo = candidato_modelo
                        data = resp.json()
                        break
                    import logging
                    logging.getLogger(__name__).warning(
                        "Gemini API error %s (%s): %s", resp.status_code, candidato_modelo, resp.text[:300]
                    )
                    if resp.status_code not in (404, 429, 503):
                        return None, tools, herramientas_usadas
                except Exception as exc:
                    import logging
                    logging.getLogger(__name__).warning("Gemini API exception (%s): %s", candidato_modelo, exc)

            if not data:
                return None, tools, herramientas_usadas

            candidate = (data.get('candidates') or [{}])[0]
            content = candidate.get('content') or {}
            parts = content.get('parts') or []

            function_calls = [p['functionCall'] for p in parts if 'functionCall' in p]
            if not function_calls:
                textos = [p.get('text', '') for p in parts if 'text' in p]
                respuesta_final = "\n".join(t for t in textos if t).strip()
                return (respuesta_final or None), tools, herramientas_usadas

            # Agregar la respuesta del modelo (con sus functionCall) al historial del turno
            contents.append({'role': 'model', 'parts': parts})

            # Ejecutar cada herramienta solicitada y devolver functionResponse
            response_parts = []
            for fc in function_calls:
                nombre_fn = fc.get('name', '')
                args_fn = fc.get('args') or {}
                resultado = tools.ejecutar(nombre_fn, args_fn)
                herramientas_usadas.append(nombre_fn)
                response_parts.append({
                    'functionResponse': {
                        'name': nombre_fn,
                        'response': {'result': resultado},
                    }
                })
            contents.append({'role': 'user', 'parts': response_parts})

        return None, tools, herramientas_usadas

    def responder(self, mensaje_usuario: str, historial: list = None) -> dict:
        api_key = os.environ.get('GEMINI_API_KEY', '').strip()
        if api_key:
            respuesta_ia, _tools, usadas = self._ejecutar_gemini_con_herramientas(
                api_key=api_key,
                mensaje_usuario=mensaje_usuario,
                modo='interno',
                historial=historial,
            )
            if respuesta_ia:
                return {
                    'respuesta': respuesta_ia,
                    'modo': 'gemini_tools',
                    'herramientas_usadas': usadas,
                }

        ctx = self._recopilar_contexto_taller()
        vehiculo_encontrado, ordenes_vehiculo = self._buscar_placa_en_mensaje(mensaje_usuario)
        return {
            'respuesta': self._respuesta_local(mensaje_usuario, ctx, vehiculo_encontrado, ordenes_vehiculo),
            'modo': 'analitico',
            'herramientas_usadas': [],
        }

    def responder_whatsapp(
        self,
        mensaje_usuario: str,
        conductor_actual=None,
        telefono_remitente: str = '',
        historial: list = None,
    ) -> dict:
        api_key = os.environ.get('GEMINI_API_KEY', '').strip()
        if not api_key:
            return {'ok': False, 'respuesta': None, 'transferido_a_humano': False}

        respuesta_ia, tools, usadas = self._ejecutar_gemini_con_herramientas(
            api_key=api_key,
            mensaje_usuario=mensaje_usuario,
            modo='whatsapp',
            conductor_actual=conductor_actual,
            telefono_remitente=telefono_remitente,
            historial=historial,
        )
        return {
            'ok': bool(respuesta_ia),
            'respuesta': respuesta_ia,
            'transferido_a_humano': tools.transferido_a_humano,
            'herramientas_usadas': usadas,
        }

    def _respuesta_local(self, mensaje, ctx, vehiculo, ordenes_vehiculo):
        msg = mensaje.lower()

        if vehiculo:
            propietario = vehiculo.conductor.nombre if vehiculo.conductor else "Sin asignar"
            lineas = [
                f"🚗 **Vehículo {vehiculo.placa}** — {vehiculo.marca} {vehiculo.modelo} ({vehiculo.anio})",
                f"• Propietario: {propietario}",
                f"• Kilometraje registrado: {vehiculo.kilometraje:,} km",
            ]
            if ordenes_vehiculo:
                lineas.append("• Últimas órdenes:")
                for o in ordenes_vehiculo:
                    lineas.append(f"  - Orden #{o.id}: {o.get_estado_display()} — ${o.total:.2f} ({o.fecha_creacion.strftime('%d/%m/%Y')})")
            else:
                lineas.append("• Aún no tiene órdenes de servicio registradas.")
            return "\n".join(lineas)

        if any(k in msg for k in ['stock', 'inventario', 'repuesto', 'falta', 'agotado']):
            if not ctx['repuestos_bajos']:
                return "✅ **Inventario saludable:** No tienes repuestos por debajo del stock mínimo en este momento."
            lineas = ["⚠️ **Repuestos con stock bajo o agotado:**"]
            for r in ctx['repuestos_bajos']:
                lineas.append(f"• {r['nombre']}: quedan **{r['stock']}** uds (mínimo: {r['stock_minimo']}) — PVP ${r['precio_venta']}")
            return "\n".join(lineas)

        if any(k in msg for k in ['venta', 'ingreso', 'factur', 'dinero', 'ganancia', 'plata', 'mes', 'semana']):
            return (
                f"💰 **Reporte de Ingresos — {self.cliente.nombre}**\n"
                f"• Últimos 7 días: **${ctx['ingresos_semana']:.2f}**\n"
                f"• Acumulado del mes: **${ctx['ingresos_mes']:.2f}** ({ctx['ordenes_completadas_mes']} órdenes completadas/facturadas)\n"
                f"• Órdenes aún abiertas: {ctx['ordenes_pendientes']} pendientes y {ctx['ordenes_progreso']} en progreso."
            )

        if any(k in msg for k in ['cita', 'agenda', 'mañana', 'turno']):
            if not ctx['citas_proximas']:
                return "📅 No tienes citas pendientes ni confirmadas para los próximos días."
            lineas = ["📅 **Próximas citas agendadas:**"]
            for c in ctx['citas_proximas']:
                cond = c.conductor.nombre if c.conductor else "Sin cliente"
                placa = c.vehiculo.placa if c.vehiculo else "Sin placa"
                lineas.append(f"• {c.fecha_cita.strftime('%d/%m/%Y %H:%M')} — {cond} ({placa}) [{c.estado}]")
            return "\n".join(lineas)

        if any(k in msg for k in ['servicio', 'precio', 'tarifa', 'catalogo', 'catálogo']):
            if not ctx['servicios_activos']:
                return "🔧 Aún no tienes servicios activos en tu catálogo."
            lineas = ["🔧 **Catálogo de servicios activos:**"]
            for s in ctx['servicios_activos']:
                lineas.append(f"• {s['nombre']}: **${s['precio_base']}**")
            return "\n".join(lineas)

        return (
            f"📊 **Resumen en tiempo real — {self.cliente.nombre}**\n"
            f"• Órdenes pendientes: **{ctx['ordenes_pendientes']}** | En progreso: **{ctx['ordenes_progreso']}**\n"
            f"• Ingresos del mes: **${ctx['ingresos_mes']:.2f}** (últimos 7 días: ${ctx['ingresos_semana']:.2f})\n"
            f"• Repuestos con stock bajo: **{len(ctx['repuestos_bajos'])}**\n"
            f"• Próximas citas: **{len(ctx['citas_proximas'])}** | Recordatorios vencidos: **{ctx['recordatorios_vencidos']}**\n"
            f"• Flota registrada: **{ctx['total_vehiculos']}** vehículos\n\n"
            f"💡 Puedes preguntarme por **ingresos**, **stock bajo**, **citas**, **precios del catálogo** o escribir una **placa** (ej. `GTJ4569`)."
        )
