"""
Servicio de Notificaciones Automáticas para el Taller Mecánico
Integra las plantillas inteligentes de WhatsApp con eventos del sistema
"""

import logging
from django.utils import timezone
from django.conf import settings
from .message_templates import MessageTemplates
from .services.multi_taller_messaging import MultiTallerMessagingService
from .models import Cliente, Conductor, Vehiculo, OrdenServicio, PerfilUsuario

logger = logging.getLogger(__name__)

class NotificationService:
    """
    Servicio centralizado para enviar notificaciones automáticas
    via WhatsApp usando plantillas inteligentes
    """
    
    def __init__(self):
        self.whatsapp_service = MultiTallerMessagingService()
        self.templates = MessageTemplates()
    
    def get_taller_info(self, cliente):
        """Obtiene información del taller para personalizar mensajes"""
        try:
            return {
                'nombre': cliente.nombre,
                'telefono': getattr(cliente, 'telefono', 'Contáctanos'),
                'direccion': getattr(cliente, 'direccion', ''),
                'horario': getattr(cliente, 'horario_atencion', 'Lun-Vie 8AM-6PM, Sáb 8AM-2PM')
            }
        except Exception as e:
            logger.error(f"Error obteniendo info del taller: {e}")
            return {
                'nombre': 'Taller Mecánico Profesional',
                'telefono': 'Contáctanos',
                'direccion': '',
                'horario': 'Lun-Vie 8AM-6PM, Sáb 8AM-2PM'
            }
    
    def get_admin_info(self, cliente):
        """Obtiene información del administrador del taller"""
        try:
            # Buscar el usuario administrador del cliente
            perfil_admin = PerfilUsuario.objects.filter(
                cliente=cliente,
                user__is_staff=True
            ).first()
            
            if perfil_admin:
                return {
                    'nombre': perfil_admin.user.get_full_name() or perfil_admin.user.username,
                    'email': perfil_admin.user.email,
                    'telefono': getattr(perfil_admin, 'telefono', '')
                }
        except Exception as e:
            logger.error(f"Error obteniendo info del admin: {e}")
        
        return {
            'nombre': 'Administrador',
            'email': '',
            'telefono': ''
        }
    
    def notify_nuevo_conductor(self, conductor, send_to_admin=True):
        """
        Notifica el registro de un nuevo conductor
        
        Args:
            conductor: Instancia del modelo Conductor
            send_to_admin: Si enviar notificación al administrador
        """
        try:
            cliente_taller = conductor.cliente
            taller_info = self.get_taller_info(cliente_taller)
            
            # 1. Enviar mensaje de bienvenida al conductor
            if conductor.telefono:
                mensaje_conductor = self.templates.nuevo_conductor_registrado(
                    conductor=conductor,
                    cliente_taller=cliente_taller
                )
                
                resultado = self.whatsapp_service.enviar_mensaje(
                    numero=conductor.telefono,
                    mensaje=mensaje_conductor,
                    cliente=cliente_taller
                )
                
                if resultado['success']:
                    logger.info(f"Notificación de bienvenida enviada a conductor {conductor.nombre}")
                else:
                    logger.error(f"Error enviando bienvenida a conductor: {resultado['error']}")
            
            # 2. Enviar notificación al administrador si se solicita
            if send_to_admin:
                admin_info = self.get_admin_info(cliente_taller)
                
                # Buscar teléfono del admin para notificar
                perfil_admin = PerfilUsuario.objects.filter(
                    cliente=cliente_taller,
                    user__is_staff=True
                ).first()
                
                if perfil_admin and hasattr(perfil_admin, 'telefono') and perfil_admin.telefono:
                    mensaje_admin = self.templates.nuevo_conductor_registrado(
                        conductor=conductor,
                        cliente_taller=cliente_taller,
                        admin_info=admin_info
                    )
                    
                    resultado_admin = self.whatsapp_service.enviar_mensaje(
                        numero=perfil_admin.telefono,
                        mensaje=mensaje_admin,
                        cliente=cliente_taller
                    )
                    
                    if resultado_admin['success']:
                        logger.info(f"Notificación enviada al admin del taller {cliente_taller.nombre}")
                    else:
                        logger.error(f"Error enviando notificación al admin: {resultado_admin['error']}")
        
        except Exception as e:
            logger.error(f"Error en notify_nuevo_conductor: {e}")
    
    def notify_nuevo_vehiculo(self, vehiculo):
        """
        Notifica el registro de un nuevo vehículo
        
        Args:
            vehiculo: Instancia del modelo Vehiculo
        """
        try:
            conductor = vehiculo.conductor
            if not conductor or not conductor.telefono:
                logger.warning(f"No se puede notificar nuevo vehículo: conductor sin teléfono")
                return
            
            cliente_taller = conductor.cliente
            taller_info = self.get_taller_info(cliente_taller)
            
            mensaje = self.templates.nuevo_vehiculo_registrado(
                conductor=conductor,
                vehiculo=vehiculo,
                taller_info=taller_info
            )
            
            resultado = self.whatsapp_service.enviar_mensaje(
                numero=conductor.telefono,
                mensaje=mensaje,
                cliente=cliente_taller
            )
            
            if resultado['success']:
                logger.info(f"Notificación de nuevo vehículo enviada a {conductor.nombre}")
            else:
                logger.error(f"Error enviando notificación de nuevo vehículo: {resultado['error']}")
        
        except Exception as e:
            logger.error(f"Error en notify_nuevo_vehiculo: {e}")
    
    def notify_orden_creada(self, orden_servicio, servicios_solicitados):
        """
        Notifica la creación de una nueva orden de servicio
        
        Args:
            orden_servicio: Instancia del modelo OrdenServicio
            servicios_solicitados: Lista de servicios solicitados
        """
        try:
            vehiculo = orden_servicio.vehiculo
            conductor = vehiculo.conductor
            
            if not conductor or not conductor.telefono:
                logger.warning(f"No se puede notificar orden creada: conductor sin teléfono")
                return
            
            cliente_taller = conductor.cliente
            taller_info = self.get_taller_info(cliente_taller)
            
            mensaje = self.templates.orden_servicio_creada(
                conductor=conductor,
                vehiculo=vehiculo,
                orden_servicio=orden_servicio,
                servicios_solicitados=servicios_solicitados,
                taller_info=taller_info
            )
            
            resultado = self.whatsapp_service.enviar_mensaje(
                numero=conductor.telefono,
                mensaje=mensaje,
                cliente=cliente_taller
            )
            
            if resultado['success']:
                logger.info(f"Notificación de orden creada enviada a {conductor.nombre}")
            else:
                logger.error(f"Error enviando notificación de orden creada: {resultado['error']}")
        
        except Exception as e:
            logger.error(f"Error en notify_orden_creada: {e}")
    
    def notify_orden_en_progreso(self, orden_servicio, tecnico_asignado=None, progreso_actual=None):
        """
        Notifica que una orden está en progreso
        
        Args:
            orden_servicio: Instancia del modelo OrdenServicio
            tecnico_asignado: Nombre del técnico asignado (opcional)
            progreso_actual: Descripción del progreso actual (opcional)
        """
        try:
            vehiculo = orden_servicio.vehiculo
            conductor = vehiculo.conductor
            
            if not conductor or not conductor.telefono:
                logger.warning(f"No se puede notificar orden en progreso: conductor sin teléfono")
                return
            
            mensaje = self.templates.orden_en_progreso(
                conductor=conductor,
                vehiculo=vehiculo,
                orden_servicio=orden_servicio,
                tecnico_asignado=tecnico_asignado,
                progreso_actual=progreso_actual
            )
            
            cliente_taller = conductor.cliente
            resultado = self.whatsapp_service.enviar_mensaje(
                numero=conductor.telefono,
                mensaje=mensaje,
                cliente=cliente_taller
            )
            
            if resultado['success']:
                logger.info(f"Notificación de orden en progreso enviada a {conductor.nombre}")
            else:
                logger.error(f"Error enviando notificación de orden en progreso: {resultado['error']}")
        
        except Exception as e:
            logger.error(f"Error en notify_orden_en_progreso: {e}")
    
    def notify_diagnostico_adicional(self, orden_servicio, problema_encontrado, costo_adicional=None):
        """
        Notifica que se requiere autorización para trabajo adicional
        
        Args:
            orden_servicio: Instancia del modelo OrdenServicio
            problema_encontrado: Descripción del problema encontrado
            costo_adicional: Costo adicional estimado (opcional)
        """
        try:
            vehiculo = orden_servicio.vehiculo
            conductor = vehiculo.conductor
            
            if not conductor or not conductor.telefono:
                logger.warning(f"No se puede notificar diagnóstico adicional: conductor sin teléfono")
                return
            
            mensaje = self.templates.diagnostico_adicional_requerido(
                conductor=conductor,
                vehiculo=vehiculo,
                orden_servicio=orden_servicio,
                problema_encontrado=problema_encontrado,
                costo_adicional=costo_adicional
            )
            
            cliente_taller = conductor.cliente
            resultado = self.whatsapp_service.enviar_mensaje(
                numero=conductor.telefono,
                mensaje=mensaje,
                cliente=cliente_taller
            )
            
            if resultado['success']:
                logger.info(f"Notificación de diagnóstico adicional enviada a {conductor.nombre}")
            else:
                logger.error(f"Error enviando notificación de diagnóstico adicional: {resultado['error']}")
        
        except Exception as e:
            logger.error(f"Error en notify_diagnostico_adicional: {e}")
    
    def notify_recordatorio_mantenimiento(self, conductor, vehiculo, recordatorio, dias_restantes):
        """
        Envía recordatorio de mantenimiento usando la plantilla mejorada
        
        Args:
            conductor: Instancia del modelo Conductor
            vehiculo: Instancia del modelo Vehiculo
            recordatorio: Instancia del recordatorio
            dias_restantes: Días restantes para el mantenimiento
        """
        try:
            if not conductor.telefono:
                logger.warning(f"No se puede enviar recordatorio: conductor {conductor.nombre} sin teléfono")
                return
            
            cliente_taller = conductor.cliente
            taller_info = self.get_taller_info(cliente_taller)
            
            mensaje = self.templates.recordatorio_mantenimiento(
                conductor=conductor,
                vehiculo=vehiculo,
                recordatorio=recordatorio,
                dias_restantes=dias_restantes,
                taller_info=taller_info
            )
            
            resultado = self.whatsapp_service.enviar_mensaje(
                numero=conductor.telefono,
                mensaje=mensaje,
                cliente=cliente_taller
            )
            
            if resultado['success']:
                logger.info(f"Recordatorio de mantenimiento enviado a {conductor.nombre}")
            else:
                logger.error(f"Error enviando recordatorio de mantenimiento: {resultado['error']}")
        
        except Exception as e:
            logger.error(f"Error en notify_recordatorio_mantenimiento: {e}")
    
    def notify_orden_completada(self, conductor, vehiculo, orden_servicio, servicios_realizados, total):
        """
        Notifica que una orden de servicio ha sido completada
        
        Args:
            conductor: Instancia del modelo Conductor
            vehiculo: Instancia del modelo Vehiculo
            orden_servicio: Instancia del modelo OrdenServicio
            servicios_realizados: Lista de servicios realizados
            total: Total del servicio
        """
        try:
            if not conductor.telefono:
                logger.warning(f"No se puede notificar orden completada: conductor {conductor.nombre} sin teléfono")
                return
            
            cliente_taller = conductor.cliente
            taller_info = self.get_taller_info(cliente_taller)
            
            mensaje = self.templates.orden_completada(
                conductor=conductor,
                vehiculo=vehiculo,
                orden_servicio=orden_servicio,
                servicios_realizados=servicios_realizados,
                total=total,
                taller_info=taller_info
            )
            
            resultado = self.whatsapp_service.enviar_mensaje(
                numero=conductor.telefono,
                mensaje=mensaje,
                cliente=cliente_taller
            )
            
            if resultado['success']:
                logger.info(f"Notificación de orden completada enviada a {conductor.nombre}")
            else:
                logger.error(f"Error enviando notificación de orden completada: {resultado['error']}")
        
        except Exception as e:
            logger.error(f"Error en notify_orden_completada: {e}")


# Instancia global del servicio de notificaciones
notification_service = NotificationService()
