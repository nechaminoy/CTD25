# Use Python 3.11 as base image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies for OpenCV (needed for image processing)
RUN apt-get update && apt-get install -y \
    libglib2.0-0 \
    libgl1-mesa-glx \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install dependencies with trusted hosts for NetFree
COPY requirements.txt .
RUN pip config set global.trusted-host "pypi.org files.pythonhosted.org pypi.python.org"
RUN pip install --trusted-host pypi.org --trusted-host pypi.python.org --trusted-host files.pythonhosted.org --no-cache-dir -r requirements.txt

# Copy the entire application
COPY . .

# Install project dependencies manually first
RUN pip install --trusted-host pypi.org --trusted-host pypi.python.org --trusted-host files.pythonhosted.org keyboard pytest pytest-cov

# Install the application
RUN pip install --trusted-host pypi.org --trusted-host pypi.python.org --trusted-host files.pythonhosted.org -e . --no-deps

# Set Python path
ENV PYTHONPATH=/app

# Set environment variables for headless mode
ENV KFC_HEADLESS=1

# Default server configuration (can be overridden)
ENV KFC_HOST=0.0.0.0
ENV KFC_PORT=8765

# Expose the WebSocket port
EXPOSE 8765

# Default command to run the server
CMD ["python", "docker/docker_server.py"]
