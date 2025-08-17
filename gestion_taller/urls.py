from django.urls import path
from gestion_taller import views
from .views import (
    home, cambiar_estado_orden_ajax, registrar_pago_orden, imprimir_orden_pdf,
    servicios_catalogo_list, servicio_catalogo_create, servicio_catalogo_edit, 
    servicio_catalogo_delete, servicio_catalogo_toggle_status, vincular_telegram,
    conductor_por_vehiculo, productos_por_servicio_catalogo,
    # Vistas de clase implementadas
    VehiculoListView, VehiculoCreateView, VehiculoUpdateView, VehiculoDeleteView,
    RepuestoListView, RepuestoCreateView, RepuestoUpdateView, RepuestoDeleteView,
    ConductorListView, ConductorCreateView, ConductorUpdateView, ConductorDeleteView,
    OrdenServicioListView, OrdenServicioCreateView, OrdenServicioDetailView, OrdenServicioCambiarEstadoView
)

urlpatterns = [
    path('telegram_webhook/', views.telegram_webhook, name='telegram_webhook'),
    path('api/vincular-telegram/', vincular_telegram, name='vincular_telegram'),
    path('', home, name='home'),
    # path('perfil/', PerfilUsuarioView.as_view(), name='perfil_usuario'),  # Comentada hasta implementar
    path('mi-perfil/', views.perfil_usuario_view, name='mi_perfil_usuario'),
    # Conductores
    path('conductores/', ConductorListView.as_view(), name='conductores'),
    path('conductores/nuevo/', ConductorCreateView.as_view(), name='conductor_nuevo'),
    path('conductores/editar/<int:pk>/', ConductorUpdateView.as_view(), name='conductor_editar'),
    path('conductores/eliminar/<int:pk>/', ConductorDeleteView.as_view(), name='conductor_eliminar'),
    path('api/conductores/', views.api_conductores, name='api_conductores'),
    
    # Vehículos
    path('vehiculos/', VehiculoListView.as_view(), name='vehiculos'),
    path('vehiculos/nuevo/', VehiculoCreateView.as_view(), name='vehiculo_nuevo'),
    path('vehiculos/editar/<int:pk>/', VehiculoUpdateView.as_view(), name='vehiculo_editar'),
    path('vehiculos/eliminar/<int:pk>/', VehiculoDeleteView.as_view(), name='vehiculo_eliminar'),

    # Repuestos
    path('repuestos/', RepuestoListView.as_view(), name='repuestos'),
    path('repuestos/crear/', RepuestoCreateView.as_view(), name='repuesto_crear'),
    path('repuestos/editar/<int:pk>/', RepuestoUpdateView.as_view(), name='repuesto_update'),
    path('repuestos/eliminar/<int:pk>/', RepuestoDeleteView.as_view(), name='repuesto_eliminar'),


    # API para obtener conductor de un vehículo
    path('api/vehiculo/<int:vehiculo_id>/conductor/', conductor_por_vehiculo, name='conductor_por_vehiculo'),
    # API para productos por servicio catálogo
    path('api/productos_por_servicio/', productos_por_servicio_catalogo, name='productos_por_servicio_catalogo'),
    # API para calcular precios de orden
    path('api/calcular-precios/', views.calcular_precios_orden, name='calcular_precios_orden'),
    # Órdenes de Servicio
    path('ordenes-servicio/', OrdenServicioListView.as_view(), name='orden_servicio_listado'),
    path('ordenes-servicio/nueva/', OrdenServicioCreateView.as_view(), name='orden_servicio_nueva'),
    path('ordenes-servicio/<int:pk>/', OrdenServicioDetailView.as_view(), name='orden_servicio_detail'),
    path('ordenes-servicio/<int:pk>/cambiar-estado/', OrdenServicioCambiarEstadoView.as_view(), name='orden_servicio_cambiar_estado'),
    path('api/ordenes-servicio/<int:pk>/cambiar-estado/', cambiar_estado_orden_ajax, name='cambiar_estado_orden_ajax'),
    path('api/ordenes-servicio/<int:pk>/registrar-pago/', registrar_pago_orden, name='registrar_pago_orden'),
    path('ordenes-servicio/<int:pk>/imprimir/', imprimir_orden_pdf, name='imprimir_orden_pdf'),

    # URLs para Servicios del Catálogo
    path('servicios-catalogo/', servicios_catalogo_list, name='servicios_catalogo_list'),
    path('servicios-catalogo/crear/', servicio_catalogo_create, name='servicio_catalogo_create'),
    path('servicios-catalogo/<int:pk>/editar/', servicio_catalogo_edit, name='servicio_catalogo_edit'),
    path('servicios-catalogo/<int:pk>/eliminar/', servicio_catalogo_delete, name='servicio_catalogo_delete'),
    path('api/servicios-catalogo/<int:pk>/toggle-status/', servicio_catalogo_toggle_status, name='servicio_catalogo_toggle_status'),
    
    # API para obtener kilometraje de vehículo
    path('api/vehiculo/kilometraje/', views.get_vehiculo_kilometraje, name='get_vehiculo_kilometraje'),

    path('repuestos/editar/<int:pk>/', RepuestoUpdateView.as_view(), name='repuesto_update')
]
