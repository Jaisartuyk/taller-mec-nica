from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class Cliente(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True, related_name='perfil_cliente')
    nombre = models.CharField(max_length=100)
    telefono = models.CharField(max_length=20)
    correo = models.EmailField(blank=True, null=True)
    direccion = models.CharField(max_length=200, blank=True, null=True)
    logo = models.ImageField(upload_to='logos_taller/', blank=True, null=True, help_text="Logo del taller")
    def default_preferencias_notificacion():
        return {
            "canal": ["email"],  # opciones: "email", "web", "sms"
            "recordatorio_mantenimiento": True,
            "recordatorio_seguro": True,
            "promociones": False,
            "hora_envio": "09:00"
        }
    preferencias_notificacion = models.JSONField(
        default=default_preferencias_notificacion,
        help_text="Preferencias de notificación del cliente"
    )
    fecha_registro = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name_plural = "Clientes"
        ordering = ['nombre']
    
    def __str__(self):
        return self.nombre

class PerfilUsuario(models.Model):
    telegram_chat_id = models.CharField(max_length=50, blank=True, null=True, help_text="Chat ID de Telegram para notificaciones personales")
    ROL_CHOICES = [
        ('admin', 'Administrador'),
        ('empleado', 'Empleado'),
        ('conductor', 'Conductor'),
    ]
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='perfilusuario')
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE, related_name='usuarios', null=True, blank=True)
    conductor = models.OneToOneField('Conductor', on_delete=models.CASCADE, related_name='perfil', null=True, blank=True)
    rol = models.CharField(max_length=20, choices=ROL_CHOICES, default='empleado')

    def __str__(self):
        return f"{self.user.username} ({self.get_rol_display()}) - {self.cliente.nombre if self.cliente else ''}"

# Señal para crear automáticamente el PerfilUsuario al crear un usuario
from django.db.models.signals import post_save
from django.dispatch import receiver

@receiver(post_save, sender=User)
def crear_perfil_usuario(sender, instance, created, **kwargs):
    if created:
        # Si hay solo un cliente, lo asigna automáticamente; si hay varios, deberías adaptarlo
        from .models import Cliente
        cliente = Cliente.objects.first()
        if cliente:
            PerfilUsuario.objects.create(user=instance, cliente=cliente)

class Conductor(models.Model):
    telegram_chat_id = models.CharField(max_length=50, blank=True, null=True, help_text="Chat ID de Telegram si es conductor sin usuario propio")
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE, related_name='conductores')
    nombre = models.CharField(max_length=100)
    telefono = models.CharField(max_length=20, blank=True, null=True)
    correo = models.EmailField(blank=True, null=True)
    direccion = models.CharField(max_length=200, blank=True, null=True)
    fecha_registro = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.nombre

class Vehiculo(models.Model):
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE, related_name='vehiculos')
    conductor = models.ForeignKey('Conductor', on_delete=models.SET_NULL, null=True, blank=True, related_name='vehiculos')
    placa = models.CharField(max_length=10, unique=True)
    marca = models.CharField(max_length=50)
    modelo = models.CharField(max_length=50)
    anio = models.PositiveIntegerField()
    vin = models.CharField(max_length=17, unique=True, blank=True, null=True)
    color = models.CharField(max_length=30, blank=True, null=True)
    kilometraje = models.PositiveIntegerField(default=0)
    fecha_ultimo_servicio = models.DateField(null=True, blank=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    activo = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['-fecha_ultimo_servicio']
        verbose_name_plural = "Vehículos"
    
    def __str__(self):
        return f"{self.placa} - {self.marca} {self.modelo}"



class CategoriaRepuesto(models.Model):
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True)
    def __str__(self):
        return self.nombre

class Repuesto(models.Model):
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE, related_name='repuestos')
    categoria = models.ForeignKey(CategoriaRepuesto, on_delete=models.SET_NULL, null=True, blank=True, related_name='repuestos')
    nombre = models.CharField(max_length=100)
    codigo = models.CharField(max_length=50, unique=True, blank=True, null=True)
    descripcion = models.TextField(blank=True)
    imagen = models.ImageField(upload_to='repuestos/', blank=True, null=True)
    precio_compra = models.DecimalField(max_digits=10, decimal_places=2)
    precio_venta = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.PositiveIntegerField(default=0)
    stock_minimo = models.PositiveIntegerField(default=5)
    proveedor = models.CharField(max_length=100, blank=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.nombre} ({self.codigo or 'Sin código'})"

class Servicio(models.Model):
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE, related_name='servicios')
    vehiculo = models.ForeignKey(Vehiculo, on_delete=models.CASCADE, related_name='servicios')
    conductor = models.ForeignKey(Conductor, on_delete=models.CASCADE, related_name='servicios')
    descripcion = models.TextField(blank=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_servicio = models.DateTimeField(default=timezone.now)
    estado = models.CharField(max_length=20, choices=[
        ('pendiente', 'Pendiente'),
        ('en_progreso', 'En Progreso'),
        ('completado', 'Completado'),
        ('facturado', 'Facturado'),
    ], default='pendiente')
    notas_tecnico = models.TextField(blank=True)
    costo_mano_obra = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    class Meta:
        ordering = ['-fecha_creacion']

    def costo_total(self):
        return self.costo_mano_obra + sum(d.subtotal() for d in self.detalles.all())

    def __str__(self):
        return f"Servicio {self.id} - {self.vehiculo}"

class DetalleServicio(models.Model):
    servicio = models.ForeignKey(Servicio, on_delete=models.CASCADE, related_name='detalles')
    repuesto = models.ForeignKey(Repuesto, on_delete=models.PROTECT)
    cantidad = models.PositiveIntegerField(default=1)
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2)
    
    class Meta:
        unique_together = ['servicio', 'repuesto']
    
    def subtotal(self):
        return self.cantidad * self.precio_unitario
    
    def __str__(self):
        return f"{self.cantidad}x {self.repuesto}"

class RecordatorioMantenimiento(models.Model):
    vehiculo = models.ForeignKey(Vehiculo, on_delete=models.CASCADE, related_name='recordatorios')
    tipo = models.CharField(max_length=100)
    kilometraje_proximo = models.PositiveIntegerField()
    fecha_proximo = models.DateField()
    notificado = models.BooleanField(default=False)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['fecha_proximo']
        verbose_name_plural = "Recordatorios de mantenimiento"

    def __str__(self):
        return f"Recordatorio para {self.vehiculo} - {self.tipo}"

class PreguntaFrecuente(models.Model):
    CATEGORIAS = (
        ('general', 'General'),
        ('servicios', 'Servicios'),
        ('pagos', 'Pagos'),
        ('citas', 'Citas'),
    )
    
    pregunta = models.TextField()
    respuesta = models.TextField()
    palabras_clave = models.TextField(help_text="Palabras clave separadas por comas")
    categoria = models.CharField(max_length=50, choices=CATEGORIAS, default='general')
    veces_preguntada = models.PositiveIntegerField(default=0)
    activa = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    ultima_actualizacion = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name_plural = "Preguntas frecuentes"
        ordering = ['categoria', 'pregunta']
    
    def __str__(self):
        return self.pregunta[:50] + "..."

class InteraccionChat(models.Model):
    TIPOS = (
        ('consulta', 'Consulta'),
        ('solicitud', 'Solicitud de Servicio'),
        ('complaint', 'Queja'),
        ('suggestion', 'Sugerencia'),
    )
    cliente = models.ForeignKey('Cliente', on_delete=models.CASCADE, related_name='interacciones')
    vehiculo = models.ForeignKey('Vehiculo', on_delete=models.CASCADE, related_name='interacciones', null=True, blank=True)
    conductor = models.ForeignKey('Conductor', on_delete=models.CASCADE, related_name='interacciones', null=True, blank=True)
    tipo = models.CharField(max_length=20, choices=TIPOS, default='consulta')
    mensaje = models.TextField()
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    estado = models.CharField(max_length=20, choices=[
        ('pendiente', 'Pendiente'),
        ('en_progreso', 'En Progreso'),
        ('completado', 'Completado'),
        ('facturado', 'Facturado'),
        ('anulada', 'Anulada')
    ], default='pendiente')
    total = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    metodo_pago = models.CharField(max_length=30, blank=True)
    pagada = models.BooleanField(default=False)
    respuesta_ia = models.TextField(blank=True, null=True, help_text="Respuesta generada por IA (si aplica)")

    def __str__(self):
        return f"Interacción {self.id} - {self.vehiculo} - {self.estado}"

# --- MODELOS ESCALABLES AGREGADOS ---

