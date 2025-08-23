#!/usr/bin/env python3
"""
Script para debug detallado del webhook
"""
import os
import sys
import django
import json

# Configurar Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'taller_mecanica.settings')
django.setup()

from gestion_taller.views_backup.chatbot_views import extract_message_data

def test_extract_message_data():
    """Prueba la función extract_message_data directamente"""
    
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
    
    print("🔍 TESTING extract_message_data FUNCTION")
    print("=" * 50)
    print(f"📝 Input payload:")
    print(json.dumps(payload, indent=2))
    print("\n" + "=" * 50)
    
    # Llamar a la función directamente
    result = extract_message_data(payload)
    
    print(f"📤 Result from extract_message_data:")
    print(f"   Type: {type(result)}")
    print(f"   Value: {result}")
    
    if result:
        print("\n✅ SUCCESS: Message data extracted correctly!")
        print(f"   ID: {result.get('id')}")
        print(f"   From: {result.get('from')}")
        print(f"   Text: {result.get('text')}")
        print(f"   Type: {result.get('type')}")
        print(f"   Timestamp: {result.get('timestamp')}")
    else:
        print("\n❌ FAILED: No message data extracted")
        print("   Check the debug logs above for details")

if __name__ == "__main__":
    test_extract_message_data()
