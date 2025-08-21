from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.template.loader import get_template
from decimal import Decimal
import io
from .models import Vehiculo, Repuesto, ServicioCatalogo, PerfilUsuario, Conductor, User, OrdenServicio, Notificacion, Pago
from django.db import models
from .forms import VehiculoForm, RepuestoForm, PerfilUsuarioForm, ConductorForm, OrdenServicioForm, ServicioCatalogoForm, ConductorUpdateForm
from .models import Conductor
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.contrib.auth.models import User
from django.shortcuts import redirect
from django.db.models import F
from django.http import JsonResponse, HttpResponse, HttpResponseRedirect
from django.template.loader import render_to_string
from django.views.decorators.http import require_GET

from django.http import HttpResponse

# --- STUBS PARA VISTAS FALTANTES ---
def home(request):
    return HttpResponse("Vista home (stub)")

class PerfilUsuarioView(ListView):
    def get(self, request, *args, **kwargs):
        return HttpResponse("PerfilUsuarioView (stub)")

class RepuestoListView(ListView):
    def get(self, request, *args, **kwargs):
        return HttpResponse("RepuestoListView (stub)")

# Definiciones de RepuestoCreateView y RepuestoUpdateView movidas más abajo

class RepuestoDeleteView(DeleteView):
    def get(self, request, *args, **kwargs):
        return HttpResponse("RepuestoDeleteView (stub)")

class ConductorListView(ListView):
    def get(self, request, *args, **kwargs):
        return HttpResponse("ConductorListView (stub)")

class ConductorCreateView(CreateView):
    def get(self, request, *args, **kwargs):
        return HttpResponse("ConductorCreateView (stub)")

class ConductorUpdateView(UpdateView):
    def get(self, request, *args, **kwargs):
        return HttpResponse("ConductorUpdateView (stub)")

class ConductorDeleteView(DeleteView):
    def get(self, request, *args, **kwargs):
        return HttpResponse("ConductorDeleteView (stub)")

class OrdenServicioCreateView(CreateView):
    def get(self, request, *args, **kwargs):
        return HttpResponse("OrdenServicioCreateView (stub)")

class OrdenServicioListView(ListView):
    def get(self, request, *args, **kwargs):
        return HttpResponse("OrdenServicioListView (stub)")

class OrdenServicioDetailView(ListView):
    def get(self, request, *args, **kwargs):
        return HttpResponse("OrdenServicioDetailView (stub)")

def telegram_webhook(request):
    return HttpResponse("telegram_webhook (stub)")

def perfil_usuario_view(request):
    return HttpResponse("perfil_usuario_view (stub)")

def api_conductores(request):
    return HttpResponse("api_conductores (stub)")

def vincular_telegram(request):
    return HttpResponse("vincular_telegram (stub)")

# --- FIN STUBS ---

@require_GET
def productos_por_servicios_ajax(request):
    """
    Vista AJAX: recibe IDs de servicios y devuelve los productos sugeridos para esos servicios.
    """
    servicios_ids = request.GET.getlist('servicios[]')
    from .models import ServicioCatalogo, Repuesto
    productos_set = set()
    for sid in servicios_ids:
        try:
            servicio = ServicioCatalogo.objects.get(pk=sid)
            productos_set.update(servicio.productos_requeridos.all())
        except ServicioCatalogo.DoesNotExist:
            pass
    productos = [
        {'id': p.id, 'nombre': str(p)} for p in productos_set
    ]
    return JsonResponse({'success': True, 'productos': productos})


@login_required
@require_GET
def productos_por_servicio_catalogo(request):
    servicio_ids = request.GET.get('servicio_ids', '')
    ids = [int(pk) for pk in servicio_ids.split(',') if pk.isdigit()]
    productos_set = set()
    from .models import ServicioCatalogo
    for pk in ids:
        try:
            servicio = ServicioCatalogo.objects.get(pk=pk)
            productos_set.update(servicio.productos_requeridos.all())
        except ServicioCatalogo.DoesNotExist:
            pass
    productos = [
        {'id': p.id, 'nombre': str(p)} for p in productos_set
    ]
    return JsonResponse({'success': True, 'productos': productos})


@login_required
@require_GET
def conductor_por_vehiculo(request, vehiculo_id):
    try:
        vehiculo = Vehiculo.objects.select_related('conductor').filter(id=vehiculo_id).first()
        response_data = {'success': True, 'conductor': None}
        if vehiculo and vehiculo.conductor:
            response_data['conductor'] = {
                'id': vehiculo.conductor.id,
                'nombre': vehiculo.conductor.nombre,
                'telefono': vehiculo.conductor.telefono or ''
            }
        return JsonResponse(response_data)
    except Exception as e:
        return JsonResponse({'success': False, 'error': f'Error interno: {str(e)}'}, status=500)

@method_decorator(login_required, name='dispatch')
class VehiculoListView(ListView):
    model = Vehiculo
    template_name = 'gestion_taller/vehiculo_list.html'
    context_object_name = 'vehiculos'

    def dispatch(self, request, *args, **kwargs):
        from django.core.exceptions import ObjectDoesNotExist
        from django.contrib import messages
        from django.shortcuts import redirect
        try:
            _ = request.user.perfilusuario
        except ObjectDoesNotExist:
            messages.warning(request, "Debes crear tu perfil de usuario antes de continuar.")
            return redirect('mi_perfil_usuario')
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        perfil = self.request.user.perfilusuario
        if perfil.cliente:
            return Vehiculo.objects.filter(cliente=perfil.cliente)
        return Vehiculo.objects.none()

@method_decorator(login_required, name='dispatch')
class VehiculoCreateView(CreateView):
    model = Vehiculo
    form_class = VehiculoForm
    template_name = 'gestion_taller/vehiculo_modal.html'
    success_url = reverse_lazy('vehiculos')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['modal_title'] = 'Nuevo Vehículo'
        return context

    def form_valid(self, form):
        form.instance.cliente = self.request.user.perfilusuario.cliente
        self.object = form.save()
        
        if self.request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'message': 'Vehículo guardado correctamente',
                'redirect': str(self.get_success_url())
            })
            
        messages.success(self.request, 'Vehículo guardado correctamente')
        return super().form_valid(form)

    def form_invalid(self, form):
        if self.request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({
                'success': False,
                'form': self.get_context_data(form=form).get('form').as_div()
            })
            
        messages.error(self.request, 'Por favor corrija los errores en el formulario')
        return super().form_invalid(form)

@method_decorator(login_required, name='dispatch')
class VehiculoUpdateView(UpdateView):
    model = Vehiculo
    form_class = VehiculoForm
    template_name = 'gestion_taller/vehiculo_form_modal.html'
    success_url = reverse_lazy('vehiculos')

    def get_queryset(self):
        perfil = self.request.user.perfilusuario
        if perfil.cliente:
            return Vehiculo.objects.filter(cliente=perfil.cliente)
        return Vehiculo.objects.none()

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def get(self, request, *args, **kwargs):
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            self.object = self.get_object()
            form = self.get_form()
            html_form = render_to_string('gestion_taller/vehiculo_form_modal.html', {'form': form}, request=request)
            return HttpResponse(html_form)
        return super().get(request, *args, **kwargs)

    def form_valid(self, form):
        self.object = form.save()
        if self.request.headers.get('x-requested-with') == 'XMLHttpRequest':
            vehiculos = Vehiculo.objects.filter(cliente=self.request.user.perfilusuario.cliente)
            html_tabla = render_to_string('gestion_taller/vehiculo_tabla.html', {'vehiculos': vehiculos})
            return JsonResponse({'success': True, 'tabla': html_tabla})
        return super().form_valid(form)

    def form_invalid(self, form):
        if self.request.headers.get('x-requested-with') == 'XMLHttpRequest':
            html_form = render_to_string('gestion_taller/vehiculo_form_ajax.html', {'form': form}, request=self.request)
            return HttpResponse(html_form)
        return super().form_invalid(form)

