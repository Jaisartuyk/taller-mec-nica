#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'taller_mecanica.settings')
django.setup()

from django.db import connection

def check_interaccion_table():
    cursor = connection.cursor()
    
    # Verificar si la tabla existe
    cursor.execute("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public' 
        AND table_name LIKE '%interaccion%';
    """)
    tables = cursor.fetchall()
    print('Tablas que contienen interaccion:', tables)
    
    # Verificar estructura de la tabla si existe
    try:
        cursor.execute("""
            SELECT column_name, data_type, is_nullable 
            FROM information_schema.columns 
            WHERE table_name = 'gestion_taller_interaccionchat'
            ORDER BY ordinal_position;
        """)
        columns = cursor.fetchall()
        print('\nColumnas de gestion_taller_interaccionchat:')
        for col in columns:
            print(f'  {col[0]}: {col[1]} (nullable: {col[2]})')
    except Exception as e:
        print(f'Error al consultar estructura: {e}')
    
    # Verificar también la tabla Cita
    try:
        cursor.execute("""
            SELECT column_name, data_type, is_nullable 
            FROM information_schema.columns 
            WHERE table_name = 'gestion_taller_cita'
            ORDER BY ordinal_position;
        """)
        columns = cursor.fetchall()
        print('\nColumnas de gestion_taller_cita:')
        for col in columns:
            print(f'  {col[0]}: {col[1]} (nullable: {col[2]})')
    except Exception as e:
        print(f'Error al consultar estructura de Cita: {e}')

if __name__ == '__main__':
    check_interaccion_table()
