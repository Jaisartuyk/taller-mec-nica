#!/usr/bin/env python
"""
Script de prueba para verificar las correcciones del ChatbotService
Simula el flujo de conversación de WhatsApp que estaba fallando
"""

import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'taller_mecanica.settings')
django.setup()

from gestion_taller.models import Cliente, Conductor, Vehiculo
from gestion_taller.services.chatbot_service import ChatbotService

def test_chatbot_flow():
    """Prueba el flujo de agendamiento de citas que estaba fallando"""
    
    print("=== PRUEBA DE CORRECCIÓN DEL CHATBOT ===\n")
    
    # Obtener o crear un cliente de prueba
    try:
        cliente = Cliente.objects.first()
        if not cliente:
            print("❌ No hay clientes en la base de datos")
            return
        
        print(f"✅ Cliente encontrado: {cliente.nombre}")
        
        # Simular número de teléfono
        phone_number = "+573001234567"
        
        # Crear o obtener conductor de prueba
        conductor, created = Conductor.objects.get_or_create(
            cliente=cliente,
            telefono=phone_number[-8:],  # Últimos 8 dígitos
            defaults={
                'nombre': 'Marcos Pérez',
                'correo': 'marcos@test.com',
                'direccion': 'Calle Test 123'
            }
        )
        
        if created:
            print(f"✅ Conductor creado: {conductor.nombre}")
        else:
            print(f"✅ Conductor encontrado: {conductor.nombre}")
        
        # Crear o obtener vehículo de prueba
        vehiculo, created = Vehiculo.objects.get_or_create(
            conductor=conductor,
            placa='ADT654',
            defaults={
                'cliente': cliente,  # Campo requerido
                'marca': 'TOYOTA',
                'modelo': 'HILUX',
                'anio': 2023,
                'kilometraje': 20000
            }
        )
        
        if created:
            print(f"✅ Vehículo creado: {vehiculo.marca} {vehiculo.modelo}")
        else:
            print(f"✅ Vehículo encontrado: {vehiculo.marca} {vehiculo.modelo}")
        
        # Crear servicio de chatbot
        chatbot = ChatbotService(cliente)
        
        print(f"📱 Simulando conversación para: {phone_number}\n")
        
        # Paso 1: Usuario solicita cita
        print("👤 Usuario: 'Quiero agendar una cita'")
        response1 = chatbot.process_message(phone_number, "Quiero agendar una cita")
        
        if response1['success']:
            print(f"🤖 Bot: {response1['response']['message'][:200]}...")
            print(f"📋 Intent detectado: {response1['intent']}")
            print(f"🔄 Next step: {response1['response'].get('next_step', 'N/A')}")
        else:
            print(f"❌ Error: {response1['error']}")
            return
        
        print("\n" + "="*50 + "\n")
        
        # Paso 2: Usuario responde con fecha (aquí estaba el problema)
        print("👤 Usuario: 'Lunes 25'")
        response2 = chatbot.process_message(phone_number, "Lunes 25")
        
        if response2['success']:
            print(f"🤖 Bot: {response2['response']['message'][:200]}...")
            print(f"📋 Intent detectado: {response2['intent']}")
            print(f"🔄 Next step: {response2['response'].get('next_step', 'N/A')}")
            
            # Verificar si se detectó correctamente como appointment_datetime
            if response2['intent'] == 'appointment_datetime':
                print("✅ CORRECCIÓN EXITOSA: Se detectó correctamente como appointment_datetime")
            else:
                print(f"❌ PROBLEMA PERSISTE: Se detectó como {response2['intent']} en lugar de appointment_datetime")
        else:
            print(f"❌ Error: {response2['error']}")
        
        print("\n" + "="*50 + "\n")
        
        # Mostrar contexto final
        context = chatbot._get_conversation_context(phone_number)
        print("📊 CONTEXTO FINAL:")
        for key, value in context.items():
            if key != 'messages':  # No mostrar todos los mensajes
                print(f"   {key}: {value}")
        
    except Exception as e:
        print(f"❌ Error en la prueba: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_chatbot_flow()
