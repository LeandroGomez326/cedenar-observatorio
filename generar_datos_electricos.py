import os
import django
import random
from datetime import timedelta

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from monitoreo.models import Proyecto, Medicion

def generar_datos_electricos():
    """Genera datos eléctricos simulados para pruebas"""
    
    print("="*60)
    print("🔌 GENERANDO DATOS ELÉCTRICOS SIMULADOS")
    print("="*60)
    
    for proyecto in Proyecto.objects.all():
        print(f"\n📊 Proyecto: {proyecto.nombre}")
        
        # Obtener todas las mediciones del proyecto
        mediciones = Medicion.objects.filter(proyecto=proyecto).order_by('fecha_lectura')
        
        if not mediciones:
            print(f"  ⚠️ No hay mediciones para este proyecto")
            continue
        
        print(f"  📈 Procesando {mediciones.count()} mediciones...")
        count = 0
        
        for m in mediciones:
            # Obtener hora del día para simular patrones realistas
            hora = m.fecha_lectura.hour
            
            # Factor según hora del día (más actividad de día)
            if 6 <= hora <= 18:  # Día
                factor = 1.0
            else:  # Noche
                factor = 0.3
            
            # Generar valores con variación realista
            m.potencia_dc_w = random.uniform(1000, 5000) * factor
            m.potencia_reactiva_var = random.uniform(100, 500) * factor
            m.potencia_aparente_va = random.uniform(1000, 6000) * factor
            m.corriente_ac_total_a = random.uniform(5, 30) * factor
            m.corriente_dc_a = random.uniform(5, 25) * factor
            m.voltaje_ac_v = random.uniform(215, 235)  # Voltaje estable
            m.voltaje_dc_v = random.uniform(300, 800) * (0.8 + 0.4 * factor)
            m.corriente_ac_a = random.uniform(5, 30) * factor
            m.voltaje_entre_fases_v = random.uniform(380, 415)  # Estable
            m.factor_potencia_pct = random.uniform(85, 99)  # Siempre alto
            
            m.save()
            count += 1
            
            if count % 100 == 0:
                print(f"  ✅ {count} mediciones actualizadas...")
        
        print(f"  ✅ COMPLETADO: {count} mediciones actualizadas")

def verificar_datos():
    """Verifica que los datos se generaron correctamente"""
    print("\n" + "="*60)
    print("🔍 VERIFICANDO DATOS GENERADOS")
    print("="*60)
    
    for proyecto in Proyecto.objects.all():
        mediciones = Medicion.objects.filter(proyecto=proyecto)
        if mediciones.exists():
            m = mediciones.first()
            print(f"\n📊 {proyecto.nombre}")
            print(f"  📈 Total mediciones: {mediciones.count()}")
            print(f"  ⚡ Potencia DC: {m.potencia_dc_w:.2f} W")
            print(f"  🔋 Potencia Reactiva: {m.potencia_reactiva_var:.2f} VAr")
            print(f"  💡 Potencia Aparente: {m.potencia_aparente_va:.2f} VA")
            print(f"  🔌 Corriente AC Total: {m.corriente_ac_total_a:.2f} A")
            print(f"  📊 Factor Potencia: {m.factor_potencia_pct:.2f}%")

if __name__ == '__main__':
    generar_datos_electricos()
    verificar_datos()
    