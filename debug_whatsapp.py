#!/usr/bin/env python3
"""
Script de debug para verificar la asociación usuario-cliente
"""

import os
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'taller_mecanica.settings')
django.setup()

from django.contrib.auth.models import User
from gestion_taller.models import Cliente

def debug_user_cliente_association():
    print("=== DEBUG: Asociaciones Usuario-Cliente ===")
    
    # Listar todos los usuarios
    users = User.objects.all()
    print(f"\n📋 Total de usuarios: {users.count()}")
    
    for user in users:
        print(f"\n👤 Usuario: {user.username} (ID: {user.id})")
        print(f"   - Email: {user.email}")
        print(f"   - Activo: {user.is_active}")
        print(f"   - Staff: {user.is_staff}")
        
        # Buscar cliente asociado
        cliente = Cliente.objects.filter(user=user).first()
        if cliente:
            print(f"   ✅ Cliente asociado: {cliente.nombre} (ID: {cliente.id})")
            print(f"      - Teléfono: {cliente.telefono}")
            print(f"      - Email: {cliente.email}")
        else:
            print(f"   ❌ Sin cliente asociado")
    
    # Listar todos los clientes
    print(f"\n📋 Total de clientes: {Cliente.objects.count()}")
    clientes = Cliente.objects.all()
    
    for cliente in clientes:
        print(f"\n🏢 Cliente: {cliente.nombre} (ID: {cliente.id})")
        if cliente.user:
            print(f"   ✅ Usuario asociado: {cliente.user.username}")
        else:
            print(f"   ❌ Sin usuario asociado")

if __name__ == '__main__':
    debug_user_cliente_association()
