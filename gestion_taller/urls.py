from django.urls import path
from . import views

# Forzar redespliegue - Views import conflicts fixed

# Importar vistas de WhatsApp
from .views_backup.whatsapp_views import (
    whatsapp_dashboard, enviar_mensaje_individual, enviar_mensaje_masivo,
    configuracion_whatsapp, api_conductores_whatsapp, test_whatsapp_connection,
    chatbot_dashboard
)

# Importar vistas del Chatbot
from .views_backup.chatbot_views import (
    whatsapp_webhook, chatbot_test, ChatbotStatsView, chatbot_config
)

urlpatterns = [
    path('telegram_webhook/', views.telegram_webhook, name='telegram_webhook'),
    # path('api/vincular-telegram/', views.vincular_telegram, name='vincular_telegram'),  # TODO: Implementar
    path('', views.home, name='home'),
    # path('perfil/', PerfilUsuarioView.as_view(), name='perfil_usuario'),  # Comentada hasta implementar
    path('mi-perfil/', views.perfil_usuario_view, name='mi_perfil_usuario'),
    # Conductores
    path('conductores/', views.ConductorListView.as_view(), name='conductores'),
    path('conductores/nuevo/', views.ConductorCreateView.as_view(), name='conductor_nuevo'),
    path('conductores/editar/<int:pk>/', views.ConductorUpdateView.as_view(), name='conductor_editar'),
    path('conductores/eliminar/<int:pk>/', views.ConductorDeleteView.as_view(), name='conductor_eliminar'),
    path('api/conductores/', views.api_conductores, name='api_conductores'),
    
    # Vehículos
    path('vehiculos/', views.VehiculoListView.as_view(), name='vehiculos'),
    path('vehiculos/nuevo/', views.VehiculoCreateView.as_view(), name='vehiculo_nuevo'),
    path('vehiculos/editar/<int:pk>/', views.VehiculoUpdateView.as_view(), name='vehiculo_editar'),
    path('vehiculos/eliminar/<int:pk>/', views.VehiculoDeleteView.as_view(), name='vehiculo_eliminar'),

    # Repuestos
    path('repuestos/', views.RepuestoListView.as_view(), name='repuestos'),
    path('repuestos/crear/', views.RepuestoCreateView.as_view(), name='repuesto_crear'),
    path('repuestos/editar/<int:pk>/', views.RepuestoUpdateView.as_view(), name='repuesto_update'),
    path('repuestos/eliminar/<int:pk>/', views.RepuestoDeleteView.as_view(), name='repuesto_eliminar'),


    # API para obtener conductor de un vehículo
    path('api/vehiculo/<int:vehiculo_id>/conductor/', views.conductor_por_vehiculo, name='conductor_por_vehiculo'),
    # API para productos por servicio catálogo
    path('api/productos_por_servicio/', views.productos_por_servicio_catalogo, name='productos_por_servicio_catalogo'),
    # API para calcular precios de orden
    path('api/calcular-precios/', views.calcular_precios_orden, name='calcular_precios_orden'),
    # Órdenes de Servicio
    path('ordenes-servicio/', views.OrdenServicioListView.as_view(), name='orden_servicio_listado'),
    path('ordenes-servicio/nueva/', views.OrdenServicioCreateView.as_view(), name='orden_servicio_nueva'),
    path('ordenes-servicio/<int:pk>/', views.OrdenServicioDetailView.as_view(), name='orden_servicio_detail'),
    path('ordenes-servicio/<int:pk>/cambiar-estado/', views.OrdenServicioCambiarEstadoView.as_view(), name='orden_servicio_cambiar_estado'),
    path('api/ordenes-servicio/<int:pk>/cambiar-estado/', views.cambiar_estado_orden_ajax, name='cambiar_estado_orden_ajax'),
    path('api/ordenes-servicio/<int:pk>/registrar-pago/', views.registrar_pago_orden, name='registrar_pago_orden'),
    path('ordenes-servicio/<int:pk>/imprimir/', views.imprimir_orden_pdf, name='imprimir_orden_pdf'),

    # URLs para Servicios del Catálogo
    path('servicios-catalogo/', views.servicios_catalogo_list, name='servicios_catalogo_list'),
    path('servicios-catalogo/crear/', views.servicio_catalogo_create, name='servicio_catalogo_create'),
    path('servicios-catalogo/<int:pk>/editar/', views.servicio_catalogo_edit, name='servicio_catalogo_edit'),
    path('servicios-catalogo/<int:pk>/eliminar/', views.servicio_catalogo_delete, name='servicio_catalogo_delete'),
    path('api/servicios-catalogo/<int:pk>/toggle-status/', views.servicio_catalogo_toggle_status, name='servicio_catalogo_toggle_status'),
    
    # API para obtener kilometraje de vehículo
    path('api/vehiculo/kilometraje/', views.get_vehiculo_kilometraje, name='get_vehiculo_kilometraje'),
]

# URLs para WhatsApp
urlpatterns += [
    path('whatsapp/', whatsapp_dashboard, name='whatsapp_dashboard'),
    path('whatsapp/enviar-individual/', enviar_mensaje_individual, name='enviar_mensaje_individual'),
    path('whatsapp/enviar-masivo/', enviar_mensaje_masivo, name='enviar_mensaje_masivo'),
    path('whatsapp/configuracion/', configuracion_whatsapp, name='configuracion_whatsapp'),
    
    # APIs para WhatsApp
    path('api/whatsapp/conductores/', api_conductores_whatsapp, name='api_conductores_whatsapp'),
    path('api/whatsapp/test-connection/', test_whatsapp_connection, name='test_whatsapp_connection'),
    
    # URLs para Chatbot
    path('whatsapp/chatbot/', chatbot_dashboard, name='chatbot_dashboard'),
    path('webhook/whatsapp/', whatsapp_webhook, name='whatsapp_webhook'),
    path('api/chatbot/test/', chatbot_test, name='chatbot_test'),
    path('api/chatbot/stats/', ChatbotStatsView.as_view(), name='chatbot_stats'),
    path('api/chatbot/config/', chatbot_config, name='chatbot_config'),
]
