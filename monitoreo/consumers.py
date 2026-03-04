import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.utils import timezone

class NotificacionConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope['user']
        
        if self.user.is_authenticated:
            await self.channel_layer.group_add(
                "notificaciones_globales",
                self.channel_name
            )
            await self.accept()
            
            await self.send(text_data=json.dumps({
                'tipo': 'conexion',
                'titulo': '🔌 Conectado',
                'mensaje': 'Sistema de notificaciones activado',
                'nivel': 'success',
                'timestamp': str(timezone.now())
            }))
        else:
            await self.close()
    
    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            "notificaciones_globales",
            self.channel_name
        )
    
    async def notificacion_alerta(self, event):
        await self.send(text_data=json.dumps({
            'tipo': 'alerta',
            'titulo': event['titulo'],
            'mensaje': event['mensaje'],
            'nivel': event.get('nivel', 'info'),
            'proyecto_id': event.get('proyecto_id'),
            'timestamp': event['timestamp']
        }))