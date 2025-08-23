#!/usr/bin/env python3
"""
Script de debug v2 para verificar la función get_user_cliente_or_error
"""

import os
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'taller_mecanica.settings')
django.setup()

from django.contrib.auth.models import User
from gestion_taller.models import Cliente

# Importar la función que estamos usando en las vistas
import sys
sys.path.append('gestion_taller/views_backup')

def debug_get_user_cliente_function():
    print("=== DEBUG: Función get_user_cliente_or_error ===")
    
    # Simular request para cada usuario
    class MockRequest:
        def __init__(self, user):
            self.user = user
    
    users = User.objects.all()
    
    for user in users:
        print(f"\n👤 Probando usuario: {user.username}")
        
        # Método directo (como en nuestro script anterior)
        cliente_directo = Cliente.objects.filter(user=user).first()
        print(f"   Consulta directa: {cliente_directo}")
        
        # Método usando related_name
        try:
            cliente_related = user.perfil_cliente
            print(f"   Via related_name: {cliente_related}")
        except:
            print(f"   Via related_name: None (no existe)")
        
        # Simular la función get_user_cliente_or_error
        mock_request = MockRequest(user)
        cliente_funcion = Cliente.objects.filter(user=mock_request.user).first()
        print(f"   Función simulada: {cliente_funcion}")
        
        # Verificar si el user está autenticado
        print(f"   Usuario autenticado: {user.is_authenticated}")
        print(f"   Usuario activo: {user.is_active}")

def debug_reverse_lookup():
    print("\n=== DEBUG: Lookup Inverso ===")
    
    clientes = Cliente.objects.all()
    for cliente in clientes:
        print(f"\n🏢 Cliente: {cliente.nombre}")
        print(f"   User field: {cliente.user}")
        if cliente.user:
            print(f"   User ID: {cliente.user.id}")
            print(f"   Username: {cliente.user.username}")
            print(f"   User activo: {cliente.user.is_active}")

if __name__ == '__main__':
    debug_get_user_cliente_function()
    debug_reverse_lookup()
