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
    
    # Configuración específica del taller
    configuracion = models.OneToOneField(
        'ConfiguracionTaller', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='cliente_taller'
    )
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
    placa = models.CharField(max_length=10)
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
        unique_together = ['cliente', 'placa']
    
    @property
    def año(self):
        return self.anio

    def __str__(self):
        return f"{self.placa} - {self.marca} {self.modelo}"



class Repuesto(models.Model):
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE, related_name='repuestos')
    nombre = models.CharField(max_length=100)
    codigo = models.CharField(max_length=50, unique=True, blank=True, null=True)
    descripcion = models.TextField(blank=True)
    imagen = models.ImageField(upload_to='repuestos/', blank=True, null=True)
    precio_compra = models.DecimalField(max_digits=10, decimal_places=2)
    precio_venta = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.PositiveIntegerField(default=0)
    stock_minimo = models.PositiveIntegerField(default=5)
    proveedor = models.CharField(max_length=100, blank=True)
    
    # Configuración de IVA específica del producto
    aplicar_iva_producto = models.BooleanField(
        null=True, 
        blank=True, 
        help_text="Override: aplicar IVA a este producto (None = usar configuración del taller)"
    )
    porcentaje_iva_producto = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        null=True, 
        blank=True, 
        help_text="Override: porcentaje IVA específico para este producto"
    )
    
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    
    def get_aplicar_iva(self):
        """Determina si se debe aplicar IVA a este producto"""
        if self.aplicar_iva_producto is not None:
            return self.aplicar_iva_producto
        return self.cliente.configuracion.aplicar_iva if self.cliente.configuracion else False
    
    def get_porcentaje_iva(self):
        """Obtiene el porcentaje de IVA a aplicar"""
        if self.porcentaje_iva_producto is not None:
            return self.porcentaje_iva_producto
        return self.cliente.configuracion.porcentaje_iva if self.cliente.configuracion else 0
    
    def get_precio_sin_iva(self):
        """Calcula el precio sin IVA"""
        if not self.get_aplicar_iva():
            return self.precio_venta
        
        config = self.cliente.configuracion
        if config and config.precios_incluyen_iva:
            # Si los precios incluyen IVA, calculamos el precio base
            porcentaje = self.get_porcentaje_iva()
            return self.precio_venta / (1 + porcentaje / 100)
        else:
            # Si los precios no incluyen IVA, el precio actual es el base
            return self.precio_venta
    
    def get_valor_iva(self):
        """Calcula el valor del IVA"""
        if not self.get_aplicar_iva():
            return 0
        
        precio_sin_iva = self.get_precio_sin_iva()
        porcentaje = self.get_porcentaje_iva()
        return precio_sin_iva * (porcentaje / 100)
    
    def get_precio_con_iva(self):
        """Calcula el precio final con IVA"""
        return self.get_precio_sin_iva() + self.get_valor_iva()
    
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



# --- MODELOS ESCALABLES AGREGADOS ---

