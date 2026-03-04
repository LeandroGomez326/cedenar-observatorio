# monitoreo/middleware.py
from django.shortcuts import redirect
from django.urls import reverse
from .models import ConsentimientoDatos

class ConsentimientoMiddleware:
    """Middleware para verificar que el usuario aceptó la política de privacidad"""
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Excluir rutas públicas y de consentimiento
        if request.user.is_authenticated:
            path = request.path
            excluded_paths = [
                reverse('politica_privacidad'),
                reverse('aceptar_privacidad'),
                reverse('logout'),
                '/admin/',
            ]
            
            if not any(path.startswith(ex) for ex in excluded_paths):
                # Verificar si ya aceptó
                if not ConsentimientoDatos.objects.filter(
                    usuario=request.user,
                    version_politica='1.0'
                ).exists():
                    return redirect(f"{reverse('politica_privacidad')}?next={path}")
        
        return self.get_response(request)