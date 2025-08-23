"""
Vistas para la integración de WhatsApp multi-taller
"""
import json
import time
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views.generic import ListView, CreateView, UpdateView
from django.urls import reverse_lazy
import json

from ..models import Cliente, Conductor, OrdenServicio, ConfiguracionTaller
from ..services.multi_taller_messaging import MultiTallerMessagingService
from ..services.chatbot_service import ChatbotService
from ..forms import ConfiguracionTallerForm


def get_user_cliente_or_error(request):
    """Obtiene el cliente asociado al usuario autenticado de forma segura"""
    try:
        # Buscar cliente a través de PerfilUsuario
        perfil = request.user.perfilusuario
        cliente = perfil.cliente
        
        if not cliente:
            return None, "No tienes un taller asociado. Contacta al administrador."
        
        return cliente, None
        
    except Exception as e:
        return None, "No tienes un perfil de usuario válido. Contacta al administrador."


@login_required
def whatsapp_dashboard(request):
    """Dashboard principal de WhatsApp con información del sistema"""
    # Obtener información del cliente actual - SOLO SU PROPIO TALLER
    try:
        cliente, error_msg = get_user_cliente_or_error(request)
        if not cliente:
            messages.error(request, error_msg)
            return redirect('home')
        
        if cliente:
            messaging_service = MultiTallerMessagingService(cliente=cliente)
            
            # Información del taller
            taller_info = messaging_service.get_taller_info()
            whatsapp_enabled = messaging_service._is_whatsapp_enabled()
            whatsapp_number = messaging_service.get_whatsapp_number()
            
            # Estadísticas básicas
            total_conductores = Conductor.objects.filter(cliente=cliente).count()
            conductores_con_telefono = Conductor.objects.filter(
                cliente=cliente, 
                telefono__isnull=False
            ).exclude(telefono='').count()
            
            ordenes_pendientes = OrdenServicio.objects.filter(
                vehiculo__conductor__cliente=cliente,
                estado__in=['pendiente', 'en_proceso']
            ).count()
            
            context = {
                'cliente': cliente,
                'taller_info': taller_info,
                'whatsapp_enabled': whatsapp_enabled,
                'whatsapp_number': whatsapp_number,
                'total_conductores': total_conductores,
                'conductores_con_telefono': conductores_con_telefono,
                'ordenes_pendientes': ordenes_pendientes,
                'messaging_service': messaging_service,
            }
        else:
            context = {
                'error': 'No hay clientes configurados en el sistema'
            }
            
    except Exception as e:
        context = {
            'error': f'Error al cargar la configuración: {str(e)}'
        }
    
    return render(request, 'gestion_taller/whatsapp/dashboard.html', context)


@login_required
def enviar_mensaje_individual(request):
    """Vista para enviar mensajes individuales por WhatsApp"""
    if request.method == 'POST':
        try:
            # Obtener datos del formulario
            telefono = request.POST.get('telefono')
            mensaje = request.POST.get('mensaje')
            tipo_mensaje = request.POST.get('tipo_mensaje')
            conductor_id = request.POST.get('conductor_id')
            
            # Obtener cliente - SOLO SU PROPIO TALLER
            cliente, error_msg = get_user_cliente_or_error(request)
            if not cliente:
                return JsonResponse({
                    'success': False,
                    'error': error_msg
                })
            
            # Inicializar servicio de mensajería
            messaging_service = MultiTallerMessagingService(cliente=cliente)
            
            # Datos adicionales para plantillas
            datos = {}
            if conductor_id:
                try:
                    conductor = Conductor.objects.get(id=conductor_id, cliente=cliente)
                    datos['conductor_nombre'] = conductor.nombre
                    datos['conductor_telefono'] = conductor.telefono
                    if conductor.vehiculos.exists():
                        vehiculo = conductor.vehiculos.first()
                        datos['vehiculo_placa'] = vehiculo.placa
                        datos['vehiculo_marca'] = vehiculo.marca
                        datos['vehiculo_modelo'] = vehiculo.modelo
                except Conductor.DoesNotExist:
                    pass
            
            # Enviar mensaje
            if mensaje:
                # Mensaje personalizado
                resultado = messaging_service.enviar_mensaje(
                    telefono=telefono,
                    tipo_mensaje='personalizado',
                    datos={'mensaje_personalizado': mensaje},
                    canal='whatsapp'
                )
            elif tipo_mensaje:
                # Plantilla de mensaje
                resultado = messaging_service.enviar_mensaje(
                    telefono=telefono,
                    tipo_mensaje=tipo_mensaje,
                    datos=datos,
                    canal='whatsapp'
                )
            else:
                return JsonResponse({
                    'success': False,
                    'error': 'Debe proporcionar un mensaje o tipo de mensaje'
                })
            
            # Procesar resultado
            if resultado.get('whatsapp', {}).get('success'):
                return JsonResponse({
                    'success': True,
                    'message': 'Mensaje enviado exitosamente',
                    'message_id': resultado['whatsapp'].get('message_id')
                })
            else:
                error = resultado.get('whatsapp', {}).get('error', 'Error desconocido')
                return JsonResponse({
                    'success': False,
                    'error': f'Error al enviar mensaje: {error}'
                })
                
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': f'Error interno: {str(e)}'
            })
    
    # GET request - mostrar formulario
    cliente, error_msg = get_user_cliente_or_error(request)
    if not cliente:
        messages.error(request, error_msg)
        return redirect('home')
    
    conductores = []
    if cliente:
        conductores = Conductor.objects.filter(
            cliente=cliente,
            telefono__isnull=False
        ).exclude(telefono='').order_by('nombre')
    
    context = {
        'cliente': cliente,
        'conductores': conductores,
        'tipos_mensaje': [
            ('bienvenida', 'Mensaje de Bienvenida'),
            ('vehiculo_listo', 'Vehículo Listo'),
            ('recordatorio', 'Recordatorio de Mantenimiento'),
            ('promocion', 'Promoción Especial'),
            ('diagnostico', 'Diagnóstico Completado'),
        ]
    }
    
    return render(request, 'gestion_taller/whatsapp/enviar_mensaje.html', context)


