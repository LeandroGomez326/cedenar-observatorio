from django.db import models
from django.conf import settings
from django.contrib.auth.models import AbstractUser

# ELIMINA la clase Usuario si existe
class PreferenciaDashboard(models.Model):
    """Almacena las preferencias de dashboard de cada usuario"""
    usuario = models.OneToOneField(
        settings.AUTH_USER_MODEL,  # O también puede ser 'auth.User'
        on_delete=models.CASCADE,
        related_name='preferencias_dashboard'
    )
    tema = models.CharField(
        max_length=10,
        choices=[('claro', 'Claro'), ('oscuro', 'Oscuro')],
        default='claro'
    )
    layout = models.CharField(
        max_length=20,
        choices=[
            ('compacto', 'Compacto'),
            ('detallado', 'Detallado'),
            ('tarjetas', 'Tarjetas Grandes')
        ],
        default='compacto'
    )
    widgets_visibles = models.JSONField(default=list)
    orden_widgets = models.JSONField(default=list)
    ultima_actualizacion = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Preferencias de {self.usuario.username}"

class Proyecto(models.Model):
    MARCA_CHOICES = [
        ('HUAWEI', 'Huawei'),
        ('GROWATT', 'Growatt'),
    ]
    latitud = models.FloatField(null=True, blank=True, help_text="Latitud (ej: 1.227266)")
    longitud = models.FloatField(null=True, blank=True, help_text="Longitud (ej: -77.281932)")
    direccion = models.CharField(max_length=255, blank=True, help_text="Dirección física")
    nombre = models.CharField(max_length=150)
    codigo_medidor = models.CharField(max_length=100, unique=True)
    marca = models.CharField(max_length=20, choices=MARCA_CHOICES, blank=True)
    ubicacion = models.CharField(max_length=200, blank=True)
    activo = models.BooleanField(default=True, help_text="Indica si el medidor está activo")
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.nombre

class Medicion(models.Model):
    proyecto = models.ForeignKey(Proyecto, on_delete=models.CASCADE)
    codigo_usuario = models.CharField(max_length=50)
    medidor = models.CharField(max_length=50)
    fecha_lectura = models.DateTimeField()
    energia_activa_import = models.FloatField()
    energia_reactiva_import = models.FloatField()
    energia_activa_export = models.FloatField()
    energia_reactiva_export = models.FloatField()
    # NUEVOS CAMPOS PARA VARIABLES ELÉCTRICAS
    potencia_dc_w = models.FloatField(null=True, blank=True, help_text="Potencia DC (W)")
    potencia_reactiva_var = models.FloatField(null=True, blank=True, help_text="Potencia reactiva (VAr)")
    potencia_aparente_va = models.FloatField(null=True, blank=True, help_text="Potencia aparente (VA)")
    corriente_ac_total_a = models.FloatField(null=True, blank=True, help_text="Corriente AC total (A)")
    corriente_dc_a = models.FloatField(null=True, blank=True, help_text="Corriente DC (A)")
    voltaje_ac_v = models.FloatField(null=True, blank=True, help_text="Voltaje AC (V)")
    voltaje_dc_v = models.FloatField(null=True, blank=True, help_text="Voltaje DC (V)")
    corriente_ac_a = models.FloatField(null=True, blank=True, help_text="Corriente AC (A)")
    voltaje_entre_fases_v = models.FloatField(null=True, blank=True, help_text="Voltaje AC entre fases (V)")
    factor_potencia_pct = models.FloatField(null=True, blank=True, help_text="Factor de potencia (%)")


    class Meta:
        unique_together = ('proyecto', 'fecha_lectura')
        indexes = [
            models.Index(fields=['proyecto', 'fecha_lectura']),
        ]
    
