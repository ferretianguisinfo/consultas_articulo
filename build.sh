#!/usr/bin/env bash
# Actualiza los paquetes
apt-get update

# Instala los paquetes necesarios para ODBC Driver 17
apt-get install -y curl apt-transport-https gnupg

# Agrega el repositorio de Microsoft
curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add -
curl https://packages.microsoft.com/config/ubuntu/$(lsb_release -rs)/prod.list > /etc/apt/sources.list.d/mssql-release.list

# Instala el driver
apt-get update
ACCEPT_EULA=Y apt-get install -y msodbcsql17 unixodbc-dev

# Limpia el caché
apt-get clean

