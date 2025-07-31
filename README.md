# KFC Game - Kung Fu Chess

Real-time chess game with WebSocket server-client architecture.

## Quick Start

### Running with Docker (Recommended)

The easiest way to run the server is using Docker:

```bash
# Default port (8765)
cd docker
./run_docker_server.sh   # Linux/Mac
# or
run_docker_server.bat    # Windows

# Custom port
./run_docker_server.sh -p 9000   # Linux/Mac
# or  
run_docker_server.bat -p 9000    # Windows
```

### Running Locally

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Run the server:
   ```bash
   # Default settings
   python -m KFC_Game.main --mode server
   
   # Custom host and port
   python -m KFC_Game.main --mode server --host 0.0.0.0 --port 9000
   ```

3. Run a client:
   ```bash
   # Connect to default server
   python -m KFC_Game.main --mode client --player W
   
   # Connect to custom server
   python -m KFC_Game.main --mode client --host localhost --port 9000 --player W
   ```

### Configuration Options

- **Host/Port:** Use `--host` and `--port` arguments or `KFC_HOST`/`KFC_PORT` environment variables
- **Player:** Use `--player W` or `--player B` for client mode
- **Verbose logging:** Add `--verbose` flag

For detailed Docker instructions, see [docker/README.md](docker/README.md)

## Project Structure

- `KFC_Game/` - Main game engine and server/client code
- `docker/` - Docker configuration and deployment files
- `pieces/` - Chess piece images and board assets
- `tests/` - Test suites

## Development

Run tests:
```bash
python -m pytest tests/ -v
```