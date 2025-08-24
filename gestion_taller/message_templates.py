"""
Sistema Avanzado de Plantillas de Mensajes WhatsApp
Agente Inteligente para Taller Mecánico - Mensajes Profesionales y Contextuales
"""

from datetime import datetime, timedelta
from django.utils import timezone
from decimal import Decimal
import re


class MessageTemplates:
    """Sistema de plantillas inteligentes para mensajes WhatsApp profesionales"""
    
    @staticmethod
    def recordatorio_mantenimiento(conductor, vehiculo, recordatorio, dias_restantes, taller_info=None):
        """Plantilla inteligente para recordatorio de mantenimiento"""
        
        # Lógica inteligente para determinar urgencia y tono
        if dias_restantes <= 0:
            urgencia = "🚨 **MANTENIMIENTO VENCIDO**"
            mensaje_tiempo = "Tu vehículo **necesita mantenimiento inmediato**"
            emoji_vehiculo = "🚗🔴"
            tono = "urgente"
            accion = "Agenda tu cita HOY mismo para evitar daños mayores"
        elif dias_restantes <= 3:
            urgencia = "⚠️ **MANTENIMIENTO URGENTE**"
            mensaje_tiempo = f"Tu vehículo necesita mantenimiento en **{dias_restantes} días**"
            emoji_vehiculo = "🚗⚡"
            tono = "importante"
            accion = "Te recomendamos agendar tu cita esta semana"
        elif dias_restantes <= 7:
            urgencia = "📅 **MANTENIMIENTO PROGRAMADO**"
            mensaje_tiempo = f"Tu vehículo necesitará mantenimiento en **{dias_restantes} días**"
            emoji_vehiculo = "🚗🔧"
            tono = "recordatorio"
            accion = "Puedes programar tu cita con anticipación"
        else:
            urgencia = "📅 **RECORDATORIO PREVENTIVO**"
            mensaje_tiempo = f"Tu vehículo necesitará mantenimiento en **{dias_restantes} días**"
            emoji_vehiculo = "🚗✨"
            tono = "preventivo"
            accion = "Planifica tu mantenimiento con tiempo"
        
        # Información del taller (dinámica)
        if taller_info:
            nombre_taller = taller_info.get('nombre', 'Taller Mecánico Profesional')
            telefono = taller_info.get('telefono', 'Contáctanos')
            direccion = taller_info.get('direccion', 'Visita nuestro taller')
            horario = taller_info.get('horario', 'Lun-Vie 8AM-6PM, Sáb 8AM-2PM')
        else:
            nombre_taller = "Taller Mecánico Profesional"
            telefono = "Contáctanos para agendar"
            direccion = "Visita nuestro taller"
            horario = "Lun-Vie 8AM-6PM, Sáb 8AM-2PM"
        
        # Mensaje personalizado según el tipo de servicio
        tipo_servicio = recordatorio.tipo.lower() if hasattr(recordatorio, 'tipo') else "mantenimiento"
        if "aceite" in tipo_servicio:
            consejo = "🛢️ **Consejo:** El aceite es la sangre de tu motor, no lo descuides"
        elif "frenos" in tipo_servicio:
            consejo = "🛑 **Consejo:** Unos frenos en buen estado pueden salvar vidas"
        elif "llantas" in tipo_servicio or "neumáticos" in tipo_servicio:
            consejo = "🛣️ **Consejo:** Llantas en buen estado mejoran el rendimiento y seguridad"
        else:
            consejo = "🔧 **Consejo:** El mantenimiento preventivo ahorra dinero a largo plazo"
        
        return f"""
{urgencia}

👋 ¡Hola **{conductor.nombre}**!

{mensaje_tiempo}

{emoji_vehiculo} **DETALLES DEL VEHÍCULO**
• **Marca/Modelo:** {vehiculo.marca} {vehiculo.modelo}
• **Placa:** {vehiculo.placa}
• **Servicio:** {recordatorio.tipo}
• **Fecha límite:** {recordatorio.fecha_proximo.strftime('%d/%m/%Y')}
• **Kilometraje:** {recordatorio.kilometraje_proximo:,} km

{consejo}

🏢 **{nombre_taller.upper()}**
📞 {telefono}
📍 {direccion}
⏰ **Horario:** {horario}

💬 **{accion}**

✨ *¡Tu vehículo merece el mejor cuidado!* ✨
        """.strip()
    
    @staticmethod
    def orden_completada(conductor, vehiculo, orden_servicio, servicios_realizados, total, taller_info=None, incluir_garantia=True):
        """Plantilla inteligente para notificación de orden completada"""
        
        # Formatear servicios con emojis según el tipo
        servicios_formateados = []
        for servicio in servicios_realizados:
            servicio_lower = servicio.lower()
            if "aceite" in servicio_lower:
                emoji = "🛢️"
            elif "frenos" in servicio_lower or "freno" in servicio_lower:
                emoji = "🛑"
            elif "llanta" in servicio_lower or "neumático" in servicio_lower:
                emoji = "🛣️"
            elif "motor" in servicio_lower:
                emoji = "⚙️"
            elif "transmisión" in servicio_lower:
                emoji = "🔄"
            elif "batería" in servicio_lower:
                emoji = "🔋"
            elif "suspensión" in servicio_lower:
                emoji = "💹"
            else:
                emoji = "🔧"
            servicios_formateados.append(f"{emoji} **{servicio}**")
        
        servicios_texto = "\n".join(servicios_formateados)
        
        # Información del taller
        if taller_info:
            nombre_taller = taller_info.get('nombre', 'Taller Mecánico Profesional')
            telefono = taller_info.get('telefono', 'Contáctanos')
            direccion = taller_info.get('direccion', 'Nuestro taller')
            horario = taller_info.get('horario', 'Lun-Vie 8AM-6PM, Sáb 8AM-2PM')
        else:
            nombre_taller = "Taller Mecánico Profesional"
            telefono = "Contáctanos"
            direccion = "Nuestro taller"
            horario = "Lun-Vie 8AM-6PM, Sáb 8AM-2PM"
        
        # Mensaje de garantía
        garantia_texto = ""
        if incluir_garantia:
            garantia_texto = "\n🛡️ **Garantía:** Todos nuestros servicios incluyen garantía\n📄 **Factura:** Conserva tu comprobante para cualquier reclamo"
        
        # Mensaje personalizado según la hora
        hora_actual = timezone.now().hour
        if 6 <= hora_actual < 12:
            saludo_tiempo = "🌅 ¡Buenos días"
        elif 12 <= hora_actual < 18:
            saludo_tiempo = "☀️ ¡Buenas tardes"
        else:
            saludo_tiempo = "🌆 ¡Buenas noches"
        
        # Calcular tiempo de trabajo (si está disponible)
        tiempo_trabajo = ""
        if hasattr(orden_servicio, 'fecha_inicio') and hasattr(orden_servicio, 'fecha_finalizacion'):
            if orden_servicio.fecha_inicio and orden_servicio.fecha_finalizacion:
                delta = orden_servicio.fecha_finalizacion - orden_servicio.fecha_inicio
                horas = delta.total_seconds() / 3600
                if horas < 24:
                    tiempo_trabajo = f"\n⏱️ **Tiempo de trabajo:** {horas:.1f} horas"
                else:
                    dias = delta.days
                    tiempo_trabajo = f"\n⏱️ **Tiempo de trabajo:** {dias} días"
        
        return f"""
✅ **TRABAJO COMPLETADO CON ÉXITO**

{saludo_tiempo} **{conductor.nombre}**! 😊

Tu **{vehiculo.marca} {vehiculo.modelo}** (Placa: **{vehiculo.placa}**) está listo para recoger! 🚗✨

🔧 **SERVICIOS REALIZADOS:**
{servicios_texto}{tiempo_trabajo}

💰 **TOTAL INVERTIDO:** ${total:,.0f}
{garantia_texto}

🏢 **RECOGE TU VEHÍCULO EN:**
📍 **{nombre_taller}**
📞 {telefono}
📍 {direccion}
⏰ **Horario:** {horario}

👏 **¡Gracias por confiar en nuestro equipo profesional!**

⭐ *Si quedaste satisfecho, ¡recómiendanos con tus amigos!* ⭐
        """.strip()
    
    @staticmethod
    def confirmacion_cita(conductor, vehiculo, fecha_cita, servicio, direccion_taller, telefono_taller):
        """Plantilla para confirmación de cita"""
        
        fecha_formateada = fecha_cita.strftime('%d/%m/%Y a las %I:%M %p')
        
        return f"""
📅 **CITA CONFIRMADA**

¡Hola {conductor.nombre}! 

Tu cita ha sido agendada exitosamente:

🗓️ **Fecha:** {fecha_formateada}
🔧 **Servicio:** {servicio}
🚗 **Vehículo:** {vehiculo.marca} {vehiculo.modelo} ({vehiculo.placa})

📍 **Ubicación:** {direccion_taller}
📞 **Teléfono:** {telefono_taller}

⚠️ **Por favor llega 10 minutos antes de tu cita.**

¡Te esperamos! 🔧✨
        """.strip()
    
    @staticmethod
    def recordatorio_cita(conductor, vehiculo, fecha_cita, servicio, horas_antes=24):
        """Plantilla para recordatorio de cita próxima"""
        
        fecha_formateada = fecha_cita.strftime('%d/%m/%Y a las %I:%M %p')
        
        if horas_antes <= 2:
            urgencia = "🚨 **RECORDATORIO URGENTE**"
            tiempo_texto = f"en {horas_antes} horas"
        elif horas_antes <= 24:
            urgencia = "⏰ **RECORDATORIO**"
            tiempo_texto = "mañana"
        else:
            urgencia = "📅 **RECORDATORIO**"
            tiempo_texto = f"en {horas_antes//24} días"
        
        return f"""
{urgencia}

¡Hola {conductor.nombre}! 👋

Tienes una cita programada {tiempo_texto}:

🗓️ **Fecha:** {fecha_formateada}
🔧 **Servicio:** {servicio}
🚗 **Vehículo:** {vehiculo.marca} {vehiculo.modelo}

📍 **Taller Mecánico Profesional**
📞 Si necesitas reprogramar, contáctanos

⚠️ **Llega 10 minutos antes de tu cita**

¡Nos vemos pronto! 🔧😊
        """.strip()
    
    @staticmethod
    def diagnostico_completado(conductor, vehiculo, diagnostico, recomendaciones, costo_estimado):
        """Plantilla para diagnóstico completado"""
        
        recomendaciones_texto = "\n".join([f"• {rec}" for rec in recomendaciones])
        
        return f"""
🔍 **DIAGNÓSTICO COMPLETADO**

¡Hola {conductor.nombre}!

Hemos completado el diagnóstico de tu {vehiculo.marca} {vehiculo.modelo} (Placa: {vehiculo.placa})

📋 **Diagnóstico:**
{diagnostico}

🔧 **Recomendaciones:**
{recomendaciones_texto}

💰 **Costo estimado:** ${costo_estimado:,.0f}

📞 **Contáctanos para:**
• Autorizar reparaciones
• Programar el servicio
• Resolver dudas

⏰ **Horario:** Lun-Vie 8AM-6PM, Sáb 8AM-2PM

¡Estamos aquí para ayudarte! 🔧👨‍🔧
        """.strip()
    
    @staticmethod
    def vehiculo_ingresado(conductor, vehiculo, fecha_ingreso, servicio_solicitado):
        """Plantilla para confirmación de ingreso de vehículo"""
        
        fecha_formateada = fecha_ingreso.strftime('%d/%m/%Y a las %I:%M %p')
        
        return f"""
📝 **VEHÍCULO INGRESADO**

¡Hola {conductor.nombre}!

Tu vehículo ha ingresado exitosamente a nuestro taller:

🚗 **Vehículo:** {vehiculo.marca} {vehiculo.modelo}
🏷️ **Placa:** {vehiculo.placa}
🕐 **Fecha de ingreso:** {fecha_formateada}
🔧 **Servicio solicitado:** {servicio_solicitado}

📱 **Te mantendremos informado del progreso**
📞 **Cualquier consulta, contáctanos**

¡Tu vehículo está en buenas manos! 🔧✨
        """.strip()
    
    @staticmethod
    def promocion_especial(conductor, titulo_promocion, descripcion, descuento, vigencia):
        """Plantilla para promociones especiales"""
        
        vigencia_formateada = vigencia.strftime('%d/%m/%Y')
        
        return f"""
🎉 **{titulo_promocion}**

¡Hola {conductor.nombre}! 

{descripcion}

💰 **Descuento:** {descuento}%
📅 **Válido hasta:** {vigencia_formateada}

🔧 **Servicios incluidos:**
• Cambio de aceite y filtros
• Revisión general
• Diagnóstico computarizado

📞 **Agenda tu cita y menciona esta promoción**
⏰ **Horario:** Lun-Vie 8AM-6PM, Sáb 8AM-2PM

¡No dejes pasar esta oportunidad! 🚗✨
        """.strip()
    
    @staticmethod
    def mensaje_personalizado(conductor, asunto, mensaje, incluir_firma=True):
        """Plantilla para mensajes personalizados"""
        
        mensaje_completo = f"""
📢 **{asunto}**

¡Hola {conductor.nombre}!

{mensaje}
        """.strip()
        
        if incluir_firma:
            mensaje_completo += f"""

📍 **Taller Mecánico Profesional**
📞 Contáctanos para más información
⏰ Horario: Lun-Vie 8AM-6PM, Sáb 8AM-2PM

¡Gracias por confiar en nosotros! 🔧⭐
            """.strip()
        
        return mensaje_completo
    
    # ==========================================
    # NUEVAS PLANTILLAS INTELIGENTES PARA NOTIFICACIONES AUTOMÁTICAS
    # ==========================================
    
    @staticmethod
    def nuevo_conductor_registrado(conductor, cliente_taller, admin_info=None):
        """Plantilla para notificar registro de nuevo conductor al cliente/taller"""
        
        fecha_registro = timezone.now().strftime('%d/%m/%Y a las %I:%M %p')
        
        # Mensaje para el administrador del taller
        if admin_info:
            return f"""
🆕 **NUEVO CONDUCTOR REGISTRADO**

👨‍💼 **Administrador {admin_info.get('nombre', 'Admin')}**,

Se ha registrado un nuevo conductor en tu taller:

👤 **DATOS DEL CONDUCTOR:**
• **Nombre:** {conductor.nombre}
• **Teléfono:** {conductor.telefono}
• **Email:** {conductor.email or 'No proporcionado'}
• **Fecha de registro:** {fecha_registro}

🏢 **Taller:** {cliente_taller.nombre}

📋 **PRÓXIMOS PASOS:**
• Verificar datos del conductor
• Asignar vehículos si corresponde
• Configurar servicios disponibles

💼 **Accede al panel administrativo para gestionar este conductor**

✅ *Sistema de gestión automática activado*
            """.strip()
        
        # Mensaje de bienvenida para el conductor
        return f"""
🎉 **¡BIENVENIDO A NUESTRO TALLER!**

👋 ¡Hola **{conductor.nombre}**!

Te damos la más cordial bienvenida a **{cliente_taller.nombre}**

✅ **TU REGISTRO HA SIDO EXITOSO**
📅 **Fecha:** {fecha_registro}

🚗 **SERVICIOS DISPONIBLES PARA TI:**
🔧 Mantenimiento preventivo y correctivo
🛢️ Cambio de aceite y filtros
🛑 Revisión de frenos y suspensión
⚙️ Diagnóstico computarizado
🔋 Servicio eléctrico y batería

📱 **BENEFICIOS DE SER NUESTRO CLIENTE:**
• Recordatorios automáticos de mantenimiento
• Notificaciones de trabajos completados
• Historial digital de servicios
• Atención personalizada vía WhatsApp

📞 **CONTACTO DIRECTO:**
• WhatsApp: Respuesta inmediata
• Emergencias: Soporte 24/7

🏢 **{cliente_taller.nombre.upper()}**
📍 Tu taller de confianza
⏰ **Horario:** Lun-Vie 8AM-6PM, Sáb 8AM-2PM

🌟 *¡Gracias por elegirnos como tu taller de confianza!* 🌟
        """.strip()
    
    @staticmethod
    def nuevo_vehiculo_registrado(conductor, vehiculo, taller_info=None):
        """Plantilla para notificar registro de nuevo vehículo"""
        
        fecha_registro = timezone.now().strftime('%d/%m/%Y')
        
        # Información del taller
        if taller_info:
            nombre_taller = taller_info.get('nombre', 'Taller Mecánico Profesional')
            telefono = taller_info.get('telefono', 'Contáctanos')
        else:
            nombre_taller = "Taller Mecánico Profesional"
            telefono = "Contáctanos"
        
        return f"""
🚗 **NUEVO VEHÍCULO REGISTRADO**

👋 ¡Hola **{conductor.nombre}**!

Hemos registrado exitosamente tu nuevo vehículo en nuestro sistema:

🚙 **DATOS DEL VEHÍCULO:**
• **Marca/Modelo:** {vehiculo.marca} {vehiculo.modelo}
• **Año:** {vehiculo.año}
• **Placa:** {vehiculo.placa}
• **Color:** {vehiculo.color}
• **Kilometraje actual:** {vehiculo.kilometraje:,} km
• **Fecha de registro:** {fecha_registro}

📋 **SERVICIOS CONFIGURADOS:**
✅ Recordatorios automáticos de mantenimiento
✅ Historial digital de servicios
✅ Notificaciones de trabajos completados
✅ Seguimiento de kilometraje

🔧 **RECOMENDACIONES INICIALES:**
• Programa tu primera revisión general
• Actualiza el kilometraje regularmente
• Mantén al día los servicios preventivos

📱 **PRÓXIMAS NOTIFICACIONES:**
Te enviaremos recordatorios automáticos basados en:
• Kilometraje del vehículo
• Fechas de servicios anteriores
• Recomendaciones del fabricante

🏢 **{nombre_taller.upper()}**
📞 {telefono}
⏰ **Horario:** Lun-Vie 8AM-6PM, Sáb 8AM-2PM

🎯 *¡Tu vehículo ahora está bajo nuestro cuidado profesional!* 🎯
        """.strip()
    
    @staticmethod
    def orden_servicio_creada(conductor, vehiculo, orden_servicio, servicios_solicitados, taller_info=None):
        """Plantilla para notificar creación de nueva orden de servicio"""
        
        fecha_creacion = orden_servicio.fecha_creacion.strftime('%d/%m/%Y a las %I:%M %p') if hasattr(orden_servicio, 'fecha_creacion') else timezone.now().strftime('%d/%m/%Y a las %I:%M %p')
        numero_orden = getattr(orden_servicio, 'numero_orden', 'N/A')
        
        # Formatear servicios solicitados
        servicios_texto = "\n".join([f"🔧 **{servicio}**" for servicio in servicios_solicitados])
        
        # Información del taller
        if taller_info:
            nombre_taller = taller_info.get('nombre', 'Taller Mecánico Profesional')
            telefono = taller_info.get('telefono', 'Contáctanos')
        else:
            nombre_taller = "Taller Mecánico Profesional"
            telefono = "Contáctanos"
        
        # Estimación de tiempo (lógica inteligente)
        total_servicios = len(servicios_solicitados)
        if total_servicios <= 2:
            tiempo_estimado = "2-4 horas"
            urgencia = "📅 **SERVICIO RÁPIDO**"
        elif total_servicios <= 4:
            tiempo_estimado = "4-8 horas"
            urgencia = "⏰ **SERVICIO ESTÁNDAR**"
        else:
            tiempo_estimado = "1-2 días"
            urgencia = "📋 **SERVICIO COMPLETO**"
        
        return f"""
📝 **ORDEN DE SERVICIO CREADA**

👋 ¡Hola **{conductor.nombre}**!

{urgencia}
Hemos creado tu orden de servicio exitosamente:

📋 **DETALLES DE LA ORDEN:**
• **Número:** #{numero_orden}
• **Fecha:** {fecha_creacion}
• **Vehículo:** {vehiculo.marca} {vehiculo.modelo}
• **Placa:** {vehiculo.placa}
• **Tiempo estimado:** {tiempo_estimado}

🔧 **SERVICIOS SOLICITADOS:**
{servicios_texto}

📊 **ESTADO ACTUAL:** En cola de trabajo

📱 **TE MANTENDREMOS INFORMADO:**
✅ Cuando iniciemos el trabajo
✅ Si encontramos algo adicional
✅ Cuando esté listo para recoger
✅ Costo final del servicio

🏢 **{nombre_taller.upper()}**
📞 {telefono}
💬 **Responde a este mensaje para cualquier consulta**

⚡ *¡Tu vehículo está en las mejores manos!* ⚡
        """.strip()
    
    @staticmethod
    def orden_en_progreso(conductor, vehiculo, orden_servicio, tecnico_asignado=None, progreso_actual=None):
        """Plantilla para notificar que la orden está en progreso"""
        
        numero_orden = getattr(orden_servicio, 'numero_orden', 'N/A')
        
        # Información del técnico
        if tecnico_asignado:
            info_tecnico = f"\n👨‍🔧 **Técnico asignado:** {tecnico_asignado}"
        else:
            info_tecnico = "\n👥 **Equipo técnico asignado**"
        
        # Progreso actual
        if progreso_actual:
            info_progreso = f"\n📊 **Progreso actual:** {progreso_actual}"
        else:
            info_progreso = "\n🔄 **Estado:** Trabajo en progreso"
        
        return f"""
🔧 **TRABAJO EN PROGRESO**

👋 ¡Hola **{conductor.nombre}**!

Tu **{vehiculo.marca} {vehiculo.modelo}** (Placa: **{vehiculo.placa}**) está siendo atendido:

📋 **ORDEN:** #{numero_orden}{info_tecnico}{info_progreso}

⚡ **ACTUALIZACIONES EN TIEMPO REAL:**
• Nuestro equipo está trabajando en tu vehículo
• Te notificaremos cualquier hallazgo importante
• Recibirás confirmación cuando esté listo

📱 **¿TIENES ALGUNA PREGUNTA?**
Responde a este mensaje y te atenderemos inmediatamente

🎯 *¡Estamos comprometidos con la excelencia en cada trabajo!* 🎯
        """.strip()
    
    @staticmethod
    def diagnostico_adicional_requerido(conductor, vehiculo, orden_servicio, problema_encontrado, costo_adicional=None):
        """Plantilla para solicitar autorización de trabajo adicional"""
        
        numero_orden = getattr(orden_servicio, 'numero_orden', 'N/A')
        
        # Información de costo adicional
        if costo_adicional:
            info_costo = f"\n💰 **Costo adicional estimado:** ${costo_adicional:,.0f}"
        else:
            info_costo = "\n💰 **Costo:** Te proporcionaremos una cotización detallada"
        
        return f"""
🔍 **DIAGNÓSTICO ADICIONAL REQUERIDO**

👋 **{conductor.nombre}**, necesitamos tu autorización:

Mientras trabajábamos en tu **{vehiculo.marca} {vehiculo.modelo}** (Orden #{numero_orden}), nuestro equipo técnico encontró:

⚠️ **PROBLEMA DETECTADO:**
{problema_encontrado}

🔧 **RECOMENDACIÓN TÉCNICA:**
Para garantizar la seguridad y el rendimiento óptimo de tu vehículo, recomendamos atender este problema.{info_costo}

📞 **NECESITAMOS TU DECISIÓN:**
✅ Responde "SÍ" para autorizar el trabajo
❌ Responde "NO" si prefieres dejarlo para después
💬 Responde "COTIZACIÓN" para más detalles

⏰ **TIEMPO DE RESPUESTA:**
Esperamos tu respuesta para continuar con el trabajo

🛡️ *Tu seguridad es nuestra prioridad* 🛡️
        """.strip()


