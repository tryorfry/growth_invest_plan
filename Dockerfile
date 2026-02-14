# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Copy .env.example as template (user should provide their own .env)
COPY .env.example .env.example

# Create directory for charts and exports
RUN mkdir -p charts exports

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Run app.py when the container launches
ENTRYPOINT ["python", "app.py"]