@login_required
def enviar_mensaje_masivo(request):
    """Vista para enviar mensajes masivos por WhatsApp"""
    if request.method == 'POST':
        try:
            # Obtener datos del formulario
            mensaje = request.POST.get('mensaje')
            tipo_mensaje = request.POST.get('tipo_mensaje')
            conductores_ids = request.POST.getlist('conductores')
            
            # Obtener cliente - SOLO SU PROPIO TALLER
            cliente, error_msg = get_user_cliente_or_error(request)
            if not cliente:
                return JsonResponse({
                    'success': False,
                    'error': error_msg
                })
            
            # Inicializar servicio de mensajería
            messaging_service = MultiTallerMessagingService(cliente=cliente)
            
            # Obtener conductores seleccionados
            conductores = Conductor.objects.filter(
                id__in=conductores_ids,
                cliente=cliente,
                telefono__isnull=False
            ).exclude(telefono='')
            
            if not conductores.exists():
                return JsonResponse({
                    'success': False,
                    'error': 'No hay conductores válidos seleccionados'
                })
            
            # Enviar mensajes
            resultados = {
                'exitosos': 0,
                'fallidos': 0,
                'detalles': []
            }
            
            for i, conductor in enumerate(conductores):
                # Agregar delay de 5 segundos entre mensajes (excepto el primero)
                if i > 0:
                    time.sleep(5)
                
                # Preparar datos para plantillas
                datos = {
                    'conductor_nombre': conductor.nombre,
                    'conductor_telefono': conductor.telefono,
                }
                
                if conductor.vehiculos.exists():
                    vehiculo = conductor.vehiculos.first()
                    datos.update({
                        'vehiculo_placa': vehiculo.placa,
                        'vehiculo_marca': vehiculo.marca,
                        'vehiculo_modelo': vehiculo.modelo,
                    })
                
                # Enviar mensaje
                if mensaje:
                    # Mensaje personalizado
                    datos['mensaje_personalizado'] = mensaje
                    resultado = messaging_service.enviar_mensaje(
                        telefono=conductor.telefono,
                        tipo_mensaje='personalizado',
                        datos=datos,
                        canal='whatsapp'
                    )
                elif tipo_mensaje:
                    # Plantilla de mensaje
                    resultado = messaging_service.enviar_mensaje(
                        telefono=conductor.telefono,
                        tipo_mensaje=tipo_mensaje,
                        datos=datos,
                        canal='whatsapp'
                    )
                
                # Procesar resultado
                if resultado.get('whatsapp', {}).get('success'):
                    resultados['exitosos'] += 1
                    resultados['detalles'].append({
                        'conductor': conductor.nombre,
                        'telefono': conductor.telefono,
                        'status': 'exitoso'
                    })
                else:
                    resultados['fallidos'] += 1
                    error = resultado.get('whatsapp', {}).get('error', 'Error desconocido')
                    resultados['detalles'].append({
                        'conductor': conductor.nombre,
                        'telefono': conductor.telefono,
                        'status': 'fallido',
                        'error': error
                    })
            
            return JsonResponse({
                'success': True,
                'resultados': resultados
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': f'Error interno: {str(e)}'
            })
    
    # GET request - mostrar formulario
    cliente = Cliente.objects.filter(user=request.user).first()
    if not cliente:
        cliente = Cliente.objects.first()
    
    conductores = []
    if cliente:
        conductores = Conductor.objects.filter(
            cliente=cliente,
            telefono__isnull=False
        ).exclude(telefono='').order_by('nombre')
    
    context = {
        'cliente': cliente,
        'conductores': conductores,
        'tipos_mensaje': [
            ('bienvenida', 'Mensaje de Bienvenida'),
            ('vehiculo_listo', 'Vehículo Listo'),
            ('recordatorio', 'Recordatorio de Mantenimiento'),
            ('promocion', 'Promoción Especial'),
            ('diagnostico', 'Diagnóstico Completado'),
        ]
    }
    
    return render(request, 'gestion_taller/whatsapp/enviar_masivo.html', context)