@method_decorator(login_required, name='dispatch')
class VehiculoDeleteView(DeleteView):
    model = Vehiculo
    template_name = 'gestion_taller/vehiculo_confirm_delete_modal.html'
    success_url = reverse_lazy('vehiculos')

    def get_queryset(self):
        perfil = self.request.user.perfilusuario
        if perfil.cliente:
            return Vehiculo.objects.filter(cliente=perfil.cliente)
        return Vehiculo.objects.none()

    def get(self, request, *args, **kwargs):
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            self.object = self.get_object()
            context = self.get_context_data(object=self.object)
            html = render_to_string(self.template_name, context, request=request)
            return HttpResponse(html)
        return super().get(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        cliente = self.request.user.perfilusuario.cliente
        self.object.delete()
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            vehiculos = Vehiculo.objects.filter(cliente=cliente)
            html_tabla = render_to_string('gestion_taller/vehiculo_tabla.html', {'vehiculos': vehiculos})
            return JsonResponse({'success': True, 'tabla': html_tabla})
        return HttpResponseRedirect(self.get_success_url())

# Vistas para Repuestos
@method_decorator(login_required, name='dispatch')
class RepuestoListView(ListView):
    model = Repuesto
    template_name = 'gestion_taller/repuesto_list.html'
    context_object_name = 'repuestos'

    def get_queryset(self):
        perfil = self.request.user.perfilusuario
        qs = Repuesto.objects.filter(cliente=perfil.cliente) if perfil.cliente else Repuesto.objects.none()
        categoria_id = self.request.GET.get('categoria')
        if categoria_id:
            qs = qs.filter(categoria_id=categoria_id)
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        categorias = []  
        context['categorias'] = categorias
        context['categoria_seleccionada'] = self.request.GET.get('categoria', '')
        return context

@method_decorator(login_required, name='dispatch')
class RepuestoCreateView(CreateView):
    model = Repuesto
    form_class = RepuestoForm
    template_name = 'gestion_taller/repuesto_form.html'  # Plantilla por defecto
    success_url = reverse_lazy('repuestos')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        kwargs['editing'] = False
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['modal_title'] = 'Nuevo Repuesto'
        # Asegurarse de que siempre haya un objeto en el contexto
        context['object'] = getattr(self, 'object', None)
        return context
        
    def get(self, request, *args, **kwargs):
        is_ajax = request.headers.get('x-requested-with') == 'XMLHttpRequest' or 'HX-Request' in request.headers
        
        try:
            # Inicializar el objeto para el formulario
            self.object = None
            
            if is_ajax:
                # Para peticiones AJAX/HTMX, usar plantilla modal
                form = self.get_form()
                context = self.get_context_data(form=form)
                return render(request, 'gestion_taller/repuesto_form_modal_content.html', context)
            
            # Para peticiones normales, usar plantilla completa
            return super().get(request, *args, **kwargs)
            
        except Exception as e:
            print(f"Error en get: {str(e)}")
            if is_ajax:
                return JsonResponse({
                    'success': False,
                    'message': f'Error al cargar el formulario: {str(e)}',
                    'error_type': type(e).__name__
                }, status=500)
            raise

    def form_valid(self, form):
        try:
            # Verificar si el usuario tiene perfil
            if not hasattr(self.request.user, 'perfilusuario'):
                raise ValueError('El usuario no tiene un perfil configurado')
                
            # Verificar si el perfil tiene un cliente asociado
            if not hasattr(self.request.user.perfilusuario, 'cliente'):
                raise ValueError('El perfil del usuario no tiene un cliente asociado')
                
            # Asignar el cliente al repuesto
            form.instance.cliente = self.request.user.perfilusuario.cliente
            
            # Guardar el formulario
            self.object = form.save()
            
            # Si es petición AJAX/HTMX, respuesta especial
            if self.request.headers.get('x-requested-with') == 'XMLHttpRequest' or 'HX-Request' in self.request.headers:
                response = HttpResponse(status=204)
                response['HX-Trigger'] = 'repuestoActualizado'
                return response
            
            # Para peticiones normales, redirección estándar
            return super().form_valid(form)
            
        except Exception as e:
            print(f"Error en form_valid: {str(e)}")
            # En caso de error, re-renderizar el formulario con errores
            return self.form_invalid(form)

    def form_invalid(self, form):
        is_ajax = self.request.headers.get('x-requested-with') == 'XMLHttpRequest'
        
        if is_ajax:
            # Renderizar el formulario con los errores
            form_html = render_to_string(
                self.template_name,
                self.get_context_data(form=form),
                request=self.request
            )
            
            return JsonResponse({
                'success': False,
                'message': 'Por favor corrija los errores en el formulario',
                'form': form_html,
                'errors': form.errors.get_json_data()
            }, status=400)
            
        return super().form_invalid(form)

@method_decorator(login_required, name='dispatch')
class RepuestoUpdateView(UpdateView):
    model = Repuesto
    form_class = RepuestoForm
    template_name = 'gestion_taller/repuesto_form.html'  # Plantilla por defecto
    success_url = reverse_lazy('repuestos')

    def get_queryset(self):
        perfil = self.request.user.perfilusuario
        if perfil.cliente:
            return Repuesto.objects.filter(cliente=perfil.cliente)
        return Repuesto.objects.none()

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        kwargs['editing'] = True
        return kwargs
        
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['modal_title'] = 'Editar Repuesto'
        return context

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        if request.headers.get('x-requested-with') == 'XMLHttpRequest' or 'HX-Request' in request.headers:
            # Para peticiones AJAX/HTMX, usar plantilla modal
            form = self.get_form()
            context = self.get_context_data(form=form)
            return render(request, 'gestion_taller/repuesto_form_modal_content.html', context)
        # Para peticiones normales, usar plantilla completa
        return super().get(request, *args, **kwargs)

    def form_valid(self, form):
        try:
            # Guardar el formulario (el cliente ya está asignado por el queryset)
            self.object = form.save()
            
            # Si es petición AJAX/HTMX, respuesta especial
            if self.request.headers.get('x-requested-with') == 'XMLHttpRequest' or 'HX-Request' in self.request.headers:
                response = HttpResponse(status=204)
                response['HX-Trigger'] = 'repuestoActualizado'
                return response
            
            # Para peticiones normales, redirección estándar
            return super().form_valid(form)
            
        except Exception as e:
            print(f"Error en form_valid: {str(e)}")
            # En caso de error, re-renderizar el formulario con errores
            return self.form_invalid(form)

    def form_invalid(self, form):
        if self.request.headers.get('x-requested-with') == 'XMLHttpRequest':
            # Registrar los errores del formulario para depuración
            print("Errores del formulario:", form.errors)
            print("Datos del formulario:", form.data)
            
            # Devolver los errores en un formato que el frontend pueda manejar
            return JsonResponse({
                'success': False,
                'errors': form.errors,
                'message': 'Por favor corrija los errores en el formulario',
                'form': render_to_string(
                    self.template_name, 
                    {'form': form, 'object': self.object}, 
                    request=self.request
                )
            }, status=400)
        return super().form_invalid(form)

@method_decorator(login_required, name='dispatch')
class RepuestoDeleteView(DeleteView):
    model = Repuesto
    template_name = 'gestion_taller/repuesto_confirm_delete.html'
    success_url = reverse_lazy('repuestos')
    def get_queryset(self):
        perfil = self.request.user.perfilusuario
        if perfil.cliente:
            return Repuesto.objects.filter(cliente=perfil.cliente)
        return Repuesto.objects.none()

# Vistas para Conductores
@method_decorator(login_required, name='dispatch')
class ConductorListView(ListView):
    model = Conductor
    template_name = 'gestion_taller/conductor_list.html'
    context_object_name = 'conductores'
    def get_queryset(self):
        perfil = self.request.user.perfilusuario
        if perfil.cliente:
            return Conductor.objects.filter(cliente=perfil.cliente)
        return Conductor.objects.none()

@method_decorator(login_required, name='dispatch')
class ConductorCreateView(CreateView):
    model = Conductor
    form_class = ConductorForm
    template_name = 'gestion_taller/conductor_form_modal.html'
    success_url = reverse_lazy('conductores')

    def form_valid(self, form):
        perfil = self.request.user.perfilusuario
        # Siempre asigna el cliente si existe en el perfil
        if perfil.cliente:
            form.instance.cliente = perfil.cliente
        else:
            form.add_error(None, "No se puede crear un conductor sin un cliente asociado al usuario.")
            return self.form_invalid(form)
        self.object = form.save()
        if self.request.headers.get('x-requested-with') == 'XMLHttpRequest':
            conductores = Conductor.objects.filter(cliente=perfil.cliente)
            from django.template.loader import render_to_string
            html_tabla = render_to_string('gestion_taller/conductor_tabla.html', {'conductores': conductores})
            from django.http import JsonResponse
            return JsonResponse({'success': True, 'tabla': html_tabla})
        return super().form_valid(form)

    def form_invalid(self, form):
        if self.request.headers.get('x-requested-with') == 'XMLHttpRequest':
            from django.template.loader import render_to_string
            html_form = render_to_string('gestion_taller/conductor_form_ajax.html', {'form': form}, request=self.request)
            from django.http import HttpResponse
            return HttpResponse(html_form)
        return render(self.request, self.template_name, {'form': form})

    def get(self, request, *args, **kwargs):
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            self.object = None
            form = self.get_form()
            context = {'form': form}
            from django.template.loader import render_to_string
            html_form = render_to_string('gestion_taller/conductor_form_ajax.html', context, request=request)
            from django.http import HttpResponse
            return HttpResponse(html_form)
        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        perfil = self.request.user.perfilusuario
        if perfil.rol in ['admin', 'empleado'] and perfil.cliente:
            return Conductor.objects.filter(cliente=perfil.cliente)
        return Conductor.objects.none()

@method_decorator(login_required, name='dispatch')
class ConductorUpdateView(UpdateView):
    model = Conductor
    form_class = ConductorUpdateForm
    template_name = 'gestion_taller/conductor_form.html'
    success_url = reverse_lazy('conductores')
    def get_queryset(self):
        perfil = self.request.user.perfilusuario
        if perfil.cliente:
            return Conductor.objects.filter(cliente=perfil.cliente)
        return Conductor.objects.none()
    def form_valid(self, form):
        perfil = self.request.user.perfilusuario
        if perfil.rol in ['admin', 'empleado'] and perfil.cliente:
            form.instance.cliente = perfil.cliente
        self.object = form.save()
        if self.request.headers.get('x-requested-with') == 'XMLHttpRequest':
            conductores = Conductor.objects.filter(cliente=perfil.cliente)
            from django.template.loader import render_to_string
            html_tabla = render_to_string('gestion_taller/conductor_tabla.html', {'conductores': conductores})
            from django.http import JsonResponse
            return JsonResponse({'success': True, 'tabla': html_tabla})
        return super().form_valid(form)

    def form_invalid(self, form):
        if self.request.headers.get('x-requested-with') == 'XMLHttpRequest':
            from django.template.loader import render_to_string
            html_form = render_to_string('gestion_taller/conductor_form.html', {'form': form}, request=self.request)
            from django.http import HttpResponse
            return HttpResponse(html_form)
        return super().form_invalid(form)

    def get(self, request, *args, **kwargs):
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            self.object = self.get_object()
            form = self.get_form()
            context = {'form': form}
            from django.template.loader import render_to_string
            html_form = render_to_string('gestion_taller/conductor_form.html', context, request=request)
            from django.http import HttpResponse
            return HttpResponse(html_form)
        return super().get(request, *args, **kwargs)

    def form_invalid(self, form):
        if self.request.headers.get('x-requested-with') == 'XMLHttpRequest':
            from django.template.loader import render_to_string
            html_form = render_to_string('gestion_taller/conductor_form.html', {'form': form}, request=self.request)
            from django.http import HttpResponse
            return HttpResponse(html_form)
        return super().form_invalid(form)

@method_decorator(login_required, name='dispatch')
class ConductorDeleteView(DeleteView):
    model = Conductor
    template_name = 'gestion_taller/conductor_confirm_delete_modal.html'
    success_url = reverse_lazy('conductores')

    def get(self, request, *args, **kwargs):
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            self.object = self.get_object()
            context = self.get_context_data(object=self.object)
            from django.template.loader import render_to_string
            html = render_to_string(self.template_name, context, request=request)
            from django.http import HttpResponse
            return HttpResponse(html)
        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        perfil = self.request.user.perfilusuario
        if perfil.cliente:
            return Conductor.objects.filter(cliente=perfil.cliente)
        return Conductor.objects.none()

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        perfil = self.request.user.perfilusuario
        self.object.delete()
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            conductores = Conductor.objects.filter(cliente=perfil.cliente)
            from django.template.loader import render_to_string
            html_tabla = render_to_string('gestion_taller/conductor_tabla.html', {'conductores': conductores})
            from django.http import JsonResponse
            return JsonResponse({'success': True, 'tabla': html_tabla})
        
        from django.http import HttpResponseRedirect
        return HttpResponseRedirect(self.get_success_url())

# Vistas para Servicios

from .models import OrdenServicio
from django.views.generic import CreateView, ListView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin

class OrdenServicioListView(LoginRequiredMixin, ListView):
    model = OrdenServicio
    template_name = 'gestion_taller/orden_servicio_list.html'
    context_object_name = 'ordenes'
    paginate_by = 10

    def get_queryset(self):
        qs = super().get_queryset()
        perfil = self.request.user.perfilusuario
        if perfil.cliente:
            qs = qs.filter(cliente=perfil.cliente)
        # Filtros avanzados
        estado = self.request.GET.get('estado')
        vehiculo = self.request.GET.get('vehiculo')
        if estado:
            qs = qs.filter(estado=estado)
        if vehiculo:
            qs = qs.filter(vehiculo__placa__icontains=vehiculo)
        return qs.order_by('-fecha_creacion')

class OrdenServicioDetailView(LoginRequiredMixin, DetailView):
    model = OrdenServicio
    template_name = 'gestion_taller/orden_servicio_detail.html'
    context_object_name = 'orden'
    
    def get_queryset(self):
        qs = super().get_queryset()
        perfil = self.request.user.perfilusuario
        if perfil.cliente:
            qs = qs.filter(cliente=perfil.cliente)
        return qs

class OrdenServicioCreateView(LoginRequiredMixin, CreateView):
    model = OrdenServicio
    form_class = OrdenServicioForm
    template_name = 'gestion_taller/orden_servicio_form.html'
    success_url = reverse_lazy('orden_servicio_listado')
    
    def get_template_names(self):
        # Detectar peticiones HTMX o AJAX
        if (self.request.headers.get('hx-request') or 
            self.request.headers.get('x-requested-with') == 'XMLHttpRequest'):
            return ['gestion_taller/orden_servicio_form_modal_content.html']
        return [self.template_name]

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs
        
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if 'form' not in context:
            context['form'] = self.get_form()
        return context
        
    def get_form(self, form_class=None):
        if form_class is None:
            form_class = self.get_form_class()
        kwargs = self.get_form_kwargs()
        kwargs['user'] = self.request.user
        return form_class(**kwargs)

    def form_valid(self, form):
        # Verificar perfil y cliente
        if not hasattr(self.request.user, 'perfilusuario') or not self.request.user.perfilusuario.cliente:
            form.add_error(None, 'No tiene un cliente asociado a su perfil')
            return self.form_invalid(form)
            
        perfil = self.request.user.perfilusuario
        vehiculo = form.cleaned_data.get('vehiculo')
        
        if not vehiculo:
            form.add_error('vehiculo', 'Debe seleccionar un vehículo')
            return self.form_invalid(form)
            
        try:
            self.object = form.save(commit=False)
            self.object.cliente = perfil.cliente
            
            # Asignar conductor automáticamente del vehículo si no viene en el formulario
            if not self.object.conductor and vehiculo.conductor:
                self.object.conductor = vehiculo.conductor
                messages.info(self.request, f'Conductor asignado automáticamente: {vehiculo.conductor.nombre}')
                
            # Validar que tenga conductor
            if not self.object.conductor:
                form.add_error(None, 'El vehículo seleccionado no tiene conductor asignado')
                return self.form_invalid(form)
                
            self.object.save()
            form.save_m2m()
            
            # Recalcular y actualizar el total después de guardar las relaciones
            self.object.total = self.object.calcular_total()
            self.object.save(update_fields=['total'])


            # Notificación por Telegram
            try:
                chat_id = getattr(perfil, 'telegram_chat_id', None)
                if chat_id and hasattr(self.object, 'vehiculo') and self.object.vehiculo:
                    from .utils import enviar_telegram
                    mensaje = (
                        f"¡Nueva orden de servicio creada!\n"
                        f"Vehículo: {self.object.vehiculo.placa}\n"
                        f"Conductor: {self.object.conductor.nombre if self.object.conductor else 'No asignado'}\n"
                        f"Estado: {self.object.get_estado_display()}"
                    )
                    enviar_telegram(chat_id, mensaje)
            except Exception as e:
                print(f"[Telegram] Error enviando notificación: {e}")
                
            messages.success(self.request, 'Orden de servicio creada exitosamente.')
            
            # Respuesta para HTMX/AJAX
            if self.request.headers.get('x-requested-with') == 'XMLHttpRequest':
                response = HttpResponse(status=204)
                response['HX-Trigger'] = 'ordenCreada'
                return response
                
            return redirect(self.get_success_url())
            
        except Exception as e:
            form.add_error(None, f'Error al guardar la orden: {str(e)}')
            return self.form_invalid(form)
        
    def form_invalid(self, form):
        if self.request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({
                'success': False,
                'errors': form.errors,
                'message': 'Por favor corrija los errores en el formulario',
                'form': render_to_string(
                    self.template_name,
                    {'form': form},
                    request=self.request
                )
            }, status=400)
        return super().form_invalid(form)

# --- API: Vinculación de Telegram ---

from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse, HttpResponse
from django.db.models import F, Q, Count, Sum
from django.db.models.functions import Coalesce
import os
import json
import requests

TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')

# --- Lógica de FAQ y IA ---
FAQ = {
    "¿cómo vinculo mi cuenta?": "Para vincular tu cuenta, usa el comando /start y sigue las instrucciones para ingresar tu correo y contraseña.",
    "¿qué servicios ofrecen?": "Ofrecemos mantenimiento preventivo, correctivo, diagnóstico, alineación, balanceo y más. ¡Pregunta por tu servicio!",
    "¿cómo contacto al taller?": "Puedes contactarnos al teléfono 555-123-4567 o por este chat de Telegram.",
    "¿cuándo es mi próximo mantenimiento?": "Puedes consultar tu próximo mantenimiento en la app web o escribirnos aquí para más detalles.",
}

def buscar_faq(pregunta):
    pregunta = pregunta.lower().strip()
    for key in FAQ:
        if key in pregunta:
            return FAQ[key]
    return None

# --- IA: usando Hugging Face (debes instalar transformers y torch en Railway) ---
try:
    from transformers import AutoModelForCausalLM, AutoTokenizer
    import torch
    MODEL_NAME = "datificate/gpt2-small-spanish"
    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
    model = AutoModelForCausalLM.from_pretrained(MODEL_NAME)
    IA_READY = True
except Exception:
    IA_READY = False
    tokenizer = None
    model = None

def obtener_respuesta_ia(mensaje_usuario):
    if not IA_READY:
        return "Lo siento, la IA no está disponible en este momento."
    prompt = f"Usuario: {mensaje_usuario}\nIA: "
    inputs = tokenizer.encode(prompt, return_tensors="pt")
    outputs = model.generate(inputs, max_new_tokens=60, pad_token_id=tokenizer.eos_token_id)
    respuesta = tokenizer.decode(outputs[0], skip_special_tokens=True)
    partes = respuesta.split("IA:")
    if len(partes) > 1:
        respuesta_ia = partes[-1].strip()
    else:
        respuesta_ia = respuesta.strip()
    if not respuesta_ia or respuesta_ia.lower() in ["", "ia", "jo:"] or respuesta_ia.startswith("JO:"):
        respuesta_ia = "Lo siento, no entendí la pregunta. ¿Puedes reformularla?"
    return respuesta_ia

@csrf_exempt
def telegram_webhook(request):
    from django.contrib.auth import authenticate
    from gestion_taller.models import PerfilUsuario, Conductor
    if request.method == "POST":
        try:
            data = json.loads(request.body.decode("utf-8"))
            if "message" in data:
                chat_id = str(data["message"]["chat"]["id"])
                text = data["message"].get("text", "").strip()
                send_message_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
                # --- 1. Identificación por chat_id ---
                perfil = PerfilUsuario.objects.filter(telegram_chat_id=chat_id).first()
                conductor = Conductor.objects.filter(telegram_chat_id=chat_id).first()
                # --- 2. Si ya está vinculado ---
                if perfil:
                    if perfil.rol == 'admin':
                        # Comandos solo para admin
                        if text == '/start':
                            reply = "¡Hola, administrador! Puedes consultar el estado del taller, recibir notificaciones y gestionar todo desde aquí. Usa /faq, /ayuda, /taller_info, /conductores, /vehiculos, /ordenes o /notificar."
                        # Agregar en la sección de comandos de admin (cerca de la línea 845)
                        elif text == '/inventario':
                            reply = (
                                "📦 *Menú de Gestión de Inventario*\n\n"
                                "Elige una opción:\n"
                                "1. 🔍 Ver todo el inventario\n"
                                "2. ⚠️ Ver stock bajo\n"
                                "3. 🛠 Repuestos por servicio\n"
                                "4. 🔍 Buscar repuesto\n"
                                "5. 📊 Estadísticas de inventario\n\n"
                                "O usa:\n"
                                "/buscar_repuesto [nombre] - Para buscar un repuesto específico"
                            )
                            # Crear teclado en pantalla
                            keyboard = {
                                "keyboard": [
                                    ["Ver inventario completo", "Ver stock bajo"],
                                    ["Repuestos por servicio", "Estadísticas"],
                                    ["Buscar repuesto"]
                                ],
                                "resize_keyboard": True,
                                "one_time_keyboard": True
                            }
                            requests.post(send_message_url, json={
                                "chat_id": chat_id,
                                "text": reply,
                                "parse_mode": "Markdown",
                                "reply_markup": json.dumps(keyboard)
                            })
                            return HttpResponse("ok")

                        # Comando para ver stock bajo
                        elif text.lower() in ['⚠️ ver stock bajo', '/stock_bajo']:
                            repuestos = perfil.cliente.repuestos.filter(stock__lte=F('stock_minimo')).order_by('stock')
                            if repuestos.exists():
                                reply = "⚠️ *Productos con stock bajo:*\n\n"
                                for r in repuestos:
                                    reply += f"🔹 *{r.nombre}*\n"
                                    reply += f"   Stock actual: {r.stock} (Mínimo: {r.stock_minimo})\n"
                                    reply += f"   Precio: ${r.precio_venta:,.2f}\n"
                                    if r.proveedor:
                                        reply += f"   Proveedor: {r.proveedor}\n"
                                    reply += "────────────────────\n"
                            else:
                                reply = "✅ ¡Todo en orden! No hay productos con stock bajo."

                        # Comando para buscar repuestos
                        elif text.lower().startswith(('/buscar_repuesto', 'buscar repuesto')):
                            termino = text.split(' ', 1)[1] if ' ' in text else None
                            if not termino:
                                reply = "🔍 Por favor, indica el nombre o parte del repuesto que buscas.\nEjemplo: /buscar_repuesto filtro"
                            else:
                                repuestos = perfil.cliente.repuestos.filter(
                                    Q(nombre__icontains=termino) | 
                                    Q(descripcion__icontains=termino) |
                                    Q(codigo=termino)
                                )[:20]  # Limitar a 20 resultados
                                
                                if repuestos.exists():
                                    reply = f"🔍 *Resultados para '{termino}':*\n\n"
                                    for r in repuestos:
                                        estado = "⚠️" if r.stock <= r.stock_minimo else "✅"
                                        reply += f"{estado} *{r.nombre}*\n"
                                        reply += f"   Stock: {r.stock} | Mín: {r.stock_minimo}\n"
                                        reply += f"   Precio: ${r.precio_venta:,.2f}\n"
                                        # Eliminamos la línea de ubicación que no existe
                                        reply += "────────────────────\n"
                                else:
                                    reply = f"❌ No se encontraron repuestos que coincidan con '{termino}'"

                        # Comando para ver repuestos por servicio
                        elif text.lower() in ['🛠 repuestos por servicio', '/repuestos_por_servicio']:
                            servicios = perfil.cliente.servicios_catalogo.prefetch_related('productos_requeridos').all()
                            if servicios.exists():
                                reply = "🛠 *Repuestos por servicio:*\n\n"
                                for servicio in servicios:
                                    if servicio.productos_requeridos.exists():
                                        reply += f"🔧 *{servicio.nombre}*\n"
                                        for producto in servicio.productos_requeridos.all():
                                            estado = "⚠️" if producto.stock <= producto.stock_minimo else "✅"
                                            reply += f"   {estado} {producto.nombre} ({producto.stock} en stock)\n"
                                        reply += "────────────────────\n"
                            else:
                                reply = "No hay servicios con repuestos asignados."

                        # Manejo de respuestas del teclado
                        elif text.lower() in ['ver inventario completo', '1', 'ver todo el inventario']:
                            repuestos = perfil.cliente.repuestos.all().order_by('nombre')  # Eliminamos la agrupación por categoría que no existe
                            if repuestos.exists():
                                reply = "📦 *Inventario Completo*\n\n"
                                for r in repuestos:
                                    estado = "⚠️" if r.stock <= r.stock_minimo else "✅"
                                    reply += f"{estado} *{r.nombre}*\n"
                                    reply += f"   Stock: {r.stock} | Mín: {r.stock_minimo}\n"
                                    reply += f"   Precio: ${r.precio_venta:,.2f}\n"
                                    reply += "────────────────────\n"
                                
                                # Añadir estadísticas rápidas
                                total_repuestos = repuestos.count()
                                bajo_stock = repuestos.filter(stock__lte=F('stock_minimo')).count()
                                reply += f"\n📊 *Estadísticas:*\n"
                                reply += f"• Total repuestos: {total_repuestos}\n"
                                reply += f"• Con stock bajo: {bajo_stock}\n"
                                # Usamos una suma segura para evitar errores con valores None
                                valor_total = sum((r.precio_venta * r.stock) for r in repuestos if r.precio_venta is not None)
                                reply += f"• Valor total: ${valor_total:,.2f}"
                            else:
                                reply = "El inventario está vacío."

                        # Estadísticas de inventario
                        elif text.lower() in ['📊 estadísticas', 'estadísticas', '5']:
                            stats = perfil.cliente.repuestos.aggregate(
                                total_repuestos=Count('id'),
                                bajo_stock=Count('id', filter=Q(stock__lte=F('stock_minimo'))),
                                valor_total=Coalesce(Sum(F('precio_venta') * F('stock')), 0.0),
                                # Eliminamos el conteo de categorías que no existe
                            )
                            
                            # Productos más utilizados (contando en qué órdenes aparecen)
                            mas_usados = perfil.cliente.repuestos.annotate(
                                veces_usado=Count('ordenes_servicio')
                            ).order_by('-veces_usado')[:5]
                            
                            reply = "📊 *Estadísticas de Inventario*\n\n"
                            reply += f"• 📦 Total repuestos: {stats['total_repuestos']}\n"
                            reply += f"• ⚠️  Con stock bajo: {stats['bajo_stock']}\n"
                            reply += f"• 💰 Valor total: ${stats['valor_total']:,.2f}\n"
                            
                            if mas_usados:
                                reply += "\n🔝 *Productos más utilizados:*\n"
                                for i, r in enumerate(mas_usados, 1):
                                    reply += f"{i}. {r.nombre} ({r.veces_usado} usos)\n"
                            
                            # Añadir teclado rápido
                            keyboard = {
                                "inline_keyboard": [
                                    [{"text": "⏳ Ver histórico", "callback_data": "hist_stock"}],
                                    [{"text": "📤 Exportar a Excel", "callback_data": "export_inv"}]
                                ]
                            }
                            
                            requests.post(send_message_url, json={
                                "chat_id": chat_id,
                                "text": reply,
                                "parse_mode": "Markdown",
                                "reply_markup": json.dumps(keyboard)
                            })
                            return HttpResponse("ok")
                        elif text == '/taller_info':
                            reply = (
                                f"Taller: {perfil.cliente.nombre}\n"
                                f"Conductores: {perfil.cliente.conductores.count()}\n"
                                f"Vehículos: {perfil.cliente.vehiculos.count()}\n"
                                f"Repuestos: {perfil.cliente.repuestos.count()}\n"
                                f"Órdenes: {perfil.cliente.ordenes_servicio.count()}"
                            )
                            # Agregar nombres de conductores
                            conductores = perfil.cliente.conductores.all()
                            if conductores.exists():
                                nombres = ', '.join([c.nombre for c in conductores])
                                reply += f"\nNombres de conductores: {nombres}"
                            else:
                                reply += "\nNo hay conductores registrados."
                        elif text == '/conductores':
                            conductores = perfil.cliente.conductores.all()
                            if conductores.exists():
                                reply = 'Conductores:\n' + '\n'.join([f"{c.nombre} | {c.correo or '-'} | {c.telefono or '-'}" for c in conductores])
                            else:
                                reply = 'No hay conductores registrados.'
                        elif text == '/vehiculos':
                            vehiculos = perfil.cliente.vehiculos.all()
                            if vehiculos.exists():
                                reply = 'Vehículos:\n' + '\n'.join([f"{v.placa} | {v.marca} {v.modelo} | {v.color or '-'}" for v in vehiculos])
                            else:
                                reply = 'No hay vehículos registrados.'
                        elif text == '/ordenes':
                            ordenes = perfil.cliente.ordenes_servicio.all().order_by('-fecha_creacion')[:20]
                            if ordenes.exists():
                                reply = 'Órdenes recientes:\n' + '\n'.join([f"#{o.id}: {o.estado} | {o.vehiculo.placa} | {o.fecha_creacion.date()}" for o in ordenes])
                            else:
                                reply = 'No hay órdenes registradas.'
                        elif text.startswith('/notificar'):
                            mensaje = text[len('/notificar'):].strip()
                            if not mensaje:
                                reply = 'Debes escribir el mensaje después de /notificar. Ejemplo:\n/notificar Mañana hay reunión.'
                            else:
                                # Notificar a empleados y conductores vinculados
                                chat_ids = set()
                                # Empleados (PerfilUsuario) con chat_id
                                for usuario in perfil.cliente.usuarios.exclude(telegram_chat_id__isnull=True).exclude(telegram_chat_id=''):
                                    chat_ids.add(usuario.telegram_chat_id)
                                # Conductores con chat_id
                                for c in perfil.cliente.conductores.exclude(telegram_chat_id__isnull=True).exclude(telegram_chat_id=''):
                                    chat_ids.add(c.telegram_chat_id)
                                enviados = 0
                                for cid in chat_ids:
                                    try:
                                        requests.post(send_message_url, json={"chat_id": cid, "text": f"[Notificación del taller]:\n{mensaje}"})
                                        enviados += 1
                                    except Exception:
                                        pass
                                reply = f'Notificación enviada a {enviados} destinatarios.'
                        elif text in ['/ayuda', '/help']:
                            reply = (
                                "📋 *Comandos de Administración*\n\n"
                                "🏭 *Información del Taller*\n"
                                "/taller_info — Estado general\n"
                                "/inventario — Gestión de inventario\n"
                                "/stock_bajo — Alertas de stock bajo\n"
                                "/repuestos_por_servicio — Ver repuestos por servicio\n"
                                "/buscar_repuesto [nombre] — Buscar en inventario\n\n"
                                "👥 *Gestión de Personas*\n"
                                "/conductores — Lista de conductores\n"
                                "/vehiculos — Lista de vehículos\n"
                                "/clientes — Lista de clientes\n\n"
                                "📝 *Órdenes y Servicios*\n"
                                "/ordenes — Órdenes recientes\n"
                                "/servicios — Catálogo de servicios\n\n"
                                "🔔 *Comunicación*\n"
                                "/notificar <mensaje> — Enviar notificación\n"
                                "/broadcast <mensaje> — Mensaje masivo\n\n"
                                "❓ *Ayuda y Soporte*\n"
                                "/faq — Preguntas frecuentes\n"
                                "/soporte — Contactar soporte\n"
                                "/ia <pregunta> — Asistente virtual"
                            )
                        else:
                            reply = "Comando no reconocido para admin. Usa /ayuda para ver opciones."
                    else:
                        # Empleado o usuario normal
                        reply = f"¡Hola {perfil.user.first_name}! Tu rol: {perfil.get_rol_display()}. Usa /faq o /ayuda para opciones."
                elif conductor:
                    # Comandos solo para conductor
                    if text == '/start':
                        reply = f"¡Hola {conductor.nombre}! Puedes consultar tus órdenes con /mis_ordenes, productos con /mis_productos y servicios con /servicios."
                    elif text == '/mis_ordenes':
                        ordenes = conductor.ordenes_servicio.all()
                        if ordenes.exists():
                            reply = 'Tus órdenes:\n' + '\n'.join([f"#{o.id}: {o.estado} - {o.fecha_creacion.date()}" for o in ordenes])
                        else:
                            reply = "No tienes órdenes registradas."
                    elif text == '/servicios':
                        servicios = conductor.servicios.all()
                        if servicios.exists():
                            reply = 'Tus servicios:\n' + '\n'.join([f"{s.descripcion} - {s.fecha_servicio.date()}" for s in servicios])
                        else:
                            reply = "No tienes servicios registrados."
                    elif text == '/mis_productos':
                        ordenes = conductor.ordenes_servicio.all()
                        productos = set()
                        for o in ordenes:
                            productos.update(o.productos.values_list('nombre', flat=True))
                        if productos:
                            reply = 'Tus productos/repuestos:\n' + '\n'.join(productos)
                        else:
                            reply = "No tienes productos asignados."
                    else:
                        reply = "Comando no reconocido para conductor. Usa /faq o /ayuda."
                # --- 3. Si NO está vinculado, iniciar flujo de vinculación ---
                else:
                    # Guardar estado conversacional en memoria (simple, por chat_id)
                    if not hasattr(telegram_webhook, 'pending'): telegram_webhook.pending = {}
                    pending = telegram_webhook.pending
                    if chat_id not in pending:
                        # Preguntar tipo
                        if text.lower() in ['usuario', 'conductor']:
                            pending[chat_id] = {'tipo': text.lower(), 'step': 1}
                            reply = 'Por favor, escribe tu correo:'
                        else:
                            reply = '¿Eres usuario (admin/empleado) o conductor? Responde: usuario o conductor.'
                    else:
                        tipo = pending[chat_id]['tipo']
                        step = pending[chat_id]['step']
                        if step == 1:
                            pending[chat_id]['correo'] = text
                            pending[chat_id]['step'] = 2
                            if tipo == 'usuario':
                                reply = 'Por favor, escribe tu contraseña:'
                            else:
                                reply = 'Verificando...'
                                # Buscar conductor
                                conductor = Conductor.objects.filter(correo=text).first()
                                if conductor:
                                    conductor.telegram_chat_id = chat_id
                                    conductor.save()
                                    del pending[chat_id]
                                    reply = f'¡Vinculación exitosa como conductor {conductor.nombre}!'
                                else:
                                    del pending[chat_id]
                                    reply = 'No se encontró conductor con ese correo.'
                        elif step == 2 and tipo == 'usuario':
                            correo = pending[chat_id]['correo']
                            password = text
                            user = authenticate(username=correo, password=password)
                            if user:
                                perfil = getattr(user, 'perfilusuario', None)
                                if perfil:
                                    perfil.telegram_chat_id = chat_id
                                    perfil.save()
                                    del pending[chat_id]
                                    reply = f'¡Vinculación exitosa como usuario {user.first_name} ({perfil.get_rol_display()})!'
                                else:
                                    del pending[chat_id]
                                    reply = 'No se encontró perfil asociado.'
                            else:
                                del pending[chat_id]
                                reply = 'Credenciales incorrectas.'
                        else:
                            del pending[chat_id]
                            reply = 'Ocurrió un error en el proceso de vinculación. Intenta de nuevo.'
                # Envía la respuesta al usuario
                requests.post(send_message_url, json={
                    "chat_id": chat_id,
                    "text": reply
                })
            return JsonResponse({"ok": True})
        except Exception as e:
            return JsonResponse({"ok": False, "error": str(e)}, status=500)
    return HttpResponse("Método no permitido", status=405)

from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import authenticate
from django.http import JsonResponse
import json

@csrf_exempt
def vincular_telegram(request):
    if request.method != 'POST':
        return JsonResponse({'ok': False, 'error': 'Solo POST'}, status=405)
    data = json.loads(request.body.decode())
    correo = data.get('correo')
    password = data.get('password')
    chat_id = data.get('chat_id')
    if not correo or not password or not chat_id:
        return JsonResponse({'ok': False, 'error': 'Faltan datos'}, status=400)
    user = authenticate(username=correo, password=password)
    if not user:
        return JsonResponse({'ok': False, 'error': 'Credenciales inválidas'}, status=401)
    perfil = getattr(user, 'perfilusuario', None)
    if perfil:
        perfil.telegram_chat_id = chat_id
        perfil.save()
        return JsonResponse({'ok': True, 'msg': 'Vinculado como usuario'})
    conductor = Conductor.objects.filter(correo=correo).first()
    if conductor:
        conductor.telegram_chat_id = chat_id
        conductor.save()
        return JsonResponse({'ok': True, 'msg': 'Vinculado como conductor'})
    return JsonResponse({'ok': False, 'error': 'No encontrado'}, status=404)

# --- Catálogo profesional de servicios ---
from django.utils.decorators import method_decorator

@method_decorator(login_required, name='dispatch')
class ServicioCatalogoListView(ListView):
    model = ServicioCatalogo
    template_name = 'gestion_taller/servicio_catalogo_list.html'
    context_object_name = 'servicios'
    paginate_by = 20

    def get_queryset(self):
        qs = ServicioCatalogo.objects.all()
        perfil = self.request.user.perfilusuario
        if perfil.cliente:
            # Si tienes multi-taller, puedes filtrar servicios por cliente si lo deseas
            pass
        q = self.request.GET.get('q')
        if q:
            qs = qs.filter(nombre__icontains=q) | qs.filter(descripcion__icontains=q)
        precio_min = self.request.GET.get('precio_min')
        if precio_min:
            try:
                qs = qs.filter(precio_base__gte=float(precio_min))
            except ValueError:
                pass
        precio_max = self.request.GET.get('precio_max')
        if precio_max:
            try:
                qs = qs.filter(precio_base__lte=float(precio_max))
            except ValueError:
                pass
        activo = self.request.GET.get('activo')
        if activo == '1':
            qs = qs.filter(activo=True)
        elif activo == '0':
            qs = qs.filter(activo=False)
        return qs.order_by('nombre')

# --- AJAX: sugerir servicios por kilometraje ---
from django.views.decorators.http import require_GET, require_http_methods
from django.http import JsonResponse, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt
from .utils import sugerir_servicios_por_kilometraje
from django.contrib.auth.decorators import login_required

@login_required
def api_conductores(request):
    """
    API para buscar conductores. Usada por Select2.
    """
    try:
        # Verificar que el usuario tenga un perfil y cliente asociado
        if not hasattr(request.user, 'perfilusuario') or not request.user.perfilusuario.cliente:
            return JsonResponse(
                {'results': [], 'error': 'No tiene un cliente asociado a su perfil'}, 
                status=400
            )
            
        # Obtener parámetros de búsqueda
        search = request.GET.get('q', '')
        cliente = request.user.perfilusuario.cliente
        
        # Filtrar conductores
        conductores = Conductor.objects.filter(
            cliente=cliente,
            nombre__icontains=search
        ).order_by('nombre')
        
        # Formatear resultados para Select2
        results = [{
            'id': c.id,
            'text': f"{c.nombre}",
            'telefono': c.telefono or ''
        } for c in conductores]
        
        return JsonResponse({
            'results': results,
            'pagination': {'more': False}
        })
        
    except Exception as e:
        return JsonResponse(
            {'results': [], 'error': str(e)}, 
            status=500
        )

@login_required
def conductor_por_vehiculo(request, vehiculo_id):
    """Obtiene el conductor asociado a un vehículo"""
    try:
        # Verificar cliente asociado
        if not hasattr(request.user, 'perfilusuario') or not request.user.perfilusuario.cliente:
            return JsonResponse({'success': False, 'error': 'Usuario no tiene cliente asociado'}, status=400)
            
        cliente = request.user.perfilusuario.cliente
        
        # Obtener vehículo con conductor (optimizado con select_related)
        vehiculo = Vehiculo.objects.select_related('conductor').filter(
            id=vehiculo_id,
            cliente=cliente
        ).first()
        
        if not vehiculo:
            return JsonResponse({
                'success': False,
                'error': 'Vehículo no existe o no pertenece a su cliente'
            }, status=404)
            
        response_data = {'success': True, 'conductor': None}
        
        if vehiculo.conductor:
            response_data['conductor'] = {
                'id': vehiculo.conductor.id,
                'nombre': vehiculo.conductor.nombre,
                'telefono': vehiculo.conductor.telefono or ''
            }
            
        return JsonResponse(response_data)
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Error interno: {str(e)}'
        }, status=500)

