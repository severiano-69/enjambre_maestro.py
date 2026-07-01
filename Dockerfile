FROM python:3.11-slim

WORKDIR /app

# Deshabilitar almacenamiento en caché de pip para optimizar espacio
# Copia requirements.txt o requisitos.txt, el que exista en tu repositorio
COPY req* . 

RUN pip install --no-cache-dir --upgrade pip && \
    if [ -f requirements.txt ]; then pip install --no-cache-dir -r requirements.txt; \
    elif [ -f requisitos.txt ]; then pip install --no-cache-dir -r requisitos.txt; \
    else echo "ERROR: No se encontro ningun archivo de requisitos" && exit 1; fi

COPY . .

# Puerto expuesto sincronizado para producción en Render
EXPOSE 10000

# Ejecución nativa directa para evitar fallos de hilos y asegurar logs inmediatos
CMD ["python", "enjambre_maestro.py"]
