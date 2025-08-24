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

# Simular contexto después del paso 2
chatbot.conversation_context[phone] = {
    'next_step': 'collect_service_details',
    'conductor_id': 1,
    'vehiculo_id': 1,
    'fecha_hora_info': {'time': '10:00 am', 'time_reference': 'morning'}
}

print('=== Test de detección de servicio ===')
message = 'Cambio de aceite'
context = chatbot.conversation_context.get(phone, {})

# Probar identificación de intent
intent, entities = chatbot._identify_intent(message, context)
print(f'Intent: {intent}')
print(f'Entidades: {entities}')

# Probar el handler directamente
if intent == 'appointment_service':
    result = chatbot._handle_appointment_service(entities, context, phone)
    print(f'Result type: {result.get("type")}')
    print(f'Servicio en result: {result.get("servicio", "NO ENCONTRADO")}')
else:
    print(f'Intent no es appointment_service: {intent}')
