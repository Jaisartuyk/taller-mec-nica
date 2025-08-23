"""
Configuración centralizada del taller mecánico
Maneja configuraciones de negocio, mensajería y personalización
"""

import os
from django.conf import settings
from django.core.cache import cache


class TallerConfig:
    """Configuración centralizada del taller mecánico"""
    
    # Configuración de negocio
    BUSINESS_NAME = "Taller Mecánico Profesional"
    BUSINESS_HOURS = "Lun-Vie 8AM-6PM, Sáb 8AM-2PM"
    BUSINESS_PHONE = "+57 300 123 4567"
    BUSINESS_EMAIL = "info@tallerprofesional.com"
    BUSINESS_WEBSITE = "www.tallerprofesional.com"
    BUSINESS_ADDRESS = "Calle 123 #45-67, Bogotá, Colombia"
    
    # Configuración de WhatsApp
    WHATSAPP_ENABLED = True
    WHATSAPP_API_TOKEN = os.environ.get('WASENDER_API_TOKEN')
    WHATSAPP_INSTANCE_ID = os.environ.get('WASENDER_INSTANCE_ID')
    WHATSAPP_RATE_LIMIT = 30  # mensajes por minuto
    
    # Configuración de Telegram
    TELEGRAM_ENABLED = True
    TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
    TELEGRAM_RATE_LIMIT = 30  # mensajes por minuto
    
    # Configuración de notificaciones
    NOTIFICATION_DEFAULTS = {
        'recordatorios_dias_anticipacion': 7,
        'recordatorios_urgentes_dias': 3,
        'incluir_firma_comercial': True,
        'usar_emojis': True,
        'canal_preferido': 'ambos',  # telegram, whatsapp, ambos
        'horario_envio_inicio': '08:00',
        'horario_envio_fin': '18:00',
    }
    
    # Configuración de servicios
    SERVICIOS_COMUNES = [
        'Cambio de aceite y filtros',
        'Mantenimiento preventivo',
        'Diagnóstico computarizado',
        'Reparación de frenos',
        'Alineación y balanceo',
        'Cambio de llantas',
        'Reparación de motor',
        'Reparación de transmisión',
        'Sistema eléctrico',
        'Sistema de refrigeración'
    ]
    
    # Configuración de precios base (en COP)
    PRECIOS_BASE = {
        'cambio_aceite': 80000,
        'mantenimiento_preventivo': 150000,
        'diagnostico': 50000,
        'frenos': 200000,
        'alineacion': 60000,
        'hora_mano_obra': 25000
    }
    
    @classmethod
    def get_business_info(cls):
        """Retorna información básica del negocio"""
        return {
            'name': cls.BUSINESS_NAME,
            'hours': cls.BUSINESS_HOURS,
            'phone': cls.BUSINESS_PHONE,
            'email': cls.BUSINESS_EMAIL,
            'website': cls.BUSINESS_WEBSITE,
            'address': cls.BUSINESS_ADDRESS
        }
    
    @classmethod
    def get_signature(cls):
        """Retorna firma comercial estándar"""
        return f"""
📍 **{cls.BUSINESS_NAME}**
📞 {cls.BUSINESS_PHONE}
🌐 {cls.BUSINESS_WEBSITE}
📧 {cls.BUSINESS_EMAIL}
⏰ {cls.BUSINESS_HOURS}

¡Tu confianza es nuestro compromiso! 🔧⭐
        """.strip()
    
    @classmethod
    def is_whatsapp_enabled(cls):
        """Verifica si WhatsApp está habilitado y configurado"""
        # Solo verificar token - algunos proveedores no necesitan instance_id
        return (cls.WHATSAPP_ENABLED and 
                cls.WHATSAPP_API_TOKEN)
    
    @classmethod
    def is_telegram_enabled(cls):
        """Verifica si Telegram está habilitado y configurado"""
        return cls.TELEGRAM_ENABLED and cls.TELEGRAM_BOT_TOKEN
    
    @classmethod
    def get_available_channels(cls):
        """Retorna canales de comunicación disponibles"""
        channels = []
        if cls.is_whatsapp_enabled():
            channels.append('whatsapp')
        if cls.is_telegram_enabled():
            channels.append('telegram')
        return channels
    
    @classmethod
    def get_notification_config(cls):
        """Retorna configuración de notificaciones"""
        return cls.NOTIFICATION_DEFAULTS.copy()
    
    @classmethod
    def update_business_info(cls, **kwargs):
        """Actualiza información del negocio (para futuro admin panel)"""
        for key, value in kwargs.items():
            attr_name = f'BUSINESS_{key.upper()}'
            if hasattr(cls, attr_name):
                setattr(cls, attr_name, value)
                # Invalidar cache si existe
                cache.delete(f'taller_config_{key}')


