#!/usr/bin/env python3
"""
Script para probar send_chatbot_response localmente
"""
import os
import sys
import django

# Configurar Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'taller_mecanica.settings')
django.setup()

from gestion_taller.views_backup.chatbot_views import send_chatbot_response
from gestion_taller.models import Cliente

def test_send_response():
    """Prueba la función send_chatbot_response directamente"""
    
    print("🔍 TESTING send_chatbot_response FUNCTION")
    print("=" * 60)
    
    # Obtener cliente 'deaquipaya'
    cliente = Cliente.objects.filter(nombre='deaquipaya').first()
    if not cliente:
        print("❌ Cliente 'deaquipaya' no encontrado")
        return
    
    print(f"✅ Cliente encontrado: {cliente.nombre}")
    
    # Datos de prueba
    phone_number = "+593987654321@s.whatsapp.net"
    response_data = {
        'success': True,
        'response': 'Hola! Soy el chatbot del taller. ¿En qué puedo ayudarte?',
        'intent': 'saludo',
        'entities': {},
        'requires_human': False
    }
    
    print(f"📱 Teléfono: {phone_number}")
    print(f"🤖 Respuesta: {response_data['response']}")
    print("\n" + "=" * 60)
    
    # Llamar a la función
    try:
        result = send_chatbot_response(cliente, phone_number, response_data)
        print(f"\n📤 RESULTADO FINAL:")
        print(f"   Type: {type(result)}")
        print(f"   Value: {result}")
        
        if result and result.get('success'):
            print("\n✅ SUCCESS: Mensaje enviado correctamente!")
        else:
            print(f"\n❌ FAILED: {result}")
            
    except Exception as e:
        print(f"\n💥 ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_send_response()
