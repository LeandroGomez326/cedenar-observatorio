from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from django.utils import timezone
import json

def enviar_alerta(titulo, mensaje, nivel='info', proyecto_id=None, usuario_id=None):
    """
    Envía una alerta a través de WebSockets
    """
    channel_layer = get_channel_layer()
    
    evento = {
        'type': 'notificacion_alerta',
        'titulo': titulo,
        'mensaje': mensaje,
        'nivel': nivel,
        'proyecto_id': proyecto_id,
        'timestamp': str(timezone.now())
    }
    
    if usuario_id:
        # Enviar solo a un usuario específico
        async_to_sync(channel_layer.group_send)(
            f"user_{usuario_id}",
            evento
        )
    else:
        # Enviar a todos
        async_to_sync(channel_layer.group_send)(
            "notificaciones_globales",
            evento
        )

def notificar_nueva_medicion(proyecto, consumo, generacion):
    """
    Notifica cuando hay una nueva medición
    """
    channel_layer = get_channel_layer()
    
    async_to_sync(channel_layer.group_send)(
        "notificaciones_globales",
        {
            'type': 'notificacion_medicion',
            'proyecto_id': proyecto.id,
            'proyecto_nombre': proyecto.nombre,
            'consumo': consumo,
            'generacion': generacion,
            'timestamp': str(timezone.now())
        }
    )