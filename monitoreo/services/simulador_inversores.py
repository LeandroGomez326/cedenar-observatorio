import random
import json
from datetime import datetime, timedelta
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)

class SimuladorInversor:
    """
    Simulador de inversores para desarrollo y pruebas
    Genera datos realistas sin necesidad de APIs reales
    """
    
    def __init__(self, proyecto):
        self.proyecto = proyecto
        self.authenticated = True
        self.last_error = None
        
    def verificar_conexion(self):
        """Simula verificación de conexión"""
        return True
    
    def autenticar(self):
        """Simula autenticación exitosa"""
        logger.info(f"🔧 MODO SIMULACIÓN: Autenticando {self.proyecto.nombre}")
        return True
    
    def obtener_datos_tiempo_real(self, device_id=None):
        """
        Genera datos simulados en tiempo real
        """
        ahora = timezone.now()
        
        # Generar valores realistas según la hora del día
        hora = ahora.hour
        
        # Simular generación solar (solo de día)
        if 6 <= hora <= 18:
            # Curva de campana durante el día
            pico = 10.0  # kW pico
            factor = 1 - abs(hora - 12) / 6  # Máximo al mediodía
            potencia_generacion = round(pico * factor + random.uniform(-0.5, 0.5), 2)
        else:
            potencia_generacion = 0
        
        # Consumo variable
        if 0 <= hora <= 5:  # Madrugada
            potencia_consumo = round(random.uniform(0.5, 1.5), 2)
        elif 6 <= hora <= 8:  # Mañana
            potencia_consumo = round(random.uniform(2.0, 3.5), 2)
        elif 9 <= hora <= 17:  # Día
            potencia_consumo = round(random.uniform(1.5, 2.5), 2)
        elif 18 <= hora <= 22:  # Noche
            potencia_consumo = round(random.uniform(3.0, 4.5), 2)
        else:  # Madrugada
            potencia_consumo = round(random.uniform(1.0, 2.0), 2)
        
        return {
            'fecha': ahora,
            'generacion': max(0, potencia_generacion),
            'consumo_red': max(0, potencia_consumo),
            'voltaje': round(random.uniform(215, 235), 1),
            'corriente': round(random.uniform(5, 15), 1),
            'potencia': round(potencia_generacion + potencia_consumo, 2),
            'energia_diaria': round(random.uniform(10, 50), 2),
            'energia_total': round(random.uniform(1000, 5000), 2),
            'estado': 'online' if random.random() > 0.05 else 'offline',
            'temperatura': round(random.uniform(25, 45), 1),
            'modo_simulacion': True
        }
    
    def obtener_datos_historicos(self, device_id, fecha_inicio, fecha_fin):
        """
        Genera datos históricos simulados
        """
        datos = []
        fecha_actual = fecha_inicio
        
        while fecha_actual <= fecha_fin:
            # Generar un día completo de datos horarios
            for hora in range(24):
                fecha_hora = fecha_actual.replace(hour=hora, minute=0, second=0)
                
                # Simular generación solar
                if 6 <= hora <= 18:
                    pico = random.uniform(8, 12)
                    factor = 1 - abs(hora - 12) / 6
                    generacion = round(pico * factor + random.uniform(-0.3, 0.3), 2)
                else:
                    generacion = 0
                
                # Simular consumo
                if 0 <= hora <= 5:
                    consumo = round(random.uniform(0.3, 1.2), 2)
                elif 6 <= hora <= 8:
                    consumo = round(random.uniform(1.5, 3.0), 2)
                elif 9 <= hora <= 17:
                    consumo = round(random.uniform(1.0, 2.2), 2)
                elif 18 <= hora <= 22:
                    consumo = round(random.uniform(2.5, 4.0), 2)
                else:
                    consumo = round(random.uniform(0.8, 1.8), 2)
                
                datos.append({
                    'fecha': fecha_hora,
                    'generacion': max(0, generacion),
                    'consumo_red': max(0, consumo),
                    'voltaje': round(random.uniform(220, 240), 1),
                    'corriente': round(random.uniform(5, 20), 1),
                    'potencia': round(generacion + consumo, 2),
                    'energia_diaria': round(generacion * 24, 2),
                    'energia_total': round(random.uniform(1000, 10000), 2),
                    'estado': 'online'
                })
            
            fecha_actual += timedelta(days=1)
        
        return datos
    
    def parsear_respuesta(self, respuesta):
        """Ya viene en nuestro formato"""
        return respuesta