@require_GET
@login_required
def sugerir_servicios_ajax(request):
    vehiculo_id = request.GET.get('vehiculo_id')
    kilometraje = request.GET.get('kilometraje')
    try:
        vehiculo_id = int(vehiculo_id)
        kilometraje = int(kilometraje)
    except (TypeError, ValueError):
        return JsonResponse({'sugeridos': []})
    from .models import Vehiculo
    try:
        vehiculo = Vehiculo.objects.get(id=vehiculo_id)
    except Vehiculo.DoesNotExist:
        return JsonResponse({'sugeridos': []})
    sugeridos = sugerir_servicios_por_kilometraje(vehiculo, kilometraje)
    sugeridos_ids = [s.id for s in sugeridos]
    return JsonResponse({'sugeridos': sugeridos_ids})

@login_required
def get_productos_servicio(request, servicio_id):
    """
    Vista para obtener los productos asociados a un servicio
    """
    try:
        if not hasattr(request.user, 'perfilusuario') or not request.user.perfilusuario.cliente:
            return JsonResponse({'error': 'No tiene un cliente asociado'}, status=400)
            
        cliente = request.user.perfilusuario.cliente
        servicio = ServicioCatalogo.objects.get(id=servicio_id)
        
        # Obtener productos asociados al servicio y al cliente
        productos = servicio.productos.filter(cliente=cliente).values('id', 'nombre')
        
        return JsonResponse({
            'success': True,
            'productos': list(productos)
        })
        
    except ServicioCatalogo.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Servicio no encontrado'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@method_decorator(login_required, name='dispatch')
