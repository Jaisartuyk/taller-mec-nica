from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from datetime import timedelta
from .models import OrdenServicio, RecordatorioMantenimiento, ServicioCatalogo, Notificacion

# Puedes usar python-telegram-bot o requests para enviar mensajes a Telegram
import requests

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
