#!/usr/bin/env python3
"""
Script para crear asociaciones Usuario-Cliente
"""

import os
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'taller_mecanica.settings')
django.setup()

from django.contrib.auth.models import User
from gestion_taller.models import Cliente

def create_user_cliente_associations():
    print("=== CREANDO ASOCIACIONES USUARIO-CLIENTE ===")
    
    # Asociaciones sugeridas basadas en nombres/emails
    associations = [
        {
            'user_username': 'myrnatixe21',
            'cliente_nombre': 'LUBRICENTRO MYRNA',
            'reason': 'Nombre similar (Myrna)'
        },
        {
            'user_username': 'jairo',  # Usuario admin
            'cliente_nombre': 'deaquipaya',
            'reason': 'Usuario admin principal'
        },
        {
            'user_username': 'wchoez',
            'cliente_nombre': 'El tuercas',
            'reason': 'Asociación por defecto'
        }
    ]
    
    for assoc in associations:
        try:
            user = User.objects.get(username=assoc['user_username'])
            cliente = Cliente.objects.get(nombre=assoc['cliente_nombre'])
            
            # Crear la asociación
            cliente.user = user
            cliente.save()
            
            print(f"✅ Asociado: {user.username} → {cliente.nombre}")
            print(f"   Razón: {assoc['reason']}")
            
        except User.DoesNotExist:
            print(f"❌ Usuario no encontrado: {assoc['user_username']}")
        except Cliente.DoesNotExist:
            print(f"❌ Cliente no encontrado: {assoc['cliente_nombre']}")
        except Exception as e:
            print(f"❌ Error: {e}")
    
    print("\n=== VERIFICACIÓN FINAL ===")
    
    # Verificar asociaciones creadas
    for cliente in Cliente.objects.all():
        if cliente.user:
            print(f"✅ {cliente.nombre} → {cliente.user.username}")
        else:
            print(f"❌ {cliente.nombre} → Sin usuario")

if __name__ == '__main__':
    create_user_cliente_associations()
