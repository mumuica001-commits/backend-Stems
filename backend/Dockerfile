FROM python:3.11-slim AS base

RUN apt-get update && apt-get install -y --no-install-recommends \
    libsndfile1 \
    ffmpeg \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /srv

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app
COPY workers ./workers

ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/srv

EXPOSE 8000

# imagem única — o comando decide se sobe API ou worker (ver docker-compose.yml)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
