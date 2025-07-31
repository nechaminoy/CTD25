# KFC Game - Docker Deployment

This guide explains how to run the KFC Game server using Docker.

## Prerequisites

- Docker installed on your system
- Docker Compose (optional, for multi-container setup)

## Quick Start

### Option 1: Using the Run Script (Recommended)

**From the project root directory:**

**Windows:**
```cmd
# Run with default port (8765)
docker\run_docker_server.bat

# Run on custom port
docker\run_docker_server.bat -p 9000

# Show help
docker\run_docker_server.bat --help
```

**Linux/Mac:**
```bash
chmod +x docker/run_docker_server.sh

# Run with default port (8765)
docker/run_docker_server.sh

# Run on custom port
docker/run_docker_server.sh -p 9000

# Show help
docker/run_docker_server.sh --help
```

### Option 2: Manual Docker Commands

1. **Build the Docker image (from project root):**
   ```bash
   docker build -f docker/Dockerfile -t kfc-game-server .
   ```

2. **Run the server:**
   ```bash
   # Default port (8765)
   docker run -p 8765:8765 --name kfc-server --rm kfc-game-server
   
   # Custom host port (e.g., 9000)
   docker run -p 9000:8765 --name kfc-server --rm kfc-game-server
   
   # Custom container port
   docker run -p 8765:9000 -e KFC_PORT=9000 --name kfc-server --rm kfc-game-server
   ```

3. **Stop the server:**
   ```bash
   # Press Ctrl+C in the terminal, or in another terminal:
   docker stop kfc-server
   ```

### Option 3: Using Docker Compose

1. **Navigate to docker directory:**
   ```bash
   cd docker
   ```

2. **Start server with default settings:**
   ```bash
   docker-compose up kfc-server
   ```

3. **Start server on custom port:**
   ```bash
   # Using environment variables
   KFC_PORT=9000 HOST_PORT=9000 docker-compose up kfc-server
   
   # Or create a .env file with:
   # KFC_PORT=9000
   # HOST_PORT=9000
   ```

4. **Start server with test clients:**
   ```bash
   docker-compose --profile client up
   ```

5. **Stop all services:**
   ```bash
   docker-compose down
   ```

## File Organization

All Docker-related files are organized in the `docker/` directory:

```
docker/
├── Dockerfile              # Docker image definition
├── docker-compose.yml      # Multi-container setup
├── docker_server.py        # Server entry point script
├── .dockerignore           # Files to exclude from Docker build
├── run_docker_server.sh    # Linux/Mac build and run script
├── run_docker_server.bat   # Windows build and run script
└── README.md              # This documentation
```

## Configuration

### Environment Variables

- `KFC_HEADLESS=1` - Runs the server without graphics (default in Docker)
- `PYTHONPATH=/app` - Ensures proper module loading

### Port Configuration

The server runs on port **8765** by default. This is exposed in the Docker container.

To use a different port:
```bash
docker run -p 9000:8765 --name kfc-server --rm kfc-game-server
```
(This maps host port 9000 to container port 8765)

## Connecting Clients

Once the server is running, clients can connect to:
- `ws://localhost:8765` (if running locally)
- `ws://YOUR_SERVER_IP:8765` (if running on a remote server)

## Troubleshooting

### Common Issues

1. **Port already in use:**
   ```bash
   docker ps  # Check if container is already running
   docker stop kfc-server  # Stop existing container
   ```

2. **Build fails:**
   - Ensure Docker is running
   - Check that all files are present in the project directory
   - Try rebuilding without cache: `docker build --no-cache -f docker/Dockerfile -t kfc-game-server .`

3. **Module import errors:**
   - The `PYTHONPATH` is set automatically in the container
   - If issues persist, check that the `KFC_Game` directory structure is correct

### Viewing Logs

```bash
docker logs kfc-server
```

### Debug Mode

To run the container interactively for debugging:
```bash
docker run -it -p 8765:8765 kfc-game-server /bin/bash
```

Then manually start the server:
```bash
python docker/docker_server.py
```

## Development

### Hot Reload (Development Mode)

For development, you can mount the source code as a volume:
```bash
docker run -p 8765:8765 -v $(pwd):/app --name kfc-server --rm kfc-game-server
```

### Running Tests in Docker

```bash
docker run --rm kfc-game-server python -m pytest tests/ -v
```

## Production Deployment

For production deployment, consider:

1. **Using a process manager** like supervisor or systemd
2. **Setting up reverse proxy** with nginx
3. **Adding SSL/TLS** for secure WebSocket connections (wss://)
4. **Health checks** and monitoring
5. **Resource limits** in Docker

Example with resource limits:
```bash
docker run -p 8765:8765 --memory=512m --cpus=1.0 --name kfc-server --rm kfc-game-server
```

## Build Context

The Docker build context is the project root directory, which allows the container to access all necessary files while keeping Docker-specific files organized in the `docker/` subdirectory.
