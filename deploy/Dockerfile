# Dockerfile for accountability web application
FROM python:3.13-slim

# Set working directory
WORKDIR /app

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY web/ ./web/
COPY run_server.py .

# Expose port
EXPOSE 8000

# Run the application
CMD ["uvicorn", "web.main:app", "--host", "0.0.0.0", "--port", "8000"]