class ServicioCatalogo(models.Model):
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True)
    precio_base = models.DecimalField(max_digits=10, decimal_places=2)
    frecuencia_km = models.PositiveIntegerField(blank=True, null=True, help_text="Frecuencia recomendada en km")
    frecuencia_meses = models.PositiveIntegerField(blank=True, null=True, help_text="Frecuencia recomendada en meses")
    productos_requeridos = models.ManyToManyField('Repuesto', blank=True, related_name='servicios_catalogo')
    activo = models.BooleanField(default=True)
    
    def __str__(self):
        return self.nombre

class Notificacion(models.Model):
    cliente = models.ForeignKey('Cliente', on_delete=models.CASCADE, related_name='notificaciones')
    conductor = models.ForeignKey('Conductor', on_delete=models.CASCADE, null=True, blank=True, related_name='notificaciones')
    vehiculo = models.ForeignKey('Vehiculo', on_delete=models.CASCADE, null=True, blank=True, related_name='notificaciones')
    mensaje = models.TextField()
    tipo = models.CharField(max_length=50, default='general')
    leida = models.BooleanField(default=False)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_envio = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return f"Notificación para {self.cliente} - {self.tipo}"

class OrdenServicio(models.Model):
    cliente = models.ForeignKey('Cliente', on_delete=models.CASCADE, related_name='ordenes_servicio')
    vehiculo = models.ForeignKey('Vehiculo', on_delete=models.CASCADE, related_name='ordenes_servicio')
    conductor = models.ForeignKey('Conductor', on_delete=models.CASCADE, related_name='ordenes_servicio', null=True, blank=True)
    servicios = models.ManyToManyField('ServicioCatalogo', related_name='ordenes_servicio')
    productos = models.ManyToManyField('Repuesto', blank=True, related_name='ordenes_servicio')
    kilometraje = models.PositiveIntegerField(default=0, help_text="Kilometraje del vehículo al momento del servicio")
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    estado = models.CharField(max_length=20, choices=[
        ('pendiente', 'Pendiente'),
        ('en_progreso', 'En Progreso'),
        ('completada', 'Completada'),
        ('facturada', 'Facturada'),
        ('anulada', 'Anulada')
    ], default='pendiente')
    total = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    metodo_pago = models.CharField(max_length=30, blank=True)
    pagada = models.BooleanField(default=False)

    def __str__(self):
        return f"Orden #{self.id} - {self.vehiculo} - {self.estado}"

class Pago(models.Model):
    orden = models.ForeignKey('OrdenServicio', on_delete=models.CASCADE, related_name='pagos')
    monto = models.DecimalField(max_digits=10, decimal_places=2)
    metodo = models.CharField(max_length=30)
    estado = models.CharField(max_length=20, choices=[
        ('pendiente', 'Pendiente'),
        ('completado', 'Completado'),
        ('fallido', 'Fallido')
    ], default='pendiente')
    fecha_pago = models.DateTimeField(auto_now_add=True)
    referencia = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return f"Pago {self.id} - {self.orden} - {self.estado}"

class Cita(models.Model):
    cliente = models.ForeignKey('Cliente', on_delete=models.CASCADE, related_name='citas')
    vehiculo = models.ForeignKey('Vehiculo', on_delete=models.CASCADE, related_name='citas')
    conductor = models.ForeignKey('Conductor', on_delete=models.CASCADE, related_name='citas')
    servicios = models.ManyToManyField('ServicioCatalogo', related_name='citas')
    fecha_cita = models.DateTimeField()
    estado = models.CharField(max_length=20, choices=[
        ('pendiente', 'Pendiente'),
        ('confirmada', 'Confirmada'),
        ('cancelada', 'Cancelada'),
        ('completada', 'Completada')
    ], default='pendiente')
    notas = models.TextField(blank=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Cita {self.fecha_cita} - {self.vehiculo}"
    TIPOS = (
        ('consulta', 'Consulta'),
        ('solicitud', 'Solicitud de Servicio'),
        ('seguimiento', 'Seguimiento'),
        ('otro', 'Otro'),
    )
    
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE, related_name='interacciones_chat')
    mensaje = models.TextField()
    respuesta = models.TextField(blank=True)
    tipo = models.CharField(max_length=20, choices=TIPOS, default='consulta')
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    resuelta = models.BooleanField(default=False)
    satisfaccion = models.SmallIntegerField(
        null=True, 
        blank=True,
        help_text="Calificación de satisfacción del 1 al 5"
    )
    
    class Meta:
        ordering = ['-fecha_creacion']
        verbose_name_plural = "Interacciones de chat"
    
    def __str__(self):
        return f"Interacción de {self.cliente} - {self.get_tipo_display()}"
