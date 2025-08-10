FROM python:3.11-slim
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1

# Install minimal build deps for some wheels if needed
RUN apt-get update && apt-get install -y --no-install-recommends build-essential && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY . /app

EXPOSE 5001
# Entrypoint: app module is at /app/app.py (context is ./backend)
# Allow tuning workers/threads via env (fallback to sensible defaults)
ENV GUNICORN_WORKERS=${GUNICORN_WORKERS:-5}
ENV GUNICORN_THREADS=${GUNICORN_THREADS:-2}
CMD bash -lc "gunicorn -w ${GUNICORN_WORKERS} --threads ${GUNICORN_THREADS} -k gthread -b 0.0.0.0:5001 --timeout 120 app:app"