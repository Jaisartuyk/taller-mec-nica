"""
Sistema de Predicción de Cambio de Aceite con IA
Utiliza machine learning para predecir cuándo un vehículo necesitará cambio de aceite
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import mean_absolute_error
import joblib
import os
from django.conf import settings
from django.utils import timezone
from .models import Vehiculo, OrdenServicio, ServicioCatalogo, RecordatorioMantenimiento

class OilChangePredictorAI:
    def __init__(self):
        self.model_km = None
        self.model_days = None
        self.label_encoders = {}
        self.model_path = os.path.join(settings.BASE_DIR, 'ml_models')
        os.makedirs(self.model_path, exist_ok=True)
    
    def prepare_training_data(self, cliente):
        """Prepara los datos de entrenamiento desde la base de datos"""
        # Obtener órdenes de servicio con cambios de aceite
        cambios_aceite = OrdenServicio.objects.filter(
            cliente=cliente,
            estado='completada',
            servicios__nombre__icontains='aceite'
        ).select_related('vehiculo').prefetch_related('servicios').order_by('fecha_creacion')
        
        if cambios_aceite.count() < 5:
            return None  # Necesitamos al menos 5 registros para entrenar
        
        data = []
        for orden in cambios_aceite:
            vehiculo = orden.vehiculo
            
            # Calcular días desde el último cambio
            ordenes_anteriores = OrdenServicio.objects.filter(
                vehiculo=vehiculo,
                estado='completada',
                servicios__nombre__icontains='aceite',
                fecha_creacion__lt=orden.fecha_creacion
            ).order_by('-fecha_creacion')
            
            if ordenes_anteriores.exists():
                ultima_orden = ordenes_anteriores.first()
                dias_desde_ultimo = (orden.fecha_creacion.date() - ultima_orden.fecha_creacion.date()).days
                km_desde_ultimo = orden.kilometraje - ultima_orden.kilometraje
            else:
                # Primer cambio, usar valores por defecto
                dias_desde_ultimo = 180  # 6 meses
                km_desde_ultimo = 10000  # 10k km
            
            # Solo incluir si los valores son razonables
            if 30 <= dias_desde_ultimo <= 730 and 1000 <= km_desde_ultimo <= 50000:
                data.append({
                    'marca': vehiculo.marca,
                    'modelo': vehiculo.modelo,
                    'anio': vehiculo.anio,
                    'edad_vehiculo': orden.fecha_creacion.year - vehiculo.anio,
                    'kilometraje_actual': orden.kilometraje,
                    'km_desde_ultimo': km_desde_ultimo,
                    'dias_desde_ultimo': dias_desde_ultimo,
                    'mes_servicio': orden.fecha_creacion.month,
                })
        
        return pd.DataFrame(data) if data else None
    
    def train_model(self, cliente):
        """Entrena el modelo de IA con datos históricos"""
        df = self.prepare_training_data(cliente)
        if df is None or len(df) < 5:
            return False
        
        # Preparar features
        features = ['anio', 'edad_vehiculo', 'kilometraje_actual', 'mes_servicio']
        
        # Codificar variables categóricas
        for col in ['marca', 'modelo']:
            if col not in self.label_encoders:
                self.label_encoders[col] = LabelEncoder()
            df[f'{col}_encoded'] = self.label_encoders[col].fit_transform(df[col])
            features.append(f'{col}_encoded')
        
        X = df[features]
        y_km = df['km_desde_ultimo']
        y_days = df['dias_desde_ultimo']
        
        # Entrenar modelo para kilómetros
        self.model_km = RandomForestRegressor(n_estimators=100, random_state=42)
        self.model_km.fit(X, y_km)
        
        # Entrenar modelo para días
        self.model_days = RandomForestRegressor(n_estimators=100, random_state=42)
        self.model_days.fit(X, y_days)
        
        # Guardar modelos
        self.save_models(cliente.id)
        return True
    
    def predict_next_oil_change(self, vehiculo):
        """Predice el próximo cambio de aceite para un vehículo"""
        try:
            # Cargar modelo si existe
            if not self.load_models(vehiculo.cliente.id):
                # Si no hay modelo, usar predicción básica
                return self.basic_prediction(vehiculo)
            
            # Preparar datos del vehículo
            current_date = timezone.now()
            features_data = {
                'anio': vehiculo.anio,
                'edad_vehiculo': current_date.year - vehiculo.anio,
                'kilometraje_actual': vehiculo.kilometraje,
                'mes_servicio': current_date.month,
            }
            
            # Codificar variables categóricas
            try:
                features_data['marca_encoded'] = self.label_encoders['marca'].transform([vehiculo.marca])[0]
                features_data['modelo_encoded'] = self.label_encoders['modelo'].transform([vehiculo.modelo])[0]
            except (KeyError, ValueError):
                # Si marca/modelo no están en el encoder, usar predicción básica
                return self.basic_prediction(vehiculo)
            
            # Crear DataFrame para predicción
            X_pred = pd.DataFrame([features_data])
            
            # Hacer predicciones
            km_prediction = self.model_km.predict(X_pred)[0]
            days_prediction = self.model_days.predict(X_pred)[0]
            
            # Calcular próximo cambio
            proximo_km = vehiculo.kilometraje + max(5000, min(20000, int(km_prediction)))
            proxima_fecha = current_date.date() + timedelta(days=max(90, min(365, int(days_prediction))))
            
            return {
                'kilometraje_proximo': proximo_km,
                'fecha_proximo': proxima_fecha,
                'metodo': 'IA',
                'confianza': min(0.9, len(self.prepare_training_data(vehiculo.cliente)) / 20)
            }
            
        except Exception as e:
            print(f"Error en predicción IA: {e}")
            return self.basic_prediction(vehiculo)
    
    def basic_prediction(self, vehiculo):
        """Predicción básica basada en intervalos estándar"""
        # Buscar servicio de cambio de aceite en el catálogo
        servicio_aceite = ServicioCatalogo.objects.filter(
            cliente=vehiculo.cliente,
            nombre__icontains='aceite',
            activo=True
        ).first()
        
        if servicio_aceite and servicio_aceite.frecuencia_km:
            km_intervalo = servicio_aceite.frecuencia_km
            dias_intervalo = servicio_aceite.frecuencia_meses * 30 if servicio_aceite.frecuencia_meses else 180
        else:
            # Valores por defecto
            km_intervalo = 10000
            dias_intervalo = 180
        
        # Buscar último cambio de aceite
        ultimo_cambio = OrdenServicio.objects.filter(
            vehiculo=vehiculo,
            estado='completada',
            servicios__nombre__icontains='aceite'
        ).order_by('-fecha_creacion').first()
        
        if ultimo_cambio:
            proximo_km = ultimo_cambio.kilometraje + km_intervalo
            proxima_fecha = ultimo_cambio.fecha_creacion.date() + timedelta(days=dias_intervalo)
        else:
            # Si no hay historial, usar fecha actual
            proximo_km = vehiculo.kilometraje + km_intervalo
            proxima_fecha = timezone.now().date() + timedelta(days=dias_intervalo)
        
        return {
            'kilometraje_proximo': proximo_km,
            'fecha_proximo': proxima_fecha,
            'metodo': 'Básico',
            'confianza': 0.7
        }
    
    def save_models(self, cliente_id):
        """Guarda los modelos entrenados"""
        try:
            if self.model_km:
                joblib.dump(self.model_km, os.path.join(self.model_path, f'oil_km_model_{cliente_id}.pkl'))
            if self.model_days:
                joblib.dump(self.model_days, os.path.join(self.model_path, f'oil_days_model_{cliente_id}.pkl'))
            if self.label_encoders:
                joblib.dump(self.label_encoders, os.path.join(self.model_path, f'encoders_{cliente_id}.pkl'))
        except Exception as e:
            print(f"Error guardando modelos: {e}")
    
    def load_models(self, cliente_id):
        """Carga los modelos entrenados"""
        try:
            km_path = os.path.join(self.model_path, f'oil_km_model_{cliente_id}.pkl')
            days_path = os.path.join(self.model_path, f'oil_days_model_{cliente_id}.pkl')
            encoders_path = os.path.join(self.model_path, f'encoders_{cliente_id}.pkl')
            
            if os.path.exists(km_path) and os.path.exists(days_path):
                self.model_km = joblib.load(km_path)
                self.model_days = joblib.load(days_path)
                if os.path.exists(encoders_path):
                    self.label_encoders = joblib.load(encoders_path)
                return True
        except Exception as e:
            print(f"Error cargando modelos: {e}")
        return False

def crear_recordatorio_cambio_aceite(vehiculo):
    """Crea o actualiza recordatorio de cambio de aceite para un vehículo"""
    predictor = OilChangePredictorAI()
    prediccion = predictor.predict_next_oil_change(vehiculo)
    
    # Crear o actualizar recordatorio
    recordatorio, created = RecordatorioMantenimiento.objects.get_or_create(
        vehiculo=vehiculo,
        tipo='Cambio de aceite',
        defaults={
            'kilometraje_proximo': prediccion['kilometraje_proximo'],
            'fecha_proximo': prediccion['fecha_proximo'],
            'notificado': False
        }
    )
    
    if not created:
        recordatorio.kilometraje_proximo = prediccion['kilometraje_proximo']
        recordatorio.fecha_proximo = prediccion['fecha_proximo']
        recordatorio.notificado = False
        recordatorio.save()
    
    return recordatorio, prediccion

def entrenar_modelo_cliente(cliente):
    """Entrena el modelo de IA para un cliente específico"""
    predictor = OilChangePredictorAI()
    return predictor.train_model(cliente)

def verificar_recordatorios_pendientes():
    """Verifica recordatorios pendientes y envía notificaciones"""
    from datetime import date
    
    # Recordatorios por fecha (próximos 7 días)
    recordatorios_fecha = RecordatorioMantenimiento.objects.filter(
        fecha_proximo__lte=date.today() + timedelta(days=7),
        notificado=False
    ).select_related('vehiculo', 'vehiculo__conductor', 'vehiculo__cliente')
    
    # Recordatorios por kilometraje (dentro de 1000 km)
    recordatorios_km = RecordatorioMantenimiento.objects.filter(
        notificado=False
    ).select_related('vehiculo', 'vehiculo__conductor', 'vehiculo__cliente')
    
    notificaciones_enviadas = []
    
    for recordatorio in recordatorios_fecha:
        if recordatorio.vehiculo.conductor and recordatorio.vehiculo.conductor.telegram_chat_id:
            dias_restantes = (recordatorio.fecha_proximo - date.today()).days
            mensaje = f"🔔 *Recordatorio de Mantenimiento*\n\n"
            mensaje += f"Vehículo: {recordatorio.vehiculo.placa}\n"
            mensaje += f"Servicio: {recordatorio.tipo}\n"
            mensaje += f"Fecha programada: {recordatorio.fecha_proximo}\n"
            mensaje += f"Días restantes: {dias_restantes}\n\n"
            mensaje += "¡No olvides programar tu cita!"
            
            enviar_notificacion_conductor(recordatorio.vehiculo.conductor, mensaje)
            recordatorio.notificado = True
            recordatorio.save()
            notificaciones_enviadas.append(recordatorio)
    
    for recordatorio in recordatorios_km:
        vehiculo = recordatorio.vehiculo
        if (vehiculo.conductor and vehiculo.conductor.telegram_chat_id and 
            vehiculo.kilometraje >= recordatorio.kilometraje_proximo - 1000):
            
            km_restantes = recordatorio.kilometraje_proximo - vehiculo.kilometraje
            mensaje = f"🔔 *Recordatorio de Mantenimiento*\n\n"
            mensaje += f"Vehículo: {vehiculo.placa}\n"
            mensaje += f"Servicio: {recordatorio.tipo}\n"
            mensaje += f"Kilometraje actual: {vehiculo.kilometraje:,} km\n"
            mensaje += f"Kilometraje programado: {recordatorio.kilometraje_proximo:,} km\n"
            mensaje += f"Kilómetros restantes: {km_restantes:,} km\n\n"
            mensaje += "¡Tu vehículo necesita mantenimiento pronto!"
            
            enviar_notificacion_conductor(recordatorio.vehiculo.conductor, mensaje)
            recordatorio.notificado = True
            recordatorio.save()
            notificaciones_enviadas.append(recordatorio)
    
    return notificaciones_enviadas

def enviar_notificacion_conductor(conductor, mensaje, canal='ambos'):
    """Envía notificación a un conductor por Telegram y/o WhatsApp
    
    Args:
        conductor: Instancia del modelo Conductor
        mensaje (str): Mensaje a enviar
        canal (str): 'telegram', 'whatsapp' o 'ambos'
    
    Returns:
        dict: Resultado del envío
    """
    import requests
    from django.conf import settings
    
    resultados = {'telegram': False, 'whatsapp': False}
    
    # Enviar por Telegram
    if canal in ['telegram', 'ambos'] and conductor.telegram_chat_id:
        try:
            token = settings.TELEGRAM_BOT_TOKEN
            send_message_url = f'https://api.telegram.org/bot{token}/sendMessage'
            
            response = requests.post(send_message_url, json={
                'chat_id': conductor.telegram_chat_id,
                'text': mensaje,
                'parse_mode': 'Markdown'
            }, timeout=10)
            
            if response.ok:
                resultados['telegram'] = True
                print(f'✅ Notificación Telegram enviada a {conductor.nombre}')
            else:
                print(f'❌ Error Telegram para {conductor.nombre}: {response.text}')
                
        except Exception as e:
            print(f'❌ Error enviando Telegram a {conductor.nombre}: {str(e)}')
    
    # Enviar por WhatsApp
    if canal in ['whatsapp', 'ambos'] and conductor.telefono:
        try:
            from .whatsapp_service import enviar_recordatorio_whatsapp
            resultado_wa = enviar_recordatorio_whatsapp(conductor, mensaje)
            
            if resultado_wa.get('success'):
                resultados['whatsapp'] = True
                print(f'✅ Notificación WhatsApp enviada a {conductor.nombre}')
            else:
                print(f'❌ Error WhatsApp para {conductor.nombre}: {resultado_wa.get("error")}')
                
        except Exception as e:
            print(f'❌ Error enviando WhatsApp a {conductor.nombre}: {str(e)}')
    
    # Log del resultado
    canales_exitosos = [k for k, v in resultados.items() if v]
    if canales_exitosos:
        print(f'📱 Notificación enviada a {conductor.nombre} por: {", ".join(canales_exitosos)}')
        return True
    else:
        print(f'⚠️ No se pudo enviar notificación a {conductor.nombre} por ningún canal')
        return False


def verificar_recordatorios_pendientes_con_canal(canal='ambos'):
    """Verifica recordatorios pendientes y envía notificaciones por el canal especificado
    
    Args:
        canal (str): 'telegram', 'whatsapp' o 'ambos'
    
    Returns:
        list: Lista de recordatorios que fueron notificados
    """
    from django.utils import timezone
    from datetime import timedelta
    
    # Buscar recordatorios que deben ser notificados (próximos 7 días)
    fecha_limite = timezone.now().date() + timedelta(days=7)
    recordatorios_pendientes = RecordatorioMantenimiento.objects.filter(
        fecha_proximo__lte=fecha_limite,
        notificado=False,
        vehiculo__conductor__isnull=False
    ).select_related('vehiculo', 'vehiculo__conductor')
    
    notificaciones_enviadas = []
    
    for recordatorio in recordatorios_pendientes:
        vehiculo = recordatorio.vehiculo
        conductor = vehiculo.conductor
        
        if not conductor:
            continue
            
        # Crear mensaje personalizado
        dias_restantes = (recordatorio.fecha_proximo - timezone.now().date()).days
        
        if dias_restantes <= 0:
            urgencia = "🚨 *URGENTE*"
            mensaje_tiempo = "Tu vehículo necesita mantenimiento **HOY**"
        elif dias_restantes <= 3:
            urgencia = "⚠️ *IMPORTANTE*"
            mensaje_tiempo = f"Tu vehículo necesita mantenimiento en **{dias_restantes} días**"
        else:
            urgencia = "📅 *RECORDATORIO*"
            mensaje_tiempo = f"Tu vehículo necesitará mantenimiento en **{dias_restantes} días**"
        
        mensaje = f"""
{urgencia}

