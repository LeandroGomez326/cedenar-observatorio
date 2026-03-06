# scripts/monitor.py
import requests
import os
import datetime
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import sys
from pathlib import Path

# Configuración
SITE_URL = os.environ.get('SITE_URL', 'https://cedenar-observatorio.onrender.com')
ALERT_EMAIL = os.environ.get('ALERT_EMAIL', 'admin@cedenar.gov.co')
SMTP_SERVER = os.environ.get('SMTP_SERVER', 'smtp.gmail.com')
SMTP_PORT = int(os.environ.get('SMTP_PORT', 587))
SMTP_USER = os.environ.get('SMTP_USER', '')
SMTP_PASSWORD = os.environ.get('SMTP_PASSWORD', '')

LOG_FILE = Path(__file__).parent.parent / 'logs' / 'monitor.log'

def setup_logging():
    """Configurar archivo de log"""
    LOG_FILE.parent.mkdir(exist_ok=True)
    return LOG_FILE

def log_message(msg, level="INFO"):
    """Escribir mensaje en log"""
    timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    log_entry = f"[{timestamp}] [{level}] {msg}\n"
    
    print(log_entry.strip())
    
    with open(LOG_FILE, 'a', encoding='utf-8') as f:
        f.write(log_entry)

def enviar_alerta(asunto, mensaje):
    """Enviar alerta por email"""
    if not SMTP_USER or not SMTP_PASSWORD:
        log_message("⚠️ Email no configurado", "WARNING")
        return False
    
    try:
        msg = MIMEMultipart()
        msg['From'] = SMTP_USER
        msg['To'] = ALERT_EMAIL
        msg['Subject'] = f"🚨 {asunto} - Observatorio CEDENAR"
        
        msg.attach(MIMEText(mensaje, 'html'))
        
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SMTP_USER, SMTP_PASSWORD)
        server.send_message(msg)
        server.quit()
        
        log_message(f"✅ Alerta enviada: {asunto}")
        return True
        
    except Exception as e:
        log_message(f"❌ Error enviando email: {e}", "ERROR")
        return False

def verificar_sitio():
    """Verificar que el sitio está funcionando"""
    log_message(f"🔍 Verificando sitio: {SITE_URL}")
    
    try:
        # Verificar página principal
        response = requests.get(SITE_URL, timeout=15, allow_redirects=True)
        
        if response.status_code == 200:
            log_message(f"✅ Sitio OK - {response.elapsed.total_seconds():.2f}s")
            
            # Verificar contenido mínimo
            if 'CEDENAR' in response.text or 'Monitoreo' in response.text:
                log_message("✅ Contenido verificado")
                return True, response.elapsed.total_seconds()
            else:
                log_message("⚠️ Sitio OK pero contenido inesperado", "WARNING")
                return True, response.elapsed.total_seconds()
        else:
            error_msg = f"❌ Error HTTP {response.status_code}"
            log_message(error_msg, "ERROR")
            return False, response.status_code
            
    except requests.exceptions.Timeout:
        error_msg = "❌ Timeout - El sitio no responde"
        log_message(error_msg, "ERROR")
        return False, "timeout"
        
    except requests.exceptions.ConnectionError:
        error_msg = "❌ Error de conexión - Sitio caído"
        log_message(error_msg, "ERROR")
        return False, "connection_error"
        
    except Exception as e:
        error_msg = f"❌ Error inesperado: {e}"
        log_message(error_msg, "ERROR")
        return False, str(e)

def verificar_apis_criticas():
    """Verificar APIs importantes"""
    apis = [
        f"{SITE_URL}/api/resumen/",
        f"{SITE_URL}/api/lecturas/1/?dias=1",
    ]
    
    resultados = []
    
    for api in apis:
        try:
            response = requests.get(api, timeout=10)
            if response.status_code == 200:
                log_message(f"✅ API OK: {api}")
                resultados.append(True)
            else:
                log_message(f"⚠️ API con problemas: {api} - {response.status_code}", "WARNING")
                resultados.append(False)
        except:
            log_message(f"❌ API falló: {api}", "ERROR")
            resultados.append(False)
    
    return all(resultados)

