import os
import sqlite3
import psycopg2
import psycopg2.extras
from django.core.management.base import BaseCommand
from django.conf import settings
from decouple import config

class Command(BaseCommand):
    help = 'Migra datos de SQLite a PostgreSQL en el orden correcto'
    
    def handle(self, *args, **options):
        self.stdout.write("🔄 Iniciando migración a PostgreSQL...")
        
        sqlite_path = settings.BASE_DIR / 'db.sqlite3'
        
        if not sqlite_path.exists():
            self.stdout.write(self.style.ERROR("❌ No se encuentra db.sqlite3"))
            return
        
        try:
            # Conectar a SQLite
            sqlite_conn = sqlite3.connect(str(sqlite_path))
            sqlite_conn.text_factory = lambda b: b.decode('utf-8', 'ignore')
            sqlite_conn.row_factory = sqlite3.Row
            self.stdout.write("✅ Conectado a SQLite")
            
            # Conectar a PostgreSQL
            pg_conn = psycopg2.connect(
                dbname=config('DB_NAME'),
                user=config('DB_USER'),
                password=config('DB_PASSWORD'),
                host=config('DB_HOST'),
                port=config('DB_PORT')
            )
            pg_conn.autocommit = False
            pg_cursor = pg_conn.cursor()
            self.stdout.write("✅ Conectado a PostgreSQL")
            
            # ORDEN CORRECTO DE MIGRACIÓN
            tablas_orden = [
                'django_content_type',
                'auth_permission',
                'auth_group',
                'auth_user',
                'django_admin_log',
                'monitoreo_proyecto',  # Primero proyectos
                'monitoreo_medicion',   # Después mediciones (dependen de proyectos)
                'monitoreo_estadoservidor',
                'monitoreo_configuracionalerta',
                'auth_group_permissions',
                'auth_user_groups',
                'auth_user_user_permissions',
                'django_session'
            ]
            
            total_registros = 0
            
            for tabla in tablas_orden:
                self.stdout.write(f"\n📦 Migrando tabla: {tabla}")
                
                # Verificar si la tabla existe en SQLite
                cursor = sqlite_conn.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
                    (tabla,)
                )
                if not cursor.fetchone():
                    self.stdout.write(f"   ⚠️  Tabla no existe en SQLite, saltando")
                    continue
                
                # Obtener datos
                cursor = sqlite_conn.execute(f"SELECT * FROM {tabla}")
                data = cursor.fetchall()
                
                if not data:
                    self.stdout.write(f"   ⚠️  Tabla vacía")
                    continue
                
                # Obtener nombres de columnas
                columnas = [description[0] for description in cursor.description]
                
                # Limpiar datos
                insertados = 0
                for row in data:
                    try:
                        # Convertir valores según el tipo esperado
                        valores_limpios = []
                        for col, val in zip(columnas, row):
                            if val is None:
                                valores_limpios.append(None)
                            elif isinstance(val, (int, float)):
                                valores_limpios.append(val)
                            elif isinstance(val, str):
                                # Limpiar strings
                                val_limpio = val.encode('utf-8', 'ignore').decode('utf-8')
                                valores_limpios.append(val_limpio)
                            else:
                                valores_limpios.append(str(val))
                        
                        placeholders = ','.join(['%s'] * len(columnas))
                        columnas_str = ','.join(columnas)
                        
                        pg_cursor.execute(
                            f"INSERT INTO {tabla} ({columnas_str}) VALUES ({placeholders})",
                            valores_limpios
                        )
                        insertados += 1
                        
                    except Exception as e:
                        self.stdout.write(
                            self.style.WARNING(f"   ⚠️ Error en fila: {str(e)[:100]}")
                        )
                        continue
                
                pg_conn.commit()
                total_registros += insertados
                self.stdout.write(self.style.SUCCESS(f"   ✅ {insertados} registros migrados"))
            
            self.stdout.write(self.style.SUCCESS(
                f"\n🎉 Migración completada! Total: {total_registros} registros"
            ))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Error: {e}"))
            import traceback
            traceback.print_exc()
            if 'pg_conn' in locals():
                pg_conn.rollback()
            
        finally:
            if 'sqlite_conn' in locals():
                sqlite_conn.close()
            if 'pg_conn' in locals():
                pg_conn.close()