from django import forms
from django.core.exceptions import ValidationError
from .models import Vehiculo, Repuesto, Conductor, Cliente, PreguntaFrecuente, DetalleServicio, OrdenServicio, ServicioCatalogo, ConfiguracionTaller

class KilometrajeWidget(forms.NumberInput):
    """Widget personalizado para manejar kilometraje con formato de miles"""
    
    def format_value(self, value):
        """Formatear el valor para mostrar con comas como separador de miles"""
        if value is None or value == '':
            return ''
        try:
            # Convertir a entero y formatear con comas
            return f"{int(value):,}"
        except (ValueError, TypeError):
            return value
    
    def value_from_datadict(self, data, files, name):
        """Procesar el valor del formulario removiendo comas antes de guardar"""
        value = data.get(name)
        if value:
            # Remover comas y espacios para convertir a número
            value = str(value).replace(',', '').replace(' ', '')
        return value

class OrdenServicioForm(forms.ModelForm):
    class Meta:
        model = OrdenServicio
        fields = ['vehiculo', 'conductor', 'kilometraje', 'servicios', 'productos', 'estado', 'metodo_pago', 'total']
        widgets = {
            'vehiculo': forms.Select(attrs={'class': 'form-select', 'id': 'id_vehiculo'}),
            'conductor': forms.HiddenInput(attrs={'id': 'id_conductor'}),
            'servicios': forms.SelectMultiple(attrs={'class': 'form-select', 'id': 'id_servicios'}),
            'productos': forms.SelectMultiple(attrs={'class': 'form-select', 'id': 'id_productos'}),
            'estado': forms.Select(attrs={'class': 'form-select', 'id': 'id_estado'}),
            'metodo_pago': forms.TextInput(attrs={'class': 'form-control', 'id': 'id_metodo_pago'}),
            'kilometraje': KilometrajeWidget(attrs={'class': 'form-control', 'id': 'id_kilometraje', 'placeholder': 'Ej: 35,000'}),
            'total': forms.NumberInput(attrs={'class': 'form-control', 'readonly': True, 'id': 'id_total'}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        self.fields['conductor'].required = False

        if user and hasattr(user, 'perfilusuario') and user.perfilusuario.cliente:
            cliente = user.perfilusuario.cliente
            self.fields['vehiculo'].queryset = Vehiculo.objects.filter(cliente=cliente).distinct().order_by('placa')
            self.fields['productos'].queryset = Repuesto.objects.filter(cliente=cliente).distinct().order_by('nombre')
            self.fields['servicios'].queryset = ServicioCatalogo.objects.filter(cliente=cliente).distinct().order_by('nombre')

        # Precargar conductor si ya existe
        if self.instance.pk and self.instance.vehiculo:
            self.fields['vehiculo'].initial = self.instance.vehiculo
            if self.instance.vehiculo.conductor:
                self.fields['conductor'].initial = self.instance.vehiculo.conductor.id

class ClienteForm(forms.ModelForm):
    class Meta:
        model = Cliente
        fields = ['nombre', 'telefono', 'correo', 'direccion']

class ConductorForm(forms.ModelForm):
    class Meta:
        model = Conductor
        exclude = ['cliente', 'fecha_registro']

# Formulario exclusivo para la vista de edición con estilos
class ConductorUpdateForm(ConductorForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            field.widget.attrs.update({'class': 'form-control', 'autocomplete': 'off'})

class VehiculoForm(forms.ModelForm):
    class Meta:
        model = Vehiculo
        # Incluimos 'conductor', pero lo filtraremos en __init__
        exclude = ['cliente', 'fecha_ultimo_servicio', 'fecha_creacion', 'activo']
        widgets = {
            'anio': forms.NumberInput(attrs={'min': 1980, 'max': 2025}),
            'kilometraje': KilometrajeWidget(attrs={'placeholder': 'Ej: 150,000'}),
        }

    def __init__(self, *args, **kwargs):
        # Obtenemos el usuario para poder filtrar los conductores
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        if user and hasattr(user, 'perfilusuario') and user.perfilusuario.cliente:
            # Filtramos el campo 'conductor' para mostrar solo los del cliente del usuario
            self.fields['conductor'].queryset = Conductor.objects.filter(cliente=user.perfilusuario.cliente)
            self.fields['conductor'].required = False # Hacemos el campo no obligatorio
        else:
            # Si no hay usuario o cliente, no mostramos ningún conductor
            self.fields['conductor'].queryset = Conductor.objects.none()
            self.fields['conductor'].required = False


class RepuestoForm(forms.ModelForm):
    class Meta:
        model = Repuesto
        fields = '__all__'
        widgets = {
            'aplicar_iva_producto': forms.Select(choices=[
                ('', '--- Usar configuración del taller ---'),
                (True, 'Sí, aplicar IVA'),
                (False, 'No aplicar IVA')
            ], attrs={'class': 'form-select'}),
            'porcentaje_iva_producto': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'max': '100',
                'placeholder': 'Ej: 15.00'
            })
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        self.editing = kwargs.pop('editing', False)
        instance = kwargs.get('instance', None)
        super().__init__(*args, **kwargs)

        # Eliminar el campo cliente del formulario ya que se asigna automáticamente
        if 'cliente' in self.fields:
            del self.fields['cliente']

        # Configurar campos de IVA como opcionales
        if 'aplicar_iva_producto' in self.fields:
            self.fields['aplicar_iva_producto'].required = False
            self.fields['aplicar_iva_producto'].help_text = 'Dejar vacío para usar la configuración del taller'
            
        if 'porcentaje_iva_producto' in self.fields:
            self.fields['porcentaje_iva_producto'].required = False
            self.fields['porcentaje_iva_producto'].help_text = 'Solo si se aplica IVA específico para este producto'

        # Aplicar clases de Bootstrap a todos los campos
        for field_name, field in self.fields.items():
            # Saltar campos que ya tienen widgets configurados
            if field_name in ['aplicar_iva_producto', 'porcentaje_iva_producto']:
                continue
                
            # Para campos de selección, usar 'form-select'
            if isinstance(field.widget, forms.Select):
                field.widget.attrs.update({'class': 'form-select'})
            # Para campos de número, texto, etc., usar 'form-control'
            else:
                field.widget.attrs.update({'class': 'form-control'})

# --- Formulario para ServicioCatalogo ---
class ServicioCatalogoForm(forms.ModelForm):
    class Meta:
        model = ServicioCatalogo
        fields = '__all__'

    def clean_codigo(self):
        codigo = self.cleaned_data.get('codigo')

        # Si está editando y no cambió el código, no validar
        if self.editing and self.instance and codigo == self.instance.codigo:
            return codigo

        # Permitir dejar el campo vacío durante edición
        if self.editing and not codigo:
            return self.instance.codigo

        # Validar unicidad
        if codigo:
            queryset = Repuesto.objects.filter(codigo=codigo)
            if self.instance and self.instance.pk:
                queryset = queryset.exclude(pk=self.instance.pk)
            if queryset.exists():
                raise forms.ValidationError('Ya existe un repuesto con este código.')

        return codigo

    def save(self, commit=True):
        # Mantener código actual si se deja vacío durante edición
        if self.editing and self.instance and not self.cleaned_data.get('codigo'):
            self.cleaned_data['codigo'] = self.instance.codigo

        # Asignar cliente automáticamente
        if self.user and hasattr(self.user, 'perfilusuario') and hasattr(self.user.perfilusuario, 'cliente'):
            self.instance.cliente = self.user.perfilusuario.cliente

        return super().save(commit=commit)

    class Meta:
        model = Repuesto
        exclude = ['cliente', 'fecha_creacion']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'codigo': forms.TextInput(attrs={'class': 'form-control'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'imagen': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'precio_compra': forms.NumberInput(attrs={'class': 'form-control'}),
            'precio_venta': forms.NumberInput(attrs={'class': 'form-control'}),
            'stock': forms.NumberInput(attrs={'class': 'form-control'}),
            'stock_minimo': forms.NumberInput(attrs={'class': 'form-control'}),
            'proveedor': forms.TextInput(attrs={'class': 'form-control'}),
        }



class PreguntaFrecuenteForm(forms.ModelForm):
    class Meta:
        model = PreguntaFrecuente
        exclude = ['veces_preguntada', 'fecha_creacion', 'ultima_actualizacion']

class DetalleServicioForm(forms.ModelForm):
    class Meta:
        model = DetalleServicio
        fields = ['repuesto', 'cantidad', 'precio_unitario']
        widgets = {
            'cantidad': forms.NumberInput(attrs={'min': 1, 'max': 999}),
            'precio_unitario': forms.NumberInput(attrs={'step': '0.01'}),
        }

    def __init__(self, *args, **kwargs):
        servicio = kwargs.pop('servicio', None)
        super().__init__(*args, **kwargs)
        if servicio and hasattr(servicio, 'cliente'):
            self.fields['repuesto'].queryset = Repuesto.objects.filter(cliente=servicio.cliente)

    def clean(self):
        cleaned_data = super().clean()
        cantidad = cleaned_data.get('cantidad')
        repuesto = cleaned_data.get('repuesto')
        
        if cantidad and repuesto:
            if cantidad > repuesto.stock:
                raise forms.ValidationError(
                    f'No hay suficiente stock. Hay {repuesto.stock} unidades disponibles'
                )
            if cantidad < 1:
                raise forms.ValidationError('La cantidad debe ser mayor a 0')

    def save(self, commit=True):
        detalle = super().save(commit=False)
        if commit:
            detalle.save()
        return detalle

from django.contrib.auth.models import User
from .models import PerfilUsuario


class RepuestoForm(forms.ModelForm):
    class Meta:
        model = Repuesto
        exclude = ['cliente', 'fecha_creacion']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'codigo': forms.TextInput(attrs={'class': 'form-control'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'imagen': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'precio_compra': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'precio_venta': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'stock': forms.NumberInput(attrs={'class': 'form-control'}),
            'stock_minimo': forms.NumberInput(attrs={'class': 'form-control'}),
            'proveedor': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        # Extraer argumentos personalizados
        self.user = kwargs.pop('user', None)
        self.editing = kwargs.pop('editing', False)
        super().__init__(*args, **kwargs)

    def clean_codigo(self):
        codigo = self.cleaned_data.get('codigo')
        
        # Si está editando y no cambió el código, no validar
        if self.editing and self.instance and codigo == self.instance.codigo:
            return codigo
            
        # Permitir dejar el campo vacío durante edición
        if self.editing and not codigo:
            return self.instance.codigo if self.instance else codigo
            
        # Validar unicidad
        if codigo:
            queryset = Repuesto.objects.filter(codigo=codigo)
            if self.instance and self.instance.pk:
                queryset = queryset.exclude(pk=self.instance.pk)
            if queryset.exists():
                raise forms.ValidationError('Ya existe un repuesto con este código.')
        return codigo

    def save(self, commit=True):
        # Mantener código actual si se deja vacío durante edición
        if self.editing and self.instance and not self.cleaned_data.get('codigo'):
            self.cleaned_data['codigo'] = self.instance.codigo
            
        # Asignar cliente automáticamente si se proporciona usuario
        if self.user and hasattr(self.user, 'perfilusuario') and hasattr(self.user.perfilusuario, 'cliente'):
            self.instance.cliente = self.user.perfilusuario.cliente
            
        return super().save(commit=commit)

class PerfilUsuarioForm(forms.ModelForm):
    class Meta:
        model = PerfilUsuario
        fields = ['rol', 'conductor']
        labels = {
            'rol': 'Rol de usuario',
            'conductor': 'Conductor asociado (opcional)',
        }
        widgets = {
            'rol': forms.Select(attrs={'class': 'form-select'}),
            'conductor': forms.Select(attrs={'class': 'form-select'}),
        }

class ServicioCatalogoForm(forms.ModelForm):
    class Meta:
        model = ServicioCatalogo
        exclude = ['cliente', 'fecha_creacion']
        widgets = {
            'nombre': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: Cambio de aceite, Revisión de frenos...'
            }),
            'descripcion': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Describe detalladamente el servicio...'
            }),
            'precio_base': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'placeholder': '0.00'
            }),
            'frecuencia_km': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1',
                'placeholder': 'Ej: 5000, 10000...'
            }),
            'frecuencia_meses': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1',
                'max': '60',
                'placeholder': 'Ej: 3, 6, 12...'
            }),
            'productos_requeridos': forms.CheckboxSelectMultiple(attrs={
                'class': 'form-check-input'
            }),
            'activo': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'aplicar_iva_servicio': forms.Select(choices=[
                ('', '--- Usar configuración del taller ---'),
                (True, 'Sí, aplicar IVA'),
                (False, 'No aplicar IVA')
            ], attrs={'class': 'form-select'}),
            'porcentaje_iva_servicio': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'max': '100',
                'placeholder': 'Ej: 15.00'
            })
        }
        labels = {
            'nombre': 'Nombre del Servicio',
            'descripcion': 'Descripción Detallada',
            'precio_base': 'Precio Base ($)',
            'frecuencia_km': 'Frecuencia en Kilómetros',
            'frecuencia_meses': 'Frecuencia en Meses',
            'productos_requeridos': 'Repuestos/Productos Requeridos',
            'activo': 'Servicio Activo',
            'aplicar_iva_servicio': 'Aplicar IVA a este Servicio',
            'porcentaje_iva_servicio': 'Porcentaje de IVA (%)'
        }
        help_texts = {
            'frecuencia_km': 'Cada cuántos kilómetros se recomienda este servicio',
            'frecuencia_meses': 'Cada cuántos meses se recomienda este servicio',
            'productos_requeridos': 'Selecciona los repuestos que se usan en este servicio',
            'aplicar_iva_servicio': 'Dejar vacío para usar la configuración del taller',
            'porcentaje_iva_servicio': 'Solo si se aplica IVA específico para este servicio'
        }
    
    def __init__(self, *args, **kwargs):
        cliente = kwargs.pop('cliente', None)
        super().__init__(*args, **kwargs)
        
        if cliente:
            # Filtrar productos solo del cliente
            self.fields['productos_requeridos'].queryset = Repuesto.objects.filter(
                cliente=cliente, 
                stock__gt=0
            ).order_by('nombre')
        else:
            self.fields['productos_requeridos'].queryset = Repuesto.objects.none()
            
        # Configurar campos de IVA como opcionales
        self.fields['aplicar_iva_servicio'].required = False
        self.fields['porcentaje_iva_servicio'].required = False
    
    def clean_precio_base(self):
        precio = self.cleaned_data.get('precio_base')
        if precio and precio <= 0:
            raise ValidationError('El precio debe ser mayor a 0')
        return precio
    
    def clean(self):
        cleaned_data = super().clean()
        frecuencia_km = cleaned_data.get('frecuencia_km')
        frecuencia_meses = cleaned_data.get('frecuencia_meses')
        
        if not frecuencia_km and not frecuencia_meses:
            raise ValidationError(
                'Debe especificar al menos una frecuencia (kilómetros o meses)'
            )
        
        return cleaned_data
    
    def save(self, commit=True):
        servicio = super().save(commit=False)
        if commit:
            servicio.save()
            self.save_m2m()  # Guardar relaciones many-to-many
        return servicio


