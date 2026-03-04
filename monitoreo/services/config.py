"""
Configuración para APIs de inversores
Cuando tengas las credenciales, las agregarás aquí o en settings.py
"""
from django.conf import settings

class InversorConfig:
    # Configuración HUAWEI (FusionSolar)
    HUAWEI = {
        'base_url': 'https://eu5.fusionsolar.huawei.com',  # URL por defecto
        'login_endpoint': '/thirdData/login',
        'realtime_endpoint': '/thirdData/getRealtimeDeviceData',
        'history_endpoint': '/thirdData/getDevHistoryData',
        'timeout': 30,
    }
    
    # Configuración GROWATT
    GROWATT = {
        'base_url': 'https://server-api.growatt.com',
        'login_endpoint': '/login',
        'plant_data_endpoint': '/plant/getPlantData',
        'device_data_endpoint': '/device/getDeviceData',
        'timeout': 30,
    }
    
    # Configuración de sincronización
    SYNC_INTERVAL_HOURS = 1  # Sincronizar cada hora
    RETRY_ATTEMPTS = 3  # Reintentos si falla
    RETRY_DELAY_SECONDS = 60  # Espera entre reintentos