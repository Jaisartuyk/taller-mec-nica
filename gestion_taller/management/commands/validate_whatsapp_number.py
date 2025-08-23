from django.core.management.base import BaseCommand
from gestion_taller.whatsapp_service import WhatsAppService

class Command(BaseCommand):
    help = 'Valida un número de teléfono para WhatsApp'

    def add_arguments(self, parser):
        parser.add_argument(
            '--numero',
            type=str,
            required=True,
            help='Número de teléfono a validar (ej: +593968192046, 0968192046, 968192046)'
        )

    def handle(self, *args, **options):
        numero = options['numero']
        
        whatsapp = WhatsAppService()
        
        self.stdout.write(f"\n🔍 Validando número: {numero}")
        self.stdout.write("-" * 50)
        
        # Validar número
        is_valid, message = whatsapp.validate_whatsapp_number(numero)
        
        if is_valid:
            self.stdout.write(
                self.style.SUCCESS(f"✅ {message}")
            )
            
            # Mostrar número limpio
            clean_number = whatsapp._clean_phone_number(numero)
            self.stdout.write(f"📱 Número formateado: {clean_number}")
            
            # Intentar enviar mensaje de prueba
            self.stdout.write("\n🚀 Enviando mensaje de prueba...")
            resultado = whatsapp.send_message(
                numero,
                "🔧 Mensaje de prueba desde el Taller Mecánico\n\nEste es un mensaje de validación. Si lo recibes, tu número está correctamente configurado para WhatsApp."
            )
            
            if resultado['success']:
                self.stdout.write(
                    self.style.SUCCESS("✅ Mensaje enviado exitosamente!")
                )
            else:
                self.stdout.write(
                    self.style.ERROR(f"❌ Error al enviar: {resultado['error']}")
                )
                
        else:
            self.stdout.write(
                self.style.ERROR(f"❌ {message}")
            )
            
            # Mostrar sugerencias
            self.stdout.write("\n💡 Formatos válidos para Ecuador:")
            self.stdout.write("   • +593968192046")
            self.stdout.write("   • 593968192046") 
            self.stdout.write("   • 0968192046")
            self.stdout.write("   • 968192046")
            self.stdout.write("\n⚠️  Solo números celulares (que empiecen con 09)")
