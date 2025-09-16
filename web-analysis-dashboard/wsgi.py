from monitoring import init_monitoring

# Initialize optional monitoring before the app import
init_monitoring()

from app_production import app  # noqa: E402

# Gunicorn entrypoint: `gunicorn wsgi:app`
