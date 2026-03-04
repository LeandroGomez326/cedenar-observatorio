import os
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from monitoreo.models import Proyecto

# Coordenadas para cada proyecto
coordenadas = {
    1: {  # Proyecto Solar 1
        'latitud': 1.2136,
        'longitud': -77.2811
    },
    2: {  # Proyecto Medidor 1
        'latitud': 1.2075,
        'longitud': -77.2778
    },
    3: {  # Medidor 1
        'latitud': 1.227266,
        'longitud': -77.281932
    }
}

print("🚀 Agregando coordenadas a los proyectos...")

for proyecto_id, coords in coordenadas.items():
    try:
        proyecto = Proyecto.objects.get(id=proyecto_id)
        proyecto.latitud = coords['latitud']
        proyecto.longitud = coords['longitud']
        proyecto.save()
        print(f"✅ {proyecto.nombre}: {proyecto.latitud}, {proyecto.longitud}")
    except Proyecto.DoesNotExist:
        print(f"❌ Proyecto ID {proyecto_id} no encontrado")

print("\n📊 Verificación final:")
for p in Proyecto.objects.all():
    print(f"  {p.nombre}: lat={p.latitud}, lng={p.longitud}")