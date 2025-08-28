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

def test_chatbot_context_persistence():
    """Prueba la persistencia del contexto del chatbot"""
    
    # Limpiar cache para empezar fresco
    cache.clear()
    
    # Obtener cliente
    cliente = Cliente.objects.get(nombre='deaquipaya')
    chatbot = ChatbotService(cliente)
    
    print('=== PRUEBA DE CONTEXTO PERSISTENTE ===')
    
    # Paso 1: Solicitud inicial con fecha/hora y servicio
    print('\n1. Usuario: "Necesito agendar una cita para mañana a las 2 pm para cambio de aceite"')
    response1 = chatbot.process_message('+593968192046', 'Necesito agendar una cita para mañana a las 2 pm para cambio de aceite')
    
    print(f'   Intent detectado: {response1.get("intent")}')
    print(f'   Próximo paso: {response1["response"].get("next_step")}')
    print(f'   Respuesta: {response1["response"]["message"][:200]}...\n')
    
    # Verificar que el contexto se guardó
    cache_key = f"chatbot_context_{cliente.id}_+593968192046"
    context = cache.get(cache_key)
    print(f'   Contexto guardado: {bool(context)}')
    if context:
        print(f'   Mensajes en contexto: {len(context.get("messages", []))}')
        print(f'   Último intent: {context.get("last_intent")}')
        print(f'   Próximo paso: {context.get("next_step")}')
    
    # Paso 2: Crear nueva instancia del chatbot (simula nuevo webhook)
    print('\n--- NUEVA INSTANCIA DE CHATBOT (NUEVO WEBHOOK) ---')
    chatbot2 = ChatbotService(cliente)  # Nueva instancia
    
    # Paso 3: Confirmación
    print('\n2. Usuario: "Sí, confirmo la cita"')
    response2 = chatbot2.process_message('+593968192046', 'Sí, confirmo la cita')
    
    print(f'   Intent detectado: {response2.get("intent")}')
    print(f'   Respuesta: {response2["response"]["message"][:200]}...\n')
    
    # Verificar que el contexto se mantuvo
    context_after = cache.get(cache_key)
    print(f'   Contexto después de confirmación: {bool(context_after)}')
    if context_after:
        print(f'   Mensajes en contexto: {len(context_after.get("messages", []))}')
        print(f'   Último intent: {context_after.get("last_intent")}')
    
    print('\n=== RESULTADO ===')
    if response1.get('intent') == 'appointment_datetime' and response2.get('intent') == 'appointment_confirmation':
        print('✅ ÉXITO: El contexto se mantuvo correctamente entre instancias')
        print('✅ El flujo de agendamiento funciona con persistencia')
    else:
        print('❌ ERROR: El contexto no se mantuvo correctamente')
    
    return response1, response2

if __name__ == '__main__':
    test_chatbot_context_persistence()
