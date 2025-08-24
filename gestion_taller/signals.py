from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from datetime import timedelta
from .models import OrdenServicio, RecordatorioMantenimiento, ServicioCatalogo, Notificacion, Conductor, Vehiculo

# Puedes usar python-telegram-bot o requests para enviar mensajes a Telegram
import requests
import logging

# Importar el servicio de notificaciones WhatsApp
from .notification_service import notification_service

logger = logging.getLogger(__name__)

TELEGRAM_BOT_TOKEN = '8098388898:AAFBQN4AGi4ki66E8GgGl63iAV60aXDlFcg'

# Busca y envía mensaje a todos los chat_id relevantes (usuario y conductor)
def enviar_telegram_mensaje(cliente, vehiculo, mensaje):
    from .models import PerfilUsuario, Conductor
    chat_ids = set()
    # Notificar al usuario principal del cliente (ej: administrador)
    usuarios = PerfilUsuario.objects.filter(cliente=cliente)
    for usuario in usuarios:
        if usuario.telegram_chat_id:
            chat_ids.add(usuario.telegram_chat_id)
    # Notificar al conductor principal del vehículo
    if hasattr(vehiculo, 'conductor'):
        conductor = vehiculo.conductor
        if conductor and conductor.telegram_chat_id:
            chat_ids.add(conductor.telegram_chat_id)
    # Envía a todos los chat_ids
    for chat_id in chat_ids:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        data = {"chat_id": chat_id, "text": mensaje}
        try:
            requests.post(url, data=data, timeout=5)
        except Exception:
            pass

@receiver(post_save, sender=OrdenServicio)
def crear_recordatorios_post_servicio(sender, instance, created, **kwargs):
    if not created:
        return
    if instance.estado != 'completada':
        return
    vehiculo = instance.vehiculo
    kilometraje_actual = instance.kilometraje
    cliente = instance.cliente
    fecha_base = timezone.now().date()
    servicios = instance.servicios.all()
    for servicio in servicios:
        # Calcula próximo km y fecha
        prox_km = None
        prox_fecha = None
        if servicio.frecuencia_km:
            prox_km = kilometraje_actual + servicio.frecuencia_km
        if servicio.frecuencia_meses:
            prox_fecha = fecha_base + timedelta(days=servicio.frecuencia_meses * 30)
        # Evita duplicados
        existe = RecordatorioMantenimiento.objects.filter(
            vehiculo=vehiculo,
            tipo=servicio.nombre,
            notificado=False,
        ).exists()
        if not existe:
            rec = RecordatorioMantenimiento.objects.create(
                vehiculo=vehiculo,
                tipo=servicio.nombre,
                kilometraje_proximo=prox_km or 0,
                fecha_proximo=prox_fecha or fecha_base,
            )
            # Crea notificación interna
            Notificacion.objects.create(
                cliente=cliente,
                vehiculo=vehiculo,
                mensaje=f"Recordatorio: Próximo {servicio.nombre} para {vehiculo} en {prox_km or '-'} km o el {prox_fecha or '-'}.",
                tipo='mantenimiento',
            )
            # Envía notificación a Telegram
            nombre_taller = getattr(cliente, 'nombre', 'Taller')
            mensaje = f"🔔 [{nombre_taller}] Recordatorio: Próximo {servicio.nombre} para {vehiculo.placa} en {prox_km or '-'} km o el {prox_fecha or '-'}."
            enviar_telegram_mensaje(cliente, vehiculo, mensaje)


# ==========================================
# NUEVOS SIGNALS PARA NOTIFICACIONES WHATSAPP AUTOMÁTICAS
# ==========================================

@receiver(post_save, sender=Conductor)
def notificar_nuevo_conductor(sender, instance, created, **kwargs):
    """
    Signal que se ejecuta cuando se crea un nuevo conductor
    Envía notificación de bienvenida al conductor y al administrador
    """
    if created:
        try:
            logger.info(f"Nuevo conductor creado: {instance.nombre} - Enviando notificaciones WhatsApp")
            
            # Enviar notificaciones usando el servicio
            notification_service.notify_nuevo_conductor(
                conductor=instance,
                send_to_admin=True
            )
            
        except Exception as e:
            logger.error(f"Error en signal notificar_nuevo_conductor: {e}")


@receiver(post_save, sender=Vehiculo)
def notificar_nuevo_vehiculo(sender, instance, created, **kwargs):
    """
    Signal que se ejecuta cuando se registra un nuevo vehículo
    Envía notificación al conductor propietario
    """
    if created:
        try:
            logger.info(f"Nuevo vehículo registrado: {instance.marca} {instance.modelo} - {instance.placa}")
            
            # Enviar notificación usando el servicio
            notification_service.notify_nuevo_vehiculo(vehiculo=instance)
            
        except Exception as e:
            logger.error(f"Error en signal notificar_nuevo_vehiculo: {e}")


