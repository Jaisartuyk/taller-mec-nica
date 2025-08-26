"""
Servicio de mensajería multi-taller
Maneja mensajes personalizados para cada taller/sucursal
"""
import logging
from django.conf import settings
from ..models import Cliente, ConfiguracionTaller
from gestion_taller.whatsapp_service import WhatsAppService
# from ..telegram_service import TelegramService  # TODO: Implementar cuando esté disponible

logger = logging.getLogger(__name__)

class MultiTallerMessagingService:
    """Servicio de mensajería que maneja múltiples talleres"""
    
    def __init__(self, cliente_id=None, taller_codigo=None, cliente=None):
        """
        Inicializa el servicio para un taller específico
        
        Args:
            cliente_id: ID del cliente/taller
            taller_codigo: Código del taller (alternativo al cliente_id)
            cliente: Objeto Cliente directamente
        """
        self.taller_config = None
        self.cliente = None
        
        # Prioridad 1: Objeto cliente directo
        if cliente:
            self.cliente = cliente
            if hasattr(cliente, 'configuracion_taller') and cliente.configuracion_taller:
                self.taller_config = cliente.configuracion_taller
        
        # Prioridad 2: ID del cliente
        elif cliente_id:
            try:
                self.cliente = Cliente.objects.get(id=cliente_id)
                if hasattr(self.cliente, 'configuracion_taller') and self.cliente.configuracion_taller:
                    self.taller_config = self.cliente.configuracion_taller
            except Cliente.DoesNotExist:
                logger.error(f"Cliente {cliente_id} no encontrado")
        
        # Prioridad 3: Código del taller
        elif taller_codigo:
            try:
                self.taller_config = ConfiguracionTaller.objects.get(codigo=taller_codigo, activo=True)
                # Buscar cliente asociado a esta configuración
                cliente_asociado = Cliente.objects.filter(configuracion_taller=self.taller_config).first()
                if cliente_asociado:
                    self.cliente = cliente_asociado
            except ConfiguracionTaller.DoesNotExist:
                logger.error(f"Configuración de taller {taller_codigo} no encontrada")
        
        # Si no se especifica nada, usar el taller principal si existe
        if not self.taller_config and not self.cliente:
            try:
                self.taller_config = ConfiguracionTaller.objects.filter(es_principal=True, activo=True).first()
                if self.taller_config:
                    cliente_asociado = Cliente.objects.filter(configuracion_taller=self.taller_config).first()
                    if cliente_asociado:
                        self.cliente = cliente_asociado
            except Exception as e:
                logger.error(f"Error obteniendo taller principal: {e}")
        
        # Inicializar servicios de mensajería
        self.whatsapp_service = WhatsAppService() if self._is_whatsapp_enabled() else None
        # self.telegram_service = TelegramService() if self._is_telegram_enabled() else None  # TODO: Implementar
    
    def _is_whatsapp_enabled(self):
        """Verifica si WhatsApp está habilitado para este taller"""
        # Verificar si hay token disponible - usar os.environ directamente como fallback
        import os
        token_disponible = bool(
            getattr(settings, 'WASENDER_API_TOKEN', None) or 
            os.environ.get('WASENDER_API_TOKEN')
        )
        
        # Si hay configuración de taller, verificar que esté habilitado
        if self.taller_config:
            resultado = self.taller_config.usar_whatsapp and token_disponible
            print(f"Usando taller_config - usar_whatsapp: {self.taller_config.usar_whatsapp}, resultado: {resultado}")
            return resultado
        
        # Si solo hay cliente (sin configuración), habilitar WhatsApp si hay token
        if self.cliente:
            return token_disponible
        
        # Si no hay ni cliente ni configuración, usar token si está disponible
        return token_disponible
    
    def _is_telegram_enabled(self):
        """Verifica si Telegram está habilitado para este taller"""
        # Si no hay configuración de taller, usar Telegram si hay token
        if not self.taller_config:
            return bool(getattr(settings, 'TELEGRAM_BOT_TOKEN', None))
        return self.taller_config.usar_telegram and bool(getattr(settings, 'TELEGRAM_BOT_TOKEN', None))
    
    def get_whatsapp_number(self):
        """Obtiene el número de WhatsApp del taller, priorizando Cliente"""
        # Prioridad 1: Número de WhatsApp específico en configuración
        if self.taller_config and self.taller_config.telefono_whatsapp:
            return self.taller_config.telefono_whatsapp
        
        # Prioridad 2: Teléfono principal de configuración
        if self.taller_config and self.taller_config.telefono_principal:
            return self.taller_config.telefono_principal
        
        # Prioridad 3: Teléfono del cliente (dueño del taller)
        if self.cliente and self.cliente.telefono:
            return self.cliente.telefono
        
        # Fallback: número por defecto
        return '+593 9 1234 5678'
    
    def get_taller_info(self):
        """Obtiene información del taller actual, priorizando datos del Cliente"""
        # Información por defecto
        info = {
            'nombre': 'Taller Mecánico',
            'telefono': '+593 9 1234 5678',
            'email': 'info@taller.com',
            'direccion': 'Dirección no configurada',
            'horarios': 'Lun-Vie 8AM-6PM',
            'website': '',
            'ciudad': 'Quito',
            'pais': 'Ecuador'
        }
        
        # Si hay cliente, usar su información como base
        if self.cliente:
            info.update({
                'nombre': self.cliente.nombre,
                'telefono': self.cliente.telefono,
                'email': self.cliente.correo or info['email'],
                'direccion': self.cliente.direccion or info['direccion']
            })
        
        # Si hay configuración de taller, complementar/sobrescribir
        if self.taller_config:
            # Solo sobrescribir si el campo tiene valor
            if self.taller_config.nombre:
                info['nombre'] = self.taller_config.nombre
            if self.taller_config.telefono_principal:
                info['telefono'] = self.taller_config.telefono_principal
            if self.taller_config.email:
                info['email'] = self.taller_config.email
            if self.taller_config.direccion:
                info['direccion'] = self.taller_config.direccion
            if self.taller_config.horarios:
                info['horarios'] = self.taller_config.horarios
            if self.taller_config.website:
                info['website'] = self.taller_config.website
            if self.taller_config.ciudad:
                info['ciudad'] = self.taller_config.ciudad
            if self.taller_config.pais:
                info['pais'] = self.taller_config.pais
        
        return info
    
    def crear_mensaje_personalizado(self, tipo_mensaje, datos=None):
        """
        Crea un mensaje personalizado para el taller
        
        Args:
            tipo_mensaje: Tipo de mensaje (bienvenida, recordatorio, promocion, etc.)
            datos: Datos específicos para el mensaje
        
        Returns:
            str: Mensaje personalizado
        """
        taller_info = self.get_taller_info()
        usar_emojis = self.taller_config.usar_emojis if self.taller_config else True
        
        if tipo_mensaje == 'personalizado':
            # Para mensajes personalizados, usar el mensaje tal como viene
            return datos.get('mensaje_personalizado', 'Mensaje personalizado')
        elif tipo_mensaje == 'bienvenida':
            return self._crear_mensaje_bienvenida(taller_info, datos, usar_emojis)
        elif tipo_mensaje == 'recordatorio':
            return self._crear_mensaje_recordatorio(taller_info, datos, usar_emojis)
        elif tipo_mensaje == 'promocion':
            return self._crear_mensaje_promocion(taller_info, datos, usar_emojis)
        elif tipo_mensaje == 'diagnostico_completado':
            return self._crear_mensaje_diagnostico(taller_info, datos, usar_emojis)
        elif tipo_mensaje == 'vehiculo_listo':
            return self._crear_mensaje_vehiculo_listo(taller_info, datos, usar_emojis)
        else:
            return self._crear_mensaje_generico(taller_info, datos, usar_emojis)
    
    def enviar_mensaje(self, telefono, tipo_mensaje, datos=None, canal='whatsapp'):
        """
        Envía un mensaje usando el servicio especificado
        
        Args:
            telefono: Número de teléfono destino
            tipo_mensaje: Tipo de mensaje a enviar
            datos: Datos para personalizar el mensaje
            canal: Canal de envío ('whatsapp' o 'telegram')
        
        Returns:
            dict: Resultado del envío
        """
        resultado = {
            'whatsapp': {'success': False, 'error': 'No habilitado'},
            'telegram': {'success': False, 'error': 'No habilitado'}
        }
        
        # Crear el mensaje personalizado
        if tipo_mensaje == 'personalizado' and datos and 'mensaje_personalizado' in datos:
            mensaje = datos['mensaje_personalizado']
        elif tipo_mensaje == 'generico' and datos and 'mensaje' in datos:
            mensaje = datos['mensaje']
        else:
            mensaje = self.crear_mensaje_personalizado(tipo_mensaje, datos)
        
        # Enviar por WhatsApp
        if canal == 'whatsapp' and self.whatsapp_service and self._is_whatsapp_enabled():
            try:
                respuesta = self.whatsapp_service.send_message(telefono, mensaje)
                resultado['whatsapp'] = {
                    'success': respuesta.get('success', False),
                    'error': respuesta.get('error', 'Error desconocido') if not respuesta.get('success') else None,
                    'message_id': respuesta.get('message_id')
                }
            except Exception as e:
                resultado['whatsapp'] = {
                    'success': False,
                    'error': f'Error de conexión: {str(e)}'
                }
        
        # Enviar por Telegram (cuando esté implementado)
        # if canal == 'telegram' and self.telegram_service and self._is_telegram_enabled():
        #     try:
        #         respuesta = self.telegram_service.enviar_mensaje(telefono, mensaje)
        #         resultado['telegram'] = {
        #             'success': respuesta.get('success', False),
        #             'error': respuesta.get('error') if not respuesta.get('success') else None
        #         }
        #     except Exception as e:
        #         resultado['telegram'] = {
        #             'success': False,
        #             'error': f'Error de conexión: {str(e)}'
        #         }
        
        return resultado
    
    def _crear_mensaje_bienvenida(self, taller_info, datos, usar_emojis):
        """Crea mensaje de bienvenida personalizado"""
        emoji_inicio = "🔧" if usar_emojis else ""
        emoji_saludo = "👋" if usar_emojis else ""
        emoji_auto = "🚗" if usar_emojis else ""
        emoji_ubicacion = "📍" if usar_emojis else ""
        emoji_telefono = "📞" if usar_emojis else ""
        emoji_horario = "⏰" if usar_emojis else ""
        
        # Obtener nombre del cliente
        nombre_cliente = datos.get('conductor_nombre') or datos.get('nombre_cliente', 'estimado cliente')
        
        # Construir información del vehículo
        vehiculo_info = self._construir_info_vehiculo(datos)
        
        mensaje = f"{emoji_inicio} **{taller_info['nombre'].upper()}** {emoji_inicio}\n\n"
        mensaje += f"¡Hola {nombre_cliente}! {emoji_saludo}\n\n"
        mensaje += f"Su vehículo ha sido recibido:\n"
        mensaje += f"{emoji_auto} {vehiculo_info}\n"
        
        if datos.get('servicio'):
            mensaje += f"🔍 Servicio: {datos['servicio']}\n"
        
        mensaje += f"📅 Fecha: {datos.get('fecha', 'Hoy')}\n\n"
        mensaje += f"Le notificaremos el progreso.\n"
        mensaje += f"{emoji_telefono} Consultas: {taller_info['telefono']}\n\n"
        
        if self.taller_config and self.taller_config.incluir_firma:
            mensaje += self.taller_config.get_firma_mensaje()
        
        return mensaje
    
    def _construir_info_vehiculo(self, datos):
        """Construye la información del vehículo de manera robusta"""
        # Prioridad 1: Datos de las vistas web (vehiculo_marca, vehiculo_modelo, vehiculo_placa)
        if datos.get('vehiculo_marca') or datos.get('vehiculo_modelo'):
            marca = datos.get('vehiculo_marca', '')
            modelo = datos.get('vehiculo_modelo', '')
            placa = datos.get('vehiculo_placa', 'N/A')
            
            vehiculo_str = f"{marca} {modelo}".strip()
            if not vehiculo_str:
                vehiculo_str = "Vehículo"
            
            return f"{vehiculo_str} - {placa}"
        
        # Prioridad 2: Datos del comando de prueba (vehiculo, placa)
        elif datos.get('vehiculo'):
            vehiculo = datos.get('vehiculo', 'Vehículo')
            placa = datos.get('placa', 'N/A')
            return f"{vehiculo} - {placa}"
        
        # Fallback: información genérica
        else:
            return "Vehículo - N/A"

    def _crear_mensaje_recordatorio(self, taller_info, datos, usar_emojis):
        """Crea mensaje de recordatorio personalizado"""
        emoji_campana = "🔔" if usar_emojis else ""
        emoji_auto = "🚗" if usar_emojis else ""
        emoji_calendario = "📅" if usar_emojis else ""
        emoji_telefono = "📞" if usar_emojis else ""
        
        mensaje = f"{emoji_campana} RECORDATORIO DE MANTENIMIENTO\n\n"
        mensaje += f"Estimado {datos.get('nombre_cliente', 'cliente')},\n\n"
        mensaje += f"Su vehículo necesita mantenimiento:\n"
        mensaje += f"{emoji_auto} {datos.get('vehiculo', 'Vehículo')}\n\n"
        
        if datos.get('servicios'):
            mensaje += "Servicios recomendados:\n"
            for servicio in datos['servicios']:
                mensaje += f"• {servicio}\n"
        
        mensaje += f"\n{emoji_calendario} Fecha sugerida: {datos.get('fecha_sugerida', 'A coordinar')}\n"
        mensaje += f"⏰ Hora: {datos.get('hora_sugerida', '9:00 AM')}\n\n"
        mensaje += f"Para agendar su cita:\n"
        mensaje += f"{emoji_telefono} {taller_info['telefono']}\n"
        mensaje += f"💬 Responda este mensaje\n\n"
        
        if self.taller_config and self.taller_config.incluir_firma:
            mensaje += self.taller_config.get_firma_mensaje()
        
        return mensaje
    
    def _crear_mensaje_promocion(self, taller_info, datos, usar_emojis):
        """Crea mensaje de promoción personalizado"""
        emoji_fiesta = "🎉" if usar_emojis else ""
        emoji_descuento = "🔥" if usar_emojis else ""
        emoji_dinero = "💰" if usar_emojis else ""
        emoji_calendario = "📅" if usar_emojis else ""
        emoji_telefono = "📞" if usar_emojis else ""
        
        descuento = datos.get('descuento', 20)
        titulo = datos.get('titulo', 'OFERTA ESPECIAL')
        
        mensaje = f"{emoji_fiesta} {titulo.upper()} - {descuento}% DE DESCUENTO\n\n"
        mensaje += f"¡Solo por tiempo limitado!\n\n"
        
        if datos.get('servicios'):
            for servicio in datos['servicios']:
                mensaje += f"✅ {servicio}\n"
        
        if datos.get('precio_normal') and datos.get('precio_descuento'):
            mensaje += f"\n{emoji_dinero} Precio normal: ${datos['precio_normal']}\n"
            mensaje += f"{emoji_descuento} Con descuento: ${datos['precio_descuento']}\n"
            ahorro = datos['precio_normal'] - datos['precio_descuento']
            mensaje += f"💸 ¡Ahorra ${ahorro}!\n"
        
        mensaje += f"\n{emoji_calendario} Válido hasta: {datos.get('fecha_limite', '31/12/2025')}\n"
        mensaje += f"{emoji_telefono} Reserva: {taller_info['telefono']}\n\n"
        
        if self.taller_config and self.taller_config.incluir_firma:
            mensaje += self.taller_config.get_firma_mensaje()
        
        return mensaje
    
    def _crear_mensaje_diagnostico(self, taller_info, datos, usar_emojis):
        """Crea mensaje de diagnóstico completado"""
        emoji_check = "✅" if usar_emojis else ""
        emoji_herramienta = "🔧" if usar_emojis else ""
        emoji_dinero = "💰" if usar_emojis else ""
        emoji_telefono = "📞" if usar_emojis else ""
        
        mensaje = f"{emoji_check} DIAGNÓSTICO COMPLETADO\n\n"
        mensaje += f"Estimado {datos.get('nombre_cliente', 'cliente')},\n\n"
        mensaje += f"Su {datos.get('vehiculo', 'vehículo')} necesita:\n"
        
        if datos.get('reparaciones'):
            for reparacion in datos['reparaciones']:
                mensaje += f"{emoji_herramienta} {reparacion}\n"
        
        if datos.get('costo_total'):
            mensaje += f"\n{emoji_dinero} Costo total: ${datos['costo_total']}\n\n"
        
        mensaje += f"¿Autoriza la reparación?\n"
        mensaje += f"✅ Responda \"SÍ\" para continuar\n"
        mensaje += f"❌ Responda \"NO\" para retirar\n\n"
        
        if datos.get('tiempo_estimado'):
            mensaje += f"Tiempo estimado: {datos['tiempo_estimado']}\n"
        
        mensaje += f"{emoji_telefono} {taller_info['telefono']}\n"
        
        if self.taller_config and self.taller_config.incluir_firma:
            mensaje += self.taller_config.get_firma_mensaje()
        
        return mensaje
    
    def _crear_mensaje_vehiculo_listo(self, taller_info, datos, usar_emojis):
        """Crea mensaje de vehículo listo"""
        emoji_fiesta = "🎉" if usar_emojis else ""
        emoji_check = "✅" if usar_emojis else ""
        emoji_dinero = "💰" if usar_emojis else ""
        emoji_ubicacion = "📍" if usar_emojis else ""
        emoji_telefono = "📞" if usar_emojis else ""
        
        # Obtener nombre del cliente y vehículo
        nombre_cliente = datos.get('conductor_nombre') or datos.get('nombre_cliente', 'Cliente')
        vehiculo_info = self._construir_info_vehiculo(datos)
        
        mensaje = f"{emoji_fiesta} VEHÍCULO LISTO!\n\n"
        mensaje += f"{nombre_cliente}, su {vehiculo_info} está listo:\n\n"
        
        if datos.get('trabajos_realizados'):
            for trabajo in datos['trabajos_realizados']:
                mensaje += f"{emoji_check} {trabajo}\n"
        
        mensaje += f"{emoji_check} Prueba de funcionamiento OK\n"
        
        if datos.get('total') or datos.get('costo_total'):
            total = datos.get('total') or datos.get('costo_total')
            mensaje += f"\n{emoji_dinero} Total a pagar: ${total}\n"
        
        mensaje += f"\n{emoji_ubicacion} Puede recogerlo hasta las {datos.get('hora_limite', '6:00 PM')}\n"
        mensaje += f"{emoji_telefono} {taller_info['telefono']}\n\n"
        
        if self.taller_config and self.taller_config.incluir_firma:
            mensaje += self.taller_config.get_firma_mensaje()
        
        return mensaje
    
    def _crear_mensaje_generico(self, taller_info, datos, usar_emojis):
        """Crea mensaje genérico"""
        # Buscar mensaje en diferentes claves posibles
        mensaje = datos.get('mensaje') or datos.get('mensaje_personalizado', 'Mensaje del taller')
        
        if self.taller_config and self.taller_config.incluir_firma:
            mensaje += self.taller_config.get_firma_mensaje()
        
        return mensaje
    

    
    @classmethod
    def listar_talleres_activos(cls):
        """Lista todos los talleres activos"""
        return ConfiguracionTaller.objects.filter(activo=True).order_by('nombre')
    
    @classmethod
    def get_taller_por_cliente(cls, cliente_id):
        """Obtiene la configuración de un taller por ID de cliente"""
        try:
            cliente = Cliente.objects.get(id=cliente_id)
            return cliente.configuracion
        except Cliente.DoesNotExist:
            return None
