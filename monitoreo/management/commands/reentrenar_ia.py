from django.core.management.base import BaseCommand
from monitoreo.models import Proyecto
from monitoreo.services.predictor import PredictorEnergia

class Command(BaseCommand):
    help = 'Reentrena los modelos de IA para todos los proyectos'
    
    def add_arguments(self, parser):
        parser.add_argument('--proyecto', type=int, help='ID del proyecto específico')
    
    def handle(self, *args, **options):
        proyecto_id = options.get('proyecto')
        
        if proyecto_id:
            proyectos = Proyecto.objects.filter(id=proyecto_id)
        else:
            proyectos = Proyecto.objects.filter(activo=True)
        
        for proyecto in proyectos:
            self.stdout.write(f"🤖 Entrenando IA para {proyecto.nombre}...")
            predictor = PredictorEnergia(proyecto.id)
            resultado = predictor.entrenar()
            
            if resultado:
                self.stdout.write(self.style.SUCCESS(f"✅ {proyecto.nombre} entrenado"))
            else:
                self.stdout.write(self.style.WARNING(f"⚠️ {proyecto.nombre} sin datos suficientes"))