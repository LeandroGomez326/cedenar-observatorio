from django_ratelimit.decorators import ratelimit
from django.http import HttpResponseForbidden
from functools import wraps

def rate_limit(key='ip', rate='5/m', method='POST'):
    """
    Decorador para limitar tasa de requests
    Uso: @rate_limit(rate='3/m')  # 3 intentos por minuto
    """
    def decorator(view_func):
        @wraps(view_func)
        @ratelimit(key=key, rate=rate, method=method, block=True)
        def _wrapped_view(request, *args, **kwargs):
            if getattr(request, 'limited', False):
                return HttpResponseForbidden('Demasiadas solicitudes. Intenta más tarde.')
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator