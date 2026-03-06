from django.core.management.base import BaseCommand
from monitoreo.alertas import SistemaAlertas
from monitoreo.models import Proyecto
from datetime import datetime

class Command(BaseCommand):
    help = 'Verifica y envía alertas automáticas'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--tipo',
            type=str,
            choices=['inactivos', 'generacion', 'backup', 'prueba', 'todas'],
            default='todas',
            help='Tipo de alerta a verificar'
        )
        parser.add_argument(
            '--email',
            type=str,
            help='Email para alerta de prueba'
        )
    
    def handle(self, *args, **options):
        alertas = SistemaAlertas()
        tipo = options['tipo']
        email_prueba = options.get('email')
        
        self.stdout.write(self.style.SUCCESS(f'🚀 Iniciando verificación de alertas ({tipo})...'))
        
        if tipo == 'prueba':
            self.stdout.write("🔔 Enviando alerta de prueba...")
            if email_prueba:
                resultado = alertas.alerta_prueba(email_prueba)
            else:
                resultado = alertas.alerta_prueba()
            
            if resultado:
                self.stdout.write(self.style.SUCCESS("✅ Alerta de prueba enviada"))
            else:
                self.stdout.write(self.style.ERROR("❌ Error enviando alerta"))
            return
        
        if tipo in ['inactivos', 'todas']:
            self.stdout.write("🔍 Verificando proyectos inactivos...")
            for proyecto in Proyecto.objects.filter(activo=True):
                alertas.alerta_proyecto_inactivo(proyecto)
        
        if tipo in ['generacion', 'todas']:
            self.stdout.write("☀️ Verificando generación baja...")
            for proyecto in Proyecto.objects.filter(activo=True):
                alertas.alerta_generacion_baja(proyecto)
        
        self.stdout.write(self.style.SUCCESS("✅ Verificación completada"))

    def alerta_prueba(self, email_prueba=None):
        """
        Alerta de prueba para verificar configuración
        """
        asunto = "🔔 Alerta de Prueba"
        html = render_to_string('monitoreo/alertas/alerta_prueba_simple.html', {
            'fecha': datetime.now(),
        })
        mensaje_texto = "Alerta de prueba del sistema CEDENAR"
    
        if email_prueba:
            # Enviar solo a ese email
            return self.enviar_alerta(
                asunto, 
                mensaje_texto, 
                html=html,
                grupos=None,
                email_directo=email_prueba
            )
        else:
            return self.enviar_alerta(
                asunto, 
                mensaje_texto, 
                html=html,
                grupos=['admin']
            )