# --- Formulario para Configuración de Taller (WhatsApp) ---
class ConfiguracionTallerForm(forms.ModelForm):
    class Meta:
        model = ConfiguracionTaller
        fields = [
            'nombre', 'telefono_principal', 'telefono_whatsapp', 
            'email', 'direccion', 'horarios', 'usar_whatsapp', 
            'usar_telegram'
        ]
        widgets = {
            'nombre': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nombre del taller'
            }),
            'telefono_principal': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: 0968192046'
            }),
            'telefono_whatsapp': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Número para WhatsApp (opcional)'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'correo@taller.com'
            }),
            'direccion': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Dirección completa del taller'
            }),
            'horarios': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: Lun-Vie 8AM-6PM, Sáb 8AM-2PM'
            }),
            'usar_whatsapp': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'usar_telegram': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }
        labels = {
            'nombre': 'Nombre del Taller',
            'telefono_principal': 'Teléfono Principal',
            'telefono_whatsapp': 'Teléfono WhatsApp',
            'email': 'Correo Electrónico',
            'direccion': 'Dirección',
            'horarios': 'Horarios de Atención',
            'usar_whatsapp': 'Habilitar WhatsApp',
            'usar_telegram': 'Habilitar Telegram',
        }
        help_texts = {
            'telefono_whatsapp': 'Si no se especifica, se usará el teléfono principal',
            'usar_whatsapp': 'Activar para enviar mensajes por WhatsApp',
            'usar_telegram': 'Activar para enviar mensajes por Telegram (próximamente)',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Hacer algunos campos opcionales
        self.fields['telefono_whatsapp'].required = False
        self.fields['direccion'].required = False
        self.fields['horarios'].required = False
        
    def clean_telefono_principal(self):
        telefono = self.cleaned_data.get('telefono_principal')
        if telefono:
            # Remover espacios y caracteres especiales
            telefono = ''.join(filter(str.isdigit, telefono))
            if len(telefono) < 7:
                raise ValidationError('El teléfono debe tener al menos 7 dígitos')
        return telefono
    
    def clean_telefono_whatsapp(self):
        telefono = self.cleaned_data.get('telefono_whatsapp')
        if telefono:
            # Remover espacios y caracteres especiales
            telefono = ''.join(filter(str.isdigit, telefono))
            if len(telefono) < 7:
                raise ValidationError('El teléfono WhatsApp debe tener al menos 7 dígitos')
        return telefono
