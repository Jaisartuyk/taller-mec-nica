#!/usr/bin/env python3
"""
Script para verificar las asociaciones en PerfilUsuario
"""

import os
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'taller_mecanica.settings')
django.setup()

from django.contrib.auth.models import User
from gestion_taller.models import Cliente, PerfilUsuario

def debug_perfil_usuario():
    print("=== DEBUG: PerfilUsuario ===")
    
    users = User.objects.all()
    
    for user in users:
        print(f"\n👤 Usuario: {user.username}")
        
        # Verificar PerfilUsuario
        try:
            perfil = user.perfilusuario
            print(f"   ✅ Tiene PerfilUsuario: {perfil}")
            print(f"   Rol: {perfil.rol}")
            
            # Verificar si PerfilUsuario tiene referencia a Cliente
            if hasattr(perfil, 'cliente'):
                print(f"   Cliente en perfil: {perfil.cliente}")
            else:
                print("   ❌ PerfilUsuario no tiene campo cliente")
                
        except PerfilUsuario.DoesNotExist:
            print("   ❌ Sin PerfilUsuario")
        
        # Verificar Cliente directamente
        cliente_directo = Cliente.objects.filter(user=user).first()
        print(f"   Cliente directo: {cliente_directo}")

def debug_admin_relationships():
    print("\n=== DEBUG: Verificar todas las relaciones ===")
    
    # Verificar campos del modelo PerfilUsuario
    print("\nCampos de PerfilUsuario:")
    for field in PerfilUsuario._meta.fields:
        print(f"   - {field.name}: {field.__class__.__name__}")
    
    # Verificar campos del modelo Cliente
    print("\nCampos de Cliente:")
    for field in Cliente._meta.fields:
        print(f"   - {field.name}: {field.__class__.__name__}")

if __name__ == '__main__':
    debug_perfil_usuario()
    debug_admin_relationships()
