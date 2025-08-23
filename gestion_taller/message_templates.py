"""
Sistema de plantillas de mensajes para WhatsApp y Telegram
Proporciona mensajes profesionales y consistentes para el taller mecánico
"""

from datetime import datetime
from django.utils import timezone


class MessageTemplates:
    """Plantillas de mensajes para diferentes tipos de notificaciones"""
    
    @staticmethod
    def recordatorio_mantenimiento(conductor, vehiculo, recordatorio, dias_restantes):
        """Plantilla para recordatorio de mantenimiento"""
        
        # Determinar urgencia y emoji
        if dias_restantes <= 0:
            urgencia = "🚨 *URGENTE*"
            mensaje_tiempo = "Tu vehículo necesita mantenimiento **HOY**"
            emoji_vehiculo = "🚗💨"
        elif dias_restantes <= 3:
            urgencia = "⚠️ *IMPORTANTE*"
            mensaje_tiempo = f"Tu vehículo necesita mantenimiento en **{dias_restantes} días**"
            emoji_vehiculo = "🚗⚡"
        else:
            urgencia = "📅 *RECORDATORIO*"
            mensaje_tiempo = f"Tu vehículo necesitará mantenimiento en **{dias_restantes} días**"
            emoji_vehiculo = "🚗✨"
        
        return f"""
{urgencia}

¡Hola {conductor.nombre}! 👋

{mensaje_tiempo}

{emoji_vehiculo} **Vehículo:** {vehiculo.marca} {vehiculo.modelo}
🏷️ **Placa:** {vehiculo.placa}
🔧 **Servicio:** {recordatorio.tipo}
📅 **Fecha recomendada:** {recordatorio.fecha_proximo.strftime('%d/%m/%Y')}
📏 **Kilometraje:** {recordatorio.kilometraje_proximo:,} km

📍 **Taller Mecánico Profesional**
📞 Contáctanos para agendar tu cita
⏰ Horario: Lun-Vie 8AM-6PM, Sáb 8AM-2PM

¡Mantén tu vehículo en perfecto estado! 🔧✨
        """.strip()
    
    @staticmethod
    def orden_completada(conductor, vehiculo, orden_servicio, servicios_realizados, total):
        """Plantilla para notificación de orden completada"""
        
        servicios_texto = "\n".join([f"• {servicio}" for servicio in servicios_realizados])
        
        return f"""
✅ **ORDEN DE SERVICIO COMPLETADA**

¡Hola {conductor.nombre}! 😊

Tu vehículo {vehiculo.marca} {vehiculo.modelo} (Placa: {vehiculo.placa}) ya está listo! 🚗

📋 **Servicios realizados:**
{servicios_texto}

💰 **Total:** ${total:,.0f}

📍 **Puedes recogerlo en nuestro taller**
📞 Cualquier duda, contáctanos
🕐 **Horario:** Lun-Vie 8AM-6PM, Sáb 8AM-2PM

¡Gracias por confiar en nosotros! 🔧⭐
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
