import sqlite3
import psycopg2
from django.core.management.base import BaseCommand
from django.conf import settings
from decouple import config

class Command(BaseCommand):
    help = 'Migra solo los datos de monitoreo'
    
    def handle(self, *args, **options):
        self.stdout.write("🔄 Migrando datos de monitoreo...")
        
        sqlite_path = settings.BASE_DIR / 'db.sqlite3'
        
        try:
            # Conectar a SQLite
            sqlite_conn = sqlite3.connect(str(sqlite_path))
            sqlite_conn.row_factory = sqlite3.Row
            sqlite_cursor = sqlite_conn.cursor()
            
            # Conectar a PostgreSQL
            pg_conn = psycopg2.connect(
                dbname=config('DB_NAME'),
                user=config('DB_USER'),
                password=config('DB_PASSWORD'),
                host=config('DB_HOST'),
                port=config('DB_PORT')
            )
            pg_cursor = pg_conn.cursor()
            
            # 1. Migrar proyectos
            self.stdout.write("📦 Migrando proyectos...")
            sqlite_cursor.execute("SELECT * FROM monitoreo_proyecto")
            proyectos = sqlite_cursor.fetchall()
            
            for p in proyectos:
                try:
                    pg_cursor.execute("""
                        INSERT INTO monitoreo_proyecto 
                        (id, nombre, codigo_medidor, marca, ubicacion, activo, fecha_creacion, fecha_actualizacion)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    """, (
                        p[0], p[1], p[2], p[3], p[4], 
                        bool(p[5]) if p[5] is not None else True,
                        p[6], p[7]
                    ))
                except Exception as e:
                    self.stdout.write(self.style.WARNING(f"  ⚠️ Error proyecto {p[1]}: {e}"))
            
            pg_conn.commit()
            self.stdout.write(self.style.SUCCESS(f"  ✅ {len(proyectos)} proyectos migrados"))
            
            # 2. Migrar mediciones
            self.stdout.write("📦 Migrando mediciones...")
            sqlite_cursor.execute("SELECT * FROM monitoreo_medicion")
            mediciones = sqlite_cursor.fetchall()
            
            count = 0
            for m in mediciones:
                try:
                    pg_cursor.execute("""
                        INSERT INTO monitoreo_medicion 
                        (id, proyecto_id, codigo_usuario, medidor, fecha_lectura, 
                         energia_activa_import, energia_reactiva_import, 
                         energia_activa_export, energia_reactiva_export)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """, (
                        m[0], m[1], m[2], m[3], m[4],
                        float(m[5]) if m[5] else 0,
                        float(m[6]) if m[6] else 0,
                        float(m[7]) if m[7] else 0,
                        float(m[8]) if m[8] else 0
                    ))
                    count += 1
                    if count % 1000 == 0:
                        pg_conn.commit()
                        self.stdout.write(f"    ...{count} mediciones")
                        
                except Exception as e:
                    self.stdout.write(self.style.WARNING(f"  ⚠️ Error: {e}"))
            
            pg_conn.commit()
            self.stdout.write(self.style.SUCCESS(f"  ✅ {count} mediciones migradas"))
            
            # 3. Migrar estado servidores
            self.stdout.write("📦 Migrando estado servidores...")
            sqlite_cursor.execute("SELECT * FROM monitoreo_estadoservidor")
            estados = sqlite_cursor.fetchall()
            
            for e in estados:
                try:
                    pg_cursor.execute("""
                        INSERT INTO monitoreo_estadoservidor 
                        (id, nombre, activo, ultima_verificacion, tiempo_respuesta_ms, mensaje_error)
                        VALUES (%s, %s, %s, %s, %s, %s)
                    """, (
                        e[0], e[1], bool(e[2]), e[3], e[4], e[5]
                    ))
                except Exception as ex:
                    self.stdout.write(self.style.WARNING(f"  ⚠️ Error: {ex}"))
            
            pg_conn.commit()
            self.stdout.write(self.style.SUCCESS(f"  ✅ {len(estados)} estados migrados"))
            
            self.stdout.write(self.style.SUCCESS("\n🎉 Migración completada!"))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Error: {e}"))
            import traceback
            traceback.print_exc()
            
        finally:
            if 'sqlite_conn' in locals():
                sqlite_conn.close()
            if 'pg_conn' in locals():
                pg_conn.close()