class ServicioListView(ListView):
    model = ServicioCatalogo
    template_name = 'gestion_taller/servicio_list.html'
    context_object_name = 'servicios'

    def get_queryset(self):
        if hasattr(self.request.user, 'perfilusuario') and self.request.user.perfilusuario.cliente:
            return ServicioCatalogo.objects.filter(cliente=self.request.user.perfilusuario.cliente)
        return ServicioCatalogo.objects.all()

@method_decorator(login_required, name='dispatch')
class ServicioCreateView(CreateView):
    model = ServicioCatalogo
    form_class = ServicioCatalogoForm
    template_name = 'gestion_taller/servicio_form.html'
    success_url = reverse_lazy('servicios')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def get(self, request, *args, **kwargs):
        form = self.get_form()
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            # Para peticiones AJAX, devolvemos solo el contenido del formulario
            return render(request, 'gestion_taller/servicio_modal_content.html', {'form': form})
        return super().get(request, *args, **kwargs)

    def form_valid(self, form):
        if not form.instance.cliente and hasattr(self.request.user, 'perfilusuario'):
            form.instance.cliente = self.request.user.perfilusuario.cliente
        
        response = super().form_valid(form)
        
        if self.request.headers.get('x-requested-with') == 'XMLHttpRequest':
            servicios = self.get_queryset()
            html_grid = render_to_string('gestion_taller/includes/servicio_grid.html', 
                                       {'servicios': servicios}, 
                                       request=self.request)
            return JsonResponse({'success': True, 'grid': html_grid})
        return response

    def form_invalid(self, form):
        response = super().form_invalid(form)
        if self.request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return render(self.request, self.template_name, 
                         {'form': form}, status=400)
        return response

