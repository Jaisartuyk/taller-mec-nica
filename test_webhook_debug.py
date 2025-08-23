#!/usr/bin/env python3
"""
Script para probar el webhook con debug completo
"""
import requests
import json

def test_webhook_with_debug():
    """Prueba el webhook con información de debug"""
    
    # URL del webhook
    webhook_url = "https://www.iqautoec.com/webhook/whatsapp/"
    
    # Payload con mensaje simple para debug
    payload = {
        "event": "messages.upsert",
        "sessionId": "e736f86d08e73ce5ee6f209098dc701a60deb8157f26b79485f66e1249aabee6",
        "data": {
            "messages": {
                "key": {
                    "remoteJid": "+593987654321@s.whatsapp.net",
                    "fromMe": False,
                    "id": "DEBUG_TEST_" + str(int(time.time()) if 'time' in globals() else 999999)
                },
                "messageTimestamp": 1755957200,
                "broadcast": False,
                "message": {
                    "conversation": "test debug"
                },
                "remoteJid": "+593987654321@s.whatsapp.net",
                "id": "DEBUG_TEST_999999"
            }
        },
        "timestamp": 1755957200000
    }
    
    # Convertir a JSON
    payload_json = json.dumps(payload)
    
    # Headers
    headers = {
        'Content-Type': 'application/json',
        'X-Webhook-Signature': 'ee8d0cbbb1d7271fbe00463c674be7c9'
    }
    
    print("🔍 TESTING WEBHOOK DEBUG")
    print("=" * 50)
    print(f"🔗 URL: {webhook_url}")
    print(f"💬 Mensaje: 'test debug'")
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
        print(f"📝 Response Headers: {dict(response.headers)}")
        print(f"📝 Response Text: {response.text}")
        
        if response.status_code == 200:
            try:
                response_data = response.json()
                print(f"\n📊 Response JSON: {json.dumps(response_data, indent=2)}")
                
                if response_data.get('status') == 'processed':
                    response_sent = response_data.get('response_sent', False)
                    print(f"\n🎯 Status: processed")
                    print(f"🎯 Intent: {response_data.get('intent')}")
                    print(f"🎯 Response sent: {response_sent}")
                    
                    if response_sent:
                        print("\n🎉 ¡CHATBOT FUNCIONANDO COMPLETAMENTE!")
                    else:
                        print("\n⚠️  Chatbot procesa pero no envía respuesta")
                else:
                    print(f"\n📊 Status: {response_data.get('status')}")
                    
            except json.JSONDecodeError:
                print(f"\n❌ Response no es JSON válido")
        else:
            print(f"\n❌ Error HTTP: {response.status_code}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Error de conexión: {e}")

if __name__ == "__main__":
    import time
    test_webhook_with_debug()
