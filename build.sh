#!/bin/bash
# Instalar ODBC Driver 17
apt-get update && apt-get install -y \
    unixodbc \
    unixodbc-dev \
    odbcinst \
    odbcinst1debian2 \
    libodbc1 \
    curl \
    gnupg

# Agregar claves y repositorio de Microsoft ODBC
curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add -
add-apt-repository "$(curl -s https://packages.microsoft.com/config/ubuntu/20.04/prod.list)"

# Instalar Microsoft ODBC Driver 17
apt-get update && apt-get install -y msodbcsql17

# Ejecutar la aplicación
python app.py
