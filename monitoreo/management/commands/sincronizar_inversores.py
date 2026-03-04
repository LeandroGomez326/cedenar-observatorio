from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from monitoreo.models import Proyecto, Medicion
from monitoreo.services.simulador_inversores import SimuladorInversor
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Sincroniza datos de inversores (MODO SIMULACIÓN)'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--marca',
            type=str,
            choices=['HUAWEI', 'GROWATT', 'TODOS'],
            default='TODOS',
            help='Filtrar por marca de inversor'
        )
        parser.add_argument(
            '--proyecto',
            type=int,
            help='ID del proyecto específico a sincronizar'
        )
        parser.add_argument(
            '--dias',
            type=int,
            default=1,
            help='Días hacia atrás a sincronizar (default: 1)'
        )
        parser.add_argument(
            '--intervalo',
            type=int,
            default=1,
            help='Intervalo en horas entre lecturas (default: 1)'
        )
    
    def handle(self, *args, **options):
        marca = options['marca']
        proyecto_id = options['proyecto']
        dias = options['dias']
        intervalo = options['intervalo']
        
        self.stdout.write(self.style.WARNING(
            "🔧 MODO SIMULACIÓN ACTIVADO - Generando datos ficticios"
        ))
        self.stdout.write(f"Iniciando sincronización de inversores...")
        
        # Filtrar proyectos
        proyectos = Proyecto.objects.filter(activo=True)
        if proyecto_id:
            proyectos = proyectos.filter(id=proyecto_id)
        if marca != 'TODOS':
            proyectos = proyectos.filter(marca=marca)
        
        if not proyectos.exists():
            self.stdout.write(self.style.WARNING("No hay proyectos activos para sincronizar"))
            return
        
        self.stdout.write(f"Proyectos a sincronizar: {proyectos.count()}")
        
        resultados = {'exitosos': 0, 'fallidos': 0, 'mediciones': 0}
        
        for proyecto in proyectos:
            self.stdout.write(f"\n📊 Procesando: {proyecto.nombre} ({proyecto.marca})")
            
            try:
                # Usar simulador para TODOS los proyectos
                inversor = SimuladorInversor(proyecto)
                
                # Calcular fechas
                fecha_fin = timezone.now()
                fecha_inicio = fecha_fin - timedelta(days=dias)
                
                # Obtener datos históricos simulados
                datos_historicos = inversor.obtener_datos_historicos(
                    device_id=proyecto.codigo_medidor,
                    fecha_inicio=fecha_inicio,
                    fecha_fin=fecha_fin
                )
                
                # Guardar mediciones
                nuevas = 0
                for dato in datos_historicos:
                    # Verificar si ya existe
                    existente = Medicion.objects.filter(
                        proyecto=proyecto,
                        fecha_lectura=dato['fecha']
                    ).first()
                    
                    if not existente:
                        Medicion.objects.create(
                            proyecto=proyecto,
                            codigo_usuario=proyecto.codigo_medidor,
                            medidor=proyecto.codigo_medidor,
                            fecha_lectura=dato['fecha'],
                            energia_activa_import=dato['consumo_red'],
                            energia_reactiva_import=0,
                            energia_activa_export=dato['generacion'],
                            energia_reactiva_export=0,
                        )
                        nuevas += 1
                
                resultados['exitosos'] += 1
                resultados['mediciones'] += nuevas
                
                self.stdout.write(self.style.SUCCESS(
                    f"  ✅ {nuevas} nuevas mediciones generadas"
                ))
                
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"  ❌ Error: {str(e)}"))
                resultados['fallidos'] += 1
        
        # Resumen final
        self.stdout.write(self.style.SUCCESS("\n" + "="*60))
        self.stdout.write(self.style.SUCCESS("📊 RESUMEN DE SIMULACIÓN:"))
        self.stdout.write(self.style.SUCCESS(f"  Proyectos exitosos: {resultados['exitosos']}"))
        self.stdout.write(self.style.SUCCESS(f"  Proyectos fallidos: {resultados['fallidos']}"))
        self.stdout.write(self.style.SUCCESS(f"  Mediciones generadas: {resultados['mediciones']}"))
        self.stdout.write(self.style.SUCCESS("="*60))