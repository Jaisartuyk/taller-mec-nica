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
        # Parsear datos del webhook
        data = json.loads(request.body)
        logger.info(f"Mensaje recibido: {data}")
        
        # Extraer información del mensaje
        message_data = extract_message_data(data)
        
        if not message_data:
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
                response_data['response']
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


def extract_message_data(webhook_data):
    """Extrae datos del mensaje del webhook"""
    try:
        # Estructura típica de webhook de WhatsApp Business API
        if 'messages' in webhook_data:
            message = webhook_data['messages'][0]
            return {
                'id': message.get('id'),
                'from': message.get('from'),
                'text': message.get('text', {}).get('body', ''),
                'type': message.get('type', 'text'),
                'timestamp': message.get('timestamp')
            }
        
        # Estructura de WASender API (si es diferente)
        elif 'message' in webhook_data:
            message = webhook_data['message']
            return {
                'id': message.get('id'),
                'from': message.get('from'),
                'text': message.get('body', ''),
                'type': message.get('type', 'text'),
                'timestamp': message.get('timestamp')
            }
            
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
        messaging_service = MultiTallerMessagingService(cliente=cliente)
        
        # Preparar datos del mensaje
        datos = {
            'mensaje_personalizado': response_data['message']
        }
        
        # Enviar mensaje
        resultado = messaging_service.enviar_mensaje(
            telefono=phone_number,
            tipo_mensaje='personalizado',
            datos=datos,
            canal='whatsapp'
        )
        
        return resultado.get('whatsapp', {})
        
    except Exception as e:
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
