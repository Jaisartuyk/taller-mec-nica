from django.urls import path
from gestion_taller import views
from .views import home

from .views import (
    VehiculoListView, VehiculoCreateView, VehiculoUpdateView, VehiculoDeleteView,
    RepuestoListView, RepuestoCreateView, RepuestoUpdateView, RepuestoDeleteView,
    PerfilUsuarioView,
    ConductorListView, ConductorCreateView, ConductorUpdateView, ConductorDeleteView,
    OrdenServicioCreateView, OrdenServicioListView, OrdenServicioDetailView,
    conductor_por_vehiculo
)

from .views import vincular_telegram

urlpatterns = [
    path('telegram_webhook/', views.telegram_webhook, name='telegram_webhook'),
    path('api/vincular-telegram/', vincular_telegram, name='vincular_telegram'),
    path('', home, name='home'),
    path('perfil/', PerfilUsuarioView.as_view(), name='perfil_usuario'),
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
    path('repuestos/nuevo/', RepuestoCreateView.as_view(), name='repuesto_nuevo'),
    path('repuestos/editar/<int:pk>/', RepuestoUpdateView.as_view(), name='repuesto_editar'),
    path('repuestos/eliminar/<int:pk>/', RepuestoDeleteView.as_view(), name='repuesto_eliminar'),


    # API para obtener conductor de un vehículo
    path('api/vehiculo/<int:vehiculo_id>/conductor/', views.conductor_por_vehiculo, name='conductor_por_vehiculo'),
    # API para productos por servicio catálogo
    path('api/productos_por_servicio/', views.productos_por_servicio_catalogo, name='productos_por_servicio_catalogo'),
    # Órdenes de Servicio
    path('ordenes-servicio/', OrdenServicioListView.as_view(), name='orden_servicio_listado'),
    path('ordenes-servicio/nueva/', OrdenServicioCreateView.as_view(), name='orden_servicio_nueva'),
    path('ordenes-servicio/<int:pk>/', OrdenServicioDetailView.as_view(), name='orden_servicio_detalle'),




]   
