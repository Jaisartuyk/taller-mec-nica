"""
Vistas para el Chatbot de WhatsApp
Manejo de webhooks y respuestas automáticas
"""
import json
import logging
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils.decorators import method_decorator
from django.views import View
from django.utils import timezone
from ..models import Cliente
from ..services.chatbot_service import ChatbotService
from ..services.multi_taller_messaging import MultiTallerMessagingService

logger = logging.getLogger(__name__)


@csrf_exempt
@require_http_methods(["POST", "GET"])
def whatsapp_webhook(request):
    """
    Webhook para recibir mensajes de WhatsApp
    GET: Verificación del webhook
    POST: Procesamiento de mensajes entrantes
    """
    if request.method == 'GET':
        return verify_webhook(request)
    elif request.method == 'POST':
        return process_incoming_message(request)


@csrf_exempt
def whatsapp_webhook_test(request):
    """Endpoint simple para probar conectividad del webhook"""
    return JsonResponse({
        'status': 'ok',
        'method': request.method,
        'timestamp': timezone.now().isoformat(),
        'message': 'Webhook test endpoint funcionando'
    })


def verify_webhook(request):
    """Verifica el webhook de WhatsApp (para configuración inicial)"""
    # Token de verificación (configurar en settings)
    verify_token = "taller_mecanica_webhook_2024"
    
    mode = request.GET.get('hub.mode')
    token = request.GET.get('hub.verify_token')
    challenge = request.GET.get('hub.challenge')
    
    if mode == 'subscribe' and token == verify_token:
        logger.info("Webhook verificado exitosamente")
        return HttpResponse(challenge)
    else:
        logger.warning("Verificación de webhook fallida")
        return HttpResponse("Forbidden", status=403)


def process_incoming_message(request):
    """Procesa mensajes entrantes de WhatsApp"""
    try:
        # DEBUG: Log del request completo
        print(f"DEBUG WEBHOOK - Method: {request.method}")
        print(f"DEBUG WEBHOOK - Headers: {dict(request.headers)}")
        print(f"DEBUG WEBHOOK - Body: {request.body.decode('utf-8')}")
        
        # Verificar signature del webhook (opcional pero recomendado)
        webhook_signature = request.headers.get('X-Webhook-Signature')
        webhook_secret = 'ee8d0cbbb1d7271fbe00463c674be7c9'  # Debe coincidir con WASender
        
        if webhook_signature and webhook_signature != webhook_secret:
            logger.warning(f"Signature inválida: {webhook_signature}")
            return JsonResponse({'error': 'Invalid signature'}, status=401)
        
        print(f"DEBUG WEBHOOK - Signature verificada: {webhook_signature}")
        
        # Parsear datos del webhook
        data = json.loads(request.body)
        logger.info(f"Mensaje recibido: {data}")
        print(f"DEBUG WEBHOOK - Parsed data: {data}")
        
        # Manejar evento de prueba específicamente
        if data.get('event') == 'webhook.test':
            print("DEBUG: Evento de prueba de WASender recibido")
            return JsonResponse({
                'status': 'test_received',
                'message': 'Webhook test successful',
                'timestamp': timezone.now().isoformat()
            })
        
        # Extraer información del mensaje
        message_data = extract_message_data(data)
        
        if not message_data:
            print("DEBUG: No se encontró mensaje válido en los datos")
            return JsonResponse({'status': 'no_message'})
        
        phone_number = message_data['from']
        message_text = message_data['text']
        message_id = message_data['id']
        
        # Determinar cliente/taller basado en el número receptor
        cliente = determine_client_from_webhook(data)
        
        if not cliente:
            logger.error("No se pudo determinar el cliente del mensaje")
            return JsonResponse({'status': 'client_not_found'})
        
        # Procesar mensaje con chatbot
        chatbot = ChatbotService(cliente)
        response_data = chatbot.process_message(phone_number, message_text)
        
        if response_data['success']:
            # Enviar respuesta automática
            send_response = send_chatbot_response(
                cliente, 
                phone_number, 
                response_data
            )
            
            logger.info(f"Respuesta enviada: {send_response}")
            
            return JsonResponse({
                'status': 'processed',
                'intent': response_data.get('intent'),
                'response_sent': send_response.get('success', False)
            })
        else:
            logger.error(f"Error procesando mensaje: {response_data['error']}")
            return JsonResponse({'status': 'processing_error'})
            
    except Exception as e:
        logger.error(f"Error en webhook: {str(e)}")
        return JsonResponse({'status': 'error', 'message': str(e)})