@receiver(post_save, sender=OrdenServicio)
def notificar_orden_servicio_eventos(sender, instance, created, **kwargs):
    """
    Signal que maneja diferentes eventos de la orden de servicio:
    - Creación de nueva orden
    - Cambio de estado a 'en_progreso'
    - Completación de orden
    """
    try:
        if created:
            # Nueva orden creada
            logger.info(f"Nueva orden de servicio creada: #{getattr(instance, 'numero_orden', 'N/A')}")
            
            # Obtener servicios solicitados
            servicios_solicitados = []
            if hasattr(instance, 'servicios'):
                servicios_solicitados = [servicio.nombre for servicio in instance.servicios.all()]
            
            # Si no hay servicios específicos, usar descripción general
            if not servicios_solicitados and hasattr(instance, 'descripcion_trabajo'):
                servicios_solicitados = [instance.descripcion_trabajo or "Servicio general"]
            
            # Enviar notificación de orden creada
            notification_service.notify_orden_creada(
                orden_servicio=instance,
                servicios_solicitados=servicios_solicitados
            )
            
        else:
            # Orden actualizada - verificar cambios de estado
            if hasattr(instance, '_state') and instance._state.adding is False:
                # Obtener el estado anterior desde la base de datos
                try:
                    old_instance = OrdenServicio.objects.get(pk=instance.pk)
                    old_estado = old_instance.estado
                    new_estado = instance.estado
                    
                    # Notificar cuando la orden pasa a 'en_progreso'
                    if old_estado != 'en_progreso' and new_estado == 'en_progreso':
                        logger.info(f"Orden #{getattr(instance, 'numero_orden', 'N/A')} cambió a en progreso")
                        
                        # Obtener técnico asignado si existe
                        tecnico_asignado = getattr(instance, 'tecnico_asignado', None)
                        if tecnico_asignado:
                            tecnico_nombre = str(tecnico_asignado)
                        else:
                            tecnico_nombre = None
                        
                        notification_service.notify_orden_en_progreso(
                            orden_servicio=instance,
                            tecnico_asignado=tecnico_nombre
                        )
                    
                    # Notificar cuando la orden se completa
                    elif old_estado != 'completada' and new_estado == 'completada':
                        logger.info(f"Orden #{getattr(instance, 'numero_orden', 'N/A')} completada")
                        
                        # Obtener servicios realizados
                        servicios_realizados = []
                        if hasattr(instance, 'servicios'):
                            servicios_realizados = [servicio.nombre for servicio in instance.servicios.all()]
                        
                        # Obtener total del servicio
                        total = getattr(instance, 'total', 0)
                        
                        # Usar el método existente de notificación de orden completada
                        notification_service.notify_orden_completada(
                            conductor=instance.vehiculo.conductor,
                            vehiculo=instance.vehiculo,
                            orden_servicio=instance,
                            servicios_realizados=servicios_realizados,
                            total=total
                        )
                        
                except OrdenServicio.DoesNotExist:
                    # La instancia anterior no existe, probablemente es una creación
                    pass
                    
    except Exception as e:
        logger.error(f"Error en signal notificar_orden_servicio_eventos: {e}")


def notificar_diagnostico_adicional_manual(orden_servicio, problema_encontrado, costo_adicional=None):
    """
    Función helper para notificar diagnósticos adicionales manualmente
    Esta función debe ser llamada desde las vistas cuando se detecte un problema adicional
    
    Args:
        orden_servicio: Instancia de OrdenServicio
        problema_encontrado: Descripción del problema
        costo_adicional: Costo adicional estimado (opcional)
    """
    try:
        logger.info(f"Notificando diagnóstico adicional para orden #{getattr(orden_servicio, 'numero_orden', 'N/A')}")
        
        notification_service.notify_diagnostico_adicional(
            orden_servicio=orden_servicio,
            problema_encontrado=problema_encontrado,
            costo_adicional=costo_adicional
        )
        
    except Exception as e:
        logger.error(f"Error en notificar_diagnostico_adicional_manual: {e}")


def enviar_recordatorio_mantenimiento_manual(conductor, vehiculo, recordatorio, dias_restantes):
    """
    Función helper para enviar recordatorios de mantenimiento manualmente
    Esta función debe ser llamada desde comandos de management o tareas programadas
    
    Args:
        conductor: Instancia de Conductor
        vehiculo: Instancia de Vehiculo
        recordatorio: Instancia del recordatorio
        dias_restantes: Días restantes para el mantenimiento
    """
    try:
        logger.info(f"Enviando recordatorio de mantenimiento a {conductor.nombre} para {vehiculo.placa}")
        
        notification_service.notify_recordatorio_mantenimiento(
            conductor=conductor,
            vehiculo=vehiculo,
            recordatorio=recordatorio,
            dias_restantes=dias_restantes
        )
        
    except Exception as e:
        logger.error(f"Error en enviar_recordatorio_mantenimiento_manual: {e}")
