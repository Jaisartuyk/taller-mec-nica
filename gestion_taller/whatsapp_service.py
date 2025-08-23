"""
Servicio de WhatsApp usando WASenderAPI
Integración para envío de notificaciones y recordatorios
"""

import requests
import json
import os
from django.conf import settings
from django.utils import timezone
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class WhatsAppService:
    def __init__(self):
        self.api_token = os.environ.get('WASENDER_API_TOKEN')
        self.instance_id = os.environ.get('WASENDER_INSTANCE_ID', 'default')
        
        # Detectar el proveedor basado en el token o configuración
        if 'wasenderapi.com' in os.environ.get('WASENDER_BASE_URL', '') or not os.environ.get('WASENDER_INSTANCE_ID'):
            # WasenderAPI.com format
            self.base_url = "https://wasenderapi.com/api"
            self.use_instance_id = False
        else:
            # WASender.com format (original)
            self.base_url = "https://api.wasender.com/v1"
            self.use_instance_id = True
        
        # Configurar estado del servicio
        self.is_configured = bool(self.api_token)
        
        if not self.api_token:
            logger.warning("WASENDER_API_TOKEN no está configurado. WhatsApp estará deshabilitado.")
        elif self.use_instance_id and not self.instance_id:
            logger.warning("WASENDER_INSTANCE_ID no está configurado para este proveedor. WhatsApp estará deshabilitado.")
            self.is_configured = False
        
    def send_message(self, phone_number, message, message_type="text"):
        """
        Envía un mensaje de WhatsApp
        
        Args:
            phone_number (str): Número de teléfono con código de país (ej: +57xxxxxxxxx)
            message (str): Mensaje a enviar
            message_type (str): Tipo de mensaje (text, image, document, etc.)
        
        Returns:
            dict: Respuesta de la API
        """
        if not self.is_configured:
            logger.warning("WhatsApp no está configurado. Mensaje no enviado.")
            return {"success": False, "error": "WhatsApp no configurado"}
        
        # Limpiar número de teléfono
        phone_number = self._clean_phone_number(phone_number)
        
        headers = {
            'Authorization': f'Bearer {self.api_token}',
            'Content-Type': 'application/json'
        }
        
        # Preparar payload según el proveedor
        if self.use_instance_id:
            # Formato original (wasender.com)
            payload = {
                "instance_id": self.instance_id,
                "to": phone_number,
                "type": message_type,
                "message": message
            }
            endpoint = f"{self.base_url}/messages"
        else:
            # Formato wasenderapi.com
            payload = {
                "to": phone_number,
                "text": message
            }
            endpoint = f"{self.base_url}/send-message"
        
        try:
            response = requests.post(
                endpoint,
                headers=headers,
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                logger.info(f"Mensaje WhatsApp enviado exitosamente a {phone_number}")
                return {"success": True, "data": response.json()}
            else:
                logger.error(f"Error enviando mensaje WhatsApp: {response.status_code} - {response.text}")
                return {"success": False, "error": f"HTTP {response.status_code}: {response.text}"}
                
        except requests.RequestException as e:
            logger.error(f"Error de conexión con WASender API: {e}")
            return {"success": False, "error": str(e)}
    
    def send_image(self, phone_number, image_url, caption=""):
        """Envía una imagen por WhatsApp"""
        payload = {
            "instance_id": self.instance_id,
            "to": self._clean_phone_number(phone_number),
            "type": "image",
            "message": {
                "url": image_url,
                "caption": caption
            }
        }
        return self._make_request(payload)
    
    def send_document(self, phone_number, document_url, filename, caption=""):
        """Envía un documento por WhatsApp"""
        payload = {
            "instance_id": self.instance_id,
            "to": self._clean_phone_number(phone_number),
            "type": "document",
            "message": {
                "url": document_url,
                "filename": filename,
                "caption": caption
            }
        }
        return self._make_request(payload)
    
    def _clean_phone_number(self, phone_number):
        """Limpia y formatea el número de teléfono"""
        # Remover espacios, guiones y paréntesis
        clean_number = ''.join(filter(str.isdigit, phone_number))
        
        # Si no tiene código de país, agregar +57 (Colombia)
        if not phone_number.startswith('+'):
            if len(clean_number) == 10:  # Número colombiano sin código
                clean_number = f"57{clean_number}"
            elif len(clean_number) == 12 and clean_number.startswith('57'):
                pass  # Ya tiene código de país
        
        return clean_number
    
    def _make_request(self, payload):
        """Método auxiliar para hacer requests a la API"""
        headers = {
            'Authorization': f'Bearer {self.token}',
            'Content-Type': 'application/json'
        }
        
        try:
            response = requests.post(
                f"{self.api_url}/messages",
                headers=headers,
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                return {"success": True, "data": response.json()}
            else:
                return {"success": False, "error": response.text}
                
        except requests.RequestException as e:
            return {"success": False, "error": str(e)}


# Funciones de conveniencia para usar en el resto de la aplicación
def enviar_recordatorio_whatsapp(conductor, mensaje_personalizado=None, vehiculo=None, recordatorio=None):
    """Envía recordatorio de mantenimiento por WhatsApp usando plantillas
    
    Args:
        conductor: Instancia del modelo Conductor
        mensaje_personalizado: Mensaje personalizado (opcional)
        vehiculo: Instancia del modelo Vehiculo (opcional)
        recordatorio: Instancia del modelo RecordatorioMantenimiento (opcional)
    
    Returns:
        dict: Resultado del envío
    """
    from .message_templates import MessageTemplates
    from django.utils import timezone
    
    whatsapp = WhatsAppService()
    
    if mensaje_personalizado:
        mensaje = mensaje_personalizado
    elif vehiculo and recordatorio:
        # Usar plantilla profesional con datos del recordatorio
        dias_restantes = (recordatorio.fecha_proximo - timezone.now().date()).days
        mensaje = MessageTemplates.recordatorio_mantenimiento(
            conductor, vehiculo, recordatorio, dias_restantes
        )
    else:
        # Mensaje genérico mejorado
        mensaje = f"""
🔧 **RECORDATORIO DE MANTENIMIENTO**

¡Hola {conductor.nombre}! 👋

Tu vehículo necesita mantenimiento preventivo.

📍 **Taller Mecánico Profesional**
📞 Contáctanos para agendar tu cita
⏰ **Horario:** Lun-Vie 8AM-6PM, Sáb 8AM-2PM

¡Mantén tu vehículo en perfecto estado! 🚗✨
        """.strip()
    
    return whatsapp.send_message(conductor.telefono, mensaje)


def enviar_notificacion_orden_lista(conductor, orden_servicio):
    """
    Notifica que una orden de servicio está lista
    
    Args:
        conductor: Instancia del modelo Conductor
        orden_servicio: Instancia del modelo OrdenServicio
    """
    if not conductor.telefono:
        return {"success": False, "error": "Sin teléfono"}
    
    whatsapp = WhatsAppService()
    
    mensaje = f"""
✅ *ORDEN DE SERVICIO COMPLETADA*

Hola {conductor.nombre}! 

Tu vehículo *{orden_servicio.vehiculo.marca} {orden_servicio.vehiculo.modelo}* (Placa: {orden_servicio.vehiculo.placa}) ya está listo! 🚗

📋 *Servicios realizados:*
{orden_servicio.descripcion}

💰 *Total:* ${orden_servicio.costo_total:,.0f}

📍 Puedes recogerlo en nuestro taller
📞 Cualquier duda, contáctanos

¡Gracias por confiar en nosotros! 🔧
    """.strip()
    
    return whatsapp.send_message(conductor.telefono, mensaje)


def enviar_confirmacion_cita(conductor, fecha_cita, servicio):
    """
    Envía confirmación de cita agendada
    
    Args:
        conductor: Instancia del modelo Conductor
        fecha_cita (datetime): Fecha y hora de la cita
        servicio (str): Descripción del servicio
    """
    if not conductor.telefono:
        return {"success": False, "error": "Sin teléfono"}
    
    whatsapp = WhatsAppService()
    
    fecha_formateada = fecha_cita.strftime("%d/%m/%Y a las %I:%M %p")
    
    mensaje = f"""
📅 *CITA CONFIRMADA*

Hola {conductor.nombre}! 

Tu cita ha sido agendada exitosamente:

🗓️ *Fecha:* {fecha_formateada}
🔧 *Servicio:* {servicio}
🚗 *Vehículo:* {conductor.vehiculo_set.first().marca if conductor.vehiculo_set.exists() else 'Por confirmar'}

📍 *Ubicación:* [Dirección del Taller]
📞 *Teléfono:* [Número del Taller]

⚠️ Por favor llega 10 minutos antes de tu cita.

¡Te esperamos! 🔧✨
    """.strip()

    return whatsapp.send_message(conductor.telefono, mensaje)


def enviar_confirmacion_cita_whatsapp(conductor, vehiculo, fecha_cita, servicio, direccion_taller="Taller Mecánico Profesional", telefono_taller="[Tu Número]"):
    """Envía confirmación de cita por WhatsApp usando plantillas

    Args:
        conductor: Instancia del modelo Conductor
        vehiculo: Instancia del modelo Vehiculo
        fecha_cita: Fecha y hora de la cita
        servicio: Tipo de servicio
        direccion_taller: Dirección del taller (opcional)
        telefono_taller: Teléfono del taller (opcional)
    
    Returns:
        dict: Resultado del envío
    """
    from .message_templates import MessageTemplates
    
    whatsapp = WhatsAppService()
    
    mensaje = MessageTemplates.confirmacion_cita(
        conductor, vehiculo, fecha_cita, servicio, direccion_taller, telefono_taller
    )
    
    return whatsapp.send_message(conductor.telefono, mensaje)


# Instancia global del servicio
whatsapp_service = WhatsAppService()
