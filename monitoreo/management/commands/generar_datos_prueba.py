from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
import random
from monitoreo.models import Proyecto, Medicion

class Command(BaseCommand):
    help = 'Genera datos de prueba para todos los proyectos'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--dias',
            type=int,
            default=30,
            help='Número de días hacia atrás para generar datos'
        )
        parser.add_argument(
            '--proyecto',
            type=int,
            help='ID del proyecto específico'
        )
    
    def handle(self, *args, **options):
        dias = options['dias']
        proyecto_id = options['proyecto']
        
        proyectos = Proyecto.objects.filter(activo=True)
        if proyecto_id:
            proyectos = proyectos.filter(id=proyecto_id)
        
        self.stdout.write(f"Generando datos de prueba para {proyectos.count()} proyectos...")
        
        total_mediciones = 0
        fecha_fin = timezone.now().replace(minute=0, second=0, microsecond=0)
        fecha_inicio = fecha_fin - timedelta(days=dias)
        
        for proyecto in proyectos:
            self.stdout.write(f"\n📊 Proyecto: {proyecto.nombre}")
            
            nuevas = 0
            fecha_actual = fecha_inicio
            
            while fecha_actual <= fecha_fin:
                for hora in range(0, 24, 1):  # Cada hora
                    fecha_lectura = fecha_actual.replace(hour=hora)
                    
                    # Generar datos realistas
                    if 6 <= hora <= 18:
                        pico = random.uniform(8, 12)
                        factor = 1 - abs(hora - 12) / 6
                        generacion = pico * factor + random.uniform(-0.3, 0.3)
                    else:
                        generacion = 0
                    
                    if 0 <= hora <= 5:
                        consumo = random.uniform(0.3, 1.2)
                    elif 6 <= hora <= 8:
                        consumo = random.uniform(1.5, 3.0)
                    elif 9 <= hora <= 17:
                        consumo = random.uniform(1.0, 2.2)
                    elif 18 <= hora <= 22:
                        consumo = random.uniform(2.5, 4.0)
                    else:
                        consumo = random.uniform(0.8, 1.8)
                    
                    # Crear o actualizar medición
                    _, created = Medicion.objects.update_or_create(
                        proyecto=proyecto,
                        fecha_lectura=fecha_lectura,
                        defaults={
                            'codigo_usuario': proyecto.codigo_medidor,
                            'medidor': proyecto.codigo_medidor,
                            'energia_activa_import': max(0, consumo),
                            'energia_reactiva_import': 0,
                            'energia_activa_export': max(0, generacion),
                            'energia_reactiva_export': 0,
                        }
                    )
                    
                    if created:
                        nuevas += 1
                
                fecha_actual += timedelta(days=1)
            
            total_mediciones += nuevas
            self.stdout.write(self.style.SUCCESS(f"  ✅ {nuevas} nuevas mediciones"))
        
        self.stdout.write(self.style.SUCCESS(
            f"\n🎉 Total: {total_mediciones} mediciones generadas"
        ))