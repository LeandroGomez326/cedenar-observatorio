from django.core.management.base import BaseCommand
from django.utils import timezone
from monitoreo.models import EstadoServidor
import requests
import time
from django.db import connections

class Command(BaseCommand):
    help = 'Verifica el estado de los servidores y APIs'
    
    def handle(self, *args, **options):
        self.stdout.write("Verificando estado de servidores...")
        
        # Verificar base de datos
        self.verificar_base_datos()
        
        # Verificar API Huawei (cuando tengas credenciales)
        # self.verificar_api_huawei()
        
        # Verificar API Growatt (cuando tengas credenciales)
        # self.verificar_api_growatt()
        
        self.stdout.write(self.style.SUCCESS("Verificación completada"))
    
    def verificar_base_datos(self):
        """Verifica conexión a base de datos"""
        servidor, _ = EstadoServidor.objects.get_or_create(
            nombre='BASE_DATOS',
            defaults={'activo': True}
        )
        
        try:
            start = time.time()
            # Ejecutar consulta simple
            from django.db import connection
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                cursor.fetchone()
            
            elapsed = int((time.time() - start) * 1000)
            
            servidor.activo = True
            servidor.tiempo_respuesta_ms = elapsed
            servidor.mensaje_error = ''
            servidor.save()
            
            self.stdout.write(self.style.SUCCESS(f"✓ Base de datos: OK ({elapsed}ms)"))
            
        except Exception as e:
            servidor.activo = False
            servidor.mensaje_error = str(e)
            servidor.save()
            
            self.stdout.write(self.style.ERROR(f"✗ Base de datos: {str(e)}"))