#!/usr/bin/env python3
"""
Script para debug completo del flujo del chatbot
"""
import os
import sys
import django
import json

# Configurar Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'taller_mecanica.settings')
django.setup()

from gestion_taller.views_backup.chatbot_views import extract_message_data, determine_client_from_webhook
from gestion_taller.services.chatbot_service import ChatbotService

def test_full_flow():
    """Prueba el flujo completo del chatbot paso a paso"""
    
    # Payload simulando un mensaje personal
    payload = {
        "event": "messages.upsert",
        "sessionId": "e736f86d08e73ce5ee6f209098dc701a60deb8157f26b79485f66e1249aabee6",
        "data": {
            "messages": {
                "key": {
                    "remoteJid": "+593987654321@s.whatsapp.net",
                    "fromMe": False,
                    "id": "TEST_MESSAGE_123456"
                },
                "messageTimestamp": 1755956200,
                "broadcast": False,
                "message": {
                    "conversation": "Hola chatbot"
                },
                "remoteJid": "+593987654321@s.whatsapp.net",
                "id": "TEST_MESSAGE_123456"
            }
        },
        "timestamp": 1755956200000
    }
    
    print("🔍 TESTING FULL CHATBOT FLOW")
    print("=" * 60)
    
    # Paso 1: Extraer datos del mensaje
    print("📝 STEP 1: Extract message data")
    message_data = extract_message_data(payload)
    print(f"   Result: {message_data}")
    
    if not message_data:
        print("❌ FAILED: No message data extracted")
        return
    
    print("✅ SUCCESS: Message data extracted")
    
    # Paso 2: Determinar cliente
    print("\n🏢 STEP 2: Determine client")
    cliente = determine_client_from_webhook(payload)
    print(f"   Result: {cliente}")
    
    if not cliente:
        print("❌ FAILED: No client determined")
        return
    
    print(f"✅ SUCCESS: Client determined - {cliente.nombre}")
    
    # Paso 3: Procesar mensaje con chatbot
    print("\n🤖 STEP 3: Process message with chatbot")
    try:
        chatbot = ChatbotService(cliente)
        phone_number = message_data['from']
        message_text = message_data['text']
        
        print(f"   Phone: {phone_number}")
        print(f"   Message: {message_text}")
        
        response_data = chatbot.process_message(phone_number, message_text)
        print(f"   Chatbot response: {response_data}")
        
        if response_data['success']:
            print("✅ SUCCESS: Chatbot processed message successfully")
            print(f"   Intent: {response_data.get('intent')}")
            print(f"   Response: {response_data.get('response')}")
        else:
            print(f"❌ FAILED: Chatbot error - {response_data['error']}")
            
    except Exception as e:
        print(f"❌ ERROR in chatbot processing: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_full_flow()
