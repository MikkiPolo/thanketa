FROM python:3.11-slim
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
COPY . /app
RUN pip install --no-cache-dir -r /app/backend/requirements.txt
WORKDIR /app/backend
EXPOSE 5001
CMD ["gunicorn","-w","2","-b","0.0.0.0:5001","app:app"]
