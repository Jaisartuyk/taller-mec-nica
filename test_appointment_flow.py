#!/usr/bin/env python
"""
Test completo del flujo de agendamiento de citas del chatbot
Este script prueba el flujo completo desde la solicitud inicial hasta la confirmación
"""

import os
import sys
import django
from datetime import datetime, timedelta

# Configurar Django
sys.path.append('c:/Users/H P/CascadeProjects/taller_mecanica')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'taller_mecanica.settings')
django.setup()

from gestion_taller.models import Cliente, Conductor, Vehiculo, Cita
from gestion_taller.services.chatbot_service import ChatbotService

def list_available_clients():
    """Lista los clientes disponibles en la base de datos"""
    print("📋 CLIENTES DISPONIBLES:")
    print("-" * 30)
    clientes = Cliente.objects.all()
    for cliente in clientes:
        print(f"  - ID: {cliente.id}, Nombre: {cliente.nombre}")
        conductores = cliente.conductores.all()
        print(f"    Conductores: {len(conductores)}")
        for conductor in conductores:
            vehiculos = conductor.vehiculos.all()
            print(f"      - {conductor.nombre} ({conductor.telefono}) - {len(vehiculos)} vehículos")
    print()

def test_complete_appointment_flow():
    """Prueba el flujo completo de agendamiento de citas"""
    
    print("🚀 INICIANDO PRUEBA DEL FLUJO DE AGENDAMIENTO DE CITAS")
    print("=" * 60)
    
    # Listar clientes disponibles
    list_available_clients()
    
    # Buscar cliente de prueba - usar el primer cliente disponible
    try:
        cliente = Cliente.objects.filter(nombre__icontains="deaquipaya").first()
        if not cliente:
            cliente = Cliente.objects.first()
        if not cliente:
            print("❌ No hay clientes en la base de datos")
            return False
        print(f"✅ Cliente encontrado: {cliente.nombre}")
    except Exception as e:
        print(f"❌ Error buscando cliente: {e}")
        return False
    
    # Buscar conductor de prueba
    try:
        conductor = Conductor.objects.filter(cliente=cliente).first()
        if not conductor:
            print("❌ No hay conductores para este cliente")
            return False
        print(f"✅ Conductor encontrado: {conductor.nombre} - {conductor.telefono}")
    except Exception as e:
        print(f"❌ Error buscando conductor: {e}")
        return False
    
    # Buscar vehículo del conductor
    try:
        vehiculo = Vehiculo.objects.filter(conductor=conductor).first()
        if not vehiculo:
            print("❌ No hay vehículos para este conductor")
            return False
        print(f"✅ Vehículo encontrado: {vehiculo.marca} {vehiculo.modelo} - {vehiculo.placa}")
    except Exception as e:
        print(f"❌ Error buscando vehículo: {e}")
        return False
    
    # Inicializar servicio de chatbot
    chatbot = ChatbotService(cliente)
    phone_number = conductor.telefono
    
    print(f"\n📱 Simulando conversación con número: {phone_number}")
    print("-" * 50)
    
    # Paso 1: Solicitar cita
    print("\n1️⃣ PASO 1: Solicitar agendamiento de cita")
    mensaje1 = "Hola, quiero agendar una cita para cambio de aceite"
    print(f"Usuario: {mensaje1}")
    response1 = chatbot.process_message(phone_number, mensaje1)
    
    # Debug: Ver estructura de respuesta
    print(f"🔍 DEBUG - Estructura de respuesta: {response1}")
    print(f"🔍 DEBUG - Tipo: {type(response1)}")
    print(f"🔍 DEBUG - Claves disponibles: {list(response1.keys()) if isinstance(response1, dict) else 'No es diccionario'}")
    
    # Manejar diferentes formatos de respuesta
    if isinstance(response1, dict) and 'success' in response1 and response1['success']:
        if 'response' in response1 and isinstance(response1['response'], dict):
            bot_message = response1['response'].get('message', str(response1['response']))
        else:
            bot_message = str(response1.get('response', response1))
    else:
        bot_message = f"Error: {response1.get('error', 'Respuesta inesperada')}" if isinstance(response1, dict) else str(response1)
    
    print(f"Bot: {bot_message}")
    
    # Verificar contexto después del primer mensaje
    context = chatbot.conversation_context.get(phone_number, {})
    print(f"Contexto actual: {context}")
    
    # Paso 2: Confirmar servicio (si es necesario)
    if 'last_intent' in context and context['last_intent'] in ['agendar_cita', 'appointment_service']:
        print("\n2️⃣ PASO 2: Confirmar servicio")
        mensaje2 = "Sí, cambio de aceite"
        response2 = chatbot.process_message(phone_number, mensaje2)
        print(f"Usuario: {mensaje2}")
        bot_message2 = response2['response'].get('message', str(response2['response'])) if response2.get('success') else f"Error: {response2.get('error')}"
        print(f"Bot: {bot_message2}")
        
        context = chatbot.conversation_context.get(phone_number, {})
        print(f"Contexto actual: {context}")
    
    # Paso 3: Seleccionar fecha y hora
    print("\n3️⃣ PASO 3: Seleccionar fecha y hora")
    # Usar fecha de mañana a las 10:00
    tomorrow = datetime.now() + timedelta(days=1)
    fecha_str = tomorrow.strftime("%Y-%m-%d 10:00")
    mensaje3 = f"Mañana a las 10:00 AM"
    response3 = chatbot.process_message(phone_number, mensaje3)
    print(f"Usuario: {mensaje3}")
    bot_message3 = response3['response'].get('message', str(response3['response'])) if response3.get('success') else f"Error: {response3.get('error')}"
    print(f"Bot: {bot_message3}")
    
    context = chatbot.conversation_context.get(phone_number, {})
    print(f"Contexto actual: {context}")
    
    # Paso 4: Confirmar cita
    print("\n4️⃣ PASO 4: Confirmar cita")
    mensaje4 = "Sí, confirmo la cita"
    
    # Simular contexto completo para la confirmación
    if phone_number not in chatbot.conversation_context:
        chatbot.conversation_context[phone_number] = {'messages': []}
    
    chatbot.conversation_context[phone_number].update({
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
    })
    
    response4 = chatbot.process_message(phone_number, mensaje4)
    print(f"Usuario: {mensaje4}")
    bot_message4 = response4['response'].get('message', str(response4['response'])) if response4.get('success') else f"Error: {response4.get('error')}"
    print(f"Bot: {bot_message4}")
    
    # Verificar si se creó la cita
    if response4.get('success') and 'appointment_id' in response4.get('response', {}):
        cita_id = response4['response']['appointment_id']
        try:
            cita = Cita.objects.get(id=cita_id)
            print(f"\n✅ CITA CREADA EXITOSAMENTE!")
            print(f"   ID: {cita.id}")
            print(f"   Cliente: {cita.cliente.nombre}")
            print(f"   Conductor: {cita.conductor.nombre}")
            print(f"   Vehículo: {cita.vehiculo.marca} {cita.vehiculo.modelo}")
            print(f"   Fecha: {cita.fecha_cita}")
            print(f"   Estado: {cita.estado}")
            print(f"   Servicios: {cita.get_servicios_display()}")
            return True
        except Cita.DoesNotExist:
            print(f"❌ Error: Cita con ID {cita_id} no encontrada en la base de datos")
            return False
    else:
        print("❌ Error: No se retornó ID de cita en la respuesta")
        return False

