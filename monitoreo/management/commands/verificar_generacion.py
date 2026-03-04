from django.core.management.base import BaseCommand
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from datetime import timedelta
from monitoreo.models import Proyecto, Medicion, ConfiguracionAlerta

class Command(BaseCommand):
    help = 'Verifica si la generación está por debajo del umbral'
    
    def handle(self, *args, **options):
        ayer = timezone.now() - timedelta(days=1)
        inicio_dia = ayer.replace(hour=0, minute=0, second=0, microsecond=0)
        fin_dia = ayer.replace(hour=23, minute=59, second=59, microsecond=999999)
        
        for proyecto in Proyecto.objects.filter(activo=True):
            config, _ = ConfiguracionAlerta.objects.get_or_create(proyecto=proyecto)
            
            if not config.alerta_umbral_generacion:
                continue
            
            # Mediciones de ayer
            mediciones = Medicion.objects.filter(
                proyecto=proyecto,
                fecha_lectura__range=[inicio_dia, fin_dia]
            ).order_by('fecha_lectura')
            
            if mediciones.count() < 2:
                continue
            
            # Calcular generación del día
            primera = mediciones.first()
            ultima = mediciones.last()
            generacion_dia = ultima.energia_activa_export - primera.energia_activa_export
            
            if generacion_dia < config.umbral_generacion_kwh:
                asunto = f"⚠️ Baja generación: {proyecto.nombre}"
                mensaje = f"""
El proyecto {proyecto.nombre} generó solo {generacion_dia:.2f} kWh ayer,
por debajo del umbral de {config.umbral_generacion_kwh} kWh configurado.
                """
                
                emails = config.get_emails_destino()
                if emails:
                    send_mail(asunto, mensaje, settings.DEFAULT_FROM_EMAIL, emails)
                    self.stdout.write(self.style.SUCCESS(f"Alerta de baja generación para {proyecto.nombre}"))