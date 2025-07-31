#!/bin/bash

# Build and run KFC Game Server with Docker

# Default values
HOST_PORT=${KFC_HOST_PORT:-8765}
CONTAINER_PORT=${KFC_PORT:-8765}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -p|--port)
            HOST_PORT="$2"
            shift 2
            ;;
        --container-port)
            CONTAINER_PORT="$2"
            shift 2
            ;;
        -h|--help)
            echo "Usage: $0 [OPTIONS]"
            echo "Options:"
            echo "  -p, --port PORT          Host port to bind to (default: 8765)"
            echo "  --container-port PORT    Container port (default: 8765)"
            echo "  -h, --help              Show this help message"
            echo ""
            echo "Environment variables:"
            echo "  KFC_HOST_PORT           Host port to bind to"
            echo "  KFC_PORT               Container port"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            echo "Use -h or --help for usage information"
            exit 1
            ;;
    esac
done

echo "Building KFC Game Server Docker image..."
docker build -f docker/Dockerfile -t kfc-game-server .

if [ $? -eq 0 ]; then
    echo "Build successful! Starting server..."
    echo "Server will be available on ws://localhost:${HOST_PORT}"
    echo "Press Ctrl+C to stop the server"
    docker run -p ${HOST_PORT}:${CONTAINER_PORT} \
               -e KFC_PORT=${CONTAINER_PORT} \
               --name kfc-server --rm kfc-game-server
else
    echo "Build failed!"
    exit 1
fi
