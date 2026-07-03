FROM python:3.12-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    HF_HUB_OFFLINE=0

RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev gcc \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

# torch/torchvision CPU-only primero (evita el build CUDA de varios GB); sentence-transformers
# y facenet-pytorch los toman como ya satisfechos.
RUN pip install --no-cache-dir torch==2.5.1 torchvision==0.20.1 --index-url https://download.pytorch.org/whl/cpu
RUN pip install --no-cache-dir -r requirements.txt
# facenet-pytorch (detección + embedding de caras) con --no-deps para no reinstalar torch (CUDA).
RUN pip install --no-cache-dir --no-deps facenet-pytorch==2.6.0

# Se hornean los modelos CLIP en la imagen para que el sistema sea 100% local/offline:
#   clip-ViT-B-32                 -> encoder de imágenes (512d)
#   clip-ViT-B-32-multilingual-v1 -> encoder de texto multilingüe alineado (español incluido)
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('clip-ViT-B-32'); SentenceTransformer('clip-ViT-B-32-multilingual-v1')"

# Modelo de NER en español para el analizador de entidades (personas, lugares, organizaciones).
RUN python -m spacy download es_core_news_md

# Nota: los pesos de reconocimiento facial (VGGFace2) NO se hornean aquí — se descargan en el
# primer uso y se persisten en el volumen montado en /root/.cache/torch (ver docker-compose).
# Hornearlos en build disparaba el uso de memoria y tumbaba el daemon de Docker Desktop.

COPY . .

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
