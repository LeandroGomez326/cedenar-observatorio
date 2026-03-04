from django.contrib import admin
from .models import Proyecto, Medicion, EstadoServidor, ConfiguracionAlerta

@admin.register(Proyecto)
class ProyectoAdmin(admin.ModelAdmin):
    list_display = ['id', 'nombre', 'codigo_medidor', 'marca', 'ubicacion', 'activo', 'latitud', 'longitud']
    list_filter = ['marca', 'activo']
    search_fields = ['nombre', 'codigo_medidor']
    list_editable = ['latitud', 'longitud']  # Para editar coordenadas directamente

@admin.register(Medicion)
class MedicionAdmin(admin.ModelAdmin):  
    list_display = ['id', 'proyecto', 'fecha_lectura', 'energia_activa_import', 'energia_activa_export']
    list_filter = ['proyecto']
    date_hierarchy = 'fecha_lectura'

@admin.register(EstadoServidor)
class EstadoServidorAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'activo', 'ultima_verificacion', 'tiempo_respuesta_ms']

@admin.register(ConfiguracionAlerta)
class ConfiguracionAlertaAdmin(admin.ModelAdmin):
    list_display = ['proyecto', 'alerta_inactividad', 'alerta_umbral_generacion', 'enviar_reporte_semanal']