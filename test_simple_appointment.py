#!/usr/bin/env python
import os
import django
from datetime import datetime, timedelta

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'taller_mecanica.settings')
django.setup()

from gestion_taller.models import Cliente, Conductor, Vehiculo, Cita
from gestion_taller.services.chatbot_service import ChatbotService

def test_simple_appointment():
    print("🧪 PRUEBA SIMPLE DE CREACIÓN DE CITAS")
    print("=" * 50)
    
    # Obtener cliente y conductor
    cliente = Cliente.objects.first()
    if not cliente:
        print("❌ No hay clientes en la base de datos")
        return
    
    conductor = cliente.conductores.first()
    if not conductor:
        print("❌ No hay conductores para el cliente")
        return
    
    vehiculo = conductor.vehiculos.first()
    if not vehiculo:
        print("❌ No hay vehículos para el conductor")
        return
    
    print(f"📋 Cliente: {cliente.nombre}")
    print(f"👤 Conductor: {conductor.nombre}")
    print(f"🚗 Vehículo: {vehiculo.marca} {vehiculo.modelo} ({vehiculo.placa})")
    
    # Crear servicio de chatbot
    chatbot = ChatbotService(cliente)
    phone_number = conductor.telefono
    
    # Preparar contexto completo
    fecha_futura = datetime.now() + timedelta(days=1)
    fecha_str = fecha_futura.strftime('%Y-%m-%d %H:%M:%S')
    
    chatbot.conversation_context[phone_number] = {
        'messages': [],
        'conductor_id': conductor.id,
        'vehiculo_id': vehiculo.id,
        'servicio': 'cambio de aceite',
        'fecha_hora': fecha_str,  # Clave requerida para confirmación
        'fecha_hora_info': {
            'day': 'lunes',
            'day_number': '25',
            'time': '2 pm',
            'parsed_datetime': fecha_str
        },
        'next_step': 'confirm_appointment',  # Estado correcto para confirmación
        'last_intent': 'appointment_datetime',
        'entities': {}
    }
    
    print(f"\n🔧 Contexto preparado:")
    print(f"   - Conductor ID: {conductor.id}")
    print(f"   - Vehículo ID: {vehiculo.id}")
    print(f"   - Servicio: cambio de aceite")
    print(f"   - Fecha: {fecha_str}")
    
    # Procesar mensaje de confirmación
    print(f"\n💬 Enviando confirmación...")
    response = chatbot.process_message(phone_number, "Sí, confirmo la cita")
    
    print(f"\n📤 Respuesta del chatbot:")
    print(f"   - Success: {response.get('success')}")
    print(f"   - Response type: {type(response.get('response'))}")
    
    if response.get('success'):
        bot_response = response.get('response', {})
        print(f"   - Message: {bot_response.get('message', 'No message')[:100]}...")
        print(f"   - Type: {bot_response.get('type')}")
        print(f"   - Appointment ID: {bot_response.get('appointment_id')}")
        
        # Verificar si se creó la cita
        if 'appointment_id' in bot_response:
            cita_id = bot_response['appointment_id']
            try:
                cita = Cita.objects.get(id=cita_id)
                print(f"\n✅ CITA CREADA EXITOSAMENTE!")
                print(f"   - ID: {cita.id}")
                print(f"   - Fecha: {cita.fecha_cita}")
                print(f"   - Estado: {cita.estado}")
                print(f"   - Conductor: {cita.conductor.nombre}")
                print(f"   - Vehículo: {cita.vehiculo.marca} {cita.vehiculo.modelo}")
                return True
            except Cita.DoesNotExist:
                print(f"❌ No se encontró la cita con ID {cita_id}")
        else:
            print("❌ No se retornó appointment_id en la respuesta")
    else:
        print(f"❌ Error en la respuesta: {response.get('error')}")
    
    return False

if __name__ == '__main__':
    success = test_simple_appointment()
    if success:
        print(f"\n🎉 PRUEBA EXITOSA - El flujo de citas funciona correctamente!")
    else:
        print(f"\n⚠️ PRUEBA FALLIDA - Revisar implementación")
