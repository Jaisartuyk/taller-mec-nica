#!/usr/bin/env python3
"""
Script para probar el chatbot simulando un mensaje personal de WhatsApp
"""
import os
import sys
import django
import json
import requests
import hashlib
import hmac

# Configurar Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'taller_mecanica.settings')
django.setup()

def test_personal_message():
    """Simula un mensaje personal al webhook del chatbot"""
    
    # URL del webhook
    webhook_url = "https://www.iqautoec.com/webhook/whatsapp/"
    
    # Payload simulando un mensaje personal
    payload = {
        "event": "messages.upsert",
        "sessionId": "e736f86d08e73ce5ee6f209098dc701a60deb8157f26b79485f66e1249aabee6",
        "data": {
            "messages": {
                "key": {
                    "remoteJid": "+593987654321@s.whatsapp.net",  # Número personal simulado
                    "fromMe": False,
                    "id": "TEST_MESSAGE_123456"
                },
                "messageTimestamp": 1755956200,
                "broadcast": False,
                "message": {
                    "conversation": "Hola chatbot"  # Mensaje simple de prueba
                },
                "remoteJid": "+593987654321@s.whatsapp.net",
                "id": "TEST_MESSAGE_123456"
            }
        },
        "timestamp": 1755956200000
    }
    
    # Convertir a JSON
    payload_json = json.dumps(payload)
    
    # Webhook secret
    webhook_secret = "ee8d0cbbb1d7271fbe00463c674be7c9"
    
    # Headers
    headers = {
        'Content-Type': 'application/json',
        'X-Webhook-Signature': webhook_secret,
        'User-Agent': 'WASender-Test/1.0'
    }
    
    print("🚀 Enviando mensaje personal simulado al webhook...")
    print(f"📱 Número simulado: +593987654321")
    print(f"💬 Mensaje: 'Hola chatbot'")
    print(f"🔗 URL: {webhook_url}")
    print(f"🔐 Signature: {webhook_secret}")
    print()
    
    try:
        # Enviar request
        response = requests.post(
            webhook_url,
            data=payload_json,
            headers=headers,
            timeout=30
        )
        
        print(f"✅ Status Code: {response.status_code}")
        print(f"📝 Response: {response.text}")
        
        if response.status_code == 200:
            print("\n🎉 ¡Webhook procesado exitosamente!")
            print("🤖 Verifica si el chatbot respondió correctamente")
        else:
            print(f"\n❌ Error en webhook: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error enviando request: {e}")

if __name__ == "__main__":
    test_personal_message()
