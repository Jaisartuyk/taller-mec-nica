#!/usr/bin/env python
"""
Prueba paso a paso del flujo de agendamiento
Analiza cada respuesta del chatbot para entender el flujo
"""

import os
import sys
import django

# Configurar Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'taller_mecanica.settings')
django.setup()

from gestion_taller.models import Cliente, Cita, Conductor
from gestion_taller.services.chatbot_service import ChatbotService

def analizar_respuesta(response):
    """
    Analiza la respuesta del chatbot en detalle
    """
    print(f"🎯 Intención: {response.get('intent', 'N/A')}")
    print(f"✅ Éxito: {response.get('success', False)}")
    
    if 'response' in response:
        resp = response['response']
        print(f"💬 Mensaje: {resp.get('message', 'N/A')[:100]}...")
        print(f"📋 Tipo: {resp.get('type', 'N/A')}")
        
        if 'next_step' in resp:
            print(f"➡️ Siguiente paso: {resp['next_step']}")
        if 'conductor_id' in resp:
            print(f"👤 Conductor ID: {resp['conductor_id']}")
        if 'vehiculo_id' in resp:
            print(f"🚗 Vehículo ID: {resp['vehiculo_id']}")
    
    if 'context' in response:
        print(f"📝 Contexto: {response['context']}")
    
    print("-" * 60)

def test_flujo_agendamiento():
    """
    Prueba el flujo de agendamiento paso a paso
    """
    print("🚀 PRUEBA DETALLADA DEL FLUJO DE AGENDAMIENTO")
    print("=" * 70)
    
    # Obtener cliente
    cliente = Cliente.objects.first()
    if not cliente:
        print("❌ No hay clientes en la base de datos")
        return
    
    print(f"🏢 Cliente: {cliente.nombre}")
    
    # Crear chatbot
    chatbot = ChatbotService(cliente)
    phone_number = "+573001234567"
    
    # Paso 1: Saludo
    print("\n📋 PASO 1: SALUDO INICIAL")
    response = chatbot.process_message(phone_number, "Hola")
    analizar_respuesta(response)
    
    # Paso 2: Solicitar agendamiento
    print("\n📋 PASO 2: SOLICITAR AGENDAMIENTO")
    response = chatbot.process_message(phone_number, "Quiero agendar una cita")
    analizar_respuesta(response)
    
    # Guardar datos del paso 2 para análisis
    conductor_id = None
    vehiculo_id = None
    if 'response' in response:
        conductor_id = response['response'].get('conductor_id')
        vehiculo_id = response['response'].get('vehiculo_id')
    
    # Paso 3: Responder con fecha/hora
    print("\n📋 PASO 3: SELECCIONAR FECHA Y HORA")
    response = chatbot.process_message(phone_number, "Mañana a las 9:00 AM")
    analizar_respuesta(response)
    
    # Paso 4: Especificar servicio
    print("\n📋 PASO 4: ESPECIFICAR SERVICIO")
    response = chatbot.process_message(phone_number, "Reparación de motor")
    analizar_respuesta(response)
    
    # Paso 5: Confirmar
    print("\n📋 PASO 5: CONFIRMAR CITA")
    response = chatbot.process_message(phone_number, "Sí, confirmo la cita")
    analizar_respuesta(response)
    
    # Verificar si se creó la cita
    print("\n📅 VERIFICACIÓN DE CITA CREADA")
    print("-" * 40)
    
    if conductor_id:
        try:
            conductor = Conductor.objects.get(id=conductor_id)
            citas = Cita.objects.filter(conductor=conductor).order_by('-fecha_creacion')
            
            print(f"👤 Conductor: {conductor.nombre}")
            print(f"📱 Teléfono: {conductor.telefono}")
            
            if citas.exists():
                print(f"✅ Se encontraron {citas.count()} citas para este conductor:")
                for cita in citas[:3]:
                    print(f"   • ID: {cita.id} | Estado: {cita.estado}")
                    print(f"   • Fecha: {cita.fecha_cita}")
                    print(f"   • Servicios: {cita.get_servicios_display()}")
            else:
                print("❌ No se crearon citas nuevas")
                
        except Conductor.DoesNotExist:
            print(f"❌ No se encontró conductor con ID {conductor_id}")
    else:
        print("❌ No se obtuvo ID de conductor del chatbot")
    
    # Mostrar contexto final del chatbot
    print(f"\n🧠 CONTEXTO FINAL DEL CHATBOT")
    print("-" * 40)
    context = chatbot._get_conversation_context(phone_number)
    if context:
        print(f"📝 Mensajes en contexto: {len(context.get('messages', []))}")
        print(f"🎯 Última intención: {context.get('last_intent', 'N/A')}")
        print(f"📊 Entidades: {context.get('entities', {})}")
    else:
        print("❌ No hay contexto guardado")

def test_mensajes_individuales():
    """
    Prueba mensajes individuales para entender el comportamiento
    """
    print("\n🔍 PRUEBA DE MENSAJES INDIVIDUALES")
    print("=" * 50)
    
    cliente = Cliente.objects.first()
    chatbot = ChatbotService(cliente)
    phone_number = "+573001234567"
    
    mensajes_prueba = [
        "Hola",
        "Quiero agendar una cita",
        "Mañana a las 10 AM",
        "Cambio de aceite",
        "Sí, confirmo"
    ]
    
    for i, mensaje in enumerate(mensajes_prueba, 1):
        print(f"\n🔸 MENSAJE {i}: '{mensaje}'")
        response = chatbot.process_message(phone_number, mensaje)
        print(f"   Intención: {response.get('intent')}")
        print(f"   Tipo respuesta: {response.get('response', {}).get('type', 'N/A')}")

if __name__ == "__main__":
    test_flujo_agendamiento()
    test_mensajes_individuales()
