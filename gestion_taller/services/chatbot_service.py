"""
Servicio de Chatbot Inteligente para WhatsApp
Agente conversacional para taller mecánico
"""
import re
import json
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
from django.utils import timezone
from django.core.cache import cache
from ..models import Cliente, Conductor, Vehiculo, ConfiguracionTaller, Cita, ServicioCatalogo


class ChatbotService:
    """Servicio de chatbot inteligente para WhatsApp"""
    
    def __init__(self, cliente: Cliente):
        self.cliente = cliente
        self.taller_config = getattr(cliente, 'configuracion', None)
        
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
            
            # Actualizar contexto con información de la respuesta
            self._update_conversation_context(phone_number, intent, entities, message)
            self._save_response_context(phone_number, response)
            
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
        Identifica la intención del mensaje usando patrones y contexto conversacional
        
        Returns:
            Tuple[intent, entities]
        """
        try:
            # Convertir a minúsculas para comparación
            message_lower = message.lower()
            
            # Verificar contexto conversacional primero
            current_step = context.get('next_step', '')
            
            # Si estamos esperando confirmación de cita, priorizar detección de confirmación
            if current_step in ['confirm_appointment', 'awaiting_confirmation']:
                confirmation_patterns = [
                    r'\b(sí|si|confirmo|confirmar|está bien|ok|vale|perfecto|agendar|proceder|acepto|de acuerdo)\b'
                ]
                
                for pattern in confirmation_patterns:
                    if re.search(pattern, message_lower, re.IGNORECASE):
                        return 'appointment_confirmation', {}
                
                # Detectar negación
                negation_patterns = [
                    r'\b(no|nope|mejor no|cancelar|no gracias)\b'
                ]
                
                for pattern in negation_patterns:
                    if re.search(pattern, message_lower, re.IGNORECASE):
                        return 'appointment_cancellation', {}
            
            # Si estamos en proceso de agendamiento, detectar respuestas contextuales
            if current_step in ['select_datetime', 'collect_appointment_details', 'collect_service_details']:
                # Priorizar fecha/hora si se detecta
                if self._contains_datetime_info(message_lower):
                    return 'appointment_datetime', self._extract_datetime_entities(message)
                # Detectar servicios mencionados
                if self._contains_service_info(message_lower):
                    return 'appointment_service', self._extract_service_entities(message)
        
            # Si estamos esperando confirmación
            elif current_step in ['awaiting_confirmation', 'confirm_appointment']:
                # Detectar confirmaciones
                confirmation_patterns = [
                    r'\b(sí|si|confirmo|confirmar|está bien|ok|vale|perfecto)\b',
                    r'\b(acepto|de acuerdo|correcto)\b'
                ]
                for pattern in confirmation_patterns:
                    if re.search(pattern, message_lower, re.IGNORECASE):
                        return 'appointment_confirmation', {}
            
            elif current_step == 'collect_new_customer_data':
                # Detectar datos de registro de nuevo cliente
                if self._contains_customer_data(message_lower):
                    return 'customer_registration', self._extract_customer_entities(message)
            
            elif current_step == 'select_vehicle':
                # Detectar selección de vehículo por número
                vehicle_selection = self._extract_vehicle_selection(message)
                if vehicle_selection:
                    return 'vehicle_selection', vehicle_selection
            
            # PRIORIDAD ALTA: Detectar solicitudes de cita con información de fecha/hora directamente
            agendar_patterns = [
                r'\b(agendar|reservar|programar|solicitar)\b.*\b(cita|turno|hora)\b',
                r'\b(quiero|necesito|me gustaría)\b.*\b(cita|turno|hora)\b',
                r'\b(quiero|necesito)\b.*\b(agendar|reservar|programar)\b',
                r'\b(agendar|reservar|programar)\b.*\b(para|el|la)\b'
            ]
            
            for pattern in agendar_patterns:
                if re.search(pattern, message_lower, re.IGNORECASE):
                    # Si también contiene información de fecha/hora, es appointment_datetime
                    if self._contains_datetime_info(message_lower):
                        # Extraer tanto entidades de fecha/hora como de servicio
                        datetime_entities = self._extract_datetime_entities(message)
                        service_entities = self._extract_service_entities(message)
                        # Combinar entidades
                        combined_entities = {**datetime_entities, **service_entities}
                        return 'appointment_datetime', combined_entities
                    # Si solo es solicitud de cita, es agendar_cita
                    else:
                        return 'agendar_cita', {}
            
            # PRIORIDAD ALTA: Detectar mensajes que contienen fecha/hora en contexto de agendamiento
            if self._contains_datetime_info(message_lower):
                # Verificar si también menciona servicios o agendamiento
                agendar_keywords = ['agendar', 'reservar', 'programar', 'cita', 'turno', 'quiero', 'necesito']
                servicio_keywords = ['aceite', 'frenos', 'motor', 'mantenimiento', 'servicio', 'cambio', 'revisión']
                
                has_agendar = any(keyword in message_lower for keyword in agendar_keywords)
                has_servicio = any(keyword in message_lower for keyword in servicio_keywords)
                
                if has_agendar or has_servicio:
                    # Es claramente una solicitud de cita con fecha/hora
                    datetime_entities = self._extract_datetime_entities(message)
                    service_entities = self._extract_service_entities(message)
                    combined_entities = {**datetime_entities, **service_entities}
                    return 'appointment_datetime', combined_entities
            
            # Patrones de intenciones principales
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
                    r'\bcuanto cuesta\b',
                    r'\bcuánto cuesta\b',
                    r'\bprecio\b',
                    r'\bprecios\b',
                    r'\bcosto\b',
                    r'\bcostos\b',
                    r'\bcotización\b',
                    r'\bcotizacion\b',
                    r'\bpresupuesto\b',
                    r'\btarifa\b',
                    r'\bvalor\b',
                    r'\bcuanto cobran\b',
                    r'\bcuánto cobran\b'
                ],
                'agendar_cita': [
                    r'\bagendar\b',
                    r'\bcita\b',
                    r'\bturno\b',
                    r'\breservar\b',
                    r'\bapartar\b',
                    r'\bquiero.*cita\b',
                    r'\bnecesito.*cita\b'
                ],
                'ubicacion_horario': [
                    r'\bdonde estan\b',
                    r'\bdónde están\b',
                    r'\bdonde quedan\b',
                    r'\bubicación\b',
                    r'\bubicacion\b',
                    r'\bdirección\b',
                    r'\bdireccion\b',
                    r'\bhorario\b',
                    r'\bhorarios\b',
                    r'\bque hora abren\b',
                    r'\bqué hora abren\b'
                ],
                'estado_vehiculo': [
                    r'\bcómo está\b',
                    r'\bcomo esta\b',
                    r'\bestado.*vehiculo\b',
                    r'\bestado.*carro\b',
                    r'\blisto\b',
                    r'\bterminado\b'
                ],
                'emergencia': [
                    r'\bemergencia\b',
                    r'\burgente\b',
                    r'\bayuda\b',
                    r'\bse dañó\b',
                    r'\bno arranca\b'
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
            'ubicacion_horario': self._handle_location_inquiry,
            'estado_vehiculo': self._handle_vehicle_status,
            'emergencia': self._handle_emergency,
            'despedida': self._handle_farewell,
            'consulta_general': self._handle_general_inquiry,
            # Nuevos intents contextuales
            'appointment_datetime': self._handle_appointment_datetime,
            'appointment_service': self._handle_appointment_service,
            'customer_registration': self._handle_customer_registration,
            'vehicle_selection': self._handle_vehicle_selection,
            'appointment_confirmation': self._handle_appointment_confirmation,
            'appointment_cancellation': self._handle_appointment_cancellation
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
    
    def _get_specific_service_info(self, servicio: str) -> Dict:
        """Obtiene información específica de un servicio"""
        servicios_info = {
            'aceite': {
                'titulo': '🛢️ CAMBIO DE ACEITE',
                'descripcion': 'Cambio completo de aceite y filtro',
                'incluye': ['Aceite motor', 'Filtro de aceite', 'Revisión de niveles'],
                'precio': '$25 - $45',
                'tiempo': '30-45 minutos'
            },
            'frenos': {
                'titulo': '🔩 SISTEMA DE FRENOS',
                'descripcion': 'Revisión y reparación completa de frenos',
                'incluye': ['Pastillas', 'Discos', 'Líquido de frenos', 'Revisión completa'],
                'precio': '$35 - $85',
                'tiempo': '1-2 horas'
            },
            'motor': {
                'titulo': '⚙️ REPARACIÓN DE MOTOR',
                'descripcion': 'Diagnóstico y reparación de motor',
                'incluye': ['Diagnóstico', 'Bujías', 'Filtros', 'Afinación'],
                'precio': '$45 - $150',
                'tiempo': '2-4 horas'
            },
            'transmision': {
                'titulo': '🔧 TRANSMISIÓN',
                'descripcion': 'Servicio de caja y embrague',
                'incluye': ['Revisión completa', 'Aceite de caja', 'Ajustes'],
                'precio': '$60 - $200',
                'tiempo': '2-6 horas'
            },
            'suspension': {
                'titulo': '🚗 SUSPENSIÓN',
                'descripcion': 'Reparación de suspensión y amortiguadores',
                'incluye': ['Amortiguadores', 'Muelles', 'Revisión completa'],
                'precio': '$80 - $250',
                'tiempo': '2-4 horas'
            }
        }
        
        info = servicios_info.get(servicio)
        if not info:
            return self._handle_general_inquiry({}, {}, '')
        
        message = f"{info['titulo']}\n\n"
        message += f"📋 **Descripción:** {info['descripcion']}\n\n"
        message += "✅ **Incluye:**\n"
        for item in info['incluye']:
            message += f"• {item}\n"
        message += f"\n💰 **Precio:** {info['precio']}\n"
        message += f"⏱️ **Tiempo:** {info['tiempo']}\n\n"
        message += "¿Te gustaría agendar una cita para este servicio?"
        
        return {
            'message': message,
            'type': 'specific_service_info'
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
    
    def _get_service_price(self, servicio: str) -> Dict:
        """Obtiene precio específico de un servicio"""
        precios = {
            'aceite': {'precio': '$25 - $45', 'descripcion': 'Cambio completo de aceite y filtro'},
            'frenos': {'precio': '$35 - $85', 'descripcion': 'Pastillas, discos y revisión completa'},
            'motor': {'precio': '$45 - $150', 'descripcion': 'Diagnóstico, bujías y afinación'},
            'transmision': {'precio': '$60 - $200', 'descripcion': 'Servicio de caja y embrague'},
            'suspension': {'precio': '$80 - $250', 'descripcion': 'Amortiguadores y suspensión completa'}
        }
        
        info = precios.get(servicio)
        if not info:
            return self._handle_general_inquiry({}, {}, '')
        
        message = f"💰 **PRECIO - {servicio.upper()}**\n\n"
        message += f"📋 {info['descripcion']}\n\n"
        message += f"💵 **Precio:** {info['precio']}\n\n"
        message += "💡 *Los precios pueden variar según el vehículo*\n\n"
        message += "¿Te gustaría una cotización exacta? Compárteme:\n"
        message += "• Marca y modelo\n"
        message += "• Año del vehículo"
        
        return {
            'message': message,
            'type': 'specific_price'
        }
    
    def _handle_location_inquiry(self, entities: Dict, context: Dict, phone_number: str) -> Dict:
        """Maneja consultas de ubicación y horarios"""
        message = f"📍 **UBICACIÓN DE {self.cliente.nombre.upper()}**\n\n"
        
        if self.cliente.direccion:
            message += f"🏢 **Dirección:** {self.cliente.direccion}\n"
        
        if self.cliente.telefono:
            message += f"📞 **Teléfono:** {self.cliente.telefono}\n"
        
        message += "\n🕒 **HORARIOS DE ATENCIÓN:**\n"
        message += "• Lunes a Viernes: 8:00 AM - 6:00 PM\n"
        message += "• Sábados: 8:00 AM - 4:00 PM\n"
        message += "• Domingos: Cerrado\n\n"
        message += "📱 También puedes llamarnos para confirmar disponibilidad"
        
        return {
            'message': message,
            'type': 'location_info'
        }
    
    def _handle_appointment_request(self, entities: Dict, context: Dict, phone_number: str) -> Dict:
        """Maneja solicitudes de citas de forma inteligente"""
        try:
            # 1. Identificar conductor por teléfono
            conductor = self._find_conductor_by_phone(phone_number)
            
            if not conductor:
                return self._handle_new_customer_registration(phone_number)
            
            # 2. Obtener vehículos del conductor
            vehiculos = self._get_vehiculos_conductor(conductor)
            
            if not vehiculos:
                return self._handle_no_vehicles(conductor)
            
            # 3. Gestión inteligente de vehículos
            if len(vehiculos) == 1:
                vehiculo = vehiculos[0]
                return self._handle_single_vehicle_appointment(conductor, vehiculo, entities, context)
            else:
                return self._handle_multiple_vehicles_selection(conductor, vehiculos)
                
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error en _handle_appointment_request: {str(e)}", exc_info=True)
            return self._get_error_response("Disculpa, hubo un problema al procesar tu solicitud de cita.")
    
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
        """Obtiene contexto de conversación desde cache"""
        cache_key = f"chatbot_context_{self.cliente.id}_{phone_number}"
        return cache.get(cache_key, {})
    
    def _update_conversation_context(self, phone_number: str, intent: str, entities: Dict, message: str):
        """Actualiza contexto de conversación en cache"""
        cache_key = f"chatbot_context_{self.cliente.id}_{phone_number}"
        context = cache.get(cache_key, {
            'messages': [],
            'last_intent': None,
            'entities': {},
            'created_at': timezone.now()
        })
        
        context['messages'].append({
            'message': message,
            'intent': intent,
            'timestamp': timezone.now()
        })
        context['last_intent'] = intent
        context['entities'].update(entities)
        
        # Mantener solo últimos 10 mensajes
        context['messages'] = context['messages'][-10:]
        
        # Guardar en cache por 24 horas
        cache.set(cache_key, context, 86400)
    
    def _save_response_context(self, phone_number: str, response: Dict):
        """Guarda información de la respuesta en el contexto usando cache"""
        cache_key = f"chatbot_context_{self.cliente.id}_{phone_number}"
        context = cache.get(cache_key, {})
        
        # Guardar información importante de la respuesta
        if 'next_step' in response:
            context['next_step'] = response['next_step']
        
        if 'conductor_id' in response:
            context['conductor_id'] = response['conductor_id']
        
        if 'vehiculo_id' in response:
            context['vehiculo_id'] = response['vehiculo_id']
        
        if 'servicio_sugerido' in response:
            context['servicio_sugerido'] = response['servicio_sugerido']
        
        if 'fecha_hora_info' in response:
            context['fecha_hora_info'] = response['fecha_hora_info']
        
        if 'servicio' in response:
            context['servicio'] = response['servicio']
        
        if 'type' in response:
            context['last_response_type'] = response['type']
        
        # Guardar en cache por 24 horas
        cache.set(cache_key, context, 86400)
    
    def _get_error_response(self, custom_message: str = None) -> Dict:
        """Respuesta de error genérica"""
        message = custom_message or "Lo siento, no pude procesar tu mensaje en este momento. ¿Podrías intentar de nuevo o contactar directamente con el taller?"
        
        return {
            'message': message,
            'type': 'error',
            'escalate_to_human': True
        }
    
    # ============= MÉTODOS PARA AGENTE INTELIGENTE DE CITAS =============
    
    def _get_conductor_by_phone(self, phone_number: str):
        """Busca conductor por número de teléfono en el taller actual"""
        try:
            from ..models import Conductor
            # Normalizar número de teléfono
            phone_clean = self._normalize_phone_number(phone_number)
            
            conductor = Conductor.objects.filter(
                cliente=self.cliente,
                telefono__icontains=phone_clean[-8:]  # Últimos 8 dígitos
            ).first()
            
            return conductor
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error buscando conductor: {str(e)}")
            return None
    
    def _normalize_phone_number(self, phone_number: str) -> str:
        """Normaliza número de teléfono eliminando caracteres especiales"""
        import re
        return re.sub(r'[^0-9]', '', phone_number)
    
    def _get_vehiculos_conductor(self, conductor):
        """Obtiene vehículos activos del conductor"""
        try:
            return conductor.vehiculos.filter(activo=True).order_by('-fecha_creacion')
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error obteniendo vehículos: {str(e)}")
            return []
    
    def _get_vehiculo_for_conductor(self, conductor):
        """Obtiene el vehículo principal del conductor (el más reciente)"""
        try:
            vehiculos = self._get_vehiculos_conductor(conductor)
            return vehiculos.first() if vehiculos else None
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error obteniendo vehículo principal: {str(e)}")
            return None
    
    def _get_available_slots(self) -> str:
        """Genera lista de horarios disponibles"""
        try:
            from datetime import datetime, timedelta
            
            # Obtener fecha actual
            today = datetime.now()
            slots = []
            
            # Generar próximos 5 días laborables
            for i in range(1, 8):  # Próximos 7 días
                date = today + timedelta(days=i)
                
                # Saltar domingos (weekday 6)
                if date.weekday() == 6:
                    continue
                    
                day_name = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado'][date.weekday()]
                date_str = date.strftime('%d/%m')
                
                if date.weekday() < 5:  # Lunes a Viernes
                    slots.append(f"   • {day_name} {date_str}: 8:00 AM - 6:00 PM")
                else:  # Sábado
                    slots.append(f"   • {day_name} {date_str}: 8:00 AM - 4:00 PM")
                    
                if len(slots) >= 5:
                    break
            
            return "\n".join(slots)
            
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error generando horarios: {str(e)}")
            return "   • Lunes a Viernes: 8:00 AM - 6:00 PM\n   • Sábados: 8:00 AM - 4:00 PM"
    
    def _handle_new_customer_registration(self, phone_number: str) -> Dict:
        """Maneja el registro de un nuevo cliente"""
        taller_name = self.cliente.nombre
        
        message = f"¡Hola! Bienvenido a **{taller_name}**.\n\n"
        message += "Veo que es la primera vez que nos contactas por WhatsApp. "
        message += "Para poder ayudarte mejor y agendar tu cita, necesito algunos datos:\n\n"
        message += " **Tu nombre completo**\n"
        message += " **Datos de tu vehículo:**\n"
        message += "   • Marca (ej: Toyota)\n"
        message += "   • Modelo (ej: Corolla)\n"
        message += "   • Año (ej: 2018)\n"
        message += "   • Placa\n\n"
        message += "Puedes enviarme toda la información en un solo mensaje.\n\n"
        message += "**Ejemplo:** Juan Pérez, Toyota Corolla 2018, ABC-1234"
        
        return {
            'message': message,
            'type': 'new_customer_registration',
            'next_step': 'collect_customer_data'
        }
    
    def _handle_new_customer_flow(self, entities: Dict, context: Dict, phone_number: str) -> Dict:
        """Maneja el flujo de registro de nuevo cliente cuando no se encuentra en la base de datos"""
        return self._handle_new_customer_registration(phone_number)
    
    def _handle_no_vehicles(self, conductor) -> Dict:
        """Maneja el caso cuando un conductor no tiene vehículos registrados"""
        message = f"Hola **{conductor.nombre}**!\n\n"
        message += "Veo que aún no tienes vehículos registrados en nuestro sistema. "
        message += "Para agendar tu cita, necesito los datos de tu vehículo:\n\n"
        message += " **Datos del vehículo:**\n"
        message += "   • Marca (ej: Toyota)\n"
        message += "   • Modelo (ej: Corolla)\n"
        message += "   • Año (ej: 2018)\n"
        message += "   • Placa\n\n"
        message += "Envíame los datos en un solo mensaje.\n\n"
        message += "**Ejemplo:** Toyota Corolla 2018, ABC-1234"
        
        return {
            'message': message,
            'type': 'vehicle_registration',
            'next_step': 'collect_vehicle_data',
            'conductor_id': conductor.id
        }
    
    def _handle_multiple_vehicles_selection(self, conductor, vehiculos) -> Dict:
        """Maneja la selección cuando el conductor tiene múltiples vehículos"""
        message = f"Hola **{conductor.nombre}**!\n\n"
        message += "Veo que tienes varios vehículos registrados. ¿Para cuál quieres agendar la cita?\n\n"
        
        for i, vehiculo in enumerate(vehiculos, 1):
            message += f"**{i}.** {vehiculo.marca} {vehiculo.modelo} {vehiculo.anio} - {vehiculo.placa}\n"
            
            # Agregar info del último servicio si existe
            if vehiculo.fecha_ultimo_servicio:
                dias_desde_servicio = (timezone.now().date() - vehiculo.fecha_ultimo_servicio).days
                message += f"   Último servicio: hace {dias_desde_servicio} días\n"
            
            message += f"   Kilometraje: {vehiculo.kilometraje:,} km\n\n"
        
        message += "Responde con el **número** del vehículo (ej: 1, 2, 3...)"
        
        return {
            'message': message,
            'type': 'vehicle_selection',
            'next_step': 'select_vehicle',
            'conductor_id': conductor.id,
            'vehiculos_ids': [v.id for v in vehiculos]
        }
    
    def _handle_single_vehicle_appointment(self, conductor, vehiculo, entities: Dict, context: Dict) -> Dict:
        """Maneja cita cuando el conductor tiene un solo vehículo"""
        message = f"Hola **{conductor.nombre}**!\n\n"
        message += f"Perfecto, veo que quieres agendar una cita para tu **{vehiculo.marca} {vehiculo.modelo} {vehiculo.anio}** (Placa: {vehiculo.placa}).\n\n"
        
        # Mostrar información del vehículo
        message += " **Estado del vehículo:**\n"
        message += f"   • Kilometraje actual: {vehiculo.kilometraje:,} km\n"
        
        if vehiculo.fecha_ultimo_servicio:
            dias_desde_servicio = (timezone.now().date() - vehiculo.fecha_ultimo_servicio).days
            message += f"   • Último servicio: hace {dias_desde_servicio} días\n\n"
            
            # Sugerencias inteligentes basadas en historial
            sugerencias = self._get_service_suggestions(vehiculo)
            if sugerencias:
                message += " **Servicios recomendados:**\n"
                message += sugerencias + "\n"
        else:
            message += "   • Sin historial de servicios\n\n"
        
        # Detectar servicio mencionado en el mensaje original
        servicio_detectado = self._detect_service_from_entities(entities)
        if servicio_detectado:
            message += f" **Entiendo que necesitas:** **{servicio_detectado}**\n\n"
        
        # Mostrar horarios disponibles
        horarios_disponibles = self._get_available_slots()
        message += " **Horarios disponibles:**\n"
        message += horarios_disponibles + "\n"
        message += "¿Qué día y hora te conviene más?"
        
        return {
            'message': message,
            'type': 'appointment_scheduling',
            'next_step': 'select_datetime',
            'conductor_id': conductor.id,
            'vehiculo_id': vehiculo.id,
            'servicio_sugerido': servicio_detectado
        }
    
    def _get_service_suggestions(self, vehiculo) -> str:
        """Genera sugerencias de servicio basadas en el historial del vehículo"""
        try:
            from ..models import OrdenServicio
            from django.utils import timezone
            from datetime import timedelta
            
            sugerencias = []
            
            # Obtener últimas órdenes de servicio
            ordenes_recientes = OrdenServicio.objects.filter(
                vehiculo=vehiculo,
                estado='completada'
            ).order_by('-fecha_creacion')[:3]
            
            # Sugerencias basadas en kilometraje
            km_actual = vehiculo.kilometraje
            if km_actual > 0:
                # Cada 5000 km - cambio de aceite
                km_desde_aceite = km_actual % 5000
                if km_desde_aceite > 4000:
                    sugerencias.append(" **Cambio de aceite (próximo por kilometraje)**")
                
                # Cada 10000 km - revisión general
                if km_actual % 10000 > 8000:
                    sugerencias.append(" **Revisión general recomendada**")
            
            # Sugerencias basadas en tiempo
            if vehiculo.fecha_ultimo_servicio:
                dias_desde_servicio = (timezone.now().date() - vehiculo.fecha_ultimo_servicio).days
                if dias_desde_servicio > 90:  # 3 meses
                    sugerencias.append(" **Mantenimiento preventivo (por tiempo)**")
            
            return "\n".join([f"   • {s}" for s in sugerencias[:3]]) if sugerencias else ""
            
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error generando sugerencias: {str(e)}")
            return ""
    
    def _detect_service_from_entities(self, entities: Dict) -> str:
        """Detecta el servicio mencionado en las entidades extraídas"""
        # Buscar en múltiples claves posibles
        servicio_keys = ['servicio', 'service_name', 'service_type']
        servicio = ''
        
        for key in servicio_keys:
            if entities.get(key):
                servicio = entities.get(key)
                break
        
        if servicio:
            # Mapear servicios comunes
            servicios_map = {
                'aceite': 'Cambio de aceite',
                'cambio_aceite': 'Cambio de aceite',
                'frenos': 'Revisión de frenos',
                'pastillas': 'Cambio de pastillas de freno',
                'motor': 'Revisión de motor',
                'transmision': 'Revisión de transmisión',
                'suspension': 'Revisión de suspensión',
                'llantas': 'Revisión de llantas',
                'bateria': 'Revisión de batería',
                'mantenimiento': 'Mantenimiento general'
            }
            
            servicio_lower = servicio.lower()
            for key, value in servicios_map.items():
                if key in servicio_lower:
                    return value
        
        return servicio
    
    def _detect_service_from_conversation_context(self, phone_number: str) -> str:
        """Detecta servicios mencionados en el contexto conversacional"""
        try:
            # Obtener contexto desde cache
            cache_key = f"chatbot_context_{self.cliente.id}_{phone_number}"
            context = cache.get(cache_key, {})
            messages = context.get('messages', [])
            
            if not messages:
                return ''
            
            # Analizar el último mensaje para detectar servicios
            last_message = messages[-1].get('message', '').lower()
            
            # Patrones de servicios con sus nombres formales
            service_patterns = {
                r'\b(aceite|cambio.*aceite)\b': 'Cambio de aceite',
                r'\b(frenos|pastillas.*freno)\b': 'Revisión de frenos', 
                r'\b(motor|reparación.*motor|revisión.*motor)\b': 'Revisión de motor',
                r'\b(transmisión|caja.*cambios)\b': 'Revisión de transmisión',
                r'\b(suspensión|amortiguadores)\b': 'Revisión de suspensión',
                r'\b(llantas|neumáticos|neumaticos)\b': 'Revisión de llantas',
                r'\b(batería|bateria)\b': 'Revisión de batería',
                r'\b(mantenimiento.*general|servicio.*general)\b': 'Mantenimiento general',
                r'\b(diagnóstico|diagnostico)\b': 'Diagnóstico general'
            }
            
            for pattern, service_name in service_patterns.items():
                if re.search(pattern, last_message, re.IGNORECASE):
                    return service_name
            
            return ''
            
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error detectando servicio del contexto: {str(e)}")
            return ''
    
    def _get_available_slots(self) -> str:
        """Obtiene horarios disponibles dinámicamente"""
        try:
            from datetime import datetime, timedelta
            
            # Obtener configuración del taller
            if self.taller_config:
                horarios = self.taller_config.horarios
            else:
                horarios = "Lun-Vie 8AM-6PM, Sáb 8AM-2PM"
            
            # Generar próximos días disponibles
            hoy = datetime.now().date()
            slots = []
            
            for i in range(1, 8):  # Próximos 7 días
                fecha = hoy + timedelta(days=i)
                dia_semana = fecha.strftime('%A')
                
                # Saltar domingos
                if dia_semana == 'Sunday':
                    continue
                
                dia_es = self._translate_day(dia_semana)
                fecha_str = fecha.strftime('%d/%m')
                
                if dia_semana == 'Saturday':
                    slots.append(f"   • {dia_es} {fecha_str}: 8:00 AM - 2:00 PM")
                else:
                    slots.append(f"   • {dia_es} {fecha_str}: 8:00 AM - 6:00 PM")
                
                if len(slots) >= 5:  # Mostrar máximo 5 días
                    break
            
            return "\n".join(slots)
            
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error obteniendo horarios: {str(e)}")
            return "   • Lunes a Viernes: 8:00 AM - 6:00 PM\n   • Sábados: 8:00 AM - 2:00 PM"
    
    def _translate_day(self, day_english: str) -> str:
        """Traduce días de la semana al español"""
        days_map = {
            'Monday': 'Lunes',
            'Tuesday': 'Martes', 
            'Wednesday': 'Miércoles',
            'Thursday': 'Jueves',
            'Friday': 'Viernes',
            'Saturday': 'Sábado',
            'Sunday': 'Domingo'
        }
        return days_map.get(day_english, day_english)
    
    def _load_response_patterns(self) -> Dict:
        """Carga patrones de respuesta (expandible)"""
        return {
            'greetings': ['hola', 'buenos días', 'buenas tardes', 'hey'],
            'services': ['servicio', 'trabajo', 'reparación', 'mantenimiento'],
            'prices': ['precio', 'costo', 'cuánto', 'cotización'],
            'appointments': ['cita', 'turno', 'agendar', 'reservar']
        }
    
    # ===============================
    # MÉTODOS PARA CONTEXTO CONVERSACIONAL
    # ===============================
    
    def _contains_datetime_info(self, message: str) -> bool:
        """Detecta si el mensaje contiene información de fecha/hora"""
        datetime_patterns = [
            # Días de la semana
            r'\b(lunes|martes|miércoles|miercoles|jueves|viernes|sábado|sabado|domingo)\b',
            # Referencias temporales
            r'\b(mañana|tarde|noche|hoy|pasado mañana)\b',
            # Horas en formato HH:MM
            r'\b([0-9]{1,2}:[0-9]{2})\b',
            # Horas en formato 12h con AM/PM
            r'\b([0-9]{1,2}\s*(am|pm))\b',
            r'\b([0-9]{1,2}:[0-9]{2}\s*(am|pm))\b',
            # Números de día
            r'\b([0-9]{1,2})\s*(de\s*)?(enero|febrero|marzo|abril|mayo|junio|julio|agosto|septiembre|octubre|noviembre|diciembre)\b',
            # Patrones como "lunes 25", "martes 10"
            r'\b(lunes|martes|miércoles|miercoles|jueves|viernes|sábado|sabado|domingo)\s+([0-9]{1,2})\b',
            # Referencias como "a las 10", "las 2 pm"
            r'\b(a\s+las|las)\s+([0-9]{1,2})(:[0-9]{2})?\s*(am|pm)?\b'
        ]
        
        for pattern in datetime_patterns:
            if re.search(pattern, message, re.IGNORECASE):
                return True
        return False
    
    def _contains_service_info(self, message: str) -> bool:
        """Detecta si el mensaje menciona servicios específicos"""
        service_patterns = [
            r'\b(aceite|cambio.*aceite)\b',
            r'\b(frenos|pastillas)\b',
            r'\b(motor|reparación.*motor)\b',
            r'\b(transmisión|caja)\b',
            r'\b(suspensión|amortiguadores)\b',
            r'\b(revisión|chequeo|inspección)\b',
            r'\b(mantenimiento|servicio)\b'
        ]
        
        for pattern in service_patterns:
            if re.search(pattern, message, re.IGNORECASE):
                return True
        return False
    
    def _contains_customer_data(self, message: str) -> bool:
        """Detecta si el mensaje contiene datos de cliente (nombre, vehículo, etc.)"""
        # Buscar patrones de datos personales
        data_patterns = [
            r'\b[A-Z][a-z]+\s+[A-Z][a-z]+\b',  # Nombre y apellido
            r'\b[A-Z]{3}-\d{3,4}\b',  # Placa formato ABC-123
            r'\b(toyota|chevrolet|ford|nissan|hyundai|kia|mazda|honda)\b',  # Marcas
            r'\b\d{4}\b'  # Año
        ]
        
        matches = 0
        for pattern in data_patterns:
            if re.search(pattern, message, re.IGNORECASE):
                matches += 1
        
        return matches >= 2  # Al menos 2 patrones para considerar datos completos
    
    def _extract_datetime_entities(self, message: str) -> Dict:
        """Extrae entidades de fecha y hora de forma más precisa y secuencial."""
        entities = {}
        text = message.lower()

        # 1. Detectar y extraer referencias temporales (hoy, mañana)
        temporal_patterns = {
            'hoy': 'today',
            'mañana': 'tomorrow'
        }
        for word, value in temporal_patterns.items():
            if word in text:
                entities['time_reference'] = value
                text = text.replace(word, '') # Eliminar para no interferir
                break

        # 2. Detectar y extraer la hora
        time_patterns = [
            r'\b([0-9]{1,2}:[0-9]{2}\s*(?:am|pm))\b',      # "10:30 am"
            r'\b(a las|las|al)\s+([0-9]{1,2}:[0-9]{2})\s*(am|pm)?\b', # "a las 10:30"
            r'\b(a las|las|al)\s+([0-9]{1,2})\s*(am|pm)?\b',    # "a las 10 am"
            r'\b([0-9]{1,2})\s*(am|pm)\b',                   # "10 am"
            r'\b([0-9]{1,2}:[0-9]{2})\b'                      # "10:30"
        ]
        for pattern in time_patterns:
            match = re.search(pattern, text)
            if match:
                # Limpiar y guardar la hora encontrada
                raw_time = match.group(0).replace('a las', '').replace('las', '').replace('al', '').strip()
                entities['time'] = raw_time
                text = text.replace(match.group(0), '') # Eliminar para no interferir
                break

        # 3. Detectar día de la semana en el texto restante
        days_pattern = r'\b(lunes|martes|miércoles|miercoles|jueves|viernes|sábado|sabado|domingo)\b'
        match = re.search(days_pattern, text)
        if match:
            entities['day'] = match.group(1)
            text = text.replace(match.group(0), '')

        # 4. Detectar número del día en el texto restante
        day_number_pattern = r'\b([0-9]{1,2})\b'
        match = re.search(day_number_pattern, text)
        if match:
            entities['day_number'] = match.group(1)

        return entities
    
    def _extract_service_entities(self, message: str) -> Dict:
        """Extrae servicios mencionados en el mensaje"""
        entities = {'services': []}
        
        service_mapping = {
            r'\b(aceite|cambio.*aceite)\b': 'aceite',
            r'\b(frenos|pastillas)\b': 'frenos',
            r'\b(motor|reparación.*motor)\b': 'motor',
            r'\b(transmisión|caja)\b': 'transmision',
            r'\b(suspensión|amortiguadores)\b': 'suspension',
            r'\b(revisión|chequeo|inspección)\b': 'revision',
            r'\b(mantenimiento|servicio)\b': 'mantenimiento'
        }
        
        for pattern, service in service_mapping.items():
            if re.search(pattern, message, re.IGNORECASE):
                entities['services'].append(service)
        
        return entities
    
    def _extract_customer_entities(self, message: str) -> Dict:
        """Extrae datos de cliente del mensaje de registro"""
        entities = {}
        
        # Extraer nombre (primeras dos palabras capitalizadas)
        name_pattern = r'\b([A-Z][a-z]+\s+[A-Z][a-z]+)\b'
        name_match = re.search(name_pattern, message)
        if name_match:
            entities['name'] = name_match.group(1)
        
        # Extraer placa
        plate_pattern = r'\b([A-Z]{3}-\d{3,4})\b'
        plate_match = re.search(plate_pattern, message, re.IGNORECASE)
        if plate_match:
            entities['plate'] = plate_match.group(1).upper()
        
        # Extraer marca
        brands = ['toyota', 'chevrolet', 'ford', 'nissan', 'hyundai', 'kia', 'mazda', 'honda']
        for brand in brands:
            if re.search(rf'\b{brand}\b', message, re.IGNORECASE):
                entities['brand'] = brand.title()
                break
        
        # Extraer modelo (palabra después de la marca)
        if 'brand' in entities:
            model_pattern = rf'\b{entities["brand"]}\s+([A-Za-z0-9]+)\b'
            model_match = re.search(model_pattern, message, re.IGNORECASE)
            if model_match:
                entities['model'] = model_match.group(1).title()
        
        # Extraer año
        year_pattern = r'\b(19|20)\d{2}\b'
        year_match = re.search(year_pattern, message)
        if year_match:
            entities['year'] = int(year_match.group(0))
        
        return entities
    
    def _extract_vehicle_selection(self, message: str) -> Dict:
        """Extrae selección de vehículo por número"""
        # Buscar números en el mensaje
        number_pattern = r'\b([1-9])\b'
        number_match = re.search(number_pattern, message)
        
        if number_match:
            return {'vehicle_number': int(number_match.group(1))}
        
        return {}
    
    def _handle_appointment_datetime(self, entities: Dict, context: Dict, phone_number: str) -> Dict:
        """Maneja la selección de fecha/hora para una cita de forma contextual e inteligente."""
        try:
            conductor = self._find_conductor_by_phone(phone_number)
            if not conductor:
                return self._handle_new_customer_flow(entities, context, phone_number)

            # 1. Fusionar contexto y extraer entidades del mensaje ACTUAL
            fecha_hora_info = context.get('fecha_hora_info', {})
            current_message_entities = self._extract_datetime_entities(context.get('last_message', ''))
            fecha_hora_info.update({k: v for k, v in current_message_entities.items() if v})

            day = fecha_hora_info.get('day') or fecha_hora_info.get('time_reference')
            time = fecha_hora_info.get('time')
            day_number = fecha_hora_info.get('day_number')

            # 2. Detectar servicio del mensaje ACTUAL o del contexto
            vehiculo = self._get_vehiculo_for_conductor(conductor)
            # Usamos las entidades del intent actual, no de todo el contexto
            servicio_detectado = self._detect_service_from_entities(entities)
            if servicio_detectado:
                context['selected_service'] = servicio_detectado
            
            servicio_final = context.get('selected_service')

            # 3. Lógica de decisión unificada
            # CASO 1: Tenemos TODO (fecha, hora y servicio). Ir a confirmación.
            if day and time and servicio_final:
                return self._prepare_appointment_confirmation(context, vehiculo, fecha_hora_info, servicio_final)

            # CASO 2: Tenemos fecha y hora, pero FALTA el servicio.
            elif day and time and not servicio_final:
                message = f"Perfecto **{conductor.nombre}**!\n\n"
                message += self._format_datetime_info(day, time, day_number)
                message += f"\n\n*¿Qué servicio necesitas para tu {vehiculo.marca} {vehiculo.modelo}?*\n"
                message += self._get_suggested_services_message(vehiculo)
                return {
                    'message': message,
                    'type': 'ask_service',
                    'next_step': 'collect_service_details',
                    'fecha_hora_info': fecha_hora_info
                }

            # CASO 3: Tenemos día pero no hora.
            elif day and not time:
                message = f"Perfecto **{conductor.nombre}**!\n\n"
                message += self._format_datetime_info(day, None, day_number)
                message += "\n\n¿A qué hora prefieres? Ejemplo: 9:00 AM, 2:00 PM"
                return {
                    'message': message,
                    'type': 'ask_time',
                    'next_step': 'collect_appointment_details',
                    'fecha_hora_info': fecha_hora_info
                }

            # CASO 4: Tenemos hora pero no día.
            elif time and not day:
                message = f"Perfecto **{conductor.nombre}**, la cita sería a las *{time}*.\n\n¿Qué día te gustaría agendarla?\n"
                message += "Ej: 'mañana', 'el viernes', 'el 25'"
                return {
                    'message': message,
                    'type': 'ask_day',
                    'next_step': 'collect_appointment_details',
                    'fecha_hora_info': fecha_hora_info
                }

            # CASO 5: No se detectó información útil.
            else:
                message = "No entendí la fecha o la hora. Por favor, intenta de nuevo con más detalles. Ejemplo: 'mañana a las 10 am' o 'el viernes 25'."
                return {'message': message, 'type': 'error_datetime'}

        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error en _handle_appointment_datetime: {str(e)}", exc_info=True)
            return self._get_error_response()

    def _format_datetime_info(self, day: Optional[str], time: Optional[str], day_number: Optional[str]) -> str:
        """Construye una cadena de texto descriptiva para la fecha y hora."""
        if not day and not time:
            return "(aún no especificada)"

        date_part = ""
        if day == 'today':
            date_part = 'Hoy'
        elif day == 'tomorrow':
            date_part = 'Mañana'
        elif day:
            date_part = day.title()
        
        if day_number and day not in ['today', 'tomorrow']:
            date_part = f"{date_part} {day_number}"

        if time:
            if date_part:
                return f"📅 Has seleccionado: **{date_part} a las {time}**"
            else:
                return f"📅 Has seleccionado: **a las {time}**"
        else:
            return f"📅 Has seleccionado: **{date_part}**"
            

    
    def _prepare_appointment_confirmation(self, context: Dict, vehiculo: 'Vehiculo', fecha_hora_info: Dict, servicio: str) -> Dict:
        """Construye el mensaje y la respuesta para la confirmación de una cita."""
        conductor = vehiculo.conductor
        day = fecha_hora_info.get('day') or fecha_hora_info.get('time_reference')
        time = fecha_hora_info.get('time')
        day_number = fecha_hora_info.get('day_number')

        message = f"Perfecto **{conductor.nombre}**, por favor confirma los datos de tu cita:\n\n"
        message += f"🔧 **Servicio:** {servicio.title()}\n"
        message += self._format_datetime_info(day, time, day_number) + "\n"
        message += f"🚗 **Vehículo:** {vehiculo.marca} {vehiculo.modelo} ({vehiculo.placa})\n\n"
        message += "✅ *¿Confirmas la cita con estos detalles?*\n"
        message += "Responde 'Sí' para confirmar o 'No' para cambiar algo."

        # Guardar todo el contexto necesario para el paso de confirmación
        context['appointment_details'] = {
            'conductor_id': conductor.id,
            'vehiculo_id': vehiculo.id,
            'servicio': servicio,
            'fecha_hora_info': fecha_hora_info
        }

        return {
            'message': message,
            'type': 'appointment_confirmation_needed',
            'next_step': 'awaiting_confirmation',
        }

    def _handle_appointment_service(self, entities: Dict, context: Dict, phone_number: str) -> Dict:
        """Maneja la selección de servicio para una cita y decide el siguiente paso."""
        try:
            conductor = self._find_conductor_by_phone(phone_number)
            if not conductor:
                return self._handle_new_customer_flow(entities, context, phone_number)

            # 1. Detectar servicio del mensaje actual
            servicio_nombre = self._detect_service_from_entities(entities)
            if servicio_nombre:
                context['selected_service'] = servicio_nombre
            else:
                # Si no se detecta servicio, pedir clarificación
                message = "No pude identificar el servicio. Por favor, especifica qué necesitas.\n"
                message += self._get_suggested_services_message(self._get_vehiculo_for_conductor(conductor))
                return {
                    'message': message,
                    'type': 'service_clarification_needed',
                    'next_step': 'collect_service_details',
                }

            # 2. Verificar si tenemos fecha/hora del contexto
            fecha_hora_info = context.get('fecha_hora_info', {})
            day = fecha_hora_info.get('day') or fecha_hora_info.get('time_reference')
            time = fecha_hora_info.get('time')

            # 3. Decidir siguiente paso
            if day and time:
                # Tenemos todo, ir a confirmación
                vehiculo = self._get_vehiculo_for_conductor(conductor)
                return self._prepare_appointment_confirmation(context, vehiculo, fecha_hora_info, servicio_nombre)
            else:
                # Falta fecha/hora, la pedimos
                message = f"Excelente **{conductor.nombre}**! Has seleccionado: **{servicio_nombre}**.\n\n"
                message += "¿Qué día y hora te conviene para tu cita?\n"
                message += "Ej: 'mañana a las 10 am' o 'el viernes 25'."
                return {
                    'message': message,
                    'type': 'ask_datetime',
                    'next_step': 'collect_appointment_details',
                }

        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error en _handle_appointment_service: {str(e)}", exc_info=True)
            return self._get_error_response()
    
    def _handle_customer_registration(self, entities: Dict, context: Dict, phone_number: str) -> Dict:
        """Maneja registro de nuevo cliente"""
        try:
            from ..models import Conductor, Vehiculo
            
            # Extraer datos del mensaje
            name = entities.get('name', '')
            brand = entities.get('brand', '')
            model = entities.get('model', '')
            year = entities.get('year', '')
            plate = entities.get('plate', '')
            
            # Verificar que tengamos datos suficientes
            missing_data = []
            if not name:
                missing_data.append('nombre completo')
            if not brand:
                missing_data.append('marca del vehículo')
            if not model:
                missing_data.append('modelo del vehículo')
            if not year:
                missing_data.append('año del vehículo')
            if not plate:
                missing_data.append('placa del vehículo')
            
            if missing_data:
                message = f"📝 Necesito algunos datos adicionales:\n\n"
                message += "**Faltan:**\n"
                for item in missing_data:
                    message += f"• {item}\n"
                message += "\n**Ejemplo completo:**\n"
                message += "Juan Pérez, Toyota Corolla 2018, ABC-1234\n\n"
                message += "Por favor, envíame la información completa."
                
                return {
                    'message': message,
                    'type': 'registration_incomplete',
                    'next_step': 'collect_new_customer_data'
                }
            
            # Crear conductor y vehículo
            try:
                # Crear conductor
                conductor = Conductor.objects.create(
                    cliente=self.cliente,
                    nombre=name,
                    telefono=self._normalize_phone_number(phone_number),
                    email=f"{name.lower().replace(' ', '.')}@temp.com"  # Email temporal
                )
                
                # Crear vehículo
                vehiculo = Vehiculo.objects.create(
                    conductor=conductor,
                    marca=brand,
                    modelo=model,
                    anio=year,
                    placa=plate.upper(),
                    kilometraje=0  # Se actualizará después
                )
                
                message = f"🎉 ¡Bienvenido **{name}**!\n\n"
                message += f"✅ **Registro exitoso:**\n"
                message += f"• Cliente: {name}\n"
                message += f"• Vehículo: {brand} {model} {year}\n"
                message += f"• Placa: {plate.upper()}\n\n"
                message += f"📅 **Ahora podemos agendar tu cita:**\n"
                message += self._get_available_slots()
                message += "\n¿Qué día y hora te conviene?"
                
                return {
                    'message': message,
                    'type': 'registration_complete',
                    'next_step': 'collect_appointment_details',
                    'conductor_id': conductor.id,
                    'vehiculo_id': vehiculo.id
                }
                
            except Exception as db_error:
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Error creando conductor/vehículo: {str(db_error)}")
                
                message = "😔 Hubo un problema al registrar tus datos.\n\n"
                message += "Por favor, inténtalo nuevamente o contáctanos directamente:\n"
                message += f"📞 {self.cliente.telefono}\n"
                message += f"📍 {self.cliente.direccion}"
                
                return {
                    'message': message,
                    'type': 'registration_error',
                    'escalate_to_human': True
                }
            
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error en _handle_customer_registration: {str(e)}")
            return self._get_error_response()
    
    def _handle_vehicle_selection(self, entities: Dict, context: Dict, phone_number: str) -> Dict:
        """Maneja selección de vehículo cuando el conductor tiene múltiples vehículos"""
        try:
            conductor = self._find_conductor_by_phone(phone_number)
            if not conductor:
                return self._handle_new_customer_flow(entities, context, phone_number)
            
            vehicle_number = entities.get('vehicle_number', 0)
            vehiculos = list(conductor.vehiculos.all())
            
            if vehicle_number < 1 or vehicle_number > len(vehiculos):
                message = f"**{conductor.nombre}**, por favor selecciona un número válido:\n\n"
                for i, vehiculo in enumerate(vehiculos, 1):
                    message += f"{i}. **{vehiculo.marca} {vehiculo.modelo} {vehiculo.anio}** (Placa: {vehiculo.placa})\n"
                message += "\nEjemplo: Escribe '1' para el primer vehículo."
                
                return {
                    'message': message,
                    'type': 'vehicle_selection_invalid',
                    'next_step': 'select_vehicle'
                }
            
            # Vehículo seleccionado
            vehiculo_seleccionado = vehiculos[vehicle_number - 1]
            
            message = f"Perfecto **{conductor.nombre}**! \n\n"
            message += f"🚗 **Vehículo seleccionado:**\n"
            message += f"• {vehiculo_seleccionado.marca} {vehiculo_seleccionado.modelo} {vehiculo_seleccionado.anio}\n"
            message += f"• Placa: {vehiculo_seleccionado.placa}\n"
            message += f"• Kilometraje: {vehiculo_seleccionado.kilometraje:,} km\n\n"
            
            # Sugerencias de servicio
            suggestions = self._get_service_suggestions(vehiculo_seleccionado)
            message += suggestions
            message += "\n📅 **Horarios disponibles:**\n"
            message += self._get_available_slots()
            message += "\n¿Qué día, hora y servicio prefieres?"
            
            return {
                'message': message,
                'type': 'vehicle_selected',
                'next_step': 'collect_appointment_details',
                'selected_vehicle_id': vehiculo_seleccionado.id
            }
            
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error en _handle_vehicle_selection: {str(e)}")
            return self._get_error_response()
    
    def _handle_vehicle_status(self, entities: Dict, context: Dict, phone_number: str) -> Dict:
        """Maneja consultas sobre el estado del vehículo"""
        try:
            conductor = self._find_conductor_by_phone(phone_number)
            if not conductor:
                return {
                    'message': "Para consultar el estado de tu vehículo, necesito que te registres primero. ¿Cómo te llamas y cuál es tu vehículo?",
                    'type': 'registration_required',
                    'next_step': 'collect_new_customer_data'
                }
            
            from ..models import OrdenServicio
            
            # Buscar órdenes de servicio activas
            ordenes_activas = OrdenServicio.objects.filter(
                vehiculo__conductor=conductor,
                estado__in=['pendiente', 'en_proceso']
            ).order_by('-fecha_creacion')
            
            message = f"Hola **{conductor.nombre}**! \n\n"
            
            if ordenes_activas.exists():
                message += "🔧 **Estado de tus servicios:**\n\n"
                for orden in ordenes_activas[:3]:  # Máximo 3 órdenes
                    vehiculo = orden.vehiculo
                    message += f"🚗 **{vehiculo.marca} {vehiculo.modelo}** (Placa: {vehiculo.placa})\n"
                    message += f"• Estado: **{orden.get_estado_display()}**\n"
                    message += f"• Servicio: {orden.descripcion_trabajo}\n"
                    message += f"• Fecha: {orden.fecha_creacion.strftime('%d/%m/%Y')}\n\n"
                
                message += "Para más detalles, puedes llamarnos:\n"
                message += f"📞 {self.cliente.telefono}"
            else:
                message += "No tienes servicios activos en este momento.\n\n"
                message += "🚗 **Tus vehículos registrados:**\n"
                for vehiculo in conductor.vehiculos.all():
                    message += f"• {vehiculo.marca} {vehiculo.modelo} {vehiculo.anio} (Placa: {vehiculo.placa})\n"
                
                message += "\n¿Necesitas agendar un nuevo servicio?"
            
            return {
                'message': message,
                'type': 'vehicle_status_info',
                'next_step': 'general_conversation'
            }
            
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error en _handle_vehicle_status: {str(e)}")
            return self._get_error_response()
    
    def _handle_emergency(self, entities: Dict, context: Dict, phone_number: str) -> Dict:
        """Maneja situaciones de emergencia"""
        try:
            conductor = self._find_conductor_by_phone(phone_number)
            nombre = conductor.nombre if conductor else "Cliente"
            
            message = f"🆘 **EMERGENCIA - {nombre}**\n\n"
            message += "🚑 **Atención inmediata:**\n"
            message += f"• Llámanos AHORA: **{self.cliente.telefono}**\n"
            message += f"• Ubicación: {self.cliente.direccion}\n\n"
            
            if self.taller_config and hasattr(self.taller_config, 'telefono_emergencia'):
                message += f"• Emergencias 24h: **{self.taller_config.telefono_emergencia}**\n\n"
            
            message += "📍 **Si estás en carretera:**\n"
            message += "• Enciende las luces de emergencia\n"
            message += "• Colócate en un lugar seguro\n"
            message += "• Llámanos para asistencia\n\n"
            message += "Un técnico te contactará en breve."
            
            return {
                'message': message,
                'type': 'emergency_response',
                'escalate_to_human': True,
                'priority': 'high'
            }
            
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error en _handle_emergency: {str(e)}")
            return {
                'message': "🆘 **EMERGENCIA**\n\nLlámanos inmediatamente:\n📞 " + str(self.cliente.telefono),
                'type': 'emergency_fallback',
                'escalate_to_human': True
            }
    
    def _contains_datetime_info(self, message: str) -> bool:
        """Detecta si el mensaje contiene información de fecha/hora"""
        datetime_patterns = [
            r'\b(lunes|martes|miércoles|miercoles|jueves|viernes|sábado|sabado|domingo)\b',
            r'\b(mañana|tarde|noche)\b',
            r'\b\d{1,2}\s*[:/]\s*\d{2}\b',  # 9:00, 14:30
            r'\b\d{1,2}\s*(am|pm|a\.m\.|p\.m\.)\b',  # 9 AM, 2 PM
            r'\b(hoy|mañana|pasado mañana)\b',
            r'\b\d{1,2}\s*de\s*(enero|febrero|marzo|abril|mayo|junio|julio|agosto|septiembre|octubre|noviembre|diciembre)\b',
            r'\b\d{1,2}/\d{1,2}\b',  # 25/08
            r'\b(enero|febrero|marzo|abril|mayo|junio|julio|agosto|septiembre|octubre|noviembre|diciembre)\s*\d{1,2}\b'
        ]
        
        for pattern in datetime_patterns:
            if re.search(pattern, message, re.IGNORECASE):
                return True
        return False
    
    def _extract_datetime_entities(self, message: str) -> Dict:
        """Extrae entidades de fecha y hora del mensaje"""
        entities = {}
        message_lower = message.lower()
        
        # Detectar días de la semana
        days_pattern = r'\b(lunes|martes|miércoles|miercoles|jueves|viernes|sábado|sabado|domingo)\b'
        day_match = re.search(days_pattern, message_lower)
        if day_match:
            entities['day'] = day_match.group(1)
        
        # Detectar números de día (ej: "lunes 25")
        day_number_pattern = r'\b(\d{1,2})\b'
        day_numbers = re.findall(day_number_pattern, message)
        if day_numbers:
            entities['day_number'] = day_numbers[0]
        
        # Detectar horas
        time_patterns = [
            r'\b(\d{1,2})\s*[:/]\s*(\d{2})\s*(am|pm|a\.m\.|p\.m\.)?\b',
            r'\b(\d{1,2})\s*(am|pm|a\.m\.|p\.m\.)\b'
        ]
        
        for pattern in time_patterns:
            time_match = re.search(pattern, message_lower)
            if time_match:
                entities['time'] = time_match.group(0)
                break
        
        # Detectar referencias temporales
        time_refs = {
            'mañana': 'morning',
            'tarde': 'afternoon', 
            'noche': 'evening',
            'madrugada': 'dawn'
        }
        
        for ref, value in time_refs.items():
            if ref in message_lower:
                entities['time_reference'] = value
                break
        
        return entities
    
    def _contains_service_info(self, message: str) -> bool:
        """Detecta si el mensaje contiene información de servicios"""
        service_patterns = [
            r'\b(aceite|cambio de aceite)\b',
            r'\b(frenos|pastillas)\b',
            r'\b(motor|revisión de motor)\b',
            r'\b(mantenimiento|servicio)\b',
            r'\b(reparación|arreglo)\b',
            r'\b(diagnóstico|diagnostico)\b',
            r'\b(llantas|neumáticos|neumaticos)\b'
        ]
        
        for pattern in service_patterns:
            if re.search(pattern, message, re.IGNORECASE):
                return True
        return False
    
    def _extract_service_entities(self, message: str) -> Dict:
        """Extrae entidades de servicios del mensaje"""
        entities = {}
        message_lower = message.lower()
        
        service_mapping = {
            'aceite': 'cambio_aceite',
            'cambio de aceite': 'cambio_aceite',
            'frenos': 'revision_frenos',
            'pastillas': 'revision_frenos',
            'motor': 'revision_motor',
            'mantenimiento': 'mantenimiento_general',
            'servicio': 'mantenimiento_general',
            'diagnóstico': 'diagnostico',
            'diagnostico': 'diagnostico'
        }
        
        for keyword, service_type in service_mapping.items():
            if keyword in message_lower:
                entities['service_type'] = service_type
                entities['service_name'] = keyword
                break
        
        return entities
    
    def _contains_customer_data(self, message: str) -> bool:
        """Detecta si el mensaje contiene datos de nuevo cliente"""
        # Detectar nombres (palabras con mayúscula inicial)
        name_pattern = r'\b[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+\s+[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+\b'
        if re.search(name_pattern, message):
            return True
        
        # Detectar información de vehículos
        vehicle_patterns = [
            r'\b(toyota|nissan|chevrolet|ford|hyundai|kia|mazda|honda|volkswagen)\b',
            r'\b(hilux|corolla|sentra|aveo|accent|rio|cx-5|civic|jetta)\b',
            r'\b[A-Z]{3}-\d{3,4}\b'  # Placas
        ]
        
        for pattern in vehicle_patterns:
            if re.search(pattern, message, re.IGNORECASE):
                return True
        
        return False
    
    def _extract_customer_entities(self, message: str) -> Dict:
        """Extrae entidades de datos de cliente del mensaje"""
        entities = {}
        
        # Extraer nombre
        name_pattern = r'\b([A-ZÁÉÍÓÚÑ][a-záéíóúñ]+\s+[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+)\b'
        name_match = re.search(name_pattern, message)
        if name_match:
            entities['customer_name'] = name_match.group(1)
        
        # Extraer información de vehículo
        vehicle_pattern = r'\b(toyota|nissan|chevrolet|ford|hyundai|kia|mazda|honda|volkswagen)\s+(\w+)\b'
        vehicle_match = re.search(vehicle_pattern, message, re.IGNORECASE)
        if vehicle_match:
            entities['vehicle_brand'] = vehicle_match.group(1).title()
            entities['vehicle_model'] = vehicle_match.group(2).title()
        
        # Extraer placa
        placa_pattern = r'\b([A-Z]{3}-\d{3,4})\b'
        placa_match = re.search(placa_pattern, message.upper())
        if placa_match:
            entities['vehicle_plate'] = placa_match.group(1)
        
        return entities
    
    def _extract_vehicle_selection(self, message: str) -> Dict:
        """Extrae selección de vehículo por número"""
        # Buscar números en el mensaje
        number_pattern = r'\b(\d+)\b'
        numbers = re.findall(number_pattern, message)
        
        if numbers:
            try:
                selection = int(numbers[0])
                return {'vehicle_selection': selection}
            except ValueError:
                pass
        
        return {}
    
    def _handle_appointment_confirmation(self, entities: Dict, context: Dict, phone_number: str) -> Dict:
        """Maneja la confirmación de citas y crea la cita en la base de datos"""
        try:
            # Verificar que tenemos los detalles de la cita en el contexto
            if 'appointment_details' not in context:
                return {
                    'message': "❌ No encontré los detalles de la cita para confirmar. Por favor, empecemos de nuevo.\n\n¿Qué servicio necesitas?",
                    'type': 'error'
                }

            # Obtener datos del sub-diccionario de detalles de la cita
            details = context['appointment_details']
            conductor_id = details.get('conductor_id')
            vehiculo_id = details.get('vehiculo_id')
            servicio_nombre = details.get('servicio')
            fecha_hora_info = details.get('fecha_hora_info')

            # Verificar que todos los datos necesarios están presentes
            if not all([conductor_id, vehiculo_id, servicio_nombre, fecha_hora_info]):
                return {
                    'message': "❌ La información de la cita está incompleta. Por favor, inicia el proceso de nuevo.",
                    'type': 'error'
                }
            
            # Buscar conductor y vehículo
            try:
                conductor = Conductor.objects.get(id=conductor_id, cliente=self.cliente)
                vehiculo = Vehiculo.objects.get(id=vehiculo_id, conductor=conductor)
            except (Conductor.DoesNotExist, Vehiculo.DoesNotExist):
                return {
                    'message': "❌ Error al encontrar tus datos. Por favor, inicia el proceso nuevamente.",
                    'type': 'error'
                }
            
            # Convertir fecha_hora_info a datetime
            try:
                fecha_hora = self._convert_fecha_hora_info_to_datetime(fecha_hora_info)
            except ValueError as e:
                return {
                    'message': f"❌ Error en el formato de fecha: {str(e)}. Por favor, agenda nuevamente.",
                    'type': 'error'
                }
            
            # Buscar servicio en el catálogo
            servicio_catalogo = None
            try:
                servicio_catalogo = ServicioCatalogo.objects.filter(
                    cliente=self.cliente,
                    nombre__icontains=servicio_nombre
                ).first()
            except:
                pass
            
            # Crear la cita
            cita = Cita.objects.create(
                cliente=self.cliente,
                conductor=conductor,
                vehiculo=vehiculo,
                fecha_cita=fecha_hora,
                estado='pendiente',
                notas=f"Cita agendada via WhatsApp para: {servicio_nombre}",
                mensaje=f"Cita confirmada para {servicio_nombre} el {fecha_hora.strftime('%d/%m/%Y a las %H:%M')}"
            )
            
            # Si encontramos el servicio en el catálogo, agregarlo
            if servicio_catalogo:
                cita.servicios.add(servicio_catalogo)
            
            # Limpiar contexto después de crear la cita
            cache_key = f"chatbot_context_{self.cliente.id}_{phone_number}"
            cache.set(cache_key, {
                'messages': [],
                'last_intent': 'appointment_confirmed',
                'entities': {}
            }, 86400)
            
            # Generar mensaje de confirmación
            message = "✅ **¡CITA CONFIRMADA!**\n\n"
            message += f"👤 **Cliente:** {conductor.nombre}\n"
            message += f"🚗 **Vehículo:** {vehiculo.marca} {vehiculo.modelo} ({vehiculo.placa})\n"
            message += f"🔧 **Servicio:** {servicio_nombre}\n"
            message += f"📅 **Fecha:** {fecha_hora.strftime('%d/%m/%Y')}\n"
            message += f"🕐 **Hora:** {fecha_hora.strftime('%H:%M')}\n\n"
            message += f"📋 **Número de Cita:** #{cita.id}\n\n"
            message += "📞 Si necesitas cambiar o cancelar tu cita, contáctanos.\n\n"
            message += "¡Te esperamos! 👋"
            
            return {
                'message': message,
                'type': 'appointment_confirmed',
                'appointment_id': cita.id
            }
            
        except Exception as e:
            # Log del error para debugging
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error creando cita: {str(e)}", exc_info=True)
            return {
                'message': "❌ Ocurrió un error al crear tu cita. Por favor, inténtalo nuevamente o contáctanos directamente.",
                'type': 'error'
            }
    
    def _handle_appointment_cancellation(self, entities: Dict, context: Dict, phone_number: str) -> Dict:
        """Maneja la cancelación de citas"""
        # Limpiar contexto
        cache_key = f"chatbot_context_{self.cliente.id}_{phone_number}"
        cache.set(cache_key, {
            'messages': [],
            'last_intent': 'appointment_cancelled',
            'entities': {}
        }, 86400)
        
        return {
            'message': "❌ **Proceso de cita cancelado**\n\n" +
                      "No hay problema, puedes agendar cuando gustes.\n\n" +
                      "¿En qué más puedo ayudarte?",
            'type': 'appointment_cancelled'
        }
    
    def _convert_fecha_hora_info_to_datetime(self, fecha_hora_info: Dict) -> datetime:
        """Convierte la información de fecha/hora del contexto en un objeto datetime"""
        from datetime import datetime, timedelta
        from django.utils import timezone
        
        # Obtener fecha base (hoy por defecto)
        now = timezone.now()
        fecha_base = now.date()
        
        # Procesar día de la semana
        if fecha_hora_info.get('day'):
            day_name = fecha_hora_info['day'].lower()
            days_map = {
                'lunes': 0, 'martes': 1, 'miercoles': 2, 'miércoles': 2,
                'jueves': 3, 'viernes': 4, 'sabado': 5, 'sábado': 5, 'domingo': 6
            }
            
            if day_name in days_map:
                target_weekday = days_map[day_name]
                current_weekday = fecha_base.weekday()
                
                # Calcular días hasta el día objetivo
                days_ahead = target_weekday - current_weekday
                if days_ahead <= 0:  # Si es hoy o ya pasó, ir a la próxima semana
                    days_ahead += 7
                
                fecha_base = fecha_base + timedelta(days=days_ahead)
        
        # Procesar referencia temporal
        if fecha_hora_info.get('time_reference'):
            ref = fecha_hora_info['time_reference']
            if ref == 'tomorrow':
                fecha_base = now.date() + timedelta(days=1)
            elif ref == 'today':
                fecha_base = now.date()
        
        # Procesar número de día (ej: "lunes 25")
        if fecha_hora_info.get('day_number'):
            try:
                day_num = int(fecha_hora_info['day_number'])
                # Asumir el próximo mes si el día ya pasó este mes
                if day_num < now.day:
                    # Próximo mes
                    if now.month == 12:
                        fecha_base = fecha_base.replace(year=now.year + 1, month=1, day=day_num)
                    else:
                        fecha_base = fecha_base.replace(month=now.month + 1, day=day_num)
                else:
                    # Este mes
                    fecha_base = fecha_base.replace(day=day_num)
            except (ValueError, TypeError):
                pass
        
        # Procesar hora
        hora = 9  # Hora por defecto: 9 AM
        minuto = 0
        
        if fecha_hora_info.get('time'):
            time_str = fecha_hora_info['time'].lower()
            
            # Patrones de hora
            import re
            
            # Formato HH:MM AM/PM
            match = re.search(r'(\d{1,2}):(\d{2})\s*(am|pm)', time_str)
            if match:
                hora = int(match.group(1))
                minuto = int(match.group(2))
                if match.group(3) == 'pm' and hora != 12:
                    hora += 12
                elif match.group(3) == 'am' and hora == 12:
                    hora = 0
            else:
                # Formato H AM/PM
                match = re.search(r'(\d{1,2})\s*(am|pm)', time_str)
                if match:
                    hora = int(match.group(1))
                    if match.group(2) == 'pm' and hora != 12:
                        hora += 12
                    elif match.group(2) == 'am' and hora == 12:
                        hora = 0
                else:
                    # Formato HH:MM
                    match = re.search(r'(\d{1,2}):(\d{2})', time_str)
                    if match:
                        hora = int(match.group(1))
                        minuto = int(match.group(2))
        elif fecha_hora_info.get('time_reference'):
            # Asignar horas por defecto según referencia
            ref = fecha_hora_info['time_reference']
            if ref == 'morning':
                hora = 9
            elif ref == 'afternoon':
                hora = 14
            elif ref == 'evening':
                hora = 17
        
        # Crear datetime en zona horaria local
        try:
            import pytz
            # Crear datetime naive
            fecha_hora_naive = datetime.combine(fecha_base, datetime.min.time().replace(hour=hora, minute=minuto))
            
            # Aplicar zona horaria local (Ecuador)
            tz_local = pytz.timezone('America/Guayaquil')
            fecha_hora_local = tz_local.localize(fecha_hora_naive)
            
            return fecha_hora_local
        except ValueError as e:
            raise ValueError(f"No se pudo crear fecha válida: {str(e)}")