class ServicioCatalogo(models.Model):
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE, related_name='servicios_catalogo')
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True)
    precio_base = models.DecimalField(max_digits=10, decimal_places=2)
    frecuencia_km = models.PositiveIntegerField(blank=True, null=True, help_text="Frecuencia recomendada en km")
    frecuencia_meses = models.PositiveIntegerField(blank=True, null=True, help_text="Frecuencia recomendada en meses")
    productos_requeridos = models.ManyToManyField('Repuesto', blank=True, related_name='servicios_catalogo')
    activo = models.BooleanField(default=True)
    
    @property
    def precio(self):
        return self.precio_base
    
    def get_productos_requeridos_ids(self):
        """Retorna los IDs de repuestos asociados como string separado por comas"""
        return ",".join(str(p_id) for p_id in self.productos_requeridos.values_list('id', flat=True))
    
    # Configuración de IVA específica del servicio
    aplicar_iva_servicio = models.BooleanField(
        null=True, 
        blank=True, 
        help_text="Override: aplicar IVA a este servicio (None = usar configuración del taller)"
    )
    porcentaje_iva_servicio = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        null=True, 
        blank=True, 
        help_text="Override: porcentaje IVA específico para este servicio"
    )
    
    fecha_creacion = models.DateTimeField(default=timezone.now)
    
    class Meta:
        verbose_name = 'Servicio del Catálogo'
        verbose_name_plural = 'Servicios del Catálogo'
        ordering = ['nombre']
    
    def get_aplicar_iva(self):
        """Determina si se debe aplicar IVA a este servicio"""
        if self.aplicar_iva_servicio is not None:
            return self.aplicar_iva_servicio
        return self.cliente.configuracion.aplicar_iva if self.cliente.configuracion else False
    
    def get_porcentaje_iva(self):
        """Obtiene el porcentaje de IVA a aplicar"""
        if self.porcentaje_iva_servicio is not None:
            return self.porcentaje_iva_servicio
        return self.cliente.configuracion.porcentaje_iva if self.cliente.configuracion else 0
    
    def get_precio_sin_iva(self):
        """Calcula el precio sin IVA"""
        if not self.get_aplicar_iva():
            return self.precio_base
        
        config = self.cliente.configuracion
        if config and config.precios_incluyen_iva:
            # Si los precios incluyen IVA, calculamos el precio base
            porcentaje = self.get_porcentaje_iva()
            return self.precio_base / (1 + porcentaje / 100)
        else:
            # Si los precios no incluyen IVA, el precio actual es el base
            return self.precio_base
    
    def get_valor_iva(self):
        """Calcula el valor del IVA"""
        if not self.get_aplicar_iva():
            return 0
        
        precio_sin_iva = self.get_precio_sin_iva()
        porcentaje = self.get_porcentaje_iva()
        return precio_sin_iva * (porcentaje / 100)
    
    def get_precio_con_iva(self):
        """Calcula el precio final con IVA"""
        return self.get_precio_sin_iva() + self.get_valor_iva()
    
    def __str__(self):
        return f"{self.nombre} - {self.cliente.nombre}"

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

    def calcular_total(self):
        """Calcula el total de la orden sumando servicios y productos"""
        total_servicios = sum(servicio.precio_base for servicio in self.servicios.all())
        total_productos = sum(producto.precio_venta for producto in self.productos.all())
        return total_servicios + total_productos
    
    def save(self, *args, **kwargs):
        """Actualiza el total automáticamente, maneja inventario según estado y actualiza kilometraje del vehículo"""
        # Detectar cambio de estado si ya existe la orden
        old_estado = None
        if self.pk:
            try:
                old_instance = OrdenServicio.objects.get(pk=self.pk)
                old_estado = old_instance.estado
            except OrdenServicio.DoesNotExist:
                pass
        
        # Actualizar kilometraje del vehículo si es mayor
        if self.vehiculo and self.kilometraje > self.vehiculo.kilometraje:
            self.vehiculo.kilometraje = self.kilometraje
            self.vehiculo.save(update_fields=['kilometraje'])
        
        # Guardar primero para tener ID
        super().save(*args, **kwargs)
        
        # Manejar cambios de estado y inventario
        if self.pk and old_estado != self.estado:
            self._manejar_cambio_estado(old_estado, self.estado)
        
        # Calcular total si ya existe (para relaciones ManyToMany)
        if self.pk:
            nuevo_total = self.calcular_total()
            if self.total != nuevo_total:
                self.total = nuevo_total
                super().save(update_fields=['total'])
    
    def _manejar_cambio_estado(self, old_estado, new_estado):
        """Maneja los cambios de inventario según el cambio de estado"""
        from django.contrib import messages
        
        # Descontar stock al completar la orden
        if old_estado != 'completada' and new_estado == 'completada':
            self.descontar_stock()
            
        # Devolver stock si se anula una orden completada
        elif old_estado == 'completada' and new_estado == 'anulada':
            self.devolver_stock()
    
    def descontar_stock(self):
        """Descuenta stock de productos cuando se completa la orden"""
        productos_sin_stock = []
        
        for producto in self.productos.all():
            if producto.stock > 0:
                producto.stock -= 1
                producto.save()
                
                # Verificar si queda stock bajo
                if producto.stock <= producto.stock_minimo:
                    # Crear notificación de stock bajo
                    self._crear_notificacion_stock_bajo(producto)
            else:
                productos_sin_stock.append(producto.nombre)
        
        # Si hay productos sin stock, crear notificación
        if productos_sin_stock:
            self._crear_notificacion_sin_stock(productos_sin_stock)
    
    def devolver_stock(self):
        """Devuelve stock si se anula una orden completada"""
        for producto in self.productos.all():
            producto.stock += 1
            producto.save()
    
    def _crear_notificacion_stock_bajo(self, producto):
        """Crea notificación cuando un producto tiene stock bajo"""
        try:
            Notificacion.objects.create(
                cliente=self.cliente,
                mensaje=f"⚠️ Stock bajo: {producto.nombre} - Quedan {producto.stock} unidades (Mínimo: {producto.stock_minimo})",
                tipo='stock_bajo'
            )
        except Exception:
            pass  # No fallar si no se puede crear la notificación
    
    def _crear_notificacion_sin_stock(self, productos_sin_stock):
        """Crea notificación cuando productos no tienen stock"""
        try:
            productos_str = ", ".join(productos_sin_stock)
            Notificacion.objects.create(
                cliente=self.cliente,
                mensaje=f"🚫 Sin stock: {productos_str} - Se completó la orden pero estos productos no tenían stock disponible",
                tipo='sin_stock'
            )
        except Exception:
            pass
    
    def puede_cambiar_estado(self, nuevo_estado):
        """Verifica si se puede cambiar al nuevo estado"""
        estados_validos = {
            'pendiente': ['en_progreso', 'anulada'],
            'en_progreso': ['completada', 'pendiente', 'anulada'],
            'completada': ['facturada', 'anulada'],
            'facturada': ['anulada'],  # Solo se puede anular
            'anulada': []  # No se puede cambiar desde anulada
        }
        
        return nuevo_estado in estados_validos.get(self.estado, [])
    
    def get_siguiente_estados(self):
        """Obtiene los estados válidos para transición"""
        estados_siguientes = {
            'pendiente': [('en_progreso', 'Iniciar Trabajo'), ('anulada', 'Anular')],
            'en_progreso': [('completada', 'Completar'), ('pendiente', 'Pausar'), ('anulada', 'Anular')],
            'completada': [('facturada', 'Facturar'), ('anulada', 'Anular')],
            'facturada': [('anulada', 'Anular')],
            'anulada': []
        }
        
        return estados_siguientes.get(self.estado, [])

    def __str__(self):
        return f"Orden #{self.id} - {self.vehiculo} - {self.estado}"