class ServicioUpdateView(LoginRequiredMixin, UpdateView):
    model = ServicioCatalogo
    form_class = ServicioCatalogoForm
    template_name = 'gestion_taller/servicio_modal.html'
    success_url = reverse_lazy('servicios')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        if hasattr(self.request.user, 'perfilusuario'):
            kwargs['user'] = self.request.user
        return kwargs

    def get_queryset(self):
        if hasattr(self.request.user, 'perfilusuario') and self.request.user.perfilusuario.cliente:
            return ServicioCatalogo.objects.filter(cliente=self.request.user.perfilusuario.cliente)
        return ServicioCatalogo.objects.all()

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return render(request, self.template_name, 
                        {'form': self.get_form(), 'object': self.object})
        return super().get(request, *args, **kwargs)

    def form_valid(self, form):
        response = super().form_valid(form)
        if self.request.headers.get('x-requested-with') == 'XMLHttpRequest':
            servicios = ServicioCatalogo.objects.all()
            html_grid = render_to_string('gestion_taller/includes/servicio_grid.html', 
                                       {'servicios': servicios}, 
                                       request=self.request)
            return JsonResponse({'success': True, 'grid': html_grid})
        return response

    def form_invalid(self, form):
        response = super().form_invalid(form)
        if self.request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return render(self.request, self.template_name, 
                        {'form': form, 'object': self.object}, status=400)
        return response

