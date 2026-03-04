# scripts/backup_db.py
import os
import datetime
import subprocess
from pathlib import Path
import gzip
import shutil

# Configuración
BASE_DIR = Path(__file__).parent.parent
BACKUP_DIR = BASE_DIR / 'backups'

def crear_backup():
    """Crea un backup de la base de datos PostgreSQL"""
    
    # Crear directorio si no existe
    BACKUP_DIR.mkdir(exist_ok=True)
    
    # Obtener URL de la base de datos desde entorno
    db_url = os.environ.get('DATABASE_URL')
    
    if not db_url:
        print("❌ Error: DATABASE_URL no está configurada")
        return None
    
    # Nombre del archivo con timestamp
    timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_file = BACKUP_DIR / f'backup_{timestamp}.sql'
    
    print(f"📦 Creando backup: {backup_file}")
    
    try:
        # Extraer datos de la URL de PostgreSQL
        # Formato: postgresql://usuario:password@host:puerto/base_datos
        
        # Comando pg_dump
        cmd = f'pg_dump "{db_url}" > "{backup_file}"'
        
        # Ejecutar
        resultado = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        
        if resultado.returncode == 0:
            print(f"✅ Backup creado: {backup_file}")
            
            # Comprimir
            with open(backup_file, 'rb') as f_in:
                with gzip.open(f"{backup_file}.gz", 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
            
            # Eliminar archivo sin comprimir
            backup_file.unlink()
            
            print(f"✅ Backup comprimido: {backup_file}.gz")
            return f"{backup_file}.gz"
        else:
            print(f"❌ Error en pg_dump: {resultado.stderr}")
            return None
            
    except Exception as e:
        print(f"❌ Error inesperado: {e}")
        return None

def limpiar_backups_viejos(dias=30):
    """Elimina backups más antiguos que 'dias'"""
    import time
    ahora = time.time()
    eliminados = 0
    
    for f in BACKUP_DIR.glob('*.gz'):
        # Tiempo de modificación del archivo
        tiempo_mod = f.stat().st_mtime
        edad_dias = (ahora - tiempo_mod) / 86400  # 86400 segundos por día
        
        if edad_dias > dias:
            f.unlink()
            eliminados += 1
            print(f"🗑️ Eliminado backup viejo: {f}")
    
    if eliminados > 0:
        print(f"✅ {eliminados} backups antiguos eliminados")
    else:
        print("ℹ️ No hay backups antiguos para eliminar")

def listar_backups():
    """Lista todos los backups disponibles"""
    backups = sorted(BACKUP_DIR.glob('*.gz'), reverse=True)
    
    print("\n📋 Backups disponibles:")
    print("-" * 50)
    
    for i, b in enumerate(backups, 1):
        tamaño = b.stat().st_size / (1024*1024)  # MB
        fecha = datetime.datetime.fromtimestamp(b.stat().st_mtime)
        print(f"{i}. {b.name} - {fecha.strftime('%Y-%m-%d %H:%M')} - {tamaño:.2f} MB")
    
    print("-" * 50)
    return backups

if __name__ == '__main__':
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == 'list':
        listar_backups()
    else:
        print("🚀 Iniciando proceso de backup...")
        backup = crear_backup()
        if backup:
            limpiar_backups_viejos(30)
            print("\n📊 Resumen:")
            listar_backups()