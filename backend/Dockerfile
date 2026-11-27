# Lightweight server image (e.g. for a NAS). Classification runs in the
# desktop app; see requirements-server.txt.
FROM python:3.11-slim

WORKDIR /app

COPY requirements-server.txt .
RUN pip install --no-cache-dir -r requirements-server.txt

COPY . .

ENV ATELIER_MODE=remote \
    ATELIER_DATA_DIR=/app/data \
    PYTHONUNBUFFERED=1

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health')"

CMD ["python", "run.py", "--host", "0.0.0.0", "--port", "8000"]
