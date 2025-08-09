from django import forms
from .models import Vehiculo, Repuesto, Conductor, Cliente, PreguntaFrecuente, DetalleServicio, OrdenServicio, ServicioCatalogo

class OrdenServicioForm(forms.ModelForm):
    class Meta:
        model = OrdenServicio
        fields = ['vehiculo', 'conductor', 'kilometraje', 'servicios', 'productos', 'estado', 'metodo_pago']
        widgets = {
            'vehiculo': forms.Select(attrs={'class': 'form-select select2-single'}),
            'conductor': forms.HiddenInput(),
            'servicios': forms.SelectMultiple(attrs={'class': 'form-select select2-multiple'}),
            'productos': forms.SelectMultiple(attrs={'class': 'form-select select2-multiple'}),
            'estado': forms.Select(attrs={'class': 'form-select'}),
            'metodo_pago': forms.TextInput(attrs={'class': 'form-control'}),
            'kilometraje': forms.NumberInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        self.fields['conductor'].required = False

        if user and hasattr(user, 'perfilusuario') and user.perfilusuario.cliente:
            cliente = user.perfilusuario.cliente
            self.fields['vehiculo'].queryset = Vehiculo.objects.filter(cliente=cliente)
            self.fields['productos'].queryset = Repuesto.objects.filter(cliente=cliente)

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

class VehiculoForm(forms.ModelForm):
    class Meta:
        model = Vehiculo
        # Incluimos 'conductor', pero lo filtraremos en __init__
        exclude = ['cliente', 'fecha_ultimo_servicio', 'fecha_creacion', 'activo']
        widgets = {
            'anio': forms.NumberInput(attrs={'min': 1980, 'max': 2025}),
            'kilometraje': forms.NumberInput(attrs={'placeholder': 'Ej: 150000'}),
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
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        self.editing = kwargs.pop('editing', False)
        instance = kwargs.get('instance', None)
        super().__init__(*args, **kwargs)

        # Eliminar el campo cliente del formulario ya que se asigna automáticamente
        if 'cliente' in self.fields:
            del self.fields['cliente']

        # Si estamos editando, permitir dejar el campo código vacío para mantener el actual
        if instance and self.editing:
            self.fields['codigo'].required = False
            self.fields['codigo'].help_text = 'Dejar en blanco para mantener el código actual.'

        # Estilizar campos con Bootstrap
        for field in self.fields.values():
            if not isinstance(field.widget, forms.FileInput):
                field.widget.attrs.update({'class': 'form-control'})

        # Ajuste específico para 'categoria'
        if 'categoria' in self.fields:
            self.fields['categoria'].widget.attrs.update({
                'class': 'form-select',
                'data-placeholder': 'Seleccione una categoría',
                'data-allow-clear': 'true'
            })

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
            'categoria': forms.Select(attrs={'class': 'form-select'}),
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
