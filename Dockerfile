# Use an official Python runtime as the base image
FROM python:3.12-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set the working directory in the container
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY spentbackend/requirements.txt /app/
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copy the Django project
COPY spentbackend/ /app/

# Collect static files
RUN python manage.py collectstatic --noinput

# Run migrations
RUN python manage.py migrate

# Expose the port the app runs on
EXPOSE 8000

# Start the application
CMD gunicorn spentbackend.wsgi:application --bind 0.0.0.0:$PORT