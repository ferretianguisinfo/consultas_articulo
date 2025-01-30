FROM ubuntu:20.04

# Instalar dependencias necesarias
RUN apt-get update && apt-get install -y \
    curl \
    gnupg \
    unixodbc \
    unixodbc-dev \
    odbcinst \
    odbcinst1debian2 \
    libodbc1

# Agregar claves y repositorio de Microsoft para ODBC
RUN curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add - \
    && add-apt-repository "$(curl -s https://packages.microsoft.com/config/ubuntu/20.04/prod.list)"

# Instalar ODBC Driver 17
RUN apt-get update && apt-get install -y msodbcsql17

# Instalar Python y dependencias
RUN apt-get install -y python3 python3-pip

# Copiar archivos del proyecto
WORKDIR /app
COPY . /app

# Instalar librerías de Python
RUN pip3 install -r requirements.txt

# Exponer el puerto
EXPOSE 5000

# Comando para ejecutar la aplicación
CMD ["python3", "app.py"]

