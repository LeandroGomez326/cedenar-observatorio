from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from monitoreo.decorators import rate_limit  # ← IMPORTAR

# Wrapper con rate limiting para login
login_view = rate_limit(rate='3/m')(auth_views.LoginView.as_view(template_name='monitoreo/login.html'))

urlpatterns = [
    path('admin/', admin.site.urls),
    path('login/', login_view, name='login'),  # ← USA EL WRAPPER
    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),
    path('', include('monitoreo.urls')),
]