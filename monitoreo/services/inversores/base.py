from abc import ABC, abstractmethod
import requests
import logging
import time  # ← Esta es la que falta
from datetime import datetime
from django.utils import timezone  # ← Esta también
from monitoreo.models import Medicion
from monitoreo.services.config import InversorConfig

logger = logging.getLogger(__name__)

class InversorBase(ABC):

    """
    Clase base abstracta para todos los inversores.
    Define la interfaz común que deben implementar.
    """
    
    def __init__(self, proyecto):
        self.proyecto = proyecto
        self.config = self.get_config()
        self.base_url = self.config['base_url']
        self.session = requests.Session()
        self.session.timeout = self.config.get('timeout', 30)
        self.authenticated = False
        self.last_error = None
    
    @abstractmethod
    def get_config(self):
        """Retorna la configuración específica del inversor"""
        pass
    
    @abstractmethod
    def autenticar(self):
        """Método de autenticación específico de cada API"""
        pass
    
    @abstractmethod
    def obtener_datos_tiempo_real(self, device_id):
        """Obtiene datos en tiempo real"""
        pass
    
    @abstractmethod
    def obtener_datos_historicos(self, device_id, fecha_inicio, fecha_fin):
        """Obtiene datos históricos"""
        pass
    
    @abstractmethod
    def parsear_respuesta(self, respuesta):
        """
        Convierte la respuesta de la API al formato interno
        Retorna: {
            'fecha': datetime,
            'generacion': float,
            'consumo_red': float,
            'voltaje': float,
            'corriente': float,
            'potencia': float,
            'energia_diaria': float,
            'energia_total': float,
            'estado': str
        }
        """
        pass
    
    def ejecutar_con_reintentos(self, func, *args, **kwargs):
        """Ejecuta una función con reintentos automáticos"""
        for intento in range(InversorConfig.RETRY_ATTEMPTS):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                self.last_error = str(e)
                logger.warning(f"Intento {intento + 1} falló: {e}")
                if intento < InversorConfig.RETRY_ATTEMPTS - 1:
                    time.sleep(InversorConfig.RETRY_DELAY_SECONDS)
                else:
                    logger.error(f"Todos los intentos fallaron: {e}")
                    raise
    
    def guardar_medicion(self, datos):
        """
        Guarda una medición en la base de datos
        """
        try:
            medicion, created = Medicion.objects.update_or_create(
                proyecto=self.proyecto,
                fecha_lectura=datos['fecha'],
                defaults={
                    'codigo_usuario': self.proyecto.codigo_medidor,
                    'medidor': self.proyecto.codigo_medidor,
                    'energia_activa_import': datos.get('consumo_red', 0),
                    'energia_reactiva_import': datos.get('reactiva_consumo', 0),
                    'energia_activa_export': datos.get('generacion', 0),
                    'energia_reactiva_export': datos.get('reactiva_generacion', 0),
                }
            )
            
            if created:
                logger.info(f"Nueva medición guardada para {self.proyecto.nombre}")
            return medicion
            
        except Exception as e:
            logger.error(f"Error guardando medición: {e}")
            return None
    
    def verificar_conexion(self):
        """Verifica si la API está accesible"""
        try:
            response = self.session.get(self.base_url, timeout=10)
            return response.status_code < 500
        except:
            return False
    
    def __str__(self):
        return f"Inversor({self.proyecto.marca}) - {self.proyecto.nombre}"