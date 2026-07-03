FROM python:3.12-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    HF_HUB_OFFLINE=0

RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev gcc \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

# torch CPU-only primero (evita bajar el build CUDA de varios GB); sentence-transformers
# lo tomará como ya satisfecho al instalar el resto de requirements.
RUN pip install --no-cache-dir torch==2.5.1 --index-url https://download.pytorch.org/whl/cpu
RUN pip install --no-cache-dir -r requirements.txt

# Se hornean los modelos CLIP en la imagen para que el sistema sea 100% local/offline:
#   clip-ViT-B-32                 -> encoder de imágenes (512d)
#   clip-ViT-B-32-multilingual-v1 -> encoder de texto multilingüe alineado (español incluido)
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('clip-ViT-B-32'); SentenceTransformer('clip-ViT-B-32-multilingual-v1')"

COPY . .

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
