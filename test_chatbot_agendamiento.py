#!/usr/bin/env python
"""
Script de prueba para el sistema de agendamiento de citas del chatbot WhatsApp
Simula mensajes entrantes para probar el flujo completo
"""

import os
import sys
import django
import requests
import json
from datetime import datetime

# Configurar Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'taller_mecanica.settings')
django.setup()

from gestion_taller.models import Cliente, Conductor, Vehiculo
from gestion_taller.services.chatbot_service import ChatbotService

# URL del webhook local
WEBHOOK_URL = "http://127.0.0.1:8000/webhook/whatsapp/"

def simular_mensaje_whatsapp(phone_number, message_text, cliente_id=None):
    """
    Simula un mensaje entrante de WhatsApp
    """
    # Estructura típica de mensaje de WASender
    webhook_data = {
        "event": "message.received",
        "data": {
            "id": f"msg_{datetime.now().timestamp()}",
            "from": phone_number,
            "to": "573001234567",  # Número del taller
            "type": "text",
            "text": {
                "body": message_text
            },
            "timestamp": int(datetime.now().timestamp())
        },
        "instance_id": "test_instance",
        "webhook_secret": "ee8d0cbbb1d7271fbe00463c674be7c9"
    }
    
    headers = {
        'Content-Type': 'application/json',
        'X-Webhook-Signature': 'ee8d0cbbb1d7271fbe00463c674be7c9'
    }
    
    try:
        response = requests.post(WEBHOOK_URL, json=webhook_data, headers=headers)
        print(f"📱 Mensaje enviado: {message_text}")
        print(f"📞 Desde: {phone_number}")
        print(f"✅ Respuesta: {response.status_code} - {response.json()}")
        print("-" * 50)
        return response.json()
    except Exception as e:
        print(f"❌ Error enviando mensaje: {e}")
        return None

def test_chatbot_directo(phone_number, message_text):
    """
    Prueba directa del chatbot sin webhook
    """
    try:
        # Obtener primer cliente disponible
        cliente = Cliente.objects.first()
        if not cliente:
            print("❌ No hay clientes en la base de datos")
            return
        
        print(f"🏢 Usando cliente: {cliente.nombre}")
        
        # Crear instancia del chatbot
        chatbot = ChatbotService(cliente)
        
        # Procesar mensaje
        response = chatbot.process_message(phone_number, message_text)
        
        print(f"📱 Mensaje: {message_text}")
        print(f"📞 Desde: {phone_number}")
        print(f"🤖 Intención detectada: {response.get('intent', 'N/A')}")
        print(f"💬 Respuesta: {response.get('response', 'N/A')}")
        print(f"✅ Éxito: {response.get('success', False)}")
        
        if response.get('context'):
            print(f"📋 Contexto: {response['context']}")
        
        print("-" * 50)
        return response
        
    except Exception as e:
        print(f"❌ Error en prueba directa: {e}")
        return None

def flujo_agendamiento_completo():
    """
    Simula un flujo completo de agendamiento de cita
    """
    phone_number = "+573001234567"
    
    print("🚀 INICIANDO PRUEBA DE FLUJO DE AGENDAMIENTO")
    print("=" * 60)
    
    # Paso 1: Saludo inicial
    print("📋 PASO 1: Saludo inicial")
    test_chatbot_directo(phone_number, "Hola")
    
    # Paso 2: Solicitar cita
    print("📋 PASO 2: Solicitar agendamiento de cita")
    test_chatbot_directo(phone_number, "Quiero agendar una cita")
    
    # Paso 3: Proporcionar información del vehículo
    print("📋 PASO 3: Información del vehículo")
    test_chatbot_directo(phone_number, "Mi vehículo es un Toyota Corolla 2020, placa ABC123")
    
    # Paso 4: Describir el problema
    print("📋 PASO 4: Descripción del problema")
    test_chatbot_directo(phone_number, "El motor hace ruido extraño y vibra mucho")
    
    # Paso 5: Seleccionar fecha
    print("📋 PASO 5: Selección de fecha")
    test_chatbot_directo(phone_number, "Mañana en la mañana estaría bien")
    
    # Paso 6: Confirmación
    print("📋 PASO 6: Confirmación")
    test_chatbot_directo(phone_number, "Sí, confirmo la cita")
    
    print("🎉 FLUJO DE AGENDAMIENTO COMPLETADO")
    print("=" * 60)

def mostrar_menu():
    """
    Muestra el menú de opciones de prueba
    """
    print("\n🤖 SISTEMA DE PRUEBAS - CHATBOT AGENDAMIENTO")
    print("=" * 50)
    print("1. Flujo completo de agendamiento")
    print("2. Mensaje personalizado")
    print("3. Probar webhook (requiere servidor)")
    print("4. Ver clientes disponibles")
    print("5. Ver citas existentes")
    print("0. Salir")
    print("-" * 50)

def ver_clientes():
    """
    Muestra los clientes disponibles
    """
    clientes = Cliente.objects.all()
    print(f"\n👥 CLIENTES DISPONIBLES ({clientes.count()})")
    print("-" * 30)
    for cliente in clientes:
        print(f"ID: {cliente.id} - {cliente.nombre}")
        if hasattr(cliente, 'configuracion_taller'):
            print(f"   Config: {cliente.configuracion_taller}")
    print()

def ver_citas():
    """
    Muestra las citas existentes
    """
    from gestion_taller.models import Cita
    citas = Cita.objects.all().order_by('-fecha_creacion')[:10]
    print(f"\n📅 CITAS RECIENTES ({citas.count()})")
    print("-" * 40)
    for cita in citas:
        print(f"ID: {cita.id}")
        print(f"Cliente: {cita.cliente.nombre if cita.cliente else 'N/A'}")
        print(f"Teléfono: {cita.telefono_contacto}")
        print(f"Estado: {cita.estado}")
        print(f"Fecha: {cita.fecha_hora}")
        print(f"Descripción: {cita.descripcion_problema[:50]}...")
        print("-" * 20)

def main():
    """
    Función principal del script de pruebas
    """
    while True:
        mostrar_menu()
        opcion = input("Selecciona una opción: ").strip()
        
        if opcion == "0":
            print("👋 ¡Hasta luego!")
            break
        elif opcion == "1":
            flujo_agendamiento_completo()
        elif opcion == "2":
            phone = input("Número de teléfono (+573001234567): ").strip() or "+573001234567"
            mensaje = input("Mensaje: ").strip()
            if mensaje:
                test_chatbot_directo(phone, mensaje)
        elif opcion == "3":
            phone = input("Número de teléfono (+573001234567): ").strip() or "+573001234567"
            mensaje = input("Mensaje: ").strip()
            if mensaje:
                simular_mensaje_whatsapp(phone, mensaje)
        elif opcion == "4":
            ver_clientes()
        elif opcion == "5":
            ver_citas()
        else:
            print("❌ Opción no válida")
        
        input("\nPresiona Enter para continuar...")

if __name__ == "__main__":
    main()
