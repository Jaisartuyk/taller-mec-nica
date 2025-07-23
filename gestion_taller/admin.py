from django.contrib import admin
from .models import Vehiculo, Repuesto, Servicio, Conductor, Cliente, PerfilUsuario, PreguntaFrecuente, ServicioCatalogo, Notificacion, OrdenServicio, Pago, Cita, CategoriaRepuesto
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User

# Define el Inline para el PerfilUsuario
class PerfilUsuarioInline(admin.StackedInline):
    model = PerfilUsuario
    can_delete = False
    verbose_name_plural = 'Perfil'

# Define el nuevo UserAdmin
class UserAdmin(BaseUserAdmin):
    inlines = (PerfilUsuarioInline, )

# Re-register UserAdmin
admin.site.unregister(User)
admin.site.register(User, UserAdmin)

@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'correo', 'telefono', 'direccion', 'fecha_registro', 'logo_preview')
    search_fields = ('nombre', 'correo', 'telefono')
    list_filter = ('fecha_registro',)
    fieldsets = (
        (None, {
            'fields': ('nombre', 'telefono', 'correo', 'direccion', 'logo')
        }),
        ('Preferencias', {
            'fields': ('preferencias_notificacion',)
        }),
    )
    readonly_fields = ('logo_preview',)

    def logo_preview(self, obj):
        if obj.logo:
            return f'<img src="{obj.logo.url}" width="50" height="50" style="object-fit:contain;" />'
        return "Sin logo"
    logo_preview.allow_tags = True
    logo_preview.short_description = 'Logo'

@admin.register(PerfilUsuario)
class PerfilUsuarioAdmin(admin.ModelAdmin):
    list_display = ('user', 'rol', 'cliente', 'conductor', 'get_username')
    search_fields = ('user__username', 'user__email', 'cliente__nombre')
    list_filter = ('rol', 'cliente')
    
    def get_username(self, obj):
        return obj.user.username
    get_username.short_description = 'Usuario'

@admin.register(Conductor)
class ConductorAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'telefono', 'correo', 'direccion', 'cliente', 'fecha_registro')
    search_fields = ('nombre', 'telefono', 'correo')
    list_filter = ('cliente', 'fecha_registro')
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        if hasattr(request.user, 'perfilusuario') and request.user.perfilusuario.cliente:
            return qs.filter(cliente=request.user.perfilusuario.cliente)
        return qs.none()

@admin.register(Vehiculo)
class VehiculoAdmin(admin.ModelAdmin):
    list_display = ('placa', 'marca', 'modelo', 'anio', 'conductor', 'cliente', 'fecha_creacion')


@admin.register(ServicioCatalogo)
class ServicioCatalogoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'precio_base', 'frecuencia_km', 'frecuencia_meses', 'activo')
    search_fields = ('nombre',)
    list_filter = ('activo',)

@admin.register(Notificacion)
class NotificacionAdmin(admin.ModelAdmin):
    list_display = ('cliente', 'conductor', 'vehiculo', 'tipo', 'leida', 'fecha_envio')
    search_fields = ('mensaje', 'cliente__nombre')
    list_filter = ('tipo', 'leida', 'fecha_envio')

@admin.register(OrdenServicio)
class OrdenServicioAdmin(admin.ModelAdmin):
    list_display = ('id', 'vehiculo', 'conductor', 'estado', 'total', 'pagada', 'fecha_creacion')
    search_fields = ('vehiculo__placa', 'conductor__nombre')
    list_filter = ('estado', 'pagada', 'fecha_creacion')

@admin.register(Pago)
class PagoAdmin(admin.ModelAdmin):
    list_display = ('id', 'orden', 'monto', 'metodo', 'estado', 'fecha_pago')
    search_fields = ('orden__id', 'referencia')
    list_filter = ('estado', 'metodo', 'fecha_pago')

@admin.register(Cita)
class CitaAdmin(admin.ModelAdmin):
    list_display = ('id', 'vehiculo', 'conductor', 'fecha_cita', 'estado')
    search_fields = ('vehiculo__placa', 'conductor__nombre')
    list_filter = ('estado', 'fecha_cita')

    search_fields = ('placa', 'marca', 'modelo')
    list_filter = ('cliente', 'conductor', 'fecha_creacion')
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        if hasattr(request.user, 'perfilusuario') and request.user.perfilusuario.cliente:
            return qs.filter(cliente=request.user.perfilusuario.cliente)
        return qs.none()

@admin.register(CategoriaRepuesto)
class CategoriaRepuestoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'descripcion')
    search_fields = ('nombre',)

@admin.register(Repuesto)
class RepuestoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'codigo', 'categoria', 'precio_venta', 'stock', 'cliente', 'fecha_creacion', 'imagen_preview')
    search_fields = ('nombre', 'codigo')
    list_filter = ('cliente', 'categoria', 'fecha_creacion')
    readonly_fields = ('imagen_preview',)
    fieldsets = (
        (None, {
            'fields': ('cliente', 'categoria', 'nombre', 'codigo', 'descripcion', 'imagen', 'imagen_preview', 'precio_compra', 'precio_venta', 'stock', 'stock_minimo', 'proveedor')
        }),
    )
    def imagen_preview(self, obj):
        if obj.imagen:
            return f'<img src="{obj.imagen.url}" width="60" height="60" style="object-fit:contain;" />'
        return "Sin imagen"
    imagen_preview.allow_tags = True
    imagen_preview.short_description = 'Imagen'
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        if hasattr(request.user, 'perfilusuario') and request.user.perfilusuario.cliente:
            return qs.filter(cliente=request.user.perfilusuario.cliente)
        return qs.none()

@admin.register(Servicio)
class ServicioAdmin(admin.ModelAdmin):
    list_display = ('vehiculo', 'conductor', 'fecha_servicio', 'estado', 'costo_total')
    search_fields = ('vehiculo__placa', 'conductor__nombre')
    list_filter = ('cliente', 'estado', 'fecha_servicio')
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        if hasattr(request.user, 'perfilusuario') and request.user.perfilusuario.cliente:
            return qs.filter(cliente=request.user.perfilusuario.cliente)
        return qs.none()

@admin.register(PreguntaFrecuente)
class PreguntaFrecuenteAdmin(admin.ModelAdmin):
    list_display = ('pregunta', 'categoria', 'veces_preguntada', 'activa')
    search_fields = ('pregunta', 'categoria')
    list_filter = ('categoria', 'activa')
