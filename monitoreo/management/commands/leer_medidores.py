import os
import csv
from datetime import datetime
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db import transaction
from monitoreo.models import Proyecto, Medicion

RUTA_BASE = r"C:\Users\leand\OneDrive\Documentos\CEDENAR\MEDIDORES"

class Command(BaseCommand):
    help = "Lee automáticamente los archivos de los medidores y guarda nuevas mediciones"

    def add_arguments(self, parser):
        parser.add_argument('--medidor', type=str, help='Procesar solo un medidor específico (nombre de carpeta)')
        parser.add_argument('--fecha', type=str, help='Procesar solo archivos de una fecha específica (YYYY-MM-DD)')
        parser.add_argument('--dry-run', action='store_true', help='Solo mostrar lo que se haría sin guardar')

    def handle(self, *args, **kwargs):
        medidor_especifico = kwargs.get('medidor')
        fecha_especifica = kwargs.get('fecha')
        dry_run = kwargs.get('dry_run', False)

        if not os.path.exists(RUTA_BASE):
            self.stdout.write(self.style.ERROR(f"La ruta {RUTA_BASE} no existe"))
            return

        # Estadísticas
        total_archivos = 0
        total_mediciones = 0
        proyectos_actualizados = set()
        archivos_sin_proyecto = []

        # Recorrer carpetas de medidores
        for carpeta_medidor in os.listdir(RUTA_BASE):
            ruta_carpeta = os.path.join(RUTA_BASE, carpeta_medidor)
            
            # Verificar que sea una carpeta
            if not os.path.isdir(ruta_carpeta):
                continue

            # Si se especificó un medidor, filtrar
            if medidor_especifico and carpeta_medidor != medidor_especifico:
                continue

            self.stdout.write(f"\n📁 Procesando carpeta: {carpeta_medidor}")

            # Procesar archivos en la carpeta del medidor
            for archivo in os.listdir(ruta_carpeta):
                if not archivo.endswith('.csv'):
                    continue

                ruta_archivo = os.path.join(ruta_carpeta, archivo)
                
                # Si se especificó una fecha, verificar si el archivo corresponde
                if fecha_especifica and fecha_especifica not in archivo:
                    continue

                self.stdout.write(f"  📄 Procesando archivo: {archivo}")
                
                try:
                    resultado = self.procesar_archivo(ruta_archivo, dry_run)
                    
                    if resultado['proyecto_encontrado']:
                        total_archivos += 1
                        total_mediciones += resultado['nuevas']
                        proyectos_actualizados.add(resultado['proyecto_nombre'])
                        
                        self.stdout.write(
                            self.style.SUCCESS(
                                f"    ✅ {resultado['nuevas']} nuevas mediciones "
                                f"(total en archivo: {resultado['total']})"
                            )
                        )
                    else:
                        archivos_sin_proyecto.append({
                            'archivo': archivo,
                            'carpeta': carpeta_medidor,
                            'codigo': resultado.get('codigo_encontrado', 'No encontrado')
                        })
                        self.stdout.write(
                            self.style.WARNING(
                                f"    ⚠️  No se encontró proyecto para código: {resultado.get('codigo_encontrado', 'N/A')}"
                            )
                        )

                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(f"    ❌ Error: {str(e)}")
                    )

        # Resumen final
        self.stdout.write(self.style.SUCCESS(f"\n{'='*60}"))
        self.stdout.write(self.style.SUCCESS(f"RESUMEN:"))
        self.stdout.write(self.style.SUCCESS(f"  Archivos procesados: {total_archivos}"))
        self.stdout.write(self.style.SUCCESS(f"  Nuevas mediciones: {total_mediciones}"))
        self.stdout.write(self.style.SUCCESS(f"  Proyectos actualizados: {len(proyectos_actualizados)}"))
        
        if archivos_sin_proyecto:
            self.stdout.write(self.style.WARNING(f"\n  Archivos sin proyecto asociado:"))
            for item in archivos_sin_proyecto:
                self.stdout.write(
                    self.style.WARNING(f"    - {item['carpeta']}/{item['archivo']} (código: {item['codigo']})")
                )
        
        if dry_run:
            self.stdout.write(self.style.WARNING(f"\n  ⚠️  MODO DRY RUN: No se guardaron datos en la base de datos"))
        
        self.stdout.write(self.style.SUCCESS(f"{'='*60}"))

    def procesar_archivo(self, ruta_archivo, dry_run=False):
        """
        Procesa un archivo CSV y retorna las estadísticas
        """
        self.stdout.write(f"    Leyendo archivo: {ruta_archivo}")
        
        try:
            # Leer el archivo CSV
            with open(ruta_archivo, 'r', encoding='utf-8-sig') as f:
                lineas = f.readlines()
            
            self.stdout.write(f"    Total líneas: {len(lineas)}")
            
            if len(lineas) < 2:
                return {
                    'proyecto_encontrado': False,
                    'codigo_encontrado': None,
                    'nuevas': 0,
                    'total': 0
                }
            
            # La primera línea son los encabezados
            encabezados = lineas[0].strip().split(';')
            self.stdout.write(f"    Encabezados: {encabezados[:3]}...")
            
            # Procesar datos (desde línea 1 en adelante)
            datos = []
            codigo_usuario = None
            
            for i, linea in enumerate(lineas[1:], 1):
                linea = linea.strip()
                if not linea:
                    continue
                    
                valores = linea.split(';')
                
                # Guardar el código de usuario de la primera línea de datos
                if i == 1 and len(valores) > 0:
                    codigo_usuario = valores[0].strip()
                    self.stdout.write(f"    Código de usuario encontrado: {codigo_usuario}")
                
                datos.append(valores)
            
            self.stdout.write(f"    Filas de datos: {len(datos)}")
            
            if not codigo_usuario:
                return {
                    'proyecto_encontrado': False,
                    'codigo_encontrado': None,
                    'nuevas': 0,
                    'total': len(datos)
                }
            
            # Buscar el proyecto
            try:
                proyecto = Proyecto.objects.get(codigo_medidor=codigo_usuario)
                self.stdout.write(f"    ✅ Proyecto encontrado: {proyecto.nombre}")
            except Proyecto.DoesNotExist:
                return {
                    'proyecto_encontrado': False,
                    'codigo_encontrado': codigo_usuario,
                    'nuevas': 0,
                    'total': len(datos)
                }
            
            # Procesar cada fila
            nuevas = 0
            total = len(datos)
            
            if not dry_run:
                with transaction.atomic():
                    for idx, valores in enumerate(datos):
                        try:
                            if len(valores) < 7:
                                continue
                            
                            # Extraer valores
                            fecha_str = valores[2].strip() if len(valores) > 2 else None
                            
                            if not fecha_str:
                                continue
                            
                            # Convertir fecha
                            try:
                                fecha = datetime.strptime(fecha_str, '%d/%m/%Y %H:%M')
                            except ValueError:
                                try:
                                    fecha = datetime.strptime(fecha_str, '%Y-%m-%d %H:%M:%S')
                                except ValueError:
                                    continue
                            
                            # Hacer fecha aware
                            if timezone.is_naive(fecha):
                                fecha = timezone.make_aware(fecha)
                            
                            # Limpiar números
                            def limpiar_numero(v):
                                if not v or v == '':
                                    return 0
                                return float(str(v).replace(',', '.').strip())
                            
                            # Crear o actualizar medición
                            _, created = Medicion.objects.update_or_create(
                                proyecto=proyecto,
                                fecha_lectura=fecha,
                                defaults={
                                    'codigo_usuario': codigo_usuario,
                                    'medidor': valores[1].strip() if len(valores) > 1 else codigo_usuario,
                                    'energia_activa_import': limpiar_numero(valores[3]) if len(valores) > 3 else 0,
                                    'energia_reactiva_import': limpiar_numero(valores[4]) if len(valores) > 4 else 0,
                                    'energia_activa_export': limpiar_numero(valores[5]) if len(valores) > 5 else 0,
                                    'energia_reactiva_export': limpiar_numero(valores[6]) if len(valores) > 6 else 0,
                                }
                            )
                            
                            if created:
                                nuevas += 1
                                
                        except Exception as e:
                            self.stdout.write(
                                self.style.WARNING(f"      Error en fila {idx}: {str(e)[:50]}")
                            )
                            continue
            
            return {
                'proyecto_encontrado': True,
                'proyecto_nombre': proyecto.nombre,
                'nuevas': nuevas,
                'total': total
            }
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"    Error leyendo archivo: {str(e)}"))
            return {
                'proyecto_encontrado': False,
                'codigo_encontrado': None,
                'nuevas': 0,
                'total': 0
            }