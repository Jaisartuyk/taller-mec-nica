#!/usr/bin/env python3
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'taller_mecanica.settings')
django.setup()

from gestion_taller.services.chatbot_service import ChatbotService
from gestion_taller.models import Cliente

cliente = Cliente.objects.get(nombre='deaquipaya')
chatbot = ChatbotService(cliente)
phone = '0968192046'

print("=== PASO 1: Solicitar cita ===")
r1 = chatbot.process_message(phone, "Quiero agendar una cita")
print(f"Response type: {r1['response'].get('type')}")
print(f"Next step: {r1['response'].get('next_step')}")

print("\n=== PASO 2: Fecha y hora ===")
context = chatbot.conversation_context.get(phone, {})
print(f"Context next_step: {context.get('next_step')}")

intent, entities = chatbot._identify_intent("Mañana a las 10:00 AM", context)
print(f"Intent detectado: {intent}")
print(f"Entidades: {entities}")

r2 = chatbot.process_message(phone, "Mañana a las 10:00 AM")
print(f"Response type: {r2['response'].get('type')}")
print(f"Next step: {r2['response'].get('next_step')}")

# Verificar contexto
context = chatbot.conversation_context.get(phone, {})
print(f"Fecha_hora_info en contexto: {'fecha_hora_info' in context}")
print(f"Servicio en contexto: {'servicio' in context}")

print("\n=== PASO 3: Servicio ===")
r3 = chatbot.process_message(phone, "Cambio de aceite")
print(f"Response type: {r3['response'].get('type')}")
print(f"Next step: {r3['response'].get('next_step')}")

context = chatbot.conversation_context.get(phone, {})
print(f"Servicio en contexto: {context.get('servicio', 'NO')}")
print(f"Fecha_hora_info en contexto: {context.get('fecha_hora_info', 'NO')}")

print("\n=== PASO 4: Confirmar ===")
r4 = chatbot.process_message(phone, "Sí, confirmo")
print(f"Response type: {r4['response'].get('type')}")
if 'appointment_id' in r4['response']:
    print(f"✅ Cita creada: {r4['response']['appointment_id']}")
else:
    print("❌ No se creó cita")
