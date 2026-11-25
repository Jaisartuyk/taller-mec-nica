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

    def responder(self, mensaje_usuario: str) -> dict:
        ctx = self._recopilar_contexto_taller()
        vehiculo_encontrado, ordenes_vehiculo = self._buscar_placa_en_mensaje(mensaje_usuario)

        api_key = os.environ.get('GEMINI_API_KEY', '').strip()
        if api_key:
            respuesta_ia = self._consultar_gemini(api_key, mensaje_usuario, ctx, vehiculo_encontrado, ordenes_vehiculo)
            if respuesta_ia:
                return {'respuesta': respuesta_ia, 'modo': 'gemini'}

        return {
            'respuesta': self._respuesta_local(mensaje_usuario, ctx, vehiculo_encontrado, ordenes_vehiculo),
            'modo': 'analitico'
        }

    def _consultar_gemini(self, api_key, mensaje_usuario, ctx, vehiculo, ordenes_vehiculo):
        nombre_agente = (self.config.agente_ia_nombre if self.config and self.config.agente_ia_nombre else 'Copiloto IA')
        prompt_extra = (self.config.agente_ia_prompt if self.config and self.config.agente_ia_prompt else '')

        citas_txt = "\n".join(
            f"- {c.fecha_cita.strftime('%d/%m %H:%M')} | {c.conductor.nombre if c.conductor else 'Sin nombre'} | {c.vehiculo.placa if c.vehiculo else 'Sin placa'} ({c.estado})"
            for c in ctx['citas_proximas']
        ) or "Ninguna"

        stock_txt = "\n".join(
            f"- {r['nombre']}: {r['stock']} uds (mínimo {r['stock_minimo']})"
            for r in ctx['repuestos_bajos']
        ) or "Todo el inventario está sobre el mínimo."

        servicios_txt = "\n".join(
            f"- {s['nombre']}: ${s['precio_base']}"
            for s in ctx['servicios_activos']
        ) or "Sin servicios cargados."

        vehiculo_txt = ""
        if vehiculo:
            ord_txt = ", ".join(f"#{o.id} ({o.estado}, ${o.total})" for o in ordenes_vehiculo) or "Sin órdenes"
            vehiculo_txt = (
                f"\nVEHÍCULO CONSULTADO: {vehiculo.placa} - {vehiculo.marca} {vehiculo.modelo} ({vehiculo.anio}), "
                f"Km: {vehiculo.kilometraje}, Propietario: {vehiculo.conductor.nombre if vehiculo.conductor else 'Sin asignar'}. "
                f"Últimas órdenes: {ord_txt}."
            )

        system_prompt = (
            f"Eres {nombre_agente}, el copiloto inteligente del taller '{self.cliente.nombre}'. "
            f"Responde siempre en español, de forma clara, concisa y profesional con datos reales del taller.\n"
            f"{prompt_extra}\n\n"
            f"DATOS EN TIEMPO REAL DEL TALLER ({ctx['hoy']}):\n"
            f"- Órdenes pendientes: {ctx['ordenes_pendientes']} | En progreso: {ctx['ordenes_progreso']}\n"
            f"- Órdenes completadas/facturadas este mes: {ctx['ordenes_completadas_mes']}\n"
            f"- Ingresos últimos 7 días: ${ctx['ingresos_semana']:.2f} | Ingresos este mes: ${ctx['ingresos_mes']:.2f}\n"
            f"- Total vehículos registrados: {ctx['total_vehiculos']}\n"
            f"- Recordatorios de mantenimiento vencidos: {ctx['recordatorios_vencidos']}\n"
            f"- Repuestos con stock bajo:\n{stock_txt}\n"
            f"- Próximas citas:\n{citas_txt}\n"
            f"- Catálogo de servicios:\n{servicios_txt}"
            f"{vehiculo_txt}\n\n"
            f"Pregunta del usuario: {mensaje_usuario}"
        )

        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"
            resp = requests.post(
                url,
                json={"contents": [{"parts": [{"text": system_prompt}]}]},
                timeout=15,
            )
            if resp.status_code == 200:
                data = resp.json()
                return data['candidates'][0]['content']['parts'][0]['text']
        except Exception:
            pass
        return None

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
