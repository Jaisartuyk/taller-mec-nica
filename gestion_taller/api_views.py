from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.utils import timezone
from django.contrib import messages
from .models import RecordatorioMantenimiento
from .views_backup.whatsapp_views import get_user_cliente_or_error


@login_required
def api_generar_recordatorios_automaticos(request):
    """API para generar recordatorios automáticos"""
    if request.method == 'POST':
        try:
            cliente, error_msg = get_user_cliente_or_error(request)
            if not cliente:
                return JsonResponse({
                    'success': False,
                    'message': error_msg
                })
            
            # Importar y ejecutar el comando de generación automática
            from django.core.management import call_command
            from io import StringIO
            import sys
            
            # Capturar la salida del comando
            old_stdout = sys.stdout
            sys.stdout = captured_output = StringIO()
            
            try:
                call_command('generar_recordatorios_automaticos', cliente_id=cliente.id)
                output = captured_output.getvalue()
                
                # Extraer número de recordatorios generados del output
                generados = 0
                if 'recordatorios generados' in output:
                    import re
                    match = re.search(r'(\d+) recordatorios generados', output)
                    if match:
                        generados = int(match.group(1))
                
                return JsonResponse({
                    'success': True,
                    'message': f'Recordatorios generados exitosamente',
                    'generados': generados,
                    'output': output
                })
                
            except Exception as e:
                return JsonResponse({
                    'success': False,
                    'message': f'Error al generar recordatorios: {str(e)}'
                })
            finally:
                sys.stdout = old_stdout
                
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Error interno: {str(e)}'
            })
    
    return JsonResponse({'success': False, 'message': 'Método no permitido'}, status=405)


@login_required
def api_enviar_recordatorios_masivos(request):
    """API para enviar recordatorios masivos por WhatsApp"""
    if request.method == 'POST':
        try:
            cliente, error_msg = get_user_cliente_or_error(request)
            if not cliente:
                return JsonResponse({
                    'success': False,
                    'message': error_msg
                })
            
            # Obtener recordatorios pendientes
            recordatorios_pendientes = RecordatorioMantenimiento.objects.filter(
                vehiculo__cliente=cliente,
                notificado=False
            )
            
            if not recordatorios_pendientes.exists():
                return JsonResponse({
                    'success': False,
                    'message': 'No hay recordatorios pendientes para enviar'
                })
            
            enviados = 0
            errores = []
            
            # Importar servicio de notificaciones
            from .notification_service import NotificationService
            notification_service = NotificationService()
            
            for recordatorio in recordatorios_pendientes:
                try:
                    # Enviar recordatorio
                    resultado = notification_service.enviar_recordatorio_mantenimiento(
                        recordatorio.vehiculo.conductor,
                        recordatorio.vehiculo,
                        recordatorio
                    )
                    
                    if resultado.get('success'):
                        recordatorio.notificado = True
                        recordatorio.fecha_notificacion = timezone.now()
                        recordatorio.save()
                        enviados += 1
                    else:
                        errores.append(f"Error en {recordatorio.vehiculo.placa}: {resultado.get('message', 'Error desconocido')}")
                        
                except Exception as e:
                    errores.append(f"Error en {recordatorio.vehiculo.placa}: {str(e)}")
            
            return JsonResponse({
                'success': True,
                'message': f'Proceso completado: {enviados} recordatorios enviados',
                'enviados': enviados,
                'errores': errores
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Error interno: {str(e)}'
            })
    
    return JsonResponse({'success': False, 'message': 'Método no permitido'}, status=405)


@login_required
def api_exportar_reporte_recordatorios(request):
    """API para exportar reporte de recordatorios"""
    if request.method == 'GET':
        try:
            cliente, error_msg = get_user_cliente_or_error(request)
            if not cliente:
                return JsonResponse({
                    'success': False,
                    'message': error_msg
                })
            
            # Obtener todos los recordatorios del cliente
            recordatorios = RecordatorioMantenimiento.objects.filter(
                vehiculo__cliente=cliente
            ).select_related('vehiculo', 'vehiculo__conductor')
            
            # Preparar datos para el reporte
            reporte_data = []
            for recordatorio in recordatorios:
                reporte_data.append({
                    'vehiculo_placa': recordatorio.vehiculo.placa,
                    'vehiculo_marca': recordatorio.vehiculo.marca,
                    'vehiculo_modelo': recordatorio.vehiculo.modelo,
                    'conductor_nombre': recordatorio.vehiculo.conductor.nombre,
                    'conductor_telefono': recordatorio.vehiculo.conductor.telefono,
                    'tipo_mantenimiento': recordatorio.tipo_mantenimiento,
                    'fecha_programada': recordatorio.fecha_programada.strftime('%Y-%m-%d'),
                    'kilometraje_programado': recordatorio.kilometraje_programado,
                    'notificado': 'Sí' if recordatorio.notificado else 'No',
                    'fecha_notificacion': recordatorio.fecha_notificacion.strftime('%Y-%m-%d %H:%M') if recordatorio.fecha_notificacion else 'N/A',
                    'urgencia': recordatorio.get_urgencia_display(),
                    'dias_restantes': recordatorio.dias_restantes
                })
            
            return JsonResponse({
                'success': True,
                'data': reporte_data,
                'total_recordatorios': len(reporte_data),
                'fecha_generacion': timezone.now().strftime('%Y-%m-%d %H:%M:%S')
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Error interno: {str(e)}'
            })
    
    return JsonResponse({'success': False, 'message': 'Método no permitido'}, status=405)
