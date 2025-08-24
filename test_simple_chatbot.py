#!/usr/bin/env python
"""
Prueba simple del chatbot de agendamiento
"""

import os
import sys
import django

# Configurar Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'taller_mecanica.settings')
django.setup()

from gestion_taller.models import Cliente, Cita
from gestion_taller.services.chatbot_service import ChatbotService

def test_chatbot():
    """
    Prueba básica del chatbot
    """
    print("🤖 INICIANDO PRUEBA DEL CHATBOT")
    print("=" * 40)
    
    # Obtener primer cliente
    cliente = Cliente.objects.first()
    if not cliente:
        print("❌ No hay clientes en la base de datos")
        return
    
    print(f"🏢 Cliente: {cliente.nombre}")
    
    # Crear chatbot
    chatbot = ChatbotService(cliente)
    phone_number = "+573001234567"
    
    # Secuencia de mensajes para agendar cita
    mensajes = [
        "Hola",
        "Quiero agendar una cita",
        "Mi vehículo es un Toyota Corolla 2020, placa ABC123",
        "El motor hace ruido extraño",
        "Mañana en la mañana",
        "Sí, confirmo"
    ]
    
    for i, mensaje in enumerate(mensajes, 1):
        print(f"\n📱 MENSAJE {i}: {mensaje}")
        print("-" * 30)
        
        try:
            response = chatbot.process_message(phone_number, mensaje)
            
            print(f"🎯 Intención: {response.get('intent', 'N/A')}")
            print(f"💬 Respuesta: {response.get('response', 'N/A')}")
            print(f"✅ Éxito: {response.get('success', False)}")
            
            if response.get('context'):
                print(f"📋 Contexto: {response['context']}")
                
        except Exception as e:
            print(f"❌ Error: {e}")
    
    # Verificar si se creó una cita
    print(f"\n📅 VERIFICANDO CITAS CREADAS")
    print("-" * 30)
    
    # Buscar citas por conductor que tenga el teléfono
    from gestion_taller.models import Conductor
    conductor = Conductor.objects.filter(telefono=phone_number).first()
    
    if conductor:
        citas = Cita.objects.filter(conductor=conductor).order_by('-fecha_creacion')
        print(f"📞 Conductor encontrado: {conductor.nombre}")
    else:
        # Si no hay conductor, mostrar todas las citas recientes
        citas = Cita.objects.all().order_by('-fecha_creacion')[:5]
        print(f"📞 No se encontró conductor con teléfono {phone_number}")
        print(f"📋 Mostrando últimas 5 citas del sistema:")
    
    if citas.exists():
        for cita in citas[:3]:  # Mostrar últimas 3 citas
            print(f"✅ Cita ID: {cita.id}")
            print(f"   Estado: {cita.estado}")
            print(f"   Conductor: {cita.conductor.nombre if cita.conductor else 'N/A'}")
            print(f"   Vehículo: {cita.vehiculo}")
            print(f"   Fecha: {cita.fecha_cita}")
            print(f"   Servicios: {cita.get_servicios_display()}")
            print(f"   Creada: {cita.fecha_creacion}")
    else:
        print("❌ No se encontraron citas")

if __name__ == "__main__":
    test_chatbot()
