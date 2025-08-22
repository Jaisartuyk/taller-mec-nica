# Sistema de Predicción de Cambio de Aceite con IA

## 🤖 Descripción

Este sistema utiliza inteligencia artificial para predecir cuándo los vehículos necesitarán cambio de aceite, enviando notificaciones automáticas a los conductores vía Telegram.

## 🚀 Características

- **Predicción con IA**: Usa machine learning para predecir cambios de aceite basado en historial
- **Predicción básica**: Fallback usando intervalos estándar cuando no hay suficientes datos
- **Notificaciones automáticas**: Envía recordatorios por Telegram
- **Multi-tenant**: Funciona independientemente para cada taller
- **Comandos de Telegram**: Interfaz completa para conductores y administradores

## 📋 Comandos de Telegram

### Para Conductores:
- `/recordatorios` - Ver recordatorios pendientes
- `/proximo_aceite` - Ver próximos cambios de aceite con predicción IA
- `/ayuda` - Ver todos los comandos disponibles

### Para Administradores:
- `/entrenar_ia` - Entrenar modelo de IA con datos históricos
- `/verificar_recordatorios` - Verificar y enviar recordatorios pendientes
- `/recordatorios_pendientes` - Ver todos los recordatorios del taller

## 🛠️ Instalación

1. **Instalar dependencias**:
```bash
pip install -r requirements.txt
```

2. **Ejecutar migraciones** (si es necesario):
```bash
python manage.py makemigrations
python manage.py migrate
```

3. **Crear directorio para modelos**:
```bash
mkdir ml_models
```

## 📊 Uso Manual

### Verificar recordatorios manualmente:
```bash
python manage.py verificar_recordatorios
```

### Entrenar modelos de IA:
```bash
python manage.py verificar_recordatorios --entrenar-ia
```

### Para un cliente específico:
```bash
python manage.py verificar_recordatorios --cliente-id 1 --entrenar-ia
```

## ⚙️ Automatización

### Opción 1: Cron (Linux/Mac)
Agregar a crontab:
```bash
# Verificar recordatorios diariamente a las 9:00 AM
0 9 * * * cd /path/to/project && python manage.py verificar_recordatorios

# Entrenar modelos semanalmente los lunes a las 2:00 AM
0 2 * * 1 cd /path/to/project && python manage.py verificar_recordatorios --entrenar-ia
```

### Opción 2: Task Scheduler (Windows)
1. Abrir "Programador de tareas"
2. Crear tarea básica
3. Configurar para ejecutar diariamente
4. Acción: `python manage.py verificar_recordatorios`

### Opción 3: Celery (Recomendado para producción)
1. Instalar Celery: `pip install celery redis`
2. Configurar en `settings.py`:
```python
CELERY_BROKER_URL = 'redis://localhost:6379'
CELERY_RESULT_BACKEND = 'redis://localhost:6379'

from celery.schedules import crontab
CELERY_BEAT_SCHEDULE = {
    'verificar-recordatorios-diarios': {
        'task': 'gestion_taller.tasks.verificar_recordatorios_diarios',
        'schedule': crontab(hour=9, minute=0),
    },
    'entrenar-modelos-semanalmente': {
        'task': 'gestion_taller.tasks.entrenar_modelos_ia_semanalmente',
        'schedule': crontab(hour=2, minute=0, day_of_week=1),
    },
}
```

3. Ejecutar workers:
```bash
celery -A taller_mecanica worker --loglevel=info
celery -A taller_mecanica beat --loglevel=info
```

## 🧠 Cómo Funciona la IA

1. **Recolección de datos**: Analiza el historial de cambios de aceite
2. **Entrenamiento**: Usa RandomForest para predecir intervalos
3. **Predicción**: Considera marca, modelo, año, kilometraje y patrones de uso
4. **Fallback**: Si no hay suficientes datos, usa predicción básica

### Datos necesarios para IA:
- Mínimo 5 cambios de aceite registrados
- Datos de kilometraje en cada servicio
- Fechas de servicios completados

## 🔧 Configuración

### Variables importantes:
- `TELEGRAM_BOT_TOKEN`: Token del bot de Telegram
- Modelos se guardan en: `BASE_DIR/ml_models/`

### Intervalos por defecto:
- Kilometraje: 10,000 km
- Tiempo: 6 meses (180 días)

## 📈 Monitoreo

### Logs importantes:
- Entrenamientos de IA exitosos/fallidos
- Notificaciones enviadas
- Errores de predicción

### Métricas:
- Precisión del modelo (se mejora automáticamente)
- Número de recordatorios enviados
- Tasa de respuesta de conductores

## 🚨 Solución de Problemas

### Error: "No se pudo entrenar el modelo"
- **Causa**: Menos de 5 cambios de aceite registrados
- **Solución**: Registrar más servicios o usar predicción básica

### Error: "Error enviando notificación"
- **Causa**: Conductor sin telegram_chat_id o token inválido
- **Solución**: Verificar configuración de Telegram

### Predicciones incorrectas
- **Causa**: Datos de entrenamiento insuficientes o incorrectos
- **Solución**: Revisar datos de kilometraje y fechas en órdenes de servicio

## 📞 Soporte

Para problemas o mejoras, contactar al equipo de desarrollo o revisar los logs del sistema.

## 🔄 Actualizaciones Futuras

- Predicción para otros tipos de mantenimiento
- Integración con APIs de fabricantes
- Dashboard de métricas de IA
- Notificaciones por email/SMS
- Predicción basada en condiciones de manejo
