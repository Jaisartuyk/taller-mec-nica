# 📱 Integración WhatsApp con WASenderAPI

## 🚀 Descripción

Este sistema integra **WhatsApp** usando **WASenderAPI** junto con **Telegram** para proporcionar notificaciones duales a los conductores del taller mecánico.

## 🔧 Configuración

### 1. Registro en WASenderAPI

1. Ve a [https://wasenderapi.com/](https://wasenderapi.com/)
2. Regístrate y crea una cuenta
3. Conecta tu número de WhatsApp
4. Obtén tu **API Token** e **Instance ID**

### 2. Variables de Entorno

Agrega estas variables a tu archivo `.env`:

```bash
# WhatsApp Configuration
WASENDER_API_TOKEN=tu_token_wasender_aqui
WASENDER_INSTANCE_ID=tu_instance_id_aqui
```

### 3. Instalación de Dependencias

```bash
pip install requests>=2.31.0
```

## 📋 Funcionalidades

### ✅ Notificaciones Automáticas
- **Recordatorios de mantenimiento** con predicción IA
- **Confirmaciones de cita** 
- **Notificaciones de orden lista**
- **Mensajes personalizados** con emojis

### 🔄 Sistema Dual
- **Telegram**: Comandos administrativos y gestión interna
- **WhatsApp**: Comunicación profesional con clientes
- **Ambos canales**: Máxima cobertura de notificaciones

## 🛠️ Uso

### Comandos Django

#### Probar WhatsApp
```bash
# Verificar configuración
python manage.py test_whatsapp

# Probar con conductor específico
python manage.py test_whatsapp --conductor-id 1

# Probar con número específico
python manage.py test_whatsapp --telefono "+573001234567"

# Mensaje personalizado
python manage.py test_whatsapp --telefono "+573001234567" --mensaje "Hola desde el taller"
```

#### Verificar Recordatorios
```bash
# Enviar por ambos canales (por defecto)
python manage.py verificar_recordatorios

# Solo por WhatsApp
python manage.py verificar_recordatorios --canal whatsapp

# Solo por Telegram
python manage.py verificar_recordatorios --canal telegram

# Entrenar IA y enviar recordatorios
python manage.py verificar_recordatorios --entrenar --canal ambos
```

### Uso Programático

```python
from gestion_taller.whatsapp_service import enviar_recordatorio_whatsapp

# Enviar recordatorio
conductor = Conductor.objects.get(id=1)
mensaje = "Tu vehículo necesita mantenimiento"
resultado = enviar_recordatorio_whatsapp(conductor, mensaje)

if resultado['success']:
    print("Mensaje enviado exitosamente")
else:
    print(f"Error: {resultado['error']}")
```

## 📊 Tipos de Mensajes

### 🔧 Recordatorio de Mantenimiento
```
🔧 RECORDATORIO DE MANTENIMIENTO

Hola Juan! 👋

Tu vehículo necesitará mantenimiento en 5 días

📍 Taller Mecánico
📞 Contáctanos para agendar tu cita
⏰ Horario: Lun-Vie 8AM-6PM

¡Mantén tu vehículo en perfecto estado! 🚗✨
```

### ✅ Orden Lista
```
✅ ORDEN DE SERVICIO COMPLETADA

Hola Juan! 

Tu vehículo Toyota Corolla (Placa: ABC123) ya está listo! 🚗

📋 Servicios realizados:
Cambio de aceite y filtros

💰 Total: $150,000

📍 Puedes recogerlo en nuestro taller
📞 Cualquier duda, contáctanos

¡Gracias por confiar en nosotros! 🔧
```

### 📅 Confirmación de Cita
```
📅 CITA CONFIRMADA

Hola Juan! 

Tu cita ha sido agendada exitosamente:

🗓️ Fecha: 25/08/2025 a las 10:00 AM
🔧 Servicio: Mantenimiento preventivo
🚗 Vehículo: Toyota Corolla

📍 Ubicación: [Dirección del Taller]
📞 Teléfono: [Número del Taller]

⚠️ Por favor llega 10 minutos antes de tu cita.

¡Te esperamos! 🔧✨
```

## 🔄 Integración con IA

El sistema de **predicción IA** se integra automáticamente con WhatsApp:

1. **Análisis predictivo** de mantenimiento
2. **Recordatorios inteligentes** basados en patrones
3. **Notificaciones proactivas** antes de fallas
4. **Seguimiento automático** de servicios

## 📱 Formatos de Número

El sistema acepta múltiples formatos de teléfono:

```python
# Formatos válidos
"+573001234567"    # Con código de país
"573001234567"     # Sin símbolo +
"3001234567"       # Solo número (se agrega +57 automáticamente)
"300 123 4567"     # Con espacios (se limpian automáticamente)
"300-123-4567"     # Con guiones (se limpian automáticamente)
```

## 🔍 Troubleshooting

### Error: Token no configurado
```bash
❌ WASENDER_API_TOKEN no está configurado en las variables de entorno
💡 Agrega: WASENDER_API_TOKEN=tu_token_aqui
```

**Solución:** Verifica que las variables de entorno estén correctamente configuradas.

### Error: Conductor sin teléfono
```bash
⚠️ El conductor Juan no tiene teléfono registrado
```

**Solución:** Agrega el número de teléfono al conductor en el admin de Django.

### Error de conexión
```bash
❌ Error de conexión con WASender API: Connection timeout
```

**Solución:** 
1. Verifica tu conexión a internet
2. Confirma que el token e instance ID sean correctos
3. Revisa el estado del servicio WASender

## 📈 Monitoreo

### Logs del Sistema
```python
import logging
logger = logging.getLogger(__name__)

# Los mensajes se registran automáticamente
✅ Notificación WhatsApp enviada a Juan
❌ Error WhatsApp para María: Invalid phone number
📱 Notificación enviada a Pedro por: telegram, whatsapp
```

### Métricas Recomendadas
- **Tasa de entrega** de mensajes WhatsApp vs Telegram
- **Tiempo de respuesta** de los conductores
- **Efectividad** de recordatorios preventivos
- **Reducción** de mantenimientos de emergencia

## 🔐 Seguridad

- **Tokens seguros** en variables de entorno
- **Validación** de números de teléfono
- **Rate limiting** para evitar spam
- **Logs** de auditoría de mensajes enviados

## 🆕 NUEVAS FUNCIONALIDADES AGREGADAS

### 📝 **Sistema de Plantillas Profesionales**
- **Mensajes personalizados** con datos del vehículo y conductor
- **Plantillas específicas** para cada tipo de notificación
- **Formato profesional** con emojis y estructura clara
- **Firma comercial** automática configurable

### ⚙️ **Sistema de Configuración Centralizada**
- **Configuración del taller** (nombre, teléfono, horarios, etc.)
- **Gestión de canales** de comunicación
- **Personalización de mensajes** y plantillas
- **Configuración de IA** y recordatorios inteligentes

### 📊 **Dashboard de Métricas**
- **Análisis de cobertura** de conductores por canal
- **Métricas de recordatorios** enviados vs pendientes
- **Estado de canales** de comunicación
- **Recomendaciones automáticas** para mejorar el servicio
- **Exportación de datos** a CSV

### 🎯 **Promociones Masivas**
- **Envío masivo** de promociones por WhatsApp
- **Segmentación** por canal de comunicación
- **Control de rate limiting** para evitar spam
- **Modo simulación** para pruebas
- **Seguimiento de métricas** de envío

## 🛠️ **COMANDOS EXTENDIDOS**

### Configuración del Taller
```bash
# Configuración inicial interactiva
python manage.py configurar_taller --setup

# Mostrar configuración actual
python manage.py configurar_taller --show-config

# Probar canales de comunicación
python manage.py configurar_taller --test-channels

# Exportar configuración
python manage.py configurar_taller --export-config config.json
```

### Dashboard de Métricas
```bash
# Dashboard semanal (por defecto)
python manage.py dashboard_mensajeria

# Dashboard mensual
python manage.py dashboard_mensajeria --periodo mes

# Dashboard detallado
python manage.py dashboard_mensajeria --detallado

# Exportar métricas
python manage.py dashboard_mensajeria --export metricas.csv
```

### Promociones Masivas
```bash
# Enviar promoción básica
python manage.py enviar_promocion --titulo "Oferta Especial" --descuento 20

# Promoción con configuración completa
python manage.py enviar_promocion \
  --titulo "Mantenimiento de Verano" \
  --descripcion "Prepara tu vehículo para las vacaciones" \
  --descuento 25 \
  --vigencia-dias 15 \
  --canal whatsapp

# Modo simulación (sin enviar mensajes reales)
python manage.py enviar_promocion \
  --titulo "Prueba" \
  --descuento 10 \
  --dry-run

# Envío limitado para pruebas
python manage.py enviar_promocion \
  --titulo "Prueba Limitada" \
  --descuento 15 \
  --limite 5 \
  --delay 2.0
```

## 📱 **TIPOS DE MENSAJES EXTENDIDOS**

### 🔍 Diagnóstico Completado
```
🔍 DIAGNÓSTICO COMPLETADO

¡Hola Juan!

Hemos completado el diagnóstico de tu Toyota Corolla (Placa: ABC123)

📋 Diagnóstico:
Motor presenta ruido en la correa de distribución

🔧 Recomendaciones:
• Cambio de correa de distribución
• Revisión de tensores
• Cambio de aceite

💰 Costo estimado: $450,000

¡Estamos aquí para ayudarte! 🔧👨‍🔧
```

### 📝 Vehículo Ingresado
```
📝 VEHÍCULO INGRESADO

¡Hola Juan!

Tu vehículo ha ingresado exitosamente a nuestro taller:

🚗 Vehículo: Toyota Corolla
🏷️ Placa: ABC123
🕐 Fecha de ingreso: 23/08/2025 a las 10:30 AM
🔧 Servicio solicitado: Mantenimiento preventivo

¡Tu vehículo está en buenas manos! 🔧✨
```

### 🎉 Promoción Especial
```
🎉 PROMOCIÓN DE VERANO

¡Hola Juan! 

¡Prepara tu vehículo para las vacaciones!

💰 Descuento: 25%
📅 Válido hasta: 15/09/2025

🔧 Servicios incluidos:
• Cambio de aceite y filtros
• Revisión general
• Diagnóstico computarizado

¡No dejes pasar esta oportunidad! 🚗✨
```

## 🔧 **API DE FUNCIONES EXTENDIDAS**

```python
from gestion_taller.whatsapp_service import (
    enviar_recordatorio_whatsapp,
    enviar_confirmacion_cita_whatsapp,
    enviar_diagnostico_completado_whatsapp,
    enviar_vehiculo_ingresado_whatsapp,
    enviar_promocion_whatsapp,
    enviar_mensaje_personalizado_whatsapp,
    enviar_recordatorio_cita_whatsapp
)

# Recordatorio con plantilla automática
resultado = enviar_recordatorio_whatsapp(
    conductor=conductor,
    vehiculo=vehiculo,
    recordatorio=recordatorio
)

# Confirmación de cita
resultado = enviar_confirmacion_cita_whatsapp(
    conductor=conductor,
    vehiculo=vehiculo,
    fecha_cita=datetime.now(),
    servicio="Mantenimiento preventivo"
)

# Diagnóstico completado
resultado = enviar_diagnostico_completado_whatsapp(
    conductor=conductor,
    vehiculo=vehiculo,
    diagnostico="Motor en buen estado",
    recomendaciones=["Cambio de aceite", "Revisión de frenos"],
    costo_estimado=200000
)

# Promoción personalizada
resultado = enviar_promocion_whatsapp(
    conductor=conductor,
    titulo_promocion="Oferta Especial",
    descripcion="Descuento en mantenimiento",
    descuento=20,
    vigencia=datetime(2025, 12, 31).date()
)
```

## 📊 **MÉTRICAS Y MONITOREO**

### Dashboard Automático
- **Cobertura de conductores** por canal (WhatsApp/Telegram)
- **Tasa de entrega** de mensajes
- **Recordatorios pendientes** y urgentes
- **Estado de configuración** de canales
- **Recomendaciones automáticas** de mejora

### Exportación de Datos
- **CSV** con métricas detalladas
- **JSON** con configuración completa
- **Reportes** personalizables por período

## 🚀 **Próximas Mejoras**

- [x] **Sistema de plantillas** profesionales ✅
- [x] **Configuración centralizada** ✅
- [x] **Dashboard de métricas** ✅
- [x] **Promociones masivas** ✅
- [ ] **Mensajes multimedia** (imágenes, documentos)
- [ ] **Respuestas automáticas** con IA
- [ ] **Chatbot interactivo** para consultas
- [ ] **Integración con calendario** para citas
- [ ] **Notificaciones push** web
- [ ] **API REST** para integraciones externas

## 💡 Consejos de Uso

1. **Usa ambos canales** para máxima cobertura
2. **Personaliza mensajes** con nombre del conductor
3. **Incluye emojis** para mejor engagement
4. **Programa recordatorios** con anticipación adecuada
5. **Monitorea métricas** de entrega y respuesta

---

## 📞 Soporte

Para problemas con la integración WhatsApp:
1. Revisa los logs del sistema
2. Verifica la configuración de WASenderAPI
3. Usa el comando `test_whatsapp` para diagnóstico
4. Consulta la documentación de WASenderAPI

**¡Tu taller mecánico ahora tiene comunicación profesional dual! 🔧📱**
