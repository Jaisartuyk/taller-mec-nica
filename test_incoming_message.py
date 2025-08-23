#!/usr/bin/env python3
"""
Script para simular un mensaje ENTRANTE (recibido) de WhatsApp
Basado en la estructura real de WASender para messages.upsert
"""
import requests
import json
import hmac
import hashlib

def send_incoming_message_webhook():
    """Simula un mensaje entrante de WhatsApp"""
    
    # URL del webhook
    webhook_url = "https://www.iqautoec.com/webhook/whatsapp/"
    
    # Payload simulando un mensaje RECIBIDO (messages.upsert)
    payload = {
        "event": "messages.upsert",
        "sessionId": "e736f86d08e73ce5ee6f209098dc701a60deb8157f26b79485f66e1249aabee6",
        "data": {
            "messages": {
                "key": {
                    "remoteJid": "+593987654321@s.whatsapp.net",  # Número que envía el mensaje
                    "fromMe": False,  # ← IMPORTANTE: False = mensaje recibido
                    "id": "3EB05466BF816924FC999X"
                },
                "messageTimestamp": 1755957000,
                "broadcast": False,
                "message": {
                    "conversation": "Hola chatbot, necesito ayuda"  # Mensaje del cliente
                },
                "remoteJid": "+593987654321@s.whatsapp.net",
                "id": "3EB05466BF816924FC999X"
            }
        },
        "timestamp": 1755957000000
    }
    
    # Convertir a JSON
    payload_json = json.dumps(payload)
    
    # Headers
    headers = {
        'Content-Type': 'application/json',
        'X-Webhook-Signature': 'ee8d0cbbb1d7271fbe00463c674be7c9'
    }
    
    print("🚀 Simulando mensaje ENTRANTE de WhatsApp...")
    print(f"📱 De: +593987654321 → A: +593968192046")
    print(f"💬 Mensaje: 'Hola chatbot, necesito ayuda'")
    print(f"🔗 URL: {webhook_url}")
    print(f"📊 Payload size: {len(payload_json)} bytes")
    print()
    
    try:
        # Enviar webhook
        response = requests.post(
            webhook_url,
            data=payload_json,
            headers=headers,
            timeout=30
        )
        
        print(f"✅ Status Code: {response.status_code}")
        print(f"📝 Response: {response.text}")
        
        if response.status_code == 200:
            response_data = response.json()
            if response_data.get('status') == 'processed':
                print("\n🎉 ¡CHATBOT RESPONDIÓ EXITOSAMENTE!")
                print(f"🎯 Intent detectado: {response_data.get('intent')}")
                print(f"📤 Respuesta enviada: {response_data.get('response_sent')}")
            elif response_data.get('status') == 'no_message':
                print("\n⚠️  Webhook procesado pero no detectó mensaje válido")
            else:
                print(f"\n📊 Status: {response_data.get('status')}")
        else:
            print(f"\n❌ Error HTTP: {response.status_code}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Error de conexión: {e}")
    except json.JSONDecodeError as e:
        print(f"❌ Error parsing JSON: {e}")
        print(f"Raw response: {response.text}")

if __name__ == "__main__":
    send_incoming_message_webhook()
