from django.core.management.base import BaseCommand
from django.utils import timezone
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from datetime import timedelta, datetime
from monitoreo.models import Proyecto, Medicion, ConfiguracionAlerta

class Command(BaseCommand):
    help = 'Envía reportes semanales por proyecto'
    
    def handle(self, *args, **options):
        hoy = timezone.now()
        dia_semana = hoy.weekday()  # 0 = lunes, 6 = domingo
        
        inicio_semana = hoy - timedelta(days=7)
        
        for proyecto in Proyecto.objects.filter(activo=True):
            config, _ = ConfiguracionAlerta.objects.get_or_create(proyecto=proyecto)
            
            if not config.enviar_reporte_semanal or config.dia_reporte != dia_semana:
                continue
            
            # Datos de la última semana
            mediciones = Medicion.objects.filter(
                proyecto=proyecto,
                fecha_lectura__gte=inicio_semana
            ).order_by('fecha_lectura')
            
            if mediciones.count() < 2:
                continue
            
            primera = mediciones.first()
            ultima = mediciones.last()
            consumo_semana = ultima.energia_activa_import - primera.energia_activa_import
            generacion_semana = ultima.energia_activa_export - primera.energia_activa_export
            
            # Calcular promedio diario
            consumo_promedio = consumo_semana / 7
            generacion_promedio = generacion_semana / 7
            
            # Generar tabla de últimos 7 días
            tabla_dias = []
            for i in range(7):
                dia = inicio_semana + timedelta(days=i)
                dia_siguiente = dia + timedelta(days=1)
                
                lecturas_dia = Medicion.objects.filter(
                    proyecto=proyecto,
                    fecha_lectura__range=[dia, dia_siguiente]
                ).order_by('fecha_lectura')
                
                if lecturas_dia.count() >= 2:
                    primera_dia = lecturas_dia.first()
                    ultima_dia = lecturas_dia.last()
                    consumo_dia = ultima_dia.energia_activa_import - primera_dia.energia_activa_import
                    generacion_dia = ultima_dia.energia_activa_export - primera_dia.energia_activa_export
                else:
                    consumo_dia = 0
                    generacion_dia = 0
                
                tabla_dias.append({
                    'fecha': dia.strftime('%d/%m/%Y'),
                    'consumo': round(consumo_dia, 2),
                    'generacion': round(generacion_dia, 2),
                })
            
            contexto = {
                'proyecto': proyecto,
                'inicio_semana': inicio_semana.strftime('%d/%m/%Y'),
                'fin_semana': hoy.strftime('%d/%m/%Y'),
                'consumo_semana': round(consumo_semana, 2),
                'generacion_semana': round(generacion_semana, 2),
                'balance_semana': round(generacion_semana - consumo_semana, 2),
                'consumo_promedio': round(consumo_promedio, 2),
                'generacion_promedio': round(generacion_promedio, 2),
                'tabla_dias': tabla_dias,
            }
            
            html_message = render_to_string('monitoreo/email/reporte_semanal.html', contexto)
            
            emails = config.get_emails_destino()
            if emails:
                send_mail(
                    f"📊 Reporte semanal - {proyecto.nombre}",
                    "Adjuntamos reporte semanal",
                    settings.DEFAULT_FROM_EMAIL,
                    emails,
                    html_message=html_message,
                    fail_silently=False,
                )
                self.stdout.write(self.style.SUCCESS(f"Reporte enviado para {proyecto.nombre}"))