{mensaje_tiempo}

🚗 **Vehículo:** {vehiculo.marca} {vehiculo.modelo}
🏷️ **Placa:** {vehiculo.placa}
🔧 **Servicio:** {recordatorio.tipo}
📅 **Fecha recomendada:** {recordatorio.fecha_proximo.strftime('%d/%m/%Y')}
📏 **Kilometraje:** {recordatorio.kilometraje_proximo:,} km

¡Agenda tu cita para mantener tu vehículo en perfecto estado!
        """.strip()
        
        # Enviar notificación por el canal especificado usando plantillas
        if canal in ['whatsapp', 'ambos'] and conductor.telefono:
            from .whatsapp_service import enviar_recordatorio_whatsapp
            try:
                resultado_whatsapp = enviar_recordatorio_whatsapp(
                    conductor, 
                    mensaje_personalizado=None,  # Usar plantilla automática
                    vehiculo=vehiculo,
                    recordatorio=recordatorio
                )
                if resultado_whatsapp.get('success'):
                    print(f'✅ WhatsApp enviado a {conductor.nombre}')
                else:
                    print(f'❌ Error WhatsApp para {conductor.nombre}: {resultado_whatsapp.get("error")}')
            except Exception as e:
                print(f'❌ Error WhatsApp para {conductor.nombre}: {e}')
        
        # Enviar por Telegram si está configurado
        exito = enviar_notificacion_conductor(conductor, mensaje, canal)
        
        if exito:
            recordatorio.notificado = True
            recordatorio.save()
            notificaciones_enviadas.append(recordatorio)
            print(f'✅ Recordatorio enviado: {vehiculo.placa} - {recordatorio.tipo} (canal: {canal})')
        else:
            print(f'❌ Error enviando recordatorio: {vehiculo.placa} - {recordatorio.tipo}')
    
    return notificaciones_enviadas
