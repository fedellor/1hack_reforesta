# Backend del Radar de Reforesta (FastAPI). El frontend se despliega aparte.
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    TZ=Europe/Madrid

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app
COPY fuentes ./fuentes

# La base de datos (SQLite) vive en /app/data: debe montarse como volumen para que sobreviva a los reinicios
RUN mkdir -p /app/data
VOLUME ["/app/data"]

EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=30s --retries=3 \
  CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://localhost:8000/api/v1/health', timeout=4).status == 200 else 1)"

# Una sola réplica: SQLite y la sincronización de las 07:00 no admiten varias a la vez
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
