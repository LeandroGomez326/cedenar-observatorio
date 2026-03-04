import os
import shutil
from datetime import datetime
from django.core.management.base import BaseCommand
from django.conf import settings

class Command(BaseCommand):
    help = 'Realiza backup de la base de datos'
    
    def add_arguments(self, parser):
        parser.add_argument('--dest', type=str, help='Directorio de destino')
    
    def handle(self, *args, **options):
        # Directorio de backups
        backup_dir = options.get('dest') or os.path.join(settings.BASE_DIR, 'backups')
        os.makedirs(backup_dir, exist_ok=True)
        
        # Nombre del archivo con timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_file = os.path.join(backup_dir, f'db_backup_{timestamp}.sqlite3')
        
        # Ruta de la base de datos actual
        db_path = settings.DATABASES['default']['NAME']
        
        # Copiar archivo
        if os.path.exists(db_path):
            shutil.copy2(db_path, backup_file)
            self.stdout.write(self.style.SUCCESS(f'✅ Backup creado: {backup_file}'))
            
            # Limpiar backups antiguos (mantener últimos 7)
            backups = sorted([f for f in os.listdir(backup_dir) if f.startswith('db_backup_')])
            while len(backups) > 7:
                old_backup = os.path.join(backup_dir, backups.pop(0))
                os.remove(old_backup)
                self.stdout.write(f'🗑️  Backup antiguo eliminado: {old_backup}')
        else:
            self.stdout.write(self.style.ERROR('❌ Base de datos no encontrada'))