@login_required
def configuracion_whatsapp(request):
    """Vista para configurar WhatsApp del taller"""
    cliente = Cliente.objects.filter(user=request.user).first()
    if not cliente:
        cliente = Cliente.objects.first()
    
    if not cliente:
        messages.error(request, 'No hay clientes configurados en el sistema')
        return redirect('whatsapp_dashboard')
    
    # Obtener o crear configuración del taller
    taller_config = cliente.configuracion
    if not taller_config:
        # Crear nueva configuración
        taller_config = ConfiguracionTaller.objects.create(
            nombre=cliente.nombre,
            codigo=f"TALLER-{cliente.id:03d}",
            telefono_principal=cliente.telefono,
            email=cliente.correo or '',
            direccion=cliente.direccion or '',
            ciudad='',
            usar_whatsapp=True,
        )
        # Asociar la configuración al cliente
        cliente.configuracion = taller_config
        cliente.save()
        created = True
    else:
        created = False
    
    if request.method == 'POST':
        form = ConfiguracionTallerForm(request.POST, instance=taller_config)
        if form.is_valid():
            form.save()
            messages.success(request, 'Configuración de WhatsApp actualizada exitosamente')
            return redirect('whatsapp_dashboard')
    else:
        form = ConfiguracionTallerForm(instance=taller_config)
    
    context = {
        'form': form,
        'cliente': cliente,
        'taller_config': taller_config,
    }
    
    return render(request, 'gestion_taller/whatsapp/configuracion.html', context)


@require_http_methods(["GET"])
@login_required
def api_conductores_whatsapp(request):
    """API para obtener conductores con teléfono para WhatsApp"""
    cliente = Cliente.objects.filter(user=request.user).first()
    if not cliente:
        cliente = Cliente.objects.first()
    
    if not cliente:
        return JsonResponse({'conductores': []})
    
    conductores = Conductor.objects.filter(
        cliente=cliente,
        telefono__isnull=False
    ).exclude(telefono='').values(
        'id', 'nombre', 'telefono', 'email'
    ).order_by('nombre')
    
    return JsonResponse({'conductores': list(conductores)})


@require_http_methods(["POST"])
@login_required
def test_whatsapp_connection(request):
    """Prueba la conexión de WhatsApp"""
    try:
        cliente = Cliente.objects.filter(user=request.user).first()
        if not cliente:
            return JsonResponse({
                'success': False,
                'error': 'Cliente no encontrado'
            })
        
        messaging_service = MultiTallerMessagingService(cliente=cliente)
        
        # Probar conexión
        if messaging_service._is_whatsapp_enabled():
            return JsonResponse({
                'success': True,
                'message': 'Conexión WhatsApp exitosa',
                'service_info': {
                    'whatsapp_enabled': True,
                    'telegram_enabled': False
                }
            })
        else:
            return JsonResponse({
                'success': False,
                'error': 'WhatsApp no está configurado'
            })
            
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })


@login_required
def chatbot_dashboard(request):
    """Dashboard del chatbot de WhatsApp"""
    try:
        # Buscar cliente asociado al usuario - SOLO SU PROPIO CLIENTE
        cliente = Cliente.objects.filter(user=request.user).first()
        
        # Si no hay cliente asociado, denegar acceso por seguridad
        if not cliente:
            messages.error(request, 'No tienes un taller asociado. Contacta al administrador para configurar tu acceso.')
            return redirect('home')  # Redirigir a home en lugar de whatsapp_dashboard
        
        # Verificar si el chatbot está habilitado
        messaging_service = MultiTallerMessagingService(cliente=cliente)
        chatbot_enabled = messaging_service._is_whatsapp_enabled()
        
        context = {
            'cliente': cliente,
            'page_title': 'Chatbot WhatsApp',
            'chatbot_enabled': chatbot_enabled,
            'user': request.user
        }
        
        return render(request, 'gestion_taller/whatsapp/chatbot_dashboard.html', context)
        
    except Exception as e:
        messages.error(request, f'Error cargando dashboard del chatbot: {str(e)}')
        return redirect('whatsapp_dashboard')
