# Simple production image for the Flask app with Gunicorn
FROM mcr.microsoft.com/playwright/python:v1.40.0-jammy

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Base image already has necessary system deps for Playwright

# Copy dependencies first
COPY requirements_production.txt /app/requirements_production.txt
RUN pip install -r requirements_production.txt && pip install gunicorn

# Copy application code
COPY . /app

EXPOSE 5000

CMD ["gunicorn", "wsgi:app", "--bind", "0.0.0.0:5000", "--workers", "2"]
