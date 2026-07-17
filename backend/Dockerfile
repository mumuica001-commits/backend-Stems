# Imagem base do Python
FROM python:3.10-slim

# Instalar dependências de sistema se sua aplicação precisar processar áudio (Spleeter, Demucs, FFmpeg, etc.)
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libsndfile1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copiar e instalar dependências do Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar todo o resto do projeto para dentro do container
COPY . .

# Expõe a porta dinâmica usada pelo Railway
EXPOSE 8000

# O Railway injeta a porta em $PORT, garantindo que o Uvicorn a escute
CMD ["sh", "-x", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]