class MessageFormatter:
    """Utilidades para formatear mensajes"""
    
    @staticmethod
    def format_currency(amount):
        """Formatea cantidad como moneda colombiana"""
        return f"${amount:,.0f} COP"
    
    @staticmethod
    def format_phone(phone):
        """Formatea número de teléfono para mostrar"""
        if phone.startswith('+57'):
            return f"{phone[:3]} {phone[3:6]} {phone[6:9]} {phone[9:]}"
        return phone
    
    @staticmethod
    def format_date_relative(date):
        """Formatea fecha de manera relativa (hoy, mañana, etc.)"""
        today = timezone.now().date()
        diff = (date - today).days
        
        if diff == 0:
            return "hoy"
        elif diff == 1:
            return "mañana"
        elif diff == -1:
            return "ayer"
        elif diff > 1:
            return f"en {diff} días"
        else:
            return f"hace {abs(diff)} días"
    
    @staticmethod
    def truncate_message(message, max_length=1000):
        """Trunca mensaje si es muy largo"""
        if len(message) <= max_length:
            return message
        
        return message[:max_length-3] + "..."
    
    @staticmethod
    def add_business_signature():
        """Agrega firma comercial estándar"""
        return """
📍 **Taller Mecánico Profesional**
📞 Contáctanos: [Tu Número]
🌐 Web: [Tu Sitio Web]
📧 Email: [Tu Email]
⏰ Horario: Lun-Vie 8AM-6PM, Sáb 8AM-2PM

¡Tu confianza es nuestro compromiso! 🔧⭐
        """.strip()


# Configuración de mensajes por defecto
DEFAULT_SETTINGS = {
    'include_signature': True,
    'max_message_length': 1000,
    'business_name': 'Taller Mecánico Profesional',
    'business_hours': 'Lun-Vie 8AM-6PM, Sáb 8AM-2PM',
    'contact_phone': '[Tu Número]',
    'website': '[Tu Sitio Web]',
    'email': '[Tu Email]'
}
