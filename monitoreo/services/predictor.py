# backend/monitoreo/services/predictor.py
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
import joblib
from datetime import datetime, timedelta
from ..models import Medicion, Proyecto
import os
from django.conf import settings

class PredictorEnergia:
    def __init__(self, proyecto_id=None):
        self.proyecto_id = proyecto_id
        self.modelo_gen = None
        self.modelo_cons = None
        self.scaler = StandardScaler()
        self.modelos_path = os.path.join(settings.BASE_DIR, 'modelos_ia')
        
        # Crear carpeta si no existe
        if not os.path.exists(self.modelos_path):
            os.makedirs(self.modelos_path)
    
    def _crear_caracteristicas(self, df):
        """Crea características a partir de fechas"""
        df = df.copy()
        df['hora'] = df['fecha'].dt.hour
        df['dia'] = df['fecha'].dt.day
        df['mes'] = df['fecha'].dt.month
        df['dia_semana'] = df['fecha'].dt.dayofweek
        df['es_fin_semana'] = (df['dia_semana'] >= 5).astype(int)
        df['estacion'] = df['mes'] % 12 // 3 + 1  # 1: invierno, 2: primavera, etc.
        
        # Características cíclicas (para que el modelo entienda ciclos)
        df['hora_sin'] = np.sin(2 * np.pi * df['hora'] / 24)
        df['hora_cos'] = np.cos(2 * np.pi * df['hora'] / 24)
        df['mes_sin'] = np.sin(2 * np.pi * df['mes'] / 12)
        df['mes_cos'] = np.cos(2 * np.pi * df['mes'] / 12)
        
        return df
    
    def entrenar(self, dias_historial=365):
        """Entrena modelos con datos históricos"""
        print(f"🤖 Entrenando modelos con {dias_historial} días de historial...")
        
        # Obtener datos históricos
        fecha_limite = datetime.now() - timedelta(days=dias_historial)
        mediciones = Medicion.objects.filter(
            proyecto_id=self.proyecto_id,
            fecha_lectura__gte=fecha_limite
        ).order_by('fecha_lectura')
        
        if mediciones.count() < 100:
            print("⚠️ Pocos datos para entrenar, se necesita al menos 100 registros")
            return False
        
        # Convertir a DataFrame
        datos = []
        for m in mediciones:
            datos.append({
                'fecha': m.fecha_lectura,
                'generacion': m.energia_activa_export,
                'consumo': m.energia_activa_import
            })
        
        df = pd.DataFrame(datos)
        df = self._crear_caracteristicas(df)
        
        # Características para el modelo
        features = ['hora', 'dia', 'mes', 'dia_semana', 'es_fin_semana', 
                   'estacion', 'hora_sin', 'hora_cos', 'mes_sin', 'mes_cos']
        
        X = df[features].values
        
        # Escalar características
        X_scaled = self.scaler.fit_transform(X)
        
        # Entrenar modelo de generación
        y_gen = df['generacion'].values
        X_train, X_test, y_train, y_test = train_test_split(
            X_scaled, y_gen, test_size=0.2, random_state=42
        )
        
        self.modelo_gen = RandomForestRegressor(
            n_estimators=100,
            max_depth=10,
            random_state=42,
            n_jobs=-1
        )
        self.modelo_gen.fit(X_train, y_train)
        
        # Evaluar
        score_gen = self.modelo_gen.score(X_test, y_test)
        print(f"✅ Modelo generación R²: {score_gen:.3f}")
        
        # Entrenar modelo de consumo
        y_cons = df['consumo'].values
        X_train, X_test, y_train, y_test = train_test_split(
            X_scaled, y_cons, test_size=0.2, random_state=42
        )
        
        self.modelo_cons = RandomForestRegressor(
            n_estimators=100,
            max_depth=10,
            random_state=42,
            n_jobs=-1
        )
        self.modelo_cons.fit(X_train, y_train)
        
        score_cons = self.modelo_cons.score(X_test, y_test)
        print(f"✅ Modelo consumo R²: {score_cons:.3f}")
        
        # Guardar modelos
        self._guardar_modelos()
        
        return True
    
    def _guardar_modelos(self):
        """Guarda los modelos entrenados"""
        if self.proyecto_id:
            gen_path = os.path.join(self.modelos_path, f'modelo_gen_{self.proyecto_id}.pkl')
            cons_path = os.path.join(self.modelos_path, f'modelo_cons_{self.proyecto_id}.pkl')
            scaler_path = os.path.join(self.modelos_path, f'scaler_{self.proyecto_id}.pkl')
            
            joblib.dump(self.modelo_gen, gen_path)
            joblib.dump(self.modelo_cons, cons_path)
            joblib.dump(self.scaler, scaler_path)
            print(f"💾 Modelos guardados en {self.modelos_path}")
    
    def _cargar_modelos(self):
        """Carga modelos guardados"""
        gen_path = os.path.join(self.modelos_path, f'modelo_gen_{self.proyecto_id}.pkl')
        cons_path = os.path.join(self.modelos_path, f'modelo_cons_{self.proyecto_id}.pkl')
        scaler_path = os.path.join(self.modelos_path, f'scaler_{self.proyecto_id}.pkl')
        
        if os.path.exists(gen_path) and os.path.exists(cons_path) and os.path.exists(scaler_path):
            self.modelo_gen = joblib.load(gen_path)
            self.modelo_cons = joblib.load(cons_path)
            self.scaler = joblib.load(scaler_path)
            return True
        return False
    
    def predecir_proximos_dias(self, dias=7):
        """Predice generación y consumo para los próximos días"""
        if not self._cargar_modelos():
            return {'error': 'Modelos no entrenados'}
        
        predicciones = []
        hoy = datetime.now()
        
        for i in range(1, dias + 1):
            fecha_pred = hoy + timedelta(days=i)
            
            # Crear características para cada hora del día
            for hora in range(24):
                # Crear DataFrame con una fila
                df = pd.DataFrame({
                    'fecha': [fecha_pred.replace(hour=hora, minute=0)]
                })
                df = self._crear_caracteristicas(df)
                
                features = ['hora', 'dia', 'mes', 'dia_semana', 'es_fin_semana', 
                           'estacion', 'hora_sin', 'hora_cos', 'mes_sin', 'mes_cos']
                
                X = df[features].values
                X_scaled = self.scaler.transform(X)
                
                # Predecir
                gen_pred = self.modelo_gen.predict(X_scaled)[0]
                cons_pred = self.modelo_cons.predict(X_scaled)[0]
                
                predicciones.append({
                    'fecha': fecha_pred.strftime('%Y-%m-%d'),
                    'hora': hora,
                    'generacion': max(0, round(gen_pred, 2)),
                    'consumo': max(0, round(cons_pred, 2))
                })
        
        # Agrupar por día
        resumen_diario = {}
        for p in predicciones:
            fecha = p['fecha']
            if fecha not in resumen_diario:
                resumen_diario[fecha] = {
                    'fecha': fecha,
                    'generacion_total': 0,
                    'consumo_total': 0,
                    'horas': []
                }
            resumen_diario[fecha]['generacion_total'] += p['generacion']
            resumen_diario[fecha]['consumo_total'] += p['consumo']
            resumen_diario[fecha]['horas'].append(p)
        
        return {
            'proyecto_id': self.proyecto_id,
            'fecha_prediccion': hoy.strftime('%Y-%m-%d %H:%M'),
            'dias_predichos': dias,
            'predicciones_horarias': predicciones,
            'resumen_diario': list(resumen_diario.values())
        }