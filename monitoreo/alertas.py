from django.core.mail import send_mail, EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
from django.contrib.auth.models import User, Group
from .models import Proyecto, Medicion
from datetime import datetime, timedelta
import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

logger = logging.getLogger(__name__)

class SistemaAlertas:
    """Sistema de alertas por email - solo para usuarios registrados"""
    
    def obtener_emails_por_grupo(self, grupos=None):
        """
        Obtiene emails de usuarios según su grupo
        grupos: lista de nombres de grupo ['admin', 'tecnico', 'consultor']
        """
        if grupos is None:
            grupos = ['admin']
        
        usuarios = User.objects.filter(is_active=True)
        emails = set()
        
        for grupo_nombre in grupos:
            try:
                grupo = Group.objects.get(name=grupo_nombre)
                for usuario in usuarios.filter(groups=grupo):
                    if usuario.email:
                        emails.add(usuario.email)
                        logger.debug(f"📧 Añadido {usuario.email} del grupo {grupo_nombre}")
            except Group.DoesNotExist:
                logger.warning(f"⚠️ Grupo '{grupo_nombre}' no existe")
        
        # Incluir superusuarios siempre
        for usuario in usuarios.filter(is_superuser=True):
            if usuario.email:
                emails.add(usuario.email)
                logger.debug(f"📧 Añadido superusuario {usuario.email}")
        
        return list(emails)
    
    def enviar_alerta(self, asunto, mensaje, nivel='info', html=None, grupos=None, email_directo=None):
        """
        Envía alerta a usuarios de grupos específicos
        """
        if email_directo:
            emails = [email_directo]
        else:
            emails = self.obtener_emails_por_grupo(grupos)
        
        if not emails:
            logger.warning(f"⚠️ No hay destinatarios para alerta: {asunto}")
            return False
        
        if not settings.EMAIL_HOST_USER or not settings.EMAIL_HOST_PASSWORD:
            logger.warning("Email no configurado - variables de entorno faltantes")
            return False
        
        try:
            # Crear mensaje con MIME
            msg = MIMEMultipart('alternative')
            msg['Subject'] = f"[CEDENAR] {asunto}"
            msg['From'] = settings.DEFAULT_FROM_EMAIL
            msg['To'] = ', '.join(emails)
            
            # Versión texto plano (fallback)
            parte_texto = MIMEText(mensaje, 'plain', 'utf-8')
            msg.attach(parte_texto)
            
            # Versión HTML
            if html:
                parte_html = MIMEText(html, 'html', 'utf-8')
            else:
                html_simple = f"""
                <html>
                <head>
                    <meta charset="UTF-8">
                </head>
                <body style="font-family: Arial, sans-serif; padding: 20px;">
                    <h2 style="color: #2563eb;">✅ {asunto}</h2>
                    <p>{mensaje}</p>
                </body>
                </html>
                """
                parte_html = MIMEText(html_simple, 'html', 'utf-8')
            
            msg.attach(parte_html)
            
            # Enviar
            with smtplib.SMTP(settings.EMAIL_HOST, settings.EMAIL_PORT) as server:
                server.starttls()
                server.login(settings.EMAIL_HOST_USER, settings.EMAIL_HOST_PASSWORD)
                server.send_message(msg)
            
            logger.info(f"✅ Email HTML enviado a {len(emails)} usuarios")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error enviando alerta: {e}")
            return False
    
    def alerta_proyecto_inactivo(self, proyecto, horas_sin_datos=24):
        """
        Alerta para técnicos y admins cuando un proyecto no envía datos
        """
        ultima = Medicion.objects.filter(proyecto=proyecto).order_by('-fecha_lectura').first()
        
        if not ultima:
            asunto = f"⚠️ Proyecto sin datos: {proyecto.nombre}"
            html = render_to_string('monitoreo/alertas/proyecto_inactivo.html', {
                'proyecto': proyecto,
                'ultima_lectura': 'Nunca',
                'horas_inactivo': 'N/A',
                'fecha': datetime.now(),
            })
            mensaje_texto = strip_tags(html)
            
            return self.enviar_alerta(
                asunto, 
                mensaje_texto, 
                nivel='warning', 
                html=html,
                grupos=['tecnico', 'admin']
            )
        
        tiempo_inactivo = datetime.now() - ultima.fecha_lectura
        horas = tiempo_inactivo.total_seconds() / 3600
        
        if horas > horas_sin_datos:
            asunto = f"⚠️ Proyecto inactivo: {proyecto.nombre}"
            html = render_to_string('monitoreo/alertas/proyecto_inactivo.html', {
                'proyecto': proyecto,
                'ultima_lectura': ultima.fecha_lectura,
                'horas_inactivo': round(horas, 1),
                'fecha': datetime.now(),
            })
            mensaje_texto = strip_tags(html)
            
            return self.enviar_alerta(
                asunto, 
                mensaje_texto, 
                nivel='warning', 
                html=html,
                grupos=['tecnico', 'admin']
            )
    
    def alerta_generacion_baja(self, proyecto, umbral_kwh=10):
        """
        Alerta para consultores y admins cuando la generación es baja
        """
        hoy = datetime.now().date()
        
        mediciones_hoy = Medicion.objects.filter(
            proyecto=proyecto,
            fecha_lectura__date=hoy
        ).order_by('fecha_lectura')
        
        if mediciones_hoy.count() >= 2:
            primera = mediciones_hoy.first()
            ultima = mediciones_hoy.last()
            generacion_hoy = ultima.energia_activa_export - primera.energia_activa_export
            
            if generacion_hoy < umbral_kwh:
                asunto = f"☀️ Generación baja: {proyecto.nombre}"
                html = render_to_string('monitoreo/alertas/generacion_baja.html', {
                    'proyecto': proyecto,
                    'generacion': round(generacion_hoy, 2),
                    'umbral': umbral_kwh,
                    'fecha': hoy,
                })
                mensaje_texto = strip_tags(html)
                
                return self.enviar_alerta(
                    asunto, 
                    mensaje_texto, 
                    nivel='info', 
                    html=html,
                    grupos=['consultor', 'admin']
                )
    
    def alerta_backup(self, archivo_backup, tamano):
        """
        Alerta solo para admins cuando se completa un backup
        """
        asunto = "✅ Backup completado exitosamente"
        html = render_to_string('monitoreo/alertas/backup_completado.html', {
            'archivo': archivo_backup,
            'tamano': round(tamano / (1024*1024), 2),
            'fecha': datetime.now(),
        })
        mensaje_texto = strip_tags(html)
        
        return self.enviar_alerta(
            asunto, 
            mensaje_texto, 
            nivel='success', 
            html=html,
            grupos=['admin']
        )
    
    def alerta_error_critico(self, error, modulo):
        """
        Alerta solo para admins (errores del sistema)
        """
        asunto = f"🚨 ERROR CRÍTICO en {modulo}"
        mensaje = f"""
        Se ha producido un error crítico en el sistema:
        
        Módulo: {modulo}
        Error: {str(error)}
        Hora: {datetime.now()}
        """
        
        return self.enviar_alerta(
            asunto, 
            mensaje, 
            nivel='error',
            grupos=['admin']
        )
    
    def alerta_prueba(self, email_prueba=None):
        """
        Alerta de prueba para verificar configuración
        """
        asunto = "🔔 Alerta de Prueba"
        html = render_to_string('monitoreo/alertas/alerta_prueba_simple.html', {
            'fecha': datetime.now(),
        })
        mensaje_texto = "Alerta de prueba del sistema CEDENAR"
        
        if email_prueba:
            return self.enviar_alerta(
                asunto, 
                mensaje_texto, 
                html=html,
                email_directo=email_prueba
            )
        else:
            return self.enviar_alerta(
                asunto, 
                mensaje_texto, 
                html=html,
                grupos=['admin']
            )