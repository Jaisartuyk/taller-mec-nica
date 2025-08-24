"""
Servicio de Chatbot Inteligente para WhatsApp
Agente conversacional para taller mecánico
"""
import re
import json
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
from django.utils import timezone
from ..models import Cliente, Conductor, Vehiculo, ConfiguracionTaller


class ChatbotService:
    """Servicio de chatbot inteligente para WhatsApp"""
    
    def __init__(self, cliente: Cliente):
        self.cliente = cliente
        self.taller_config = getattr(cliente, 'configuracion', None)
        
        # Contexto de conversación (en producción usar Redis/Cache)
        self.conversation_context = {}
        
        # Patrones de respuesta
        self.patterns = self._load_response_patterns()
        
    def process_message(self, phone_number: str, message: str) -> Dict:
        """
        Procesa un mensaje entrante y genera una respuesta inteligente
        
        Args:
            phone_number: Número de teléfono del remitente
            message: Mensaje recibido
            
        Returns:
            Dict con la respuesta y metadatos
        """
        try:
            # Limpiar y normalizar mensaje
            clean_message = self._clean_message(message)
            
            # Obtener contexto de conversación
            context = self._get_conversation_context(phone_number)
            
            # Identificar intención del mensaje
            intent, entities = self._identify_intent(clean_message, context)
            
            # Generar respuesta basada en intención
            response = self._generate_response(intent, entities, context, phone_number)
            
            # Actualizar contexto
            self._update_conversation_context(phone_number, intent, entities, message)
            
            return {
                'success': True,
                'response': response,
                'intent': intent,
                'entities': entities,
                'requires_human': response.get('escalate_to_human', False)
            }
            
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error en ChatbotService.process_message: {str(e)}", exc_info=True)
            return {
                'success': False,
                'error': str(e),
                'response': self._get_error_response()
            }
    
    def _clean_message(self, message: str) -> str:
        """Limpia y normaliza el mensaje"""
        # Convertir a minúsculas
        clean = message.lower().strip()
        
        # Remover caracteres especiales innecesarios
        clean = re.sub(r'[^\w\sáéíóúñ¿?¡!.,]', '', clean)
        
        # Normalizar espacios
        clean = re.sub(r'\s+', ' ', clean)
        
        return clean
    
    def _identify_intent(self, message: str, context: Dict) -> Tuple[str, Dict]:
        """
        Identifica la intención del mensaje usando patrones
        
        Returns:
            Tuple[intent, entities]
        """
        try:
            # Convertir a minúsculas para comparación
            message_lower = message.lower()
            
            # Patrones de intenciones simplificados
            intent_patterns = {
                'saludo': [
                    r'\bhola\b',
                    r'\bbuenos días\b',
                    r'\bbuenas tardes\b',
                    r'\bbuenas noches\b',
                    r'\bsaludos\b',
                    r'\bhey\b',
                    r'\bqué tal\b'
                ],
                'consulta_servicio': [
                    r'\bservicios\b',
                    r'\bqué servicios\b',
                    r'\bque hacen\b',
                    r'\btrabajos\b',
                    r'\bcambio de aceite\b',
                    r'\bfrenos\b',
                    r'\bmotor\b',
                    r'\bmantenimiento\b',
                    r'\breparación\b'
                ],
                'consulta_precio': [
                    r'\bcuánto cuesta\b',
                    r'\bprecio\b',
                    r'\bcosto\b',
                    r'\bcotización\b',
                    r'\bpresupuesto\b',
                    r'\btarifa\b'
                ],
                'agendar_cita': [
                    r'\bagendar\b',
                    r'\bcita\b',
                    r'\bturno\b',
                    r'\breservar\b',
                    r'\bapartar\b',
                    r'\bhorario\b'
                ],
                'despedida': [
                    r'\bgracias\b',
                    r'\bperfecto\b',
                    r'\bok\b',
                    r'\bvale\b',
                    r'\badiós\b',
                    r'\bchao\b'
                ]
            }
            
            # Buscar patrones
            for intent, patterns in intent_patterns.items():
                for pattern in patterns:
                    if re.search(pattern, message_lower, re.IGNORECASE):
                        entities = self._extract_entities(message, intent)
                        return intent, entities
            
            # Si no encuentra patrón específico, es consulta general
            return 'consulta_general', {}
            
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error en _identify_intent: {str(e)}", exc_info=True)
            return 'consulta_general', {}
    
    def _extract_entities(self, message: str, intent: str) -> Dict:
        """Extrae entidades específicas del mensaje"""
        try:
            entities = {}
            
            # Extraer números de teléfono
            phone_pattern = r'\b(\d{10}|\d{4}-\d{4}|\d{3}-\d{3}-\d{4})\b'
            phones = re.findall(phone_pattern, message)
            if phones:
                entities['telefono'] = phones[0]
            
            # Extraer placas de vehículos
            placa_pattern = r'\b[A-Z]{3}-\d{3,4}\b'
            placas = re.findall(placa_pattern, message.upper())
            if placas:
                entities['placa'] = placas[0]
            
            # Extraer servicios específicos
            servicios = {
                'aceite': ['aceite', 'lubricante'],
                'frenos': ['frenos', 'pastillas', 'discos'],
                'motor': ['motor', 'bujías', 'filtros'],
                'transmision': ['transmisión', 'caja', 'embrague'],
                'suspension': ['suspensión', 'amortiguadores', 'muelles']
            }
            
            message_lower = message.lower()
            for servicio, keywords in servicios.items():
                for keyword in keywords:
                    if keyword in message_lower:
                        entities['servicio'] = servicio
                        break
            
            return entities
            
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error en _extract_entities: {str(e)}", exc_info=True)
            return {}
    
    def _generate_response(self, intent: str, entities: Dict, context: Dict, phone_number: str) -> Dict:
        """Genera respuesta basada en la intención"""
        
        responses = {
            'saludo': self._handle_greeting,
            'consulta_servicio': self._handle_service_inquiry,
            'consulta_precio': self._handle_price_inquiry,
            'agendar_cita': self._handle_appointment_request,
            'consulta_estado': self._handle_status_inquiry,
            'ubicacion_horario': self._handle_location_hours,
            'despedida': self._handle_farewell,
            'consulta_general': self._handle_general_inquiry
        }
        
        handler = responses.get(intent, self._handle_general_inquiry)
        return handler(entities, context, phone_number)
    
    def _handle_greeting(self, entities: Dict, context: Dict, phone_number: str) -> Dict:
        """Maneja saludos"""
        # Buscar conductor por teléfono
        conductor = self._find_conductor_by_phone(phone_number)
        
        if conductor:
            nombre = conductor.nombre.split()[0]  # Primer nombre
            message = f"¡Hola {nombre}! 👋\n\n"
        else:
            message = "¡Hola! 👋 Bienvenido a nuestro taller.\n\n"
        
        message += f"Soy el asistente virtual de **{self.cliente.nombre.upper()}**\n\n"
        message += "¿En qué puedo ayudarte hoy?\n\n"
        message += "Puedo ayudarte con:\n"
        message += "🔧 Información sobre servicios\n"
        message += "💰 Cotizaciones\n"
        message += "📅 Agendar citas\n"
        message += "📍 Ubicación y horarios\n"
        message += "🚗 Estado de tu vehículo"
        
        return {
            'message': message,
            'type': 'greeting'
        }
    
    def _handle_service_inquiry(self, entities: Dict, context: Dict, phone_number: str) -> Dict:
        """Maneja consultas sobre servicios"""
        servicio_especifico = entities.get('servicio')
        
        if servicio_especifico:
            return self._get_specific_service_info(servicio_especifico)
        
        message = f"🔧 **SERVICIOS DE {self.cliente.nombre.upper()}**\n\n"
        message += "Ofrecemos servicios completos de mecánica:\n\n"
        message += "🛢️ **Mantenimiento Preventivo**\n"
        message += "• Cambio de aceite y filtros\n"
        message += "• Revisión de 10,000 km\n"
        message += "• Afinación completa\n\n"
        message += "🔩 **Reparaciones**\n"
        message += "• Sistema de frenos\n"
        message += "• Motor y transmisión\n"
        message += "• Suspensión y dirección\n"
        message += "• Sistema eléctrico\n\n"
        message += "¿Te interesa algún servicio en particular?"
        
        return {
            'message': message,
            'type': 'service_info'
        }
    
    def _handle_price_inquiry(self, entities: Dict, context: Dict, phone_number: str) -> Dict:
        """Maneja consultas de precios"""
        servicio = entities.get('servicio')
        
        if servicio:
            return self._get_service_price(servicio)
        
        message = "💰 **PRECIOS REFERENCIALES**\n\n"
        message += "🛢️ Cambio de aceite: $25 - $45\n"
        message += "🔩 Pastillas de freno: $35 - $65\n"
        message += "⚙️ Afinación básica: $45 - $85\n"
        message += "🔧 Revisión completa: $30 - $50\n\n"
        message += "💡 *Los precios pueden variar según el vehículo*\n\n"
        message += "Para una cotización exacta, compárteme:\n"
        message += "• Marca y modelo del vehículo\n"
        message += "• Año\n"
        message += "• Servicio específico que necesitas"
        
        return {
            'message': message,
            'type': 'price_info'
        }
    
    def _handle_appointment_request(self, entities: Dict, context: Dict, phone_number: str) -> Dict:
        """Maneja solicitudes de citas"""
        message = "📅 **AGENDAR CITA**\n\n"
        message += "¡Perfecto! Te ayudo a agendar tu cita.\n\n"
        message += "**Horarios disponibles:**\n"
        message += "🕐 Lunes a Viernes: 8:00 AM - 6:00 PM\n"
        message += "🕐 Sábados: 8:00 AM - 4:00 PM\n\n"
        message += "Para agendar necesito:\n"
        message += "• Día y hora preferida\n"
        message += "• Datos del vehículo (marca, modelo, año)\n"
        message += "• Servicio que necesitas\n\n"
        message += "¿Qué día te conviene más?"
        
        return {
            'message': message,
            'type': 'appointment_request',
            'next_step': 'collect_appointment_details'
        }
    
    def _handle_status_inquiry(self, entities: Dict, context: Dict, phone_number: str) -> Dict:
        """Maneja consultas de estado de vehículo"""
        conductor = self._find_conductor_by_phone(phone_number)
        placa = entities.get('placa')
        
        if conductor and conductor.vehiculos.exists():
            vehiculo = conductor.vehiculos.first()
            message = f"🚗 **ESTADO DE TU VEHÍCULO**\n\n"
            message += f"Vehículo: {vehiculo.marca} {vehiculo.modelo}\n"
            message += f"Placa: {vehiculo.placa}\n\n"
            message += "📋 Estado actual: En revisión\n"
            message += "⏰ Tiempo estimado: 2-3 horas\n\n"
            message += "Te notificaremos cuando esté listo. 👍"
        else:
            message = "🔍 **CONSULTAR ESTADO**\n\n"
            message += "Para consultar el estado de tu vehículo, "
            message += "compárteme la placa o número de orden de trabajo.\n\n"
            message += "Ejemplo: ABC-1234"
        
        return {
            'message': message,
            'type': 'status_inquiry'
        }
    
    def _handle_location_hours(self, entities: Dict, context: Dict, phone_number: str) -> Dict:
        """Maneja consultas de ubicación y horarios"""
        message = f"📍 **{self.cliente.nombre.upper()}**\n\n"
        
        if self.cliente.direccion:
            message += f"📍 **Dirección:**\n{self.cliente.direccion}\n\n"
        
        message += "🕐 **Horarios de Atención:**\n"
        message += "Lunes a Viernes: 8:00 AM - 6:00 PM\n"
        message += "Sábados: 8:00 AM - 4:00 PM\n"
        message += "Domingos: Cerrado\n\n"
        
        if self.cliente.telefono:
            message += f"📞 **Teléfono:** {self.cliente.telefono}\n\n"
        
        message += "¡Te esperamos! 🚗"
        
        return {
            'message': message,
            'type': 'location_hours'
        }
    
    def _handle_farewell(self, entities: Dict, context: Dict, phone_number: str) -> Dict:
        """Maneja despedidas"""
        message = "¡De nada! 😊\n\n"
        message += "Fue un placer ayudarte. Si necesitas algo más, "
        message += "no dudes en escribirme.\n\n"
        message += f"**{self.cliente.nombre}** - Tu taller de confianza 🔧"
        
        return {
            'message': message,
            'type': 'farewell'
        }
    
    def _handle_general_inquiry(self, entities: Dict, context: Dict, phone_number: str) -> Dict:
        """Maneja consultas generales"""
        message = "🤔 Entiendo que tienes una consulta.\n\n"
        message += "Puedo ayudarte con:\n\n"
        message += "🔧 **Servicios** - Qué trabajos realizamos\n"
        message += "💰 **Precios** - Cotizaciones y tarifas\n"
        message += "📅 **Citas** - Agendar tu visita\n"
        message += "📍 **Ubicación** - Dónde estamos\n"
        message += "🚗 **Estado** - Consultar tu vehículo\n\n"
        message += "¿Con cuál te puedo ayudar?"
        
        return {
            'message': message,
            'type': 'general_inquiry'
        }
    
    def _find_conductor_by_phone(self, phone_number: str) -> Optional[Conductor]:
        """Busca conductor por número de teléfono"""
        # Limpiar número de teléfono
        clean_phone = re.sub(r'[^\d]', '', phone_number)
        
        try:
            return Conductor.objects.filter(
                cliente=self.cliente,
                telefono__icontains=clean_phone[-8:]  # Últimos 8 dígitos
            ).first()
        except:
            return None
    
    def _get_conversation_context(self, phone_number: str) -> Dict:
        """Obtiene contexto de conversación"""
        return self.conversation_context.get(phone_number, {})
    
    def _update_conversation_context(self, phone_number: str, intent: str, entities: Dict, message: str):
        """Actualiza contexto de conversación"""
        if phone_number not in self.conversation_context:
            self.conversation_context[phone_number] = {
                'messages': [],
                'last_intent': None,
                'entities': {},
                'created_at': timezone.now()
            }
        
        context = self.conversation_context[phone_number]
        context['messages'].append({
            'message': message,
            'intent': intent,
            'timestamp': timezone.now()
        })
        context['last_intent'] = intent
        context['entities'].update(entities)
        
        # Mantener solo últimos 10 mensajes
        context['messages'] = context['messages'][-10:]
    
    def _get_error_response(self) -> Dict:
        """Respuesta de error genérica"""
        return {
            'message': "😅 Disculpa, tuve un pequeño problema.\n\n"
                      "Por favor, intenta de nuevo o contacta directamente "
                      f"al {self.cliente.telefono if self.cliente.telefono else 'taller'}.",
            'type': 'error'
        }
    
    def _load_response_patterns(self) -> Dict:
        """Carga patrones de respuesta (expandible)"""
        return {
            'greetings': ['hola', 'buenos días', 'buenas tardes', 'hey'],
            'services': ['servicio', 'trabajo', 'reparación', 'mantenimiento'],
            'prices': ['precio', 'costo', 'cuánto', 'cotización'],
            'appointments': ['cita', 'turno', 'agendar', 'reservar']
        }
