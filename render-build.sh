#!/usr/bin/env bash
# render-build.sh

# Instalar dependencias del sistema para WeasyPrint
apt-get update
apt-get install -y \
    libcairo2 \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libgdk-pixbuf2.0-0 \
    libffi-dev \
    shared-mime-info \
    libpq-dev \
    gcc

# Instalar dependencias de Python
pip install --upgrade pip
pip install -r requirements.txt

# Recolectar archivos estáticos
python manage.py collectstatic --noinput

# Ejecutar migraciones
python manage.py migrate