import requests
import hashlib
import time
from datetime import datetime
from django.utils import timezone  # ← Esta es la que falta
from .base import InversorBase
from monitoreo.services.config import InversorConfig
import logging

logger = logging.getLogger(__name__)

class GrowattInversor(InversorBase):
    
    """
    Implementación para inversores Growatt
    """
    
    def get_config(self):
        return InversorConfig.GROWATT
    
    def autenticar(self):
        """
        Autenticación en Growatt
        NOTA: Growatt usa un hash de contraseña
        """
        try:
            login_url = f"{self.base_url}{self.config['login_endpoint']}"
            
            # TODO: Reemplazar con credenciales reales
            # Growatt requiere password hasheado con SHA256
            password_hash = hashlib.sha256(
                'TU_PASSWORD'.encode()  # Cuando tengas el password
            ).hexdigest()
            
            payload = {
                'userName': 'TU_USUARIO',  # Cuando tengas el usuario
                'password': password_hash
            }
            
            response = self.session.post(login_url, data=payload)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('result') == 1:  # Growatt retorna result=1 en éxito
                    # Guardar token en cookies
                    self.session.cookies.set('token', data.get('token', ''))
                    self.authenticated = True
                    logger.info(f"Growatt autenticado: {self.proyecto.nombre}")
                    return True
                else:
                    logger.error(f"Error autenticando: {data.get('msg', 'desconocido')}")
                    return False
            else:
                logger.error(f"Error autenticando Growatt: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"Excepción en autenticación Growatt: {e}")
            return False
    
    def obtener_datos_tiempo_real(self, plant_id=None):
        """
        Obtiene datos en tiempo real de la planta
        """
        if not self.authenticated:
            if not self.autenticar():
                raise Exception("No autenticado")
        
        plant_id = plant_id or self.proyecto.codigo_medidor
        
        try:
            url = f"{self.base_url}{self.config['plant_data_endpoint']}"
            
            params = {
                'plantId': plant_id,
                'date': time.strftime('%Y-%m-%d')
            }
            
            response = self.session.get(url, params=params)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('result') == 1:
                    return self.parsear_respuesta(data.get('obj', {}))
                else:
                    logger.error(f"Error en respuesta: {data.get('msg', 'desconocido')}")
                    return None
            else:
                logger.error(f"Error obteniendo datos: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Error obteniendo datos tiempo real: {e}")
            return None
    
    def obtener_datos_historicos(self, device_id, fecha_inicio, fecha_fin):
        """
        Obtiene datos históricos
        TODO: Implementar cuando tengamos documentación
        """
        logger.warning("Históricos no implementados aún para Growatt")
        return None
    
    def parsear_respuesta(self, respuesta):
        """
        Convierte la respuesta de Growatt al formato interno
        """
        # Growatt tiene una estructura específica
        parsed_data = {
            'fecha': timezone.now(),
            'generacion': float(respuesta.get('ppv', 0)),  # Potencia PV
            'consumo_red': float(respuesta.get('pLocalLoad', 0)),  # Consumo local
            'voltaje': float(respuesta.get('v', 0)),
            'corriente': float(respuesta.get('i', 0)),
            'potencia': float(respuesta.get('p', 0)),
            'energia_diaria': float(respuesta.get('eToday', 0)),
            'energia_total': float(respuesta.get('eTotal', 0)),
            'estado': respuesta.get('status', 'desconocido'),
            'raw_data': respuesta
        }
        return parsed_data