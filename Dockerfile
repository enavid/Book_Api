# syntax=docker/dockerfile:1

# Match the Python version used in CI.
FROM python:3.12-slim

# Predictable Python behaviour in a container: unbuffered logs, no .pyc files.
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

# Install dependencies first so this layer is cached until requirements change.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code.
COPY . .

# The API listens on 5000.
EXPOSE 5000

# JWT_SECRET_KEY (>= 32 chars) must be provided at runtime, e.g.
#   docker run -e JWT_SECRET_KEY=... -p 5000:5000 book-api
# On start: apply DB migrations, then serve with gunicorn (a production WSGI server).
CMD ["sh", "-c", "flask --app main db upgrade && gunicorn --bind 0.0.0.0:5000 main:app"]
