# ========================================================
# Dockerfile for College Hostel Room Allocation System
# Multi-stage / hardened production Python 3.11 container
# ========================================================

FROM python:3.11-slim as base

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8000

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source
COPY . /app/

# Create a non-privileged system user for runtime security
RUN groupadd -r appuser && useradd -r -g appuser appuser \
    && mkdir -p /app/staticfiles /app/media /app/media/maintenance_photos \
    && chown -R appuser:appuser /app

USER appuser

# Collect static files with dummy secret key
RUN python manage.py collectstatic --noinput --settings=hostel_project.settings

EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD curl -f http://localhost:8000/health/ || exit 1

# Launch Gunicorn WSGI server
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "3", "--threads", "2", "--timeout", "60", "hostel_project.wsgi:application"]
