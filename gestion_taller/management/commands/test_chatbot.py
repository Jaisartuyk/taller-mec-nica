"""
Comando para probar el chatbot de WhatsApp
"""
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from gestion_taller.models import Cliente, Conductor
from gestion_taller.services.chatbot_service import ChatbotService


class Command(BaseCommand):
    help = 'Prueba el chatbot de WhatsApp con diferentes tipos de mensajes'

    def add_arguments(self, parser):
        parser.add_argument(
            '--cliente-id',
            type=int,
            help='ID del cliente/taller a usar para las pruebas'
        )
        parser.add_argument(
            '--cliente-nombre',
            type=str,
            help='Nombre del cliente/taller a usar para las pruebas'
        )
        parser.add_argument(
            '--telefono',
            type=str,
            default='+593968192046',
            help='Número de teléfono del usuario de prueba'
        )
        parser.add_argument(
            '--mensaje',
            type=str,
            help='Mensaje específico para probar'
        )
        parser.add_argument(
            '--test-suite',
            action='store_true',
            help='Ejecutar suite completa de pruebas'
        )

    def handle(self, *args, **options):
        try:
            # Obtener cliente
            cliente = self.get_cliente(options)
            if not cliente:
                raise CommandError('Cliente no encontrado')

            # Inicializar chatbot
            chatbot = ChatbotService(cliente)
            
            self.stdout.write(
                self.style.SUCCESS(f'\n🤖 CHATBOT DE {cliente.nombre.upper()}')
            )
            self.stdout.write('=' * 50)

            if options['mensaje']:
                # Probar mensaje específico
                self.test_single_message(chatbot, options['telefono'], options['mensaje'])
            elif options['test_suite']:
                # Ejecutar suite completa
                self.run_test_suite(chatbot, options['telefono'])
            else:
                # Modo interactivo
                self.interactive_mode(chatbot, options['telefono'])

        except Exception as e:
            raise CommandError(f'Error: {str(e)}')

    def get_cliente(self, options):
        """Obtiene el cliente para las pruebas"""
        if options['cliente_id']:
            try:
                return Cliente.objects.get(id=options['cliente_id'])
            except Cliente.DoesNotExist:
                return None
        
        if options['cliente_nombre']:
            return Cliente.objects.filter(
                nombre__icontains=options['cliente_nombre']
            ).first()
        
        # Cliente por defecto
        return Cliente.objects.first()

    def test_single_message(self, chatbot, phone_number, message):
        """Prueba un mensaje específico"""
        self.stdout.write(f'\n📱 Usuario: {message}')
        
        response = chatbot.process_message(phone_number, message)
        
        if response['success']:
            self.stdout.write(
                self.style.SUCCESS(f'🤖 Bot: {response["response"]["message"]}')
            )
            self.stdout.write(f'🎯 Intención: {response["intent"]}')
            if response['entities']:
                self.stdout.write(f'📊 Entidades: {response["entities"]}')
        else:
            self.stdout.write(
                self.style.ERROR(f'❌ Error: {response["error"]}')
            )

    def run_test_suite(self, chatbot, phone_number):
        """Ejecuta suite completa de pruebas"""
        test_messages = [
            # Saludos
            ('Hola', 'saludo'),
            ('Buenos días', 'saludo'),
            ('Qué tal', 'saludo'),
            
            # Consultas de servicios
            ('Qué servicios ofrecen?', 'consulta_servicio'),
            ('Necesito cambio de aceite', 'consulta_servicio'),
            ('Hacen reparación de frenos?', 'consulta_servicio'),
            
            # Consultas de precios
            ('Cuánto cuesta el cambio de aceite?', 'consulta_precio'),
            ('Precio de pastillas de freno', 'consulta_precio'),
            ('Necesito cotización', 'consulta_precio'),
            
            # Agendar citas
            ('Quiero agendar una cita', 'agendar_cita'),
            ('Cuándo tienen disponible?', 'agendar_cita'),
            ('Necesito turno para mañana', 'agendar_cita'),
            
            # Estado de vehículo
            ('Cómo va mi carro?', 'consulta_estado'),
            ('Estado de mi vehículo ABC-1234', 'consulta_estado'),
            ('Está listo mi auto?', 'consulta_estado'),
            
            # Ubicación y horarios
            ('Dónde están ubicados?', 'ubicacion_horario'),
            ('Qué horario tienen?', 'ubicacion_horario'),
            ('A qué hora abren?', 'ubicacion_horario'),
            
            # Despedidas
            ('Gracias', 'despedida'),
            ('Perfecto, nos vemos', 'despedida'),
            ('Muchas gracias por la info', 'despedida'),
            
            # Consultas generales
            ('No entiendo', 'consulta_general'),
            ('Ayuda', 'consulta_general'),
        ]

        self.stdout.write('\n🧪 EJECUTANDO SUITE DE PRUEBAS')
        self.stdout.write('=' * 50)

        correct_predictions = 0
        total_tests = len(test_messages)

        for i, (message, expected_intent) in enumerate(test_messages, 1):
            self.stdout.write(f'\n📝 Test {i}/{total_tests}: "{message}"')
            
            response = chatbot.process_message(phone_number, message)
            
            if response['success']:
                actual_intent = response['intent']
                is_correct = actual_intent == expected_intent
                
                if is_correct:
                    correct_predictions += 1
                    self.stdout.write(
                        self.style.SUCCESS(f'✅ Correcto: {actual_intent}')
                    )
                else:
                    self.stdout.write(
                        self.style.WARNING(
                            f'⚠️  Esperado: {expected_intent}, Obtenido: {actual_intent}'
                        )
                    )
                
                # Mostrar respuesta (truncada)
                bot_response = response['response']['message'][:100]
                if len(response['response']['message']) > 100:
                    bot_response += '...'
                self.stdout.write(f'🤖 "{bot_response}"')
            else:
                self.stdout.write(
                    self.style.ERROR(f'❌ Error: {response["error"]}')
                )

        # Estadísticas finales
        accuracy = (correct_predictions / total_tests) * 100
        self.stdout.write('\n' + '=' * 50)
        self.stdout.write(
            self.style.SUCCESS(
                f'📊 RESULTADOS: {correct_predictions}/{total_tests} correctos ({accuracy:.1f}%)'
            )
        )

        if accuracy >= 80:
            self.stdout.write(self.style.SUCCESS('🎉 ¡Excelente rendimiento!'))
        elif accuracy >= 60:
            self.stdout.write(self.style.WARNING('👍 Buen rendimiento'))
        else:
            self.stdout.write(self.style.ERROR('⚠️  Necesita mejoras'))

    def interactive_mode(self, chatbot, phone_number):
        """Modo interactivo para probar el chatbot"""
        self.stdout.write('\n💬 MODO INTERACTIVO')
        self.stdout.write('Escribe mensajes para probar el chatbot')
        self.stdout.write('Escribe "salir" para terminar\n')

        while True:
            try:
                message = input('📱 Tú: ')
                
                if message.lower() in ['salir', 'exit', 'quit']:
                    self.stdout.write('👋 ¡Hasta luego!')
                    break
                
                if not message.strip():
                    continue
                
                response = chatbot.process_message(phone_number, message)
                
                if response['success']:
                    self.stdout.write(
                        self.style.SUCCESS(f'🤖 Bot: {response["response"]["message"]}')
                    )
                    self.stdout.write(
                        self.style.HTTP_INFO(f'🎯 Intención: {response["intent"]}')
                    )
                    if response['entities']:
                        self.stdout.write(
                            self.style.HTTP_INFO(f'📊 Entidades: {response["entities"]}')
                        )
                else:
                    self.stdout.write(
                        self.style.ERROR(f'❌ Error: {response["error"]}')
                    )
                
                print()  # Línea en blanco
                
            except KeyboardInterrupt:
                self.stdout.write('\n👋 ¡Hasta luego!')
                break
            except EOFError:
                self.stdout.write('\n👋 ¡Hasta luego!')
                break
