from .models import ServicioCatalogo, OrdenServicio
import requests
from django.conf import settings

def enviar_telegram(chat_id, mensaje, bot_token=None):
    """
    Envía un mensaje de Telegram al chat_id especificado usando el bot.
    Si no se pasa bot_token, toma el de settings.TELEGRAM_BOT_TOKEN.
    """
    if bot_token is None:
        bot_token = getattr(settings, 'TELEGRAM_BOT_TOKEN', None)
    if not bot_token:
        print("[Telegram] No se encontró TELEGRAM_BOT_TOKEN en settings.")
        return False
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    data = {"chat_id": chat_id, "text": mensaje}
    try:
        resp = requests.post(url, data=data, timeout=10)
        if not resp.ok:
            print(f"[Telegram] Error al enviar: {resp.text}")
        return resp.ok
    except Exception as e:
        print(f"[Telegram] Excepción al enviar: {e}")
        return False

def sugerir_servicios_por_kilometraje(vehiculo, kilometraje_actual):
    """
    Devuelve una lista de servicios del catálogo cuya frecuencia_km ya se cumplió
    según el último servicio realizado al vehículo y el kilometraje actual.
    """
    sugeridos = []
    servicios_catalogo = ServicioCatalogo.objects.filter(activo=True)
    for servicio in servicios_catalogo:
        if servicio.frecuencia_km:
            # Buscar la última orden de servicio que incluyó este servicio para el vehículo
            ultima_orden = (
                OrdenServicio.objects.filter(
                    vehiculo=vehiculo, servicios=servicio
                )
                .order_by('-fecha_creacion')
                .first()
            )
            if ultima_orden:
                km_ultimo = ultima_orden.kilometraje
            else:
                # Si nunca se realizó, sugerir si el km actual supera la frecuencia
                km_ultimo = 0
            if kilometraje_actual >= km_ultimo + servicio.frecuencia_km:
                sugeridos.append(servicio)
    return sugeridos
