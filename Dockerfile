# Dockerfile para Django en Railway
FROM python:3.11-slim

WORKDIR /app

# Instala dependencias del sistema
RUN apt-get update && apt-get install -y gcc libpq-dev && rm -rf /var/lib/apt/lists/*

# Copia requirements y los instala
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia el resto del código
COPY . .

# Permisos para el script de inicio
RUN chmod +x start.sh

# Expone el puerto por defecto de Django
EXPOSE 8000

# Comando de inicio: ejecuta migraciones y luego gunicorn
CMD ["./start.sh"]