class Notificacion(models.Model):
    """Modelo para notificaciones del sistema"""
    TIPOS_NOTIFICACION = [
        ('stock_bajo', 'Stock Bajo'),
        ('sin_stock', 'Sin Stock'),
        ('orden_completada', 'Orden Completada'),
        ('general', 'General'),
    ]
    
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE, related_name='notificaciones')
    mensaje = models.TextField()
    tipo = models.CharField(max_length=20, choices=TIPOS_NOTIFICACION, default='general')
    leida = models.BooleanField(default=False)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_lectura = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-fecha_creacion']
        verbose_name = 'Notificación'
        verbose_name_plural = 'Notificaciones'
    
    def marcar_como_leida(self):
        """Marca la notificación como leída"""
        if not self.leida:
            self.leida = True
            self.fecha_lectura = timezone.now()
            self.save()
    
    def __str__(self):
        return f"{self.get_tipo_display()} - {self.cliente} - {self.fecha_creacion.strftime('%d/%m/%Y %H:%M')}"

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
    mensaje = models.TextField(blank=True, null=True)  # Campo temporal para compatibilidad
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-fecha_cita']
        verbose_name = 'Cita'
        verbose_name_plural = 'Citas'

    def __str__(self):
        return f"Cita {self.fecha_cita.strftime('%d/%m/%Y %H:%M')} - {self.vehiculo}"
    
    def get_servicios_display(self):
        """Retorna los servicios como string separado por comas"""
        return ", ".join([s.nombre for s in self.servicios.all()])
    
    def get_duracion_estimada(self):
        """Calcula la duración estimada total de todos los servicios"""
        # Como no hay campo duracion_estimada, retornamos un valor por defecto
        # o calculamos basado en el número de servicios
        num_servicios = self.servicios.count()
        return num_servicios * 60  # 60 minutos por servicio por defecto
    
    def get_precio_estimado(self):
        """Calcula el precio estimado total de todos los servicios"""
        total_precio = sum([s.get_precio_con_iva() for s in self.servicios.all()])
        return total_precio

class InteraccionChat(models.Model):
    TIPOS = (
        ('consulta', 'Consulta'),
        ('solicitud', 'Solicitud de Servicio'),
        ('seguimiento', 'Seguimiento'),
        ('otro', 'Otro'),
    )
    
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE, related_name='interacciones_chat')
    conductor = models.ForeignKey('Conductor', on_delete=models.CASCADE, null=True, blank=True, related_name='interacciones_chat')
    telefono = models.CharField(max_length=20, help_text="Número de teléfono del contacto")
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
        verbose_name = "Interacción de chat"
        verbose_name_plural = "Interacciones de chat"
    
    def __str__(self):
        conductor_name = self.conductor.nombre if self.conductor else "Desconocido"
        return f"Chat {conductor_name} - {self.get_tipo_display()} - {self.fecha_creacion.strftime('%d/%m/%Y %H:%M')}"


