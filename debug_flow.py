#!/usr/bin/env python3
"""
Script de debug para el flujo de agendamiento de citas
"""

import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'taller_mecanica.settings')
django.setup()

from gestion_taller.services.chatbot_service import ChatbotService
from gestion_taller.models import Cliente

def debug_appointment_flow():
    print("🔧 DEBUG: Flujo de Agendamiento de Citas")
    print("=" * 50)
    
    # Obtener cliente
    cliente = Cliente.objects.get(nombre='deaquipaya')
    chatbot = ChatbotService(cliente)
    phone_number = '0968192046'
    
    print(f"📱 Número de teléfono: {phone_number}")
    print()
    
    # Paso 1: Solicitar cita
    print("1️⃣ PASO 1: Solicitar agendamiento")
    message1 = "Quiero agendar una cita para cambio de aceite"
    print(f"Usuario: {message1}")
    
    response1 = chatbot.process_message(phone_number, message1)
    print(f"Bot: {response1['response']['message'][:200]}...")
    print(f"Next step: {response1['response'].get('next_step', 'N/A')}")
    print(f"Context keys: {list(chatbot.conversation_context.get(phone_number, {}).keys())}")
    print()
    
    # Paso 2: Seleccionar fecha/hora
    print("2️⃣ PASO 2: Seleccionar fecha y hora")
    message2 = "Mañana a las 10:00 AM"
    print(f"Usuario: {message2}")
    
    # Debug: verificar detección de intent
    context = chatbot.conversation_context.get(phone_number, {})
    intent, entities = chatbot._identify_intent(message2, context)
    print(f"🔍 Intent detectado: {intent}")
    print(f"🔍 Entidades: {entities}")
    
    response2 = chatbot.process_message(phone_number, message2)
    print(f"Bot: {response2['response']['message'][:200]}...")
    print(f"Next step: {response2['response'].get('next_step', 'N/A')}")
    print(f"Context keys: {list(chatbot.conversation_context.get(phone_number, {}).keys())}")
    
    # Verificar si se guardó fecha_hora_info
    context_after = chatbot.conversation_context.get(phone_number, {})
    if 'fecha_hora_info' in context_after:
        print(f"✅ fecha_hora_info guardada: {context_after['fecha_hora_info']}")
    else:
        print("❌ fecha_hora_info NO guardada")
    
    if 'servicio' in context_after:
        print(f"✅ servicio guardado: {context_after['servicio']}")
    else:
        print("❌ servicio NO guardado")
    print()
    
    # Paso 3: Confirmar servicio (si es necesario)
    print("3️⃣ PASO 3: Confirmar servicio")
    message3 = "Sí, cambio de aceite"
    print(f"Usuario: {message3}")
    
    context = chatbot.conversation_context.get(phone_number, {})
    intent, entities = chatbot._identify_intent(message3, context)
    print(f"🔍 Intent detectado: {intent}")
    print(f"🔍 Entidades: {entities}")
    
    response3 = chatbot.process_message(phone_number, message3)
    print(f"Bot: {response3['response']['message'][:200]}...")
    print(f"Next step: {response3['response'].get('next_step', 'N/A')}")
    
    # Verificar contexto después del servicio
    context_after = chatbot.conversation_context.get(phone_number, {})
    print(f"Context keys: {list(context_after.keys())}")
    if 'servicio' in context_after:
        print(f"✅ servicio guardado: {context_after['servicio']}")
    if 'fecha_hora_info' in context_after:
        print(f"✅ fecha_hora_info: {context_after['fecha_hora_info']}")
    print()
    
    # Paso 4: Confirmar cita
    print("4️⃣ PASO 4: Confirmar cita")
    message4 = "Sí, confirmo la cita"
    print(f"Usuario: {message4}")
    
    context = chatbot.conversation_context.get(phone_number, {})
    intent, entities = chatbot._identify_intent(message4, context)
    print(f"🔍 Intent detectado: {intent}")
    print(f"🔍 Context next_step: {context.get('next_step', 'N/A')}")
    print(f"🔍 Context tiene todos los datos: {all(key in context for key in ['conductor_id', 'vehiculo_id', 'servicio', 'fecha_hora_info'])}")
    
    response4 = chatbot.process_message(phone_number, message4)
    print(f"Bot: {response4['response']['message'][:200]}...")
    
    if 'appointment_id' in response4['response']:
        print(f"✅ Cita creada con ID: {response4['response']['appointment_id']}")
    else:
        print("❌ No se creó la cita")

if __name__ == "__main__":
    debug_appointment_flow()