class ServicioDeleteView(LoginRequiredMixin, DeleteView):
    model = ServicioCatalogo
    template_name = 'gestion_taller/servicio_confirm_delete.html'
    success_url = reverse_lazy('servicios')

    def get_queryset(self):
        return ServicioCatalogo.objects.all()

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        success_url = self.get_success_url()
        self.object.delete()
        
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            servicios = ServicioCatalogo.objects.all()
            html_grid = render_to_string('gestion_taller/includes/servicio_grid.html', 
                                       {'servicios': servicios}, 
                                       request=request)
            return JsonResponse({'success': True, 'grid': html_grid})
        return HttpResponseRedirect(success_url)

# Vista para crear/editar perfil de usuario
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from .models import PerfilUsuario
from .forms import PerfilUsuarioForm

@login_required
def perfil_usuario_view(request):
    try:
        perfil = request.user.perfilusuario
        editando = True
    except PerfilUsuario.DoesNotExist:
        perfil = None
        editando = False

    if request.method == 'POST':
        form = PerfilUsuarioForm(request.POST, instance=perfil)
        if form.is_valid():
            perfil = form.save(commit=False)
            perfil.user = request.user
            perfil.save()
            return redirect('perfil_usuario')
    else:
        form = PerfilUsuarioForm(instance=perfil)

    return render(request, 'gestion_taller/perfil_usuario_form.html', {
        'form': form,
        'editando': editando,
    })

# Vista para perfil de usuario
@method_decorator(login_required, name='dispatch')
class PerfilUsuarioView(UpdateView):
    model = User
    form_class = PerfilUsuarioForm
    template_name = 'gestion_taller/perfil.html'
    success_url = reverse_lazy('home')

    def get_object(self, queryset=None):
        return self.request.user.perfilusuario
@login_required
def home(request):
    cliente = None
    logo_url = None
    
    # Obtener datos del cliente si existe
    if hasattr(request.user, 'perfilusuario') and request.user.perfilusuario.cliente:
        cliente = request.user.perfilusuario.cliente
        logo_url = cliente.logo.url if cliente.logo else None
        
        # Obtener estadísticas filtradas por cliente
        stats = {
            'total_vehiculos': Vehiculo.objects.filter(cliente=cliente).count(),
            'total_conductores': Conductor.objects.filter(cliente=cliente).count(),
            'total_servicios': ServicioCatalogo.objects.filter(cliente=cliente).count(),
            'servicios_activos': ServicioCatalogo.objects.filter(cliente=cliente, activo=True).count(),
            'total_repuestos': Repuesto.objects.filter(cliente=cliente).count(),
            'total_ordenes': OrdenServicio.objects.filter(cliente=cliente).count(),
            'ultimos_servicios': OrdenServicio.objects.filter(
                cliente=cliente
            ).select_related('vehiculo', 'conductor').order_by('-fecha_creacion')[:5],
            'vehiculos_servicio': Vehiculo.objects.filter(
                cliente=cliente,
                fecha_ultimo_servicio__isnull=False
            ).order_by('fecha_ultimo_servicio')[:5],
            'repuestos_bajos': Repuesto.objects.filter(
                cliente=cliente,
                stock__lte=F('stock_minimo')
            ).order_by('stock')[:5],
        }
    else:
        # Si no hay cliente asociado, mostrar datos vacíos
        stats = {
            'total_vehiculos': 0,
            'total_conductores': 0,
            'total_servicios': 0,
            'total_repuestos': 0,
            'total_ordenes': 0,
            'ultimos_servicios': [],
            'vehiculos_servicio': [],
            'repuestos_bajos': [],
        }
    
    context = {
        'logo_url': logo_url, 
        'cliente': cliente,
        'stats': stats,
    }
    
    return render(request, 'gestion_taller/home.html', context)

