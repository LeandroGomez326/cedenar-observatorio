from django.urls import path
from . import views

# Sin app_name por ahora

urlpatterns = [
    # URLs principales
    path('', views.dashboard, name='dashboard'),
    path('registro/', views.registro, name='registro'),
    path('proyecto/<int:proyecto_id>/', views.detalle_proyecto, name='detalle_proyecto'),
    
    # APIs
    path('api/lecturas/<int:proyecto_id>/', views.api_lecturas, name='api_lecturas'),
    path('api/resumen/', views.api_resumen, name='api_resumen'),
    path('api/generacion-diaria/<int:proyecto_id>/', views.api_generacion_diaria, name='api_generacion_diaria'),
    
    # Exportación
    path('exportar/<int:proyecto_id>/', views.exportar_excel, name='exportar_excel'),
    
    # Inversores
    path('estado-inversores/', views.estado_inversores, name='estado_inversores'),
    
    # CRUD Proyectos
    path('proyectos/', views.lista_proyectos, name='lista_proyectos'),
    path('proyectos/crear/', views.crear_proyecto, name='crear_proyecto'),
    path('proyectos/<int:proyecto_id>/editar/', views.editar_proyecto, name='editar_proyecto'),
    path('proyectos/<int:proyecto_id>/eliminar/', views.eliminar_proyecto, name='eliminar_proyecto'),
    path('proyectos/<int:proyecto_id>/toggle/', views.toggle_proyecto_activo, name='toggle_proyecto_activo'),
    
    # Estado servidores
    path('estado-servidores/', views.estado_servidores, name='estado_servidores'),
    
    # Curva diaria
    path('campana/<int:proyecto_id>/', views.campana_generacion, name='campana_generacion'),

    # Generación de PDF
    path('reporte-pdf/<int:proyecto_id>/', views.reporte_pdf_mensual, name='reporte_pdf'),

    # Preferencias
    path('api/preferencias/guardar/', views.guardar_preferencias, name='guardar_preferencias'),
    path('api/preferencias/cargar/', views.cargar_preferencias, name='cargar_preferencias'),
    
    # Mapas
    path('mapa/', views.mapa_proyectos, name='mapa_proyectos'),
    path('mapa-nuevo/', views.mapa_nuevo, name='mapa_nuevo'),
    
    # CSV
    path('proyectos/<int:proyecto_id>/subir-csv/', views.subir_csv, name='subir_csv'),
    
    # Variables eléctricas - API y Vista
    path('api/variables-electricas/<int:proyecto_id>/', views.api_variables_electricas, name='api_variables'),
    path('variables/<int:proyecto_id>/', views.variables_electricas, name='variables_electricas'),  # ¡ESTA ES LA CORRECTA!
    
    # API lecturas por período
    path('api/lecturas-por-periodo/', views.api_lecturas_por_periodo, name='api_lecturas_por_periodo'),

    path('api/ia/entrenar/<int:proyecto_id>/', views.entrenar_modelo, name='entrenar_ia'),
    path('api/ia/predecir/<int:proyecto_id>/', views.predecir, name='predecir_ia'),
    path('api/ia/verificar/', views.verificar_modelos_ia, name='verificar_ia'),
    path('privacidad/', views.politica_privacidad, name='politica_privacidad'),
    path('aceptar-privacidad/', views.aceptar_privacidad, name='aceptar_privacidad'),
    path('api/ia/entrenar/<int:proyecto_id>/', views.entrenar_modelo, name='entrenar_ia'),
    path('api/ia/predecir/<int:proyecto_id>/', views.predecir, name='predecir_ia'),
]