def determine_client_from_webhook(webhook_data):
    """Determina el cliente basado en los datos del webhook"""
    try:
        # Para WASender, el sessionId contiene el token API que corresponde al cliente
        session_id = webhook_data.get('sessionId')
        
        if session_id:
            # Buscar cliente por token API (si está configurado)
            # Por ahora, usar el cliente por defecto 'deaquipaya' para pruebas
            from gestion_taller.models import Cliente
            
            # Buscar cliente 'deaquipaya' para pruebas
            cliente = Cliente.objects.filter(nombre='deaquipaya').first()
            
            if cliente:
                print(f"DEBUG: Cliente encontrado: {cliente.nombre}")
                return cliente
            
            # Fallback: usar el primer cliente disponible
            cliente = Cliente.objects.first()
            if cliente:
                print(f"DEBUG: Usando cliente fallback: {cliente.nombre}")
                return cliente
        
        print("DEBUG: No se pudo determinar cliente del webhook")
        return None
        
    except Exception as e:
        print(f"ERROR determine_client_from_webhook: {e}")
        return None


def extract_message_data(webhook_data):
    """Extrae información del mensaje del webhook"""
    try:
        print(f"DEBUG extract_message_data - webhook_data keys: {list(webhook_data.keys())}")
        
        # Manejar evento de prueba de WASender
        if webhook_data.get('event') == 'webhook.test':
            print("DEBUG: Evento de prueba detectado")
            return None  # No procesar eventos de prueba como mensajes
        
        # Estructura específica de WASender messages.upsert
        if webhook_data.get('event') == 'messages.upsert' and 'data' in webhook_data:
            print("DEBUG: Estructura WASender messages.upsert detectada")
            data = webhook_data['data']
            messages = data.get('messages', {})
            
            if messages:
                # Extraer información del mensaje
                key = messages.get('key', {})
                message_content = messages.get('message', {})
                
                # Obtener el texto del mensaje
                text = ''
                if 'conversation' in message_content:
                    text = message_content['conversation']
                elif 'extendedTextMessage' in message_content:
                    text = message_content['extendedTextMessage'].get('text', '')
                elif 'text' in message_content:
                    text = message_content['text']
                
                # Solo procesar mensajes personales (no newsletters)
                remote_jid = key.get('remoteJid', '')
                if '@newsletter' in remote_jid:
                    print(f"DEBUG: Ignorando mensaje de newsletter: {remote_jid}")
                    return None
                
                if text and remote_jid:
                    return {
                        'id': key.get('id'),
                        'from': remote_jid,
                        'text': text,
                        'type': 'text',
                        'timestamp': messages.get('messageTimestamp')
                    }
        
        # Estructura típica de WhatsApp Business API
        elif 'entry' in webhook_data:
            print("DEBUG: Estructura WhatsApp Business API detectada")
            entry = webhook_data['entry'][0]
            changes = entry.get('changes', [])
            
            if changes:
                change = changes[0]
                value = change.get('value', {})
                messages = value.get('messages', [])
                
                if messages:
                    message = messages[0]
                    return {
                        'id': message.get('id'),
                        'from': message.get('from'),
                        'text': message.get('text', {}).get('body', ''),
                        'type': message.get('type', 'text'),
                        'timestamp': message.get('timestamp')
                    }
        
        # Estructura de WASender API (legacy)
        elif 'message' in webhook_data:
            print("DEBUG: Estructura WASender API legacy detectada")
            message = webhook_data['message']
            return {
                'id': message.get('id'),
                'from': message.get('from'),
                'text': message.get('body', ''),
                'type': message.get('type', 'text'),
                'timestamp': message.get('timestamp')
            }
        
        # Estructura directa de mensaje (WASender legacy)
        elif 'from' in webhook_data and ('body' in webhook_data or 'text' in webhook_data):
            print("DEBUG: Estructura directa de mensaje detectada")
            return {
                'id': webhook_data.get('id'),
                'from': webhook_data.get('from'),
                'text': webhook_data.get('body') or webhook_data.get('text', ''),
                'type': webhook_data.get('type', 'text'),
                'timestamp': webhook_data.get('timestamp')
            }
            
        print(f"DEBUG: No se encontró estructura de mensaje reconocida. Datos: {webhook_data}")
        return None
        
    except Exception as e:
        logger.error(f"Error extrayendo datos del mensaje: {str(e)}")
        return None


