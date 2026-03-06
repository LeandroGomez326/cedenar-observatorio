# monitoreo/management/commands/monitor.py
from django.core.management.base import BaseCommand
from scripts.monitor import verificar_sitio, verificar_apis_criticas, verificar_base_datos, enviar_alerta
import os

class Command(BaseCommand):
    help = 'Monitorea el estado del sitio'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--alert',
            action='store_true',
            help='Enviar alerta si hay problemas'
        )
    
    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('🚀 Iniciando monitoreo...'))
        
        # Verificar sitio
        estado_sitio, tiempo = verificar_sitio()
        
        if estado_sitio:
            self.stdout.write(self.style.SUCCESS(f'✅ Sitio OK ({tiempo:.2f}s)'))
        else:
            self.stdout.write(self.style.ERROR(f'❌ Sitio caído: {tiempo}'))
            
            if options['alert']:
                # Configurar email desde variables de entorno
                asunto = "🚨 ALERTA: Sitio CEDENAR caído"
                mensaje = f"""
                El sitio https://cedenar-observatorio.onrender.com no responde.
                Error: {tiempo}
                Hora: {__import__('datetime').datetime.now()}
                """
                enviar_alerta(asunto, mensaje)
                self.stdout.write(self.style.WARNING('📧 Alerta enviada'))
        
        # Verificar APIs
        apis_ok = verificar_apis_criticas()
        if apis_ok:
            self.stdout.write(self.style.SUCCESS('✅ APIs OK'))
        else:
            self.stdout.write(self.style.WARNING('⚠️ APIs con problemas'))
        
        # Verificar BD
        bd_ok = verificar_base_datos()
        if bd_ok:
            self.stdout.write(self.style.SUCCESS('✅ Base de datos OK'))
        elif bd_ok is False:
            self.stdout.write(self.style.ERROR('❌ Base de datos desconectada'))
        else:
            self.stdout.write(self.style.WARNING('⚠️ No se pudo verificar BD'))