# --- API para calcular precios en tiempo real ---
@login_required
def calcular_precios_orden(request):
    """API para calcular el total de una orden de servicio en tiempo real"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Solo se permite POST'}, status=405)
    
    try:
        import json
        data = json.loads(request.body)
        servicios_ids = data.get('servicios', [])
        productos_ids = data.get('productos', [])
        
        # Verificar cliente
        if not hasattr(request.user, 'perfilusuario') or not request.user.perfilusuario.cliente:
            return JsonResponse({'error': 'Usuario no tiene cliente asociado'}, status=400)
        
        cliente = request.user.perfilusuario.cliente
        
        # Calcular total de servicios
        total_servicios = 0
        servicios_detalle = []
        if servicios_ids:
            servicios = ServicioCatalogo.objects.filter(id__in=servicios_ids)
            for servicio in servicios:
                total_servicios += servicio.precio_base
                servicios_detalle.append({
                    'id': servicio.id,
                    'nombre': servicio.nombre,
                    'precio': float(servicio.precio_base)
                })
        
        # Calcular total de productos
        total_productos = 0
        productos_detalle = []
        if productos_ids:
            productos = Repuesto.objects.filter(id__in=productos_ids, cliente=cliente)
            for producto in productos:
                total_productos += producto.precio_venta
                productos_detalle.append({
                    'id': producto.id,
                    'nombre': producto.nombre,
                    'precio': float(producto.precio_venta)
                })
        
        total_general = total_servicios + total_productos
        
        return JsonResponse({
            'success': True,
            'total_servicios': float(total_servicios),
            'total_productos': float(total_productos),
            'total_general': float(total_general),
            'servicios_detalle': servicios_detalle,
            'productos_detalle': productos_detalle,
            'moneda': 'COP'  # Puedes cambiar esto según tu configuración
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'error': 'JSON inválido'}, status=400)
    except Exception as e:
        return JsonResponse({'error': f'Error interno: {str(e)}'}, status=500)

# --- Vistas para Órdenes de Servicio ---
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, CreateView, DetailView
from .models import OrdenServicio

@method_decorator(login_required, name='dispatch')
class OrdenServicioListView(ListView):
    model = OrdenServicio
    template_name = 'gestion_taller/orden_servicio_list.html'
    context_object_name = 'ordenes'
    paginate_by = 20
    
    def get_queryset(self):
        if not (hasattr(self.request.user, 'perfilusuario') and self.request.user.perfilusuario.cliente):
            return OrdenServicio.objects.none()
            
        queryset = OrdenServicio.objects.filter(
            cliente=self.request.user.perfilusuario.cliente
        ).select_related('vehiculo', 'conductor').prefetch_related('servicios', 'productos')
        
        # Filtros
        vehiculo = self.request.GET.get('vehiculo')
        if vehiculo:
            queryset = queryset.filter(vehiculo__placa__icontains=vehiculo)
            
        estado = self.request.GET.get('estado')
        if estado:
            queryset = queryset.filter(estado=estado)
            
        precio_min = self.request.GET.get('precio_min')
        if precio_min:
            try:
                queryset = queryset.filter(total__gte=float(precio_min))
            except ValueError:
                pass
                
        precio_max = self.request.GET.get('precio_max')
        if precio_max:
            try:
                queryset = queryset.filter(total__lte=float(precio_max))
            except ValueError:
                pass
        
        return queryset.order_by('-fecha_creacion')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Asegurar que todos los totales estén actualizados
        ordenes = context['ordenes']
        total_general = 0
        ordenes_pendientes = 0
        ordenes_completadas = 0
        
        for orden in ordenes:
            total_calculado = orden.calcular_total()
            if orden.total != total_calculado:
                orden.total = total_calculado
                orden.save(update_fields=['total'])
            
            total_general += orden.total
            if orden.estado == 'pendiente':
                ordenes_pendientes += 1
            elif orden.estado == 'completada':
                ordenes_completadas += 1
        
        # Agregar estadísticas al contexto
        context.update({
            'total_general': total_general,
            'ordenes_pendientes': ordenes_pendientes,
            'ordenes_completadas': ordenes_completadas,
            'total_ordenes': len(ordenes),
        })
        
        return context

@method_decorator(login_required, name='dispatch')
class OrdenServicioCreateView(CreateView):
    model = OrdenServicio
    form_class = OrdenServicioForm
    template_name = 'gestion_taller/orden_servicio_form.html'
    success_url = reverse_lazy('orden_servicio_listado')
    
    def get_template_names(self):
        if (self.request.headers.get('hx-request') or 
            self.request.headers.get('x-requested-with') == 'XMLHttpRequest'):
            return ['gestion_taller/orden_servicio_form_modal_content.html']
        return [self.template_name]
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs
    
    def form_valid(self, form):
        # Verificar que el usuario tenga un perfil y cliente asociado
        if not hasattr(self.request.user, 'perfilusuario') or not self.request.user.perfilusuario.cliente:
            form.add_error(None, 'Su usuario no tiene un cliente asociado. Contacte al administrador.')
            return self.form_invalid(form)
            
        perfil = self.request.user.perfilusuario
        vehiculo = form.cleaned_data.get('vehiculo')
        
        # Verificar que el vehículo pertenece al cliente
        if not vehiculo or vehiculo.cliente != perfil.cliente:
            form.add_error('vehiculo', 'El vehículo seleccionado no pertenece a su cliente')
            return self.form_invalid(form)
            
        if not vehiculo:
            form.add_error('vehiculo', 'Debe seleccionar un vehículo')
            return self.form_invalid(form)
            
        try:
            self.object = form.save(commit=False)
            self.object.cliente = perfil.cliente
            
            # Asignar conductor automáticamente del vehículo si no viene en el formulario
            if not self.object.conductor and vehiculo.conductor:
                self.object.conductor = vehiculo.conductor
                messages.info(self.request, f'Conductor asignado automáticamente: {vehiculo.conductor.nombre}')
                
            # Validar que tenga conductor
            if not self.object.conductor:
                form.add_error(None, 'El vehículo seleccionado no tiene conductor asignado')
                return self.form_invalid(form)
                
            self.object.save()
            form.save_m2m()
            
            # Recalcular y actualizar el total después de guardar las relaciones
            self.object.total = self.object.calcular_total()
            self.object.save(update_fields=['total'])

            # Notificación por Telegram
            try:
                chat_id = getattr(perfil, 'telegram_chat_id', None)
                if chat_id and hasattr(self.object, 'vehiculo') and self.object.vehiculo:
                    from .utils import enviar_telegram
                    mensaje = (
                        f"¡Nueva orden de servicio creada!\n"
                        f"Vehículo: {self.object.vehiculo.placa}\n"
                        f"Conductor: {self.object.conductor.nombre if self.object.conductor else 'No asignado'}\n"
                        f"Total: ${self.object.total}\n"
                        f"Estado: {self.object.get_estado_display()}"
                    )
                    enviar_telegram(chat_id, mensaje)
            except Exception as e:
                print(f"[Telegram] Error enviando notificación: {e}")
                
            messages.success(self.request, 'Orden de servicio creada exitosamente.')
            
            # Respuesta para HTMX/AJAX
            if self.request.headers.get('x-requested-with') == 'XMLHttpRequest':
                response = HttpResponse(status=204)
                response['HX-Trigger'] = 'ordenCreada'
                return response
                
            return redirect(self.get_success_url())
            
        except Exception as e:
            form.add_error(None, f'Error al guardar la orden: {str(e)}')
            return self.form_invalid(form)
        
    def form_invalid(self, form):
        if self.request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({
                'success': False,
                'errors': form.errors,
                'message': 'Por favor corrija los errores en el formulario',
                'form': render_to_string(
                    self.template_name,
                    {'form': form},
                    request=self.request
                )
            }, status=400)
        return super().form_invalid(form)

@method_decorator(login_required, name='dispatch')
class OrdenServicioDetailView(DetailView):
    model = OrdenServicio
    template_name = 'gestion_taller/orden_servicio_detail.html'
    context_object_name = 'orden'
    
    def get_queryset(self):
        if hasattr(self.request.user, 'perfilusuario') and self.request.user.perfilusuario.cliente:
            return OrdenServicio.objects.filter(
                cliente=self.request.user.perfilusuario.cliente
            ).select_related('vehiculo', 'conductor', 'cliente').prefetch_related('servicios', 'productos')
        return OrdenServicio.objects.none()
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        orden = self.object
        
        # Calcular desglose de precios
        servicios_detalle = []
        total_servicios = 0
        for servicio in orden.servicios.all():
            servicios_detalle.append({
                'nombre': servicio.nombre,
                'precio': servicio.precio_base
            })
            total_servicios += servicio.precio_base
        
        productos_detalle = []
        total_productos = 0
        for producto in orden.productos.all():
            productos_detalle.append({
                'nombre': producto.nombre,
                'precio': producto.precio_venta
            })
            total_productos += producto.precio_venta
        
        context.update({
            'servicios_detalle': servicios_detalle,
            'productos_detalle': productos_detalle,
            'total_servicios': total_servicios,
            'total_productos': total_productos,
            'total_general': total_servicios + total_productos,
            'estados_disponibles': orden.get_siguiente_estados(),
        })
        
        return context

@method_decorator(login_required, name='dispatch')
class OrdenServicioCambiarEstadoView(UpdateView):
    """Vista para cambiar el estado de una orden de servicio"""
    model = OrdenServicio
    fields = ['estado']
    template_name = 'gestion_taller/orden_servicio_cambiar_estado.html'
    
    def get_queryset(self):
        if hasattr(self.request.user, 'perfilusuario') and self.request.user.perfilusuario.cliente:
            return OrdenServicio.objects.filter(
                cliente=self.request.user.perfilusuario.cliente
            )
        return OrdenServicio.objects.none()
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['estados_disponibles'] = self.object.get_siguiente_estados()
        return context
    
    def form_valid(self, form):
        nuevo_estado = form.cleaned_data['estado']
        
        # Validar que el cambio de estado sea válido
        if not self.object.puede_cambiar_estado(nuevo_estado):
            messages.error(
                self.request, 
                f'No se puede cambiar de {self.object.get_estado_display()} a {dict(self.object._meta.get_field("estado").choices)[nuevo_estado]}'
            )
            return self.form_invalid(form)
        
        # Guardar el objeto (esto activará el manejo de inventario)
        response = super().form_valid(form)
        
        # Mensaje de éxito
        messages.success(
            self.request,
            f'Estado cambiado a {self.object.get_estado_display()} correctamente'
        )
        
        # Si es AJAX, devolver JSON
        if self.request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'message': f'Estado cambiado a {self.object.get_estado_display()}',
                'nuevo_estado': self.object.estado,
                'nuevo_estado_display': self.object.get_estado_display(),
                'redirect': self.get_success_url()
            })
        
        return response
    
    def form_invalid(self, form):
        if self.request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({
                'success': False,
                'errors': form.errors
            }, status=400)
        return super().form_invalid(form)
    
    def get_success_url(self):
        return reverse_lazy('orden_servicio_detail', kwargs={'pk': self.object.pk})

@login_required
def cambiar_estado_orden_ajax(request, pk):
    """Vista AJAX rápida para cambiar estado desde botones"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Método no permitido'}, status=405)
    
    try:
        # Obtener la orden
        orden = OrdenServicio.objects.get(
            pk=pk,
            cliente=request.user.perfilusuario.cliente
        )
        
        nuevo_estado = request.POST.get('estado')
        
        # Validar estado
        if not nuevo_estado or not orden.puede_cambiar_estado(nuevo_estado):
            return JsonResponse({
                'success': False, 
                'error': f'Cambio de estado no válido: {orden.estado} → {nuevo_estado}'
            }, status=400)
        
        # Cambiar estado
        estado_anterior = orden.get_estado_display()
        orden.estado = nuevo_estado
        orden.save()  # Esto activará el manejo de inventario
        
        return JsonResponse({
            'success': True,
            'message': f'Estado cambiado de {estado_anterior} a {orden.get_estado_display()}',
            'nuevo_estado': orden.estado,
            'nuevo_estado_display': orden.get_estado_display(),
            'estados_disponibles': orden.get_siguiente_estados()
        })
        
    except OrdenServicio.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Orden no encontrada'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': f'Error interno: {str(e)}'}, status=500)

