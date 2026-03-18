# Use an official Python runtime as a parent image
FROM python:3.10-slim

# Set environment variables for optimized Python execution
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV STREAMLIT_SERVER_PORT=8501
ENV STREAMLIT_SERVER_ADDRESS=0.0.0.0

# Set working directory in the container
WORKDIR /app

# Install system dependencies required for native extensions (curl_cffi, psycopg2, sqlite)
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    libsqlite3-dev \
    libffi-dev \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements file first to leverage Docker build cache
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Download NLTK data required for textblob sentiment analysis
RUN python -m textblob.download_corpora

# Copy the entire source code
COPY . .

# Expose the standard Streamlit port
EXPOSE 8501

# Add resilient healthcheck to verify app is serving traffic
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl --fail http://localhost:8501/_stcore/health || exit 1

# Command to run the application
CMD ["streamlit", "run", "src/dashboard.py"]
