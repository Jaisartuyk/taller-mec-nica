"""
Vistas para la integración de WhatsApp multi-taller
"""
import json
import os
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

from ..models import Cliente, Conductor, OrdenServicio, ConfiguracionTaller, InteraccionChat
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
    """Dashboard principal de WhatsApp Meta Cloud API (Multi-tenant por taller)"""
    try:
        cliente, error_msg = get_user_cliente_or_error(request)
        if not cliente:
            messages.error(request, error_msg)
            return redirect('home')

        config = cliente.configuracion
        meta_conectado = bool(
            config and config.usar_whatsapp and config.meta_phone_number_id and config.meta_access_token
        )
        whatsapp_number = (config.get_telefono_whatsapp() if config else cliente.telefono) or 'No configurado'

        total_conductores = Conductor.objects.filter(cliente=cliente).count()
        conductores_con_telefono = Conductor.objects.filter(
            cliente=cliente,
            telefono__isnull=False
        ).exclude(telefono='').count()

        ordenes_pendientes = OrdenServicio.objects.filter(
            cliente=cliente,
            estado__in=['pendiente', 'en_progreso']
        ).count()

        conductores_chat = Conductor.objects.filter(
            cliente=cliente,
            telefono__isnull=False
        ).exclude(telefono='').order_by('-bot_pausado', 'nombre')[:50]

        context = {
            'cliente': cliente,
            'config': config,
            'whatsapp_enabled': meta_conectado and cliente.tiene_whatsapp_pro,
            'meta_conectado': meta_conectado,
            'whatsapp_number': whatsapp_number,
            'total_conductores': total_conductores,
            'conductores_con_telefono': conductores_con_telefono,
            'ordenes_pendientes': ordenes_pendientes,
            'conductores_chat': conductores_chat,
            'webhook_url': request.build_absolute_uri('/webhook/whatsapp/'),
        }
    except Exception as e:
        context = {
            'error': f'Error al cargar el panel de WhatsApp: {str(e)}'
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
    cliente, error_msg = get_user_cliente_or_error(request)
    if not cliente:
        messages.error(request, error_msg)
        return redirect('home')
    
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
    """Redirige a la configuración unificada SaaS de Meta WhatsApp Cloud API y Agente IA"""
    return redirect('plan_integraciones')


@require_http_methods(["GET"])
@login_required
def api_conductores_whatsapp(request):
    """API para obtener conductores con teléfono para WhatsApp"""
    cliente, error_msg = get_user_cliente_or_error(request)
    if not cliente:
        return JsonResponse({'conductores': [], 'error': error_msg})
    
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
        cliente, error_msg = get_user_cliente_or_error(request)
        if not cliente:
            return JsonResponse({
                'success': False,
                'error': error_msg
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
    """Vista del Copiloto / Agente IA del Taller (Multi-tenant)"""
    cliente, error_msg = get_user_cliente_or_error(request)
    if not cliente:
        messages.error(request, error_msg)
        return redirect('home')

    config = cliente.configuracion
    nombre_agente = (config.agente_ia_nombre if config and config.agente_ia_nombre else 'Copiloto IA')
    gemini_activo = bool(os.environ.get('GEMINI_API_KEY', '').strip())

    context = {
        'cliente': cliente,
        'config': config,
        'nombre_agente': nombre_agente,
        'gemini_activo': gemini_activo,
        'page_title': 'Asistente IA del Taller',
    }
    return render(request, 'gestion_taller/whatsapp/chatbot_dashboard.html', context)


@require_http_methods(["POST"])
@login_required
def api_agente_ia_chat(request):
    """Endpoint AJAX para conversar con el Copiloto IA del taller"""
    cliente, error_msg = get_user_cliente_or_error(request)
    if not cliente:
        return JsonResponse({'success': False, 'error': error_msg}, status=403)

    if not cliente.tiene_whatsapp_pro:
        return JsonResponse({
            'success': False,
            'error': 'Activa el Plan Pro o Enterprise IA para usar el Asistente IA.'
        }, status=403)

    try:
        body = json.loads(request.body.decode('utf-8')) if request.body else {}
        mensaje = (body.get('mensaje') or request.POST.get('mensaje') or '').strip()
        historial = body.get('historial') if isinstance(body.get('historial'), list) else []
        if not mensaje:
            return JsonResponse({'success': False, 'error': 'Escribe una pregunta para el asistente.'}, status=400)

        from gestion_taller.services.agente_ia_service import AgenteIATallerService
        servicio = AgenteIATallerService(cliente)
        resultado = servicio.responder(mensaje, historial=historial)
        return JsonResponse({
            'success': True,
            'respuesta': resultado['respuesta'],
            'modo': resultado['modo'],
            'herramientas_usadas': resultado.get('herramientas_usadas', []),
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': f'Error procesando consulta: {str(e)}'}, status=500)


@require_http_methods(["GET"])
@login_required
def api_whatsapp_historial(request, conductor_id):
    """Obtiene el historial de mensajes WhatsApp de un conductor y estado del bot"""
    cliente, error_msg = get_user_cliente_or_error(request)
    if not cliente:
        return JsonResponse({'success': False, 'error': error_msg}, status=403)

    conductor = get_object_or_404(Conductor, pk=conductor_id, cliente=cliente)
    interacciones = InteraccionChat.objects.filter(
        cliente=cliente,
        conductor=conductor
    ).order_by('fecha_creacion')[:100]

    mensajes = []
    for item in interacciones:
        fecha_str = item.fecha_creacion.strftime('%d/%m %H:%M')
        url_media = item.archivo.url if item.archivo else (item.media_url or '')
        t_media = item.tipo_media or ''
        if item.mensaje or (url_media and not item.respuesta):
            mensajes.append({
                'emisor': 'cliente',
                'texto': item.mensaje,
                'fecha': fecha_str,
                'tipo_media': t_media if not item.respuesta else '',
                'media_url': url_media if not item.respuesta else '',
            })
        if item.respuesta or (url_media and item.respuesta):
            es_humano = item.respuesta.startswith('[Humano]')
            texto_limpio = item.respuesta.replace('[Humano] ', '', 1).replace('[Humano]', '', 1) if es_humano else item.respuesta
            mensajes.append({
                'emisor': 'humano' if es_humano else 'bot',
                'texto': texto_limpio,
                'fecha': fecha_str,
                'tipo_media': t_media,
                'media_url': url_media,
            })

    return JsonResponse({
        'success': True,
        'conductor': {
            'id': conductor.id,
            'nombre': conductor.nombre,
            'telefono': conductor.telefono or '',
            'bot_pausado': conductor.bot_pausado,
        },
        'mensajes': mensajes,
    })


@require_http_methods(["POST"])
@login_required
def api_whatsapp_toggle_bot(request, conductor_id):
    """Pausa o reactiva el bot automático para un cliente específico (atención humana)"""
    cliente, error_msg = get_user_cliente_or_error(request)
    if not cliente:
        return JsonResponse({'success': False, 'error': error_msg}, status=403)

    conductor = get_object_or_404(Conductor, pk=conductor_id, cliente=cliente)
    conductor.bot_pausado = not conductor.bot_pausado
    conductor.save(update_fields=['bot_pausado'])
    return JsonResponse({
        'success': True,
        'bot_pausado': conductor.bot_pausado,
        'mensaje': 'Bot pausado: ahora atiendes manualmente.' if conductor.bot_pausado else 'Bot reactivado automáticamente.',
    })


@require_http_methods(["POST"])
@login_required
def api_whatsapp_responder_humano(request, conductor_id):
    """Envía una respuesta manual (texto, imagen, audio o video) desde el taller al cliente"""
    import requests as http_requests

    cliente, error_msg = get_user_cliente_or_error(request)
    if not cliente:
        return JsonResponse({'success': False, 'error': error_msg}, status=403)

    conductor = get_object_or_404(Conductor, pk=conductor_id, cliente=cliente)

    archivo = request.FILES.get('archivo')
    if request.content_type and 'application/json' in request.content_type:
        body = json.loads(request.body.decode('utf-8')) if request.body else {}
        texto = (body.get('mensaje') or '').strip()
    else:
        texto = (request.POST.get('mensaje') or '').strip()

    if not texto and not archivo:
        return JsonResponse({'success': False, 'error': 'Escribe un mensaje o adjunta un archivo.'}, status=400)

    tipo_media = ''
    if archivo:
        ctype = (archivo.content_type or '').lower()
        if ctype.startswith('image/'):
            tipo_media = 'image'
        elif ctype.startswith('audio/'):
            tipo_media = 'audio'
        elif ctype.startswith('video/'):
            tipo_media = 'video'
        else:
            return JsonResponse({'success': False, 'error': 'Solo se permiten imágenes, audios o videos.'}, status=400)

    # Registrar en historial
    interaccion = InteraccionChat.objects.create(
        cliente=cliente,
        conductor=conductor,
        telefono=conductor.telefono or '',
        mensaje='',
        respuesta=f'[Humano] {texto}' if texto else '[Humano]',
        archivo=archivo if archivo else None,
        tipo_media=tipo_media,
        tipo='seguimiento',
    )

    # Enviar vía Meta WhatsApp Cloud API si el taller tiene credenciales activas
    enviado_meta = False
    config = cliente.configuracion
    if config and config.meta_phone_number_id and config.meta_access_token and conductor.telefono:
        tel_limpio = ''.join(c for c in conductor.telefono if c.isdigit())
        headers = {'Authorization': f'Bearer {config.meta_access_token}'}
        try:
            if archivo and tipo_media:
                # 1. Subir archivo a Meta Media API
                media_url_api = f"https://graph.facebook.com/v20.0/{config.meta_phone_number_id}/media"
                interaccion.archivo.open('rb')
                files = {'file': (archivo.name, interaccion.archivo, archivo.content_type)}
                upload_resp = http_requests.post(
                    media_url_api,
                    headers=headers,
                    data={'messaging_product': 'whatsapp'},
                    files=files,
                    timeout=20,
                )
                interaccion.archivo.close()
                if upload_resp.status_code in (200, 201):
                    media_id = upload_resp.json().get('id')
                    payload_media = {'id': media_id}
                    if texto and tipo_media in ('image', 'video'):
                        payload_media['caption'] = texto
                    msg_resp = http_requests.post(
                        f"https://graph.facebook.com/v20.0/{config.meta_phone_number_id}/messages",
                        headers={**headers, 'Content-Type': 'application/json'},
                        json={
                            'messaging_product': 'whatsapp',
                            'to': tel_limpio,
                            'type': tipo_media,
                            tipo_media: payload_media,
                        },
                        timeout=10,
                    )
                    enviado_meta = msg_resp.status_code in (200, 201)
            elif texto:
                msg_resp = http_requests.post(
                    f"https://graph.facebook.com/v20.0/{config.meta_phone_number_id}/messages",
                    headers={**headers, 'Content-Type': 'application/json'},
                    json={
                        'messaging_product': 'whatsapp',
                        'to': tel_limpio,
                        'type': 'text',
                        'text': {'body': texto},
                    },
                    timeout=10,
                )
                enviado_meta = msg_resp.status_code in (200, 201)
        except Exception:
            enviado_meta = False

    return JsonResponse({
        'success': True,
        'enviado_meta': enviado_meta,
        'texto': texto,
        'tipo_media': tipo_media,
        'media_url': interaccion.archivo.url if interaccion.archivo else '',
    })