# FUNCIONALIDADES DE PAGOS E IMPRESIÓN
@login_required
def registrar_pago_orden(request, pk):
    """Vista para registrar un pago en una orden de servicio"""
    try:
        orden = get_object_or_404(OrdenServicio, pk=pk)
        
        if request.method == 'POST':
            monto = Decimal(request.POST.get('monto', '0'))
            metodo = request.POST.get('metodo', 'efectivo')
            
            if monto <= 0:
                return JsonResponse({
                    'success': False,
                    'error': 'El monto debe ser mayor a 0'
                })
            
            # Crear el pago
            pago = Pago.objects.create(
                orden=orden,
                monto=monto,
                metodo=metodo,
                estado='completado'
            )
            
            # Verificar si la orden está completamente pagada
            total_pagado = orden.pagos.filter(estado='completado').aggregate(
                total=models.Sum('monto')
            )['total'] or Decimal('0')
            
            if total_pagado >= orden.total:
                orden.pagada = True
                orden.save()
            
            return JsonResponse({
                'success': True,
                'message': f'Pago de ${monto} registrado exitosamente',
                'total_pagado': float(total_pagado),
                'orden_pagada': orden.pagada
            })
        
        return JsonResponse({'success': False, 'error': 'Método no permitido'}, status=405)
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Error interno: {str(e)}'
        }, status=500)

@login_required
def imprimir_orden_pdf(request, pk):
    """Vista para generar PDF de la orden de servicio"""
    orden = get_object_or_404(OrdenServicio, pk=pk)
    
    # Preparar contexto para el template
    context = {
        'orden': orden,
        'servicios': orden.servicios.all(),
        'productos': orden.productos.all(),
        'pagos': orden.pagos.all(),
        'total_pagado': orden.pagos.filter(estado='completado').aggregate(
            total=models.Sum('monto')
        )['total'] or Decimal('0')
    }
    
    # Renderizar template HTML
    template = get_template('gestion_taller/orden_servicio_pdf.html')
    html = template.render(context)
    
    # Crear respuesta PDF
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="orden_{orden.id}.pdf"'
    
    # Para ahora, devolvemos HTML hasta que instalemos xhtml2pdf
    response = HttpResponse(html, content_type='text/html')
    
    return response

# ===== VISTAS PARA SERVICIOS DEL CATÁLOGO =====

@login_required
def servicios_catalogo_list(request):
    """Vista para listar servicios del catálogo del cliente"""
    cliente = request.user.perfilusuario.cliente
    servicios = ServicioCatalogo.objects.filter(cliente=cliente).order_by('-fecha_creacion')
    
    context = {
        'servicios': servicios,
        'total_servicios': servicios.count(),
        'servicios_activos': servicios.filter(activo=True).count()
    }
    return render(request, 'gestion_taller/servicios_catalogo_list.html', context)

@login_required
def servicio_catalogo_create(request):
    """Vista para crear un nuevo servicio del catálogo"""
    cliente = request.user.perfilusuario.cliente
    
    if request.method == 'POST':
        form = ServicioCatalogoForm(request.POST, cliente=cliente)
        if form.is_valid():
            servicio = form.save(commit=False)
            servicio.cliente = cliente
            servicio.save()
            form.save_m2m()  # Guardar relaciones many-to-many
            
            messages.success(request, f'Servicio "{servicio.nombre}" creado exitosamente.')
            return redirect('servicios_catalogo_list')
    else:
        form = ServicioCatalogoForm(cliente=cliente)
    
    context = {
        'form': form,
        'title': 'Crear Nuevo Servicio',
        'action': 'Crear'
    }
    return render(request, 'gestion_taller/servicio_catalogo_form.html', context)

@login_required
def servicio_catalogo_edit(request, pk):
    """Vista para editar un servicio del catálogo"""
    cliente = request.user.perfilusuario.cliente
    servicio = get_object_or_404(ServicioCatalogo, pk=pk, cliente=cliente)
    
    if request.method == 'POST':
        form = ServicioCatalogoForm(request.POST, instance=servicio, cliente=cliente)
        if form.is_valid():
            servicio = form.save()
            messages.success(request, f'Servicio "{servicio.nombre}" actualizado exitosamente.')
            return redirect('servicios_catalogo_list')
    else:
        form = ServicioCatalogoForm(instance=servicio, cliente=cliente)
    
    context = {
        'form': form,
        'servicio': servicio,
        'title': f'Editar Servicio: {servicio.nombre}',
        'action': 'Actualizar'
    }
    return render(request, 'gestion_taller/servicio_catalogo_form.html', context)

@login_required
def servicio_catalogo_delete(request, pk):
    """Vista para eliminar un servicio del catálogo"""
    cliente = request.user.perfilusuario.cliente
    servicio = get_object_or_404(ServicioCatalogo, pk=pk, cliente=cliente)
    
    if request.method == 'POST':
        nombre_servicio = servicio.nombre
        servicio.delete()
        messages.success(request, f'Servicio "{nombre_servicio}" eliminado exitosamente.')
        return redirect('servicios_catalogo_list')
    
    context = {
        'servicio': servicio
    }
    return render(request, 'gestion_taller/servicio_catalogo_confirm_delete.html', context)

@login_required
def servicio_catalogo_toggle_status(request, pk):
    """Vista AJAX para activar/desactivar un servicio"""
    if request.method == 'POST':
        cliente = request.user.perfilusuario.cliente
        servicio = get_object_or_404(ServicioCatalogo, pk=pk, cliente=cliente)
        
        servicio.activo = not servicio.activo
        servicio.save()
        
        return JsonResponse({
            'success': True,
            'activo': servicio.activo,
            'message': f'Servicio {"activado" if servicio.activo else "desactivado"} exitosamente'
        })
    
    return JsonResponse({'success': False, 'error': 'Método no permitido'}, status=405)

@login_required
def get_vehiculo_kilometraje(request):
    """Vista AJAX para obtener el kilometraje actual de un vehículo"""
    if request.method == 'GET':
        vehiculo_id = request.GET.get('vehiculo_id')
        
        if vehiculo_id:
            try:
                cliente = request.user.perfilusuario.cliente
                vehiculo = Vehiculo.objects.get(pk=vehiculo_id, cliente=cliente)
                
                return JsonResponse({
                    'success': True,
                    'kilometraje': vehiculo.kilometraje,
                    'vehiculo_info': f'{vehiculo.marca} {vehiculo.modelo} - {vehiculo.placa}'
                })
            except Vehiculo.DoesNotExist:
                return JsonResponse({
                    'success': False,
                    'error': 'Vehículo no encontrado'
                })
        else:
            return JsonResponse({
                'success': False,
                'error': 'ID de vehículo no proporcionado'
            })
    
    return JsonResponse({'success': False, 'error': 'Método no permitido'}, status=405)