def verificar_base_datos():
    """Verificar conexión a BD (requiere Django)"""
    try:
        import django
        sys.path.append(str(Path(__file__).parent.parent))
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
        django.setup()
        
        from django.db import connections
        from django.db.utils import OperationalError
        
        db_conn = connections['default']
        try:
            db_conn.cursor()
            log_message("✅ Base de datos OK")
            return True
        except OperationalError:
            log_message("❌ Error conectando a BD", "ERROR")
            return False
            
    except Exception as e:
        log_message(f"⚠️ No se pudo verificar BD: {e}", "WARNING")
        return None

def generar_reporte(estado_sitio, tiempo_respuesta, apis_ok, bd_ok):
    """Generar reporte HTML del estado"""
    html = f"""
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; padding: 20px; }}
            .ok {{ color: green; }}
            .warning {{ color: orange; }}
            .error {{ color: red; }}
            .metric {{ margin: 10px 0; padding: 10px; background: #f5f5f5; border-radius: 5px; }}
        </style>
    </head>
    <body>
        <h2>📊 Reporte de Monitoreo - Observatorio CEDENAR</h2>
        <p>📅 {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        
        <div class="metric">
            <h3>🌐 Sitio Principal</h3>
            <p class="{'ok' if estado_sitio else 'error'}">
                Estado: {'✅ Funcionando' if estado_sitio else '❌ Caído'}
            </p>
            <p>Tiempo respuesta: {tiempo_respuesta:.2f}s</p>
        </div>
        
        <div class="metric">
            <h3>🔌 APIs</h3>
            <p class="{'ok' if apis_ok else 'warning'}">
                APIs: {'✅ Todas OK' if apis_ok else '⚠️ Algunas con problemas'}
            </p>
        </div>
        
        <div class="metric">
            <h3>💾 Base de Datos</h3>
            <p class="{'ok' if bd_ok else 'error' if bd_ok is False else 'warning'}">
                {'✅ Conectada' if bd_ok else '❌ Desconectada' if bd_ok is False else '⚠️ No verificada'}
            </p>
        </div>
        
        <p>🔍 Ver logs para más detalles</p>
    </body>
    </html>
    """
    return html

if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Monitoreo del sitio')
    parser.add_argument('--alert', action='store_true', help='Enviar alerta si hay problemas')
    parser.add_argument('--report', action='store_true', help='Generar reporte')
    
    args = parser.parse_args()
    
    # Configurar logging
    setup_logging()
    
    log_message("🚀 Iniciando monitoreo...")
    
    # Verificaciones
    estado_sitio, tiempo = verificar_sitio()
    apis_ok = verificar_apis_criticas()
    bd_ok = verificar_base_datos()
    
    # Enviar alerta si hay problemas
    if args.alert and not estado_sitio:
        asunto = "🚨 SITIO CAÍDO - Acción requerida"
        mensaje = f"""
        El sitio {SITE_URL} no está respondiendo.
        Tiempo: {datetime.datetime.now()}
        Error: {tiempo}
        
        Ver logs para más detalles.
        """
        enviar_alerta(asunto, mensaje)
    
    # Generar reporte
    if args.report:
        reporte = generar_reporte(estado_sitio, tiempo, apis_ok, bd_ok)
        reporte_file = Path(__file__).parent.parent / 'logs' / f'reporte_{datetime.datetime.now().strftime("%Y%m%d")}.html'
        with open(reporte_file, 'w', encoding='utf-8') as f:
            f.write(reporte)
        log_message(f"📊 Reporte guardado: {reporte_file}")
    
    log_message("✅ Monitoreo completado")