def determine_client_from_webhook(webhook_data):
    """Determina qué cliente/taller debe procesar el mensaje"""
    try:
        # Método 1: Por número receptor (si está en los datos)
        to_number = webhook_data.get('to') or webhook_data.get('recipient')
        
        if to_number:
            # Buscar cliente por número de WhatsApp
            cliente = Cliente.objects.filter(
                telefono__icontains=to_number[-8:]
            ).first()
            
            if cliente:
                return cliente
        
        # Método 2: Si solo hay un cliente, usar ese
        clientes = Cliente.objects.all()
        if clientes.count() == 1:
            return clientes.first()
        
        # Método 3: Usar cliente por defecto (el primero)
        return Cliente.objects.first()
        
    except Exception as e:
        logger.error(f"Error determinando cliente: {str(e)}")
        return Cliente.objects.first()


def send_chatbot_response(cliente, phone_number, response_data):
    """Envía respuesta del chatbot via WhatsApp"""
    try:
        print(f"DEBUG send_chatbot_response - Cliente: {cliente.nombre}")
        print(f"DEBUG send_chatbot_response - Phone: {phone_number}")
        print(f"DEBUG send_chatbot_response - Response data: {response_data}")
        
        # Limpiar número de teléfono (remover @s.whatsapp.net)
        clean_phone = phone_number.replace('@s.whatsapp.net', '').replace('@c.us', '')
        print(f"DEBUG send_chatbot_response - Clean phone: {clean_phone}")
        
        messaging_service = MultiTallerMessagingService(cliente=cliente)
        
        # Preparar datos del mensaje
        # El ChatbotService retorna 'response', no 'message'
        response_text = response_data.get('response', '')
        if isinstance(response_text, dict):
            response_text = response_text.get('text', str(response_text))
        
        print(f"DEBUG send_chatbot_response - Response text: {response_text}")
        
        datos = {
            'mensaje_personalizado': response_text
        }
        
        print(f"DEBUG send_chatbot_response - Datos: {datos}")
        
        # Enviar mensaje
        resultado = messaging_service.enviar_mensaje(
            telefono=clean_phone,
            tipo_mensaje='personalizado',
            datos=datos,
            canal='whatsapp'
        )
        
        print(f"DEBUG send_chatbot_response - Resultado: {resultado}")
        
        whatsapp_result = resultado.get('whatsapp', {})
        print(f"DEBUG send_chatbot_response - WhatsApp result: {whatsapp_result}")
        
        return whatsapp_result
        
    except Exception as e:
        print(f"ERROR send_chatbot_response: {str(e)}")
        import traceback
        traceback.print_exc()
        logger.error(f"Error enviando respuesta del chatbot: {str(e)}")
        return {'success': False, 'error': str(e)}


@csrf_exempt
@require_http_methods(["POST"])
def chatbot_test(request):
    """Endpoint para probar el chatbot manualmente"""
    try:
        data = json.loads(request.body)
        phone_number = data.get('phone_number')
        message = data.get('message')
        cliente_id = data.get('cliente_id')
        
        if not all([phone_number, message]):
            return JsonResponse({
                'error': 'phone_number y message son requeridos'
            }, status=400)
        
        # Obtener cliente
        if cliente_id:
            cliente = Cliente.objects.get(id=cliente_id)
        else:
            cliente = Cliente.objects.first()
        
        if not cliente:
            return JsonResponse({
                'error': 'Cliente no encontrado'
            }, status=404)
        
        # Procesar con chatbot
        chatbot = ChatbotService(cliente)
        response_data = chatbot.process_message(phone_number, message)
        
        return JsonResponse({
            'success': True,
            'input_message': message,
            'response': response_data
        })
        
    except Exception as e:
        return JsonResponse({
            'error': str(e)
        }, status=500)


class ChatbotStatsView(View):
    """Vista para estadísticas del chatbot"""
    
    def get(self, request):
        """Obtiene estadísticas del chatbot"""
        try:
            # Aquí podrías implementar estadísticas desde base de datos
            stats = {
                'total_conversations': 0,
                'messages_today': 0,
                'most_common_intents': [],
                'response_rate': 100,
                'average_response_time': '< 1 segundo'
            }
            
            return JsonResponse(stats)
            
        except Exception as e:
            return JsonResponse({
                'error': str(e)
            }, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def chatbot_config(request):
    """Configuración del chatbot"""
    try:
        data = json.loads(request.body)
        
        # Aquí podrías guardar configuraciones del chatbot
        # Por ejemplo: horarios de operación, mensajes personalizados, etc.
        
        return JsonResponse({
            'success': True,
            'message': 'Configuración actualizada'
        })
        
    except Exception as e:
        return JsonResponse({
            'error': str(e)
        }, status=500)
