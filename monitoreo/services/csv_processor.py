import pandas as pd
from io import BytesIO, TextIOWrapper
from datetime import datetime
from ..models import Medicion

def procesar_archivo(archivo, proyecto):
    """
    Procesa archivos del formato Microstar MeterView
    """
    try:
        nombre = archivo.name.lower()
        print(f"📄 Procesando: {nombre}")
        
        # Leer archivo según extensión
        if nombre.endswith('.csv'):
            # Intentar diferentes delimitadores
            content = archivo.read().decode('utf-8')
            archivo.seek(0)  # Resetear puntero
            
            # Detectar delimitador
            if '|' in content:
                print("✅ Delimitador detectado: '|'")
                df = pd.read_csv(TextIOWrapper(archivo, encoding='utf-8'), delimiter='|', skipinitialspace=True)
            elif ';' in content:
                print("✅ Delimitador detectado: ';'")
                df = pd.read_csv(TextIOWrapper(archivo, encoding='utf-8'), delimiter=';')
            else:
                print("✅ Delimitador detectado: ','")
                df = pd.read_csv(TextIOWrapper(archivo, encoding='utf-8'))
                
        elif nombre.endswith(('.xlsx', '.xls')):
            df = pd.read_excel(BytesIO(archivo.read()))
        else:
            return {'exito': False, 'mensaje': '❌ Formato no soportado'}
        
        print(f"📊 Columnas encontradas: {list(df.columns)}")
        
        # 🔍 BUSCAR COLUMNA DE FECHA (VERSIÓN MEJORADA)
        col_fecha = None
        col_consumo = None
        col_generacion = None
        
        for col in df.columns:
            col_str = str(col).strip()
            print(f"  Examinando: '{col_str}'")
            
            # Buscar columna de fecha (versiones con/sin acento)
            if any(term in col_str.lower() for term in ['tiempo de captura', 'tempo de captura', 'fecha']):
                col_fecha = col
                print(f"  ✅ Fecha encontrada: '{col_str}'")
            
            # Buscar columna de consumo (Energia Activa+)
            elif any(term in col_str for term in ['Energia Activa+', 'Energía Activa+', '1.8.0']):
                col_consumo = col
                print(f"  ✅ Consumo encontrado: '{col_str}'")
            
            # Buscar columna de generación (Energia Activa-)
            elif any(term in col_str for term in ['Energia Activa-', 'Energía Activa-', '2.8.0']):
                col_generacion = col
                print(f"  ✅ Generación encontrada: '{col_str}'")
        
        # Si no encuentra fecha, intentar con la primera columna
        if not col_fecha and len(df.columns) > 0:
            col_fecha = df.columns[0]
            print(f"⚠️ Usando primera columna como fecha: '{col_fecha}'")
        
        if not col_fecha:
            return {'exito': False, 'mensaje': '❌ No se encontró columna de fecha'}
        
        print(f"📌 Columnas finales: Fecha='{col_fecha}', Consumo='{col_consumo}', Generación='{col_generacion}'")
        
        # Saltar filas de encabezado (hasta encontrar datos)
        df = df.dropna(how='all')
        df = df.reset_index(drop=True)
        
        # Procesar filas
        contador = 0
        errores = 0
        filas_con_error = []
        
        for idx, fila in df.iterrows():
            try:
                # Obtener fecha
                fecha_valor = fila[col_fecha]
                
                # Saltar filas vacías
                if pd.isna(fecha_valor):
                    continue
                
                fecha_str = str(fecha_valor).strip()
                
                # Saltar filas que contienen texto del encabezado
                if any(term in fecha_str.lower() for term in ['tiempo de captura', 'fecha', 'tiempo']):
                    continue
                
                print(f"  Fila {idx}: Fecha raw = '{fecha_str}'")
                
                # Intentar diferentes formatos de fecha
                fecha = None
                formatos = [
                    '%Y-%m-%d %H:%M:%S',
                    '%Y-%m-%d %H:%M',
                    '%d/%m/%Y %H:%M:%S',
                    '%d/%m/%Y %H:%M',
                    '%d-%m-%Y %H:%M:%S',
                    '%d-%m-%Y %H:%M'
                ]
                
                for fmt in formatos:
                    try:
                        fecha = datetime.strptime(fecha_str, fmt)
                        print(f"    ✅ Formato {fmt} exitoso")
                        break
                    except:
                        continue
                
                if not fecha:
                    try:
                        fecha = pd.to_datetime(fecha_str)
                        if hasattr(fecha, 'to_pydatetime'):
                            fecha = fecha.to_pydatetime()
                        print(f"    ✅ Pandas datetime exitoso")
                    except:
                        errores += 1
                        filas_con_error.append(idx)
                        print(f"    ❌ No se pudo parsear fecha: {fecha_str}")
                        continue
                
                # Función para limpiar números (convertir coma a punto)
                def limpiar_numero(valor):
                    if pd.isna(valor):
                        return 0.0
                    # Convertir a string y reemplazar coma por punto
                    valor_str = str(valor).strip()
                    valor_str = valor_str.replace(',', '.')
                    # Quitar espacios y caracteres extraños
                    valor_str = ''.join(c for c in valor_str if c.isdigit() or c in ['.', '-'])
                    try:
                        return float(valor_str)
                    except:
                        return 0.0
                
                consumo_acum = limpiar_numero(fila[col_consumo]) if col_consumo else 0.0
                generacion_acum = limpiar_numero(fila[col_generacion]) if col_generacion else 0.0
                
                # Guardar medición
                Medicion.objects.update_or_create(
                    proyecto=proyecto,
                    fecha_lectura=fecha,
                    defaults={
                        'codigo_usuario': proyecto.codigo_medidor,
                        'medidor': proyecto.codigo_medidor,
                        'energia_activa_import': consumo_acum,
                        'energia_reactiva_import': 0.0,
                        'energia_activa_export': generacion_acum,
                        'energia_reactiva_export': 0.0,
                    }
                )
                
                contador += 1
                
            except Exception as e:
                errores += 1
                filas_con_error.append(idx)
                print(f"⚠️ Error fila {idx}: {e}")
                continue
        
        # Mensaje de resultado
        if errores > 0:
            mensaje = f"✅ {contador} registros procesados, ⚠️ {errores} errores (filas: {filas_con_error[:5]})"
        else:
            mensaje = f"✅ {contador} registros procesados exitosamente"
        
        return {
            'exito': True,
            'mensaje': mensaje
        }
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {
            'exito': False,
            'mensaje': f'❌ Error: {str(e)}'
        }