class EstadoServidor(models.Model):
    TIPO_CHOICES = [
        ('API_HUAWEI', 'API Huawei'),
        ('API_GROWATT', 'API Growatt'),
        ('BASE_DATOS', 'Base de Datos'),
        ('SERVIDOR', 'Servidor Principal'),
    ]
    
    
    nombre = models.CharField(max_length=50, choices=TIPO_CHOICES, unique=True)
    activo = models.BooleanField(default=True)
    ultima_verificacion = models.DateTimeField(auto_now=True)
    tiempo_respuesta_ms = models.IntegerField(default=0)
    mensaje_error = models.TextField(blank=True)
    
    def __str__(self):
        return f"{self.get_nombre_display()} - {'✅ Activo' if self.activo else '❌ Inactivo'}"

    def __str__(self):
        return f"{self.proyecto.nombre} - {self.fecha_lectura}"
    
class ConfiguracionAlerta(models.Model):
    proyecto = models.OneToOneField(Proyecto, on_delete=models.CASCADE, related_name='configuracion_alerta')
    
    # Alertas por inactividad
    alerta_inactividad = models.BooleanField(default=True, help_text='Enviar alerta si el medidor no envía datos')
    horas_inactividad = models.IntegerField(default=24, help_text='Horas sin datos para considerar inactivo')
    
    # Alertas por umbral de generación
    alerta_umbral_generacion = models.BooleanField(default=False, help_text='Enviar alerta si la generación es baja')
    umbral_generacion_kwh = models.FloatField(default=10.0, help_text='Mínimo de generación diaria esperada (kWh)')
    
    # Reporte semanal
    enviar_reporte_semanal = models.BooleanField(default=True, help_text='Enviar reporte semanal por email')
    dia_reporte = models.IntegerField(default=0, choices=[(0, 'Lunes'), (1, 'Martes'), (2, 'Miércoles'), (3, 'Jueves'), (4, 'Viernes'), (5, 'Sábado'), (6, 'Domingo')])
    
    # Destinatarios adicionales
    emails_adicionales = models.TextField(blank=True, help_text='Emails adicionales separados por coma')
    
    # Notificaciones personalizadas
    notificaciones_activadas = models.BooleanField(default=True)
    
    def __str__(self):
        return f"Alertas - {self.proyecto.nombre}"
    
    def get_emails_destino(self, incluir_admin=True):
        emails = []
        if incluir_admin:
            # Obtener todos los superusuarios
            from django.contrib.auth import get_user_model
            User = get_user_model()
            admins = User.objects.filter(is_superuser=True)
            emails.extend([admin.email for admin in admins if admin.email])
        
        # Agregar emails adicionales
        if self.emails_adicionales:
            extras = [email.strip() for email in self.emails_adicionales.split(',') if email.strip()]
            emails.extend(extras)
        
        return list(set(emails))  # Eliminar duplicados

class PreferenciaDashboard(models.Model):
    """Almacena las preferencias de dashboard de cada usuario"""
    usuario = models.OneToOneField(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE,
        related_name='preferencias_dashboard'
    )
    fecha_inicio = models.DateField(null=True, blank=True)
    fecha_fin = models.DateField(null=True, blank=True)
    proyectos_seleccionados = models.JSONField(default=list)
    tipo_comparacion = models.CharField(
        max_length=20,
        choices=[('dia', 'Día'), ('semana', 'Semana'), ('mes', 'Mes'), ('año', 'Año')],
        default='mes'
    )
    ultima_actualizacion = models.DateTimeField(auto_now=True)    
    tema = models.CharField(
        max_length=10,
        choices=[('claro', 'Claro'), ('oscuro', 'Oscuro')],
        default='claro'
    )
    layout = models.CharField(
        max_length=20,
        choices=[
            ('compacto', 'Compacto'),
            ('detallado', 'Detallado'),
            ('tarjetas', 'Tarjetas Grandes')
        ],
        default='compacto'
    )
    widgets_visibles = models.JSONField(default=list)
    orden_widgets = models.JSONField(default=list)
    ultima_actualizacion = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Preferencias de {self.usuario.username}"
    
    
