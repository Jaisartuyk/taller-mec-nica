"""
Tareas programadas para el sistema de recordatorios
Requiere Celery para funcionar automáticamente
"""

from celery import shared_task
from django.utils import timezone
from .ai_predictor import verificar_recordatorios_pendientes, entrenar_modelo_cliente
from .models import Cliente
import logging

logger = logging.getLogger(__name__)

@shared_task
def verificar_recordatorios_diarios():
    """
    Tarea que se ejecuta diariamente para verificar recordatorios pendientes
    """
    try:
        logger.info("Iniciando verificación diaria de recordatorios")
        notificaciones = verificar_recordatorios_pendientes()
        
        if notificaciones:
            logger.info(f"Se enviaron {len(notificaciones)} notificaciones de recordatorio")
            return f"Éxito: {len(notificaciones)} notificaciones enviadas"
        else:
            logger.info("No hay recordatorios pendientes")
            return "No hay recordatorios pendientes"
            
    except Exception as e:
        logger.error(f"Error en verificación de recordatorios: {e}")
        raise

@shared_task
def entrenar_modelos_ia_semanalmente():
    """
    Tarea que se ejecuta semanalmente para entrenar los modelos de IA
    """
    try:
        logger.info("Iniciando entrenamiento semanal de modelos de IA")
        clientes = Cliente.objects.all()
        modelos_entrenados = 0
        
        for cliente in clientes:
            try:
                exito = entrenar_modelo_cliente(cliente)
                if exito:
                    modelos_entrenados += 1
                    logger.info(f"Modelo entrenado para cliente: {cliente.nombre}")
            except Exception as e:
                logger.warning(f"No se pudo entrenar modelo para {cliente.nombre}: {e}")
        
        logger.info(f"Entrenamiento completado: {modelos_entrenados} modelos actualizados")
        return f"Éxito: {modelos_entrenados} modelos entrenados"
        
    except Exception as e:
        logger.error(f"Error en entrenamiento de modelos: {e}")
        raise

# Configuración de tareas periódicas para Celery Beat
# Agregar esto a settings.py:
"""
from celery.schedules import crontab

CELERY_BEAT_SCHEDULE = {
    'verificar-recordatorios-diarios': {
        'task': 'gestion_taller.tasks.verificar_recordatorios_diarios',
        'schedule': crontab(hour=9, minute=0),  # Todos los días a las 9:00 AM
    },
    'entrenar-modelos-semanalmente': {
        'task': 'gestion_taller.tasks.entrenar_modelos_ia_semanalmente',
        'schedule': crontab(hour=2, minute=0, day_of_week=1),  # Lunes a las 2:00 AM
    },
}
"""
