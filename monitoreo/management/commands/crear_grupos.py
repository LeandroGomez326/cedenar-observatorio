from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from monitoreo.models import Proyecto

class Command(BaseCommand):
    help = 'Crea los grupos de usuarios para alertas'
    
    def handle(self, *args, **options):
        grupos = {
            'admin': 'Administradores - acceso total',
            'tecnico': 'Técnicos - ven proyectos inactivos',
            'consultor': 'Consultores - ven generación baja',
        }
        
        self.stdout.write("🚀 Creando grupos de usuarios...")
        
        for nombre, desc in grupos.items():
            grupo, created = Group.objects.get_or_create(name=nombre)
            if created:
                self.stdout.write(self.style.SUCCESS(f'✅ Grupo creado: {nombre}'))
            else:
                self.stdout.write(f'ℹ️ Grupo existente: {nombre}')
        
        # Permiso básico para ver proyectos
        ct_proyecto = ContentType.objects.get_for_model(Proyecto)
        permiso_ver, _ = Permission.objects.get_or_create(
            codename='view_proyecto',
            name='Can view proyecto',
            content_type=ct_proyecto
        )
        
        for grupo_nombre in grupos:
            grupo = Group.objects.get(name=grupo_nombre)
            grupo.permissions.add(permiso_ver)
        
        self.stdout.write(self.style.SUCCESS('✅ Permisos básicos asignados'))
        self.stdout.write("\n📋 Para asignar usuarios a grupos:")
        self.stdout.write("  - Desde admin: /admin/auth/user/")
        self.stdout.write("  - O en consola: user.groups.add(Group.objects.get(name='tecnico'))")