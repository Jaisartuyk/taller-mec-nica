#!/usr/bin/env python
"""
Test script para verificar el funcionamiento del ChatbotService
"""
import os
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'taller_mecanica.settings')
django.setup()

from gestion_taller.models import Cliente
from gestion_taller.services.chatbot_service import ChatbotService

def test_chatbot_appointment():
    """Test para verificar detección de intents de citas"""
    
    # Obtener cliente
    cliente = Cliente.objects.first()
    if not cliente:
        print("❌ No hay clientes en la base de datos")
        return
    
    print(f"✅ Cliente encontrado: {cliente.nombre}")
    
    # Crear instancia del chatbot
    chatbot = ChatbotService(cliente)
    
    # Test messages
    test_messages = [
        "quiero agendar una cita",
        "necesito una cita",
        "agendar cita",
        "reservar turno",
        "hola",
        "que servicios tienen"
    ]
    
    print("\n🧪 PROBANDO DETECCIÓN DE INTENTS:")
    print("=" * 50)
    
    for message in test_messages:
        print(f"\n📝 Mensaje: '{message}'")
        response = chatbot.process_message('+593968192046', message)
        
        if response.get('success'):
            intent = response.get('intent', 'unknown')
            response_msg = response.get('response', {}).get('message', 'No hay mensaje')
            print(f"✅ Intent detectado: {intent}")
            print(f"💬 Respuesta: {response_msg[:100]}...")
        else:
            print(f"❌ Error: {response.get('error')}")
    
    print("\n" + "=" * 50)
    print("🏁 Test completado")

if __name__ == "__main__":
    test_chatbot_appointment()