class MessageConfig:
    """Configuración específica para mensajes"""
    
    # Emojis por tipo de mensaje
    EMOJIS = {
        'recordatorio': '🔧',
        'urgente': '🚨',
        'importante': '⚠️',
        'confirmacion': '✅',
        'cita': '📅',
        'completado': '✅',
        'diagnostico': '🔍',
        'promocion': '🎉',
        'vehiculo': '🚗',
        'telefono': '📞',
        'ubicacion': '📍',
        'horario': '⏰',
        'precio': '💰'
    }
    
    # Plantillas de asuntos
    ASUNTOS = {
        'recordatorio_mantenimiento': 'RECORDATORIO DE MANTENIMIENTO',
        'orden_completada': 'ORDEN DE SERVICIO COMPLETADA',
        'cita_confirmada': 'CITA CONFIRMADA',
        'diagnostico_listo': 'DIAGNÓSTICO COMPLETADO',
        'vehiculo_ingresado': 'VEHÍCULO INGRESADO',
        'promocion_especial': 'PROMOCIÓN ESPECIAL'
    }
    
    # Configuración de formato
    FORMAT_CONFIG = {
        'usar_negritas': True,
        'usar_emojis': True,
        'incluir_firma': True,
        'max_longitud': 1000,
        'separador_seccion': '\n\n'
    }
    
    @classmethod
    def get_emoji(cls, tipo):
        """Retorna emoji para tipo de mensaje"""
        return cls.EMOJIS.get(tipo, '📢')
    
    @classmethod
    def get_asunto(cls, tipo):
        """Retorna asunto formateado para tipo de mensaje"""
        asunto = cls.ASUNTOS.get(tipo, 'NOTIFICACIÓN')
        if cls.FORMAT_CONFIG['usar_emojis']:
            emoji = cls.get_emoji(tipo)
            return f"{emoji} **{asunto}**"
        return f"**{asunto}**"


class AIConfig:
    """Configuración para sistema de IA"""
    
    # Configuración de predicción
    PREDICTION_CONFIG = {
        'dias_anticipacion_minimo': 5,
        'dias_anticipacion_maximo': 30,
        'umbral_confianza': 0.7,
        'usar_ml_avanzado': True,
        'reentrenar_automatico': True,
        'frecuencia_reentrenamiento_dias': 30
    }
    
    # Configuración de recordatorios inteligentes
    SMART_REMINDERS = {
        'analizar_patrones_uso': True,
        'considerar_historial_servicios': True,
        'ajustar_por_tipo_vehiculo': True,
        'personalizar_por_conductor': True
    }
    
    @classmethod
    def get_prediction_config(cls):
        """Retorna configuración de predicción"""
        return cls.PREDICTION_CONFIG.copy()
    
    @classmethod
    def should_retrain_model(cls, last_training_date):
        """Determina si el modelo debe ser reentrenado"""
        from django.utils import timezone
        from datetime import timedelta
        
        if not last_training_date:
            return True
        
        days_since_training = (timezone.now().date() - last_training_date).days
        return days_since_training >= cls.PREDICTION_CONFIG['frecuencia_reentrenamiento_dias']


class SecurityConfig:
    """Configuración de seguridad"""
    
    # Rate limiting
    RATE_LIMITS = {
        'whatsapp_per_minute': 30,
        'telegram_per_minute': 30,
        'api_calls_per_hour': 1000,
        'max_mensajes_masivos': 500
    }
    
    # Validaciones
    VALIDATION_RULES = {
        'telefono_min_length': 10,
        'telefono_max_length': 15,
        'mensaje_max_length': 1000,
        'asunto_max_length': 100
    }
    
    @classmethod
    def validate_phone(cls, phone):
        """Valida formato de teléfono"""
        if not phone:
            return False
        
        # Limpiar número
        clean_phone = ''.join(filter(str.isdigit, phone))
        
        return (cls.VALIDATION_RULES['telefono_min_length'] <= 
                len(clean_phone) <= 
                cls.VALIDATION_RULES['telefono_max_length'])
    
    @classmethod
    def validate_message_length(cls, message):
        """Valida longitud de mensaje"""
        return len(message) <= cls.VALIDATION_RULES['mensaje_max_length']


# Instancia global de configuración
taller_config = TallerConfig()
message_config = MessageConfig()
ai_config = AIConfig()
security_config = SecurityConfig()

# Función de utilidad para obtener configuración completa
def get_full_config():
    """Retorna configuración completa del taller"""
    return {
        'business': taller_config.get_business_info(),
        'channels': taller_config.get_available_channels(),
        'notifications': taller_config.get_notification_config(),
        'ai': ai_config.get_prediction_config(),
        'security': security_config.RATE_LIMITS,
        'services': taller_config.SERVICIOS_COMUNES,
        'prices': taller_config.PRECIOS_BASE
    }