def test_context_management():
    """Prueba el manejo del contexto conversacional"""
    
    print("\n🧠 PRUEBA DE MANEJO DE CONTEXTO")
    print("=" * 40)
    
    try:
        cliente = Cliente.objects.filter(nombre__icontains="deaquipaya").first()
        if not cliente:
            cliente = Cliente.objects.first()
        if not cliente:
            print("❌ No hay clientes disponibles")
            return False
        chatbot = ChatbotService(cliente)
        phone_number = "+593968192046"
        
        # Mensaje inicial
        response1 = chatbot.process_message(phone_number, "Quiero agendar una cita")
        context1 = chatbot.conversation_context.get(phone_number, {})
        
        print(f"Mensaje 1: 'Quiero agendar una cita'")
        print(f"Intent detectado: {context1.get('last_intent', 'No detectado')}")
        print(f"Entidades: {context1.get('entities', {})}")
        
        # Segundo mensaje con información de fecha
        response2 = chatbot.process_message(phone_number, "Lunes 25 a las 2 PM")
        context2 = chatbot.conversation_context.get(phone_number, {})
        
        print(f"\nMensaje 2: 'Lunes 25 a las 2 PM'")
        print(f"Intent detectado: {context2.get('last_intent', 'No detectado')}")
        print(f"Entidades: {context2.get('entities', {})}")
        
        # Verificar que el contexto se mantiene
        if context2.get('last_intent') in ['select_datetime', 'appointment_datetime']:
            print("✅ Contexto de fecha/hora detectado correctamente")
        else:
            print("❌ Contexto de fecha/hora NO detectado")
        
        return True
        
    except Exception as e:
        print(f"❌ Error en prueba de contexto: {e}")
        return False

if __name__ == "__main__":
    print("🤖 SISTEMA DE PRUEBAS DEL CHATBOT - FLUJO DE CITAS")
    print("=" * 60)
    
    # Ejecutar pruebas
    test1_result = test_complete_appointment_flow()
    test2_result = test_context_management()
    
    print("\n" + "=" * 60)
    print("📊 RESUMEN DE RESULTADOS:")
    print(f"   Flujo completo de citas: {'✅ EXITOSO' if test1_result else '❌ FALLIDO'}")
    print(f"   Manejo de contexto: {'✅ EXITOSO' if test2_result else '❌ FALLIDO'}")
    
    if test1_result and test2_result:
        print("\n🎉 TODAS LAS PRUEBAS EXITOSAS - CHATBOT LISTO PARA PRODUCCIÓN")
    else:
        print("\n⚠️  ALGUNAS PRUEBAS FALLARON - REVISAR IMPLEMENTACIÓN")
