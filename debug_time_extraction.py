#!/usr/bin/env python
import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'taller_mecanica.settings')
django.setup()

from gestion_taller.models import Cliente
from gestion_taller.services.chatbot_service import ChatbotService
from django.core.cache import cache

def debug_time_extraction():
    """Debug de extracción de hora"""
    
    cliente = Cliente.objects.get(nombre='deaquipaya')
    chatbot = ChatbotService(cliente)
    
    # Probar extracción de entidades
    message = "Necesito agendar una cita para el viernes a las 2 pm para cambio de aceite"
    
    print(f"Mensaje: {message}")
    print("\n=== EXTRACCIÓN DE ENTIDADES ===")
    
    # Extraer entidades de fecha/hora
    datetime_entities = chatbot._extract_datetime_entities(message)
    print(f"Entidades extraídas: {datetime_entities}")
    
    # Simular el contexto que se crearía
    fecha_hora_info = {
        'day': datetime_entities.get('day'),
        'time': datetime_entities.get('time'),
        'time_reference': datetime_entities.get('time_reference'),
        'day_number': datetime_entities.get('day_number')
    }
    
    print(f"Información de fecha/hora: {fecha_hora_info}")
    
    # Convertir a datetime
    try:
        fecha_hora_dt = chatbot._convert_fecha_hora_info_to_datetime(fecha_hora_info)
        print(f"Datetime resultante: {fecha_hora_dt}")
        print(f"Hora: {fecha_hora_dt.hour}:{fecha_hora_dt.minute:02d}")
        print(f"Fecha: {fecha_hora_dt.date()}")
    except Exception as e:
        print(f"Error en conversión: {e}")
    
    print("\n=== PRUEBA COMPLETA ===")
    
    # Limpiar cache
    cache.clear()
    
    # Procesar mensaje completo
    response = chatbot.process_message('+593968192046', message)
    print(f"Intent: {response.get('intent')}")
    print(f"Response type: {response['response'].get('type')}")
    
    # Verificar contexto guardado
    cache_key = f"chatbot_context_{cliente.id}_+593968192046"
    context = cache.get(cache_key)
    if context and 'fecha_hora_info' in context:
        print(f"Fecha/hora en contexto: {context['fecha_hora_info']}")

if __name__ == '__main__':
    debug_time_extraction()
