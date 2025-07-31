# Quick Start Guide

## Build and Run Server

### Windows:
```cmd
# Default port (8765)
docker\run_docker_server.bat

# Custom port
docker\run_docker_server.bat -p 9000
```

### Linux/Mac:
```bash
chmod +x docker/run_docker_server.sh

# Default port (8765)
./docker/run_docker_server.sh

# Custom port
./docker/run_docker_server.sh -p 9000
```

## Using Docker Compose

```bash
cd docker

# Start server on default port (8765)
docker-compose up kfc-server

# Start server on custom port
KFC_PORT=9000 HOST_PORT=9000 docker-compose up kfc-server

# Start server with test clients
docker-compose --profile client up

# Stop all
docker-compose down
```

## Manual Commands

```bash
# Build (from project root)
docker build -f docker/Dockerfile -t kfc-game-server .

# Run on default port
docker run -p 8765:8765 --name kfc-server --rm kfc-game-server

# Run on custom port
docker run -p 9000:8765 --name kfc-server --rm kfc-game-server
```

## Direct Python Commands

```bash
# Server mode
python -m KFC_Game.main --mode server --host 0.0.0.0 --port 9000

# Client mode
python -m KFC_Game.main --mode client --host localhost --port 9000 --player W
```

**Default server address:** ws://localhost:8765
**Custom server address:** ws://localhost:[YOUR_PORT]
