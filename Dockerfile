# T31 (docs/tasks.md, Fase 9): imagen para Koyeb (o cualquier plataforma que
# hable Docker) — reemplaza railway.json. Instalación editable (`pip install
# -e .`) para que `app/` y `knowledge/` queden exactamente como los espera
# app/knowledge/loader.py (DEFAULT_BENCHMARK_PATH sube 2 niveles desde
# app/knowledge/loader.py hasta la raíz del repo) sin duplicar el árbol de
# fuentes entre el código copiado y un paquete instalado aparte.
FROM python:3.11-slim

WORKDIR /app

COPY pyproject.toml README.md ./
COPY app/ ./app/
COPY knowledge/ ./knowledge/

RUN pip install --no-cache-dir -e .

EXPOSE 8000

# $PORT lo inyecta la plataforma (Koyeb, Railway, etc.); 8000 es el default
# para correr la imagen localmente sin configurarlo a mano.
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
