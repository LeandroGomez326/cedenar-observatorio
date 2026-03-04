import os
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from monitoreo.models import Proyecto, Medicion
from datetime import datetime
from tabulate import tabulate

def analizar_proyecto(proyecto):
    """Analiza un proyecto y retorna sus estadísticas"""
    mediciones = Medicion.objects.filter(proyecto=proyecto).order_by('fecha_lectura')
    
    if mediciones.count() < 2:
        return {
            'nombre': proyecto.nombre,
            'mediciones': mediciones.count(),
            'consumo': 0,
            'generacion': 0,
            'balance': 0,
            'inicio': 'N/A',
            'fin': 'N/A'
        }
    
    primera = mediciones.first()
    ultima = mediciones.last()
    
    # Calcular totales (acumulados)
    consumo_total = ultima.energia_activa_import - primera.energia_activa_import
    generacion_total = ultima.energia_activa_export - primera.energia_activa_export
    balance = generacion_total - consumo_total
    
    return {
        'nombre': proyecto.nombre,
        'mediciones': mediciones.count(),
        'consumo': round(consumo_total, 2),
        'generacion': round(generacion_total, 2),
        'balance': round(balance, 2),
        'inicio': primera.fecha_lectura.strftime('%d/%m/%Y'),
        'fin': ultima.fecha_lectura.strftime('%d/%m/%Y')
    }

def main():
    print("=" * 80)
    print("📊 ANÁLISIS DE PROYECTOS - CONSUMO Y GENERACIÓN")
    print("=" * 80)
    
    proyectos = Proyecto.objects.all()
    
    if not proyectos:
        print("❌ No hay proyectos en la base de datos")
        return
    
    tabla = []
    total_consumo = 0
    total_generacion = 0
    total_balance = 0
    
    for p in proyectos:
        datos = analizar_proyecto(p)
        tabla.append([
            datos['nombre'],
            datos['mediciones'],
            f"{datos['consumo']:,.2f}".replace(',', ' '),
            f"{datos['generacion']:,.2f}".replace(',', ' '),
            f"{datos['balance']:,.2f}".replace(',', ' '),
            datos['inicio'],
            datos['fin']
        ])
        
        total_consumo += datos['consumo']
        total_generacion += datos['generacion']
        total_balance += datos['balance']
    
    # Mostrar tabla
    headers = ['Proyecto', 'Mediciones', 'Consumo (kWh)', 'Generación (kWh)', 'Balance (kWh)', 'Inicio', 'Fin']
    print(tabulate(tabla, headers=headers, tablefmt='grid'))
    
    print("\n" + "=" * 80)
    print("📈 RESUMEN GENERAL")
    print("=" * 80)
    print(f"🔢 Total proyectos: {len(proyectos)}")
    print(f"⚡ Consumo total: {total_consumo:,.2f} kWh".replace(',', ' '))
    print(f"☀️ Generación total: {total_generacion:,.2f} kWh".replace(',', ' '))
    print(f"⚖️ Balance total: {total_balance:,.2f} kWh".replace(',', ' '))
    
    if total_balance > 0:
        print("✅ Balance POSITIVO: Generaste más de lo que consumiste")
    elif total_balance < 0:
        print("⚠️ Balance NEGATIVO: Consumiste más de lo que generaste")
    else:
        print("⚪ Balance NEUTRO: Consumo = Generación")
    
    print("=" * 80)

if __name__ == '__main__':
    main()