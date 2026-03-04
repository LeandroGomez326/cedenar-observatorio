from django.core.management.base import BaseCommand
from django.utils import timezone
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from datetime import timedelta
from monitoreo.models import Proyecto, Medicion, ConfiguracionAlerta
from monitoreo.utils.notificaciones import enviar_alerta  # ← Ya está importado

class Command(BaseCommand):
    help = 'Verifica medidores inactivos y envía alertas'
    
    def handle(self, *args, **options):
        ahora = timezone.now()
        
        for proyecto in Proyecto.objects.filter(activo=True):
            # Obtener o crear configuración
            config, _ = ConfiguracionAlerta.objects.get_or_create(proyecto=proyecto)
            
            if not config.alerta_inactividad:
                continue
            
            # Última medición
            ultima = Medicion.objects.filter(proyecto=proyecto).order_by('-fecha_lectura').first()
            
            if not ultima:
                self.enviar_alerta(proyecto, config, 'inactividad_total')
                continue
            
            horas_sin_datos = (ahora - ultima.fecha_lectura).total_seconds() / 3600
            
            if horas_sin_datos > config.horas_inactividad:
                self.enviar_alerta(proyecto, config, 'inactividad', horas_sin_datos)
    
    def enviar_alerta(self, proyecto, config, tipo, horas=None):
        asunto = f"⚠️ Alerta: {proyecto.nombre} - "
        if tipo == 'inactividad_total':
            asunto += "Nunca ha enviado datos"
            mensaje = f"El proyecto {proyecto.nombre} (código: {proyecto.codigo_medidor}) nunca ha registrado mediciones."
        elif tipo == 'inactividad':
            asunto += f"Sin datos por {horas:.0f} horas"
            mensaje = f"El proyecto {proyecto.nombre} lleva {horas:.0f} horas sin enviar datos. Última lectura: hace {horas:.0f} horas."
        else:
            return
        
        # Email (código existente)
        emails = config.get_emails_destino()
        if emails:
            send_mail(
                asunto,
                mensaje,
                settings.DEFAULT_FROM_EMAIL,
                emails,
                fail_silently=False,
            )
            self.stdout.write(self.style.SUCCESS(f"📧 Email enviado para {proyecto.nombre} a {len(emails)} destinatarios"))
        
        # 🔴 NUEVO: Notificación en tiempo real (WebSocket)
        enviar_alerta(
            titulo=asunto,
            mensaje=mensaje,
            nivel='warning',
            proyecto_id=proyecto.id
        )
        self.stdout.write(self.style.SUCCESS(f"🔔 Notificación WebSocket enviada para {proyecto.nombre}"))