class ConfiguracionTaller(models.Model):
    """Configuración específica para cada taller/sucursal"""
    
    # Información básica del taller
    nombre = models.CharField(max_length=100, help_text="Nombre del taller")
    codigo = models.CharField(max_length=20, unique=True, help_text="Código único del taller (ej: TALLER-001)")
    
    # Información de contacto
    telefono_principal = models.CharField(
        max_length=20,
        help_text="Número principal del taller con código de país"
    )
    telefono_whatsapp = models.CharField(
        max_length=20,
        blank=True,
        help_text="Número de WhatsApp (si es diferente al principal)"
    )
    email = models.EmailField(help_text="Email del taller")
    website = models.URLField(blank=True, help_text="Sitio web del taller")
    
    # Dirección
    direccion = models.TextField(help_text="Dirección completa del taller")
    ciudad = models.CharField(max_length=50)
    pais = models.CharField(max_length=50, default="Ecuador")
    
    # Horarios
    horarios = models.TextField(
        default="Lun-Vie 8AM-6PM, Sáb 8AM-2PM",
        help_text="Horarios de atención"
    )
    
    # Configuración de mensajería
    usar_whatsapp = models.BooleanField(default=True)
    usar_telegram = models.BooleanField(default=False)
    usar_emojis = models.BooleanField(default=True)
    incluir_firma = models.BooleanField(default=True)
    
    # Configuración de recordatorios
    dias_recordatorio_mantenimiento = models.IntegerField(default=7)
    dias_recordatorio_urgente = models.IntegerField(default=3)
    hora_inicio_envios = models.TimeField(default="08:00")
    hora_fin_envios = models.TimeField(default="18:00")
    
    # Estado
    activo = models.BooleanField(default=True)
    es_principal = models.BooleanField(default=False, help_text="Taller principal por defecto")
    
    # Configuración de IVA
    aplicar_iva = models.BooleanField(default=False, help_text="Habilitar cálculo de IVA en este taller")
    porcentaje_iva = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        default=15.00, 
        help_text="Porcentaje de IVA (ej: 15.00 para 15%)"
    )
    precios_incluyen_iva = models.BooleanField(
        default=False, 
        help_text="Los precios actuales ya incluyen IVA"
    )
    mostrar_desglose_iva = models.BooleanField(
        default=True, 
        help_text="Mostrar desglose de IVA en PDFs y facturas"
    )
    
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Configuración de Taller"
        verbose_name_plural = "Configuraciones de Talleres"
        ordering = ['nombre']
    
    def __str__(self):
        return f"{self.nombre} ({self.codigo})"
    
    def get_telefono_whatsapp(self):
        """Obtiene el número de WhatsApp a usar"""
        return self.telefono_whatsapp if self.telefono_whatsapp else self.telefono_principal
    
    def get_firma_mensaje(self):
        """Genera la firma para los mensajes"""
        if not self.incluir_firma:
            return ""
        
        firma = f"\n\n---\n🔧 {self.nombre}\n"
        firma += f"📞 {self.telefono_principal}\n"
        
        if self.website:
            firma += f"🌐 {self.website}\n"
        
        firma += f"📍 {self.direccion}\n"
        firma += f"⏰ {self.horarios}"
        
        return firma
    
    @classmethod
    def get_taller_principal(cls):
        """Obtiene el taller marcado como principal"""
        try:
            return cls.objects.filter(es_principal=True, activo=True).first()
        except cls.DoesNotExist:
            return cls.objects.filter(activo=True).first()
    
    @classmethod
    def get_taller_por_codigo(cls, codigo):
        """Obtiene un taller por su código"""
        try:
            return cls.objects.get(codigo=codigo, activo=True)
        except cls.DoesNotExist:
            return None
    
    def calcular_iva(self, precio_base):
        """Calcula el valor del IVA para un precio base"""
        if not self.aplicar_iva:
            return 0
        return precio_base * (self.porcentaje_iva / 100)
    
    def calcular_precio_con_iva(self, precio_base):
        """Calcula el precio final incluyendo IVA"""
        return precio_base + self.calcular_iva(precio_base)
    
    def calcular_precio_sin_iva(self, precio_con_iva):
        """Calcula el precio base desde un precio que incluye IVA"""
        if not self.aplicar_iva:
            return precio_con_iva
        return precio_con_iva / (1 + self.porcentaje_iva / 100)
    
    def save(self, *args, **kwargs):
        # Si se marca como principal, desmarcar otros
        if self.es_principal:
            ConfiguracionTaller.objects.filter(es_principal=True).update(es_principal=False)
        
        super().save(*args, **kwargs)
