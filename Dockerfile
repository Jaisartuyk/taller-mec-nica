# Dockerfile para Django + SQLite
FROM python:3.11-slim

WORKDIR /app

# Instala dependencias del sistema
RUN apt-get update && apt-get install -y gcc libpq-dev && rm -rf /var/lib/apt/lists/*

# Copia requirements y los instala
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia el resto del código
COPY . .

# Expone el puerto por defecto de Django
EXPOSE 8000

# Comando por defecto: runserver (solo para pruebas/desarrollo)
CMD ["gunicorn", "--bind", "0.0.0.0:${PORT}", "taller_mecanica.wsgi:application"]
