# Use Python 3.11 slim image as base
FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PIP_NO_CACHE_DIR=1
ENV PIP_DISABLE_PIP_VERSION_CHECK=1

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libxml2-dev \
    libxslt-dev \
    libffi-dev \
    libssl-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Install Python dependencies using uv (faster than pip)
RUN pip install uv && \
    uv pip install --system -e .

# Copy project files
COPY . .

# Create necessary directories
RUN mkdir -p /app/logs /app/data

# Set permissions
RUN chmod +x /app/run_spiders.py

# Default command
CMD ["python", "run_spiders.py"]
