# monitoreo/management/commands/backup.py
from django.core.management.base import BaseCommand
from scripts.backup_db import crear_backup, limpiar_backups_viejos, listar_backups
import sys

class Command(BaseCommand):
    help = 'Gestiona backups de la base de datos'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--action',
            type=str,
            choices=['crear', 'listar', 'limpiar'],
            default='crear',
            help='Acción a realizar: crear, listar o limpiar'
        )
        
        parser.add_argument(
            '--dias',
            type=int,
            default=30,
            help='Días para limpiar backups antiguos (default: 30)'
        )
    
    def handle(self, *args, **options):
        action = options['action']
        dias = options['dias']
        
        if action == 'crear':
            self.stdout.write(self.style.SUCCESS('🚀 Creando backup...'))
            backup_file = crear_backup()
            
            if backup_file:
                self.stdout.write(self.style.SUCCESS(f'✅ Backup creado: {backup_file}'))
                limpiar_backups_viejos(dias)
            else:
                self.stdout.write(self.style.ERROR('❌ Error al crear backup'))
        
        elif action == 'listar':
            listar_backups()
        
        elif action == 'limpiar':
            self.stdout.write(self.style.WARNING(f'🧹 Limpiando backups con más de {dias} días...'))
            limpiar_backups_viejos(dias)