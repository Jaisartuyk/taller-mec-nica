#!/usr/bin/env python
import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'taller_mecanica.settings')
django.setup()

from gestion_taller.models import Cliente, Cita
from gestion_taller.services.chatbot_service import ChatbotService
from django.core.cache import cache

def test_appointment_time_issue():
    """Prueba específica del problema de hora de citas"""
    
    print("=== PRUEBA DEL PROBLEMA DE HORA EN CITAS ===")
    
    # Obtener cliente
    cliente = Cliente.objects.get(nombre='deaquipaya')
    phone = '+593968192046'
    
    # Limpiar cache
    cache.clear()
    
    print(f"\n1. Probando mensaje: 'viernes a las 2 pm'")
    
    # Crear chatbot
    chatbot = ChatbotService(cliente)
    
    # Mensaje con hora específica
    message = "Necesito agendar una cita para el viernes a las 2 pm para cambio de aceite"
    
    print(f"Usuario: {message}")
    
    # Procesar mensaje
    response = chatbot.process_message(phone, message)
    print(f"Intent detectado: {response['intent']}")
    print(f"Bot responde: {response['response']['message'][:100]}...")
    
    # Verificar contexto
    cache_key = f"chatbot_context_{cliente.id}_{phone}"
    context = cache.get(cache_key, {})
    
    print(f"\nContexto guardado:")
    print(f"- Next step: {context.get('next_step')}")
    print(f"- Fecha/hora info: {context.get('fecha_hora_info')}")
    
    if context.get('fecha_hora_info'):
        fecha_hora_info = context['fecha_hora_info']
        
        # Probar conversión a datetime
        try:
            fecha_hora_dt = chatbot._convert_fecha_hora_info_to_datetime(fecha_hora_info)
            print(f"\nConversión a datetime:")
            print(f"- Datetime: {fecha_hora_dt}")
            print(f"- Hora: {fecha_hora_dt.hour}:{fecha_hora_dt.minute:02d}")
            
            if fecha_hora_dt.hour == 14:
                print("✅ HORA CORRECTA: 2 PM = 14:00")
            else:
                print(f"❌ HORA INCORRECTA: Se esperaba 14:00 pero se obtuvo {fecha_hora_dt.hour}:{fecha_hora_dt.minute:02d}")
                
        except Exception as e:
            print(f"❌ Error en conversión: {e}")
    
    # Simular confirmación
    print(f"\n2. Confirmando cita...")
    
    # Crear nueva instancia para simular webhook
    chatbot2 = ChatbotService(cliente)
    confirmation_response = chatbot2.process_message(phone, "Sí, confirmo")
    
    print(f"Intent: {confirmation_response['intent']}")
    print(f"Response type: {confirmation_response['response'].get('type')}")
    
    if 'appointment_id' in confirmation_response['response']:
        cita_id = confirmation_response['response']['appointment_id']
        print(f"\n✅ CITA CREADA - ID: {cita_id}")
        
        # Verificar cita en base de datos
        try:
            import pytz
            from django.utils import timezone
            
            cita = Cita.objects.get(id=cita_id)
            print(f"\nDetalles de la cita:")
            print(f"- ID: {cita.id}")
            print(f"- Fecha/Hora UTC: {cita.fecha_cita}")
            
            # Convertir a zona horaria local para verificar
            tz_local = pytz.timezone('America/Guayaquil')
            fecha_local = cita.fecha_cita.astimezone(tz_local)
            print(f"- Fecha/Hora Local: {fecha_local}")
            print(f"- Hora específica local: {fecha_local.hour}:{fecha_local.minute:02d}")
            
            if fecha_local.hour == 14:
                print("✅ PROBLEMA RESUELTO: La hora se guardó correctamente (2 PM = 14:00)")
            else:
                print(f"❌ PROBLEMA PERSISTE: Se esperaba 14:00 pero se guardó {fecha_local.hour}:{fecha_local.minute:02d}")
                
            # Probar vista del dashboard
            print(f"\n3. Probando vista del dashboard...")
            try:
                from django.test import RequestFactory
                from gestion_taller.models import PerfilUsuario
                from gestion_taller.views import cita_detail_modal
                
                factory = RequestFactory()
                request = factory.get(f'/api/citas/{cita.id}/detalle/')
                
                perfil = PerfilUsuario.objects.filter(cliente=cliente).first()
                if perfil:
                    request.user = perfil.user
                    modal_response = cita_detail_modal(request, cita.id)
                    
                    if modal_response.status_code == 200:
                        print("✅ Vista del dashboard funciona correctamente")
                    else:
                        print(f"❌ Error en vista del dashboard: Status {modal_response.status_code}")
                else:
                    print("❌ No se encontró perfil de usuario")
                    
            except Exception as e:
                print(f"❌ Error en vista del dashboard: {e}")
                
        except Cita.DoesNotExist:
            print(f"❌ No se encontró la cita con ID {cita_id}")
    else:
        print("❌ No se creó la cita")
        print(f"Response: {confirmation_response}")

if __name__ == '__main__':
    test_appointment_time_issue()
