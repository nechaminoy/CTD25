import os, asyncio, logging, argparse
from pathlib import Path
from .server.game_factory import create_game
from .graphics.graphics_factory import ImgFactory, MockImgFactory
from .client.display import NullDisplay, Cv2Display
from .client.render_loop import ClientRenderLoop
from .client.renderer import ClientRenderer
from .client.ui_state_sync import BoardMirror, subscribe_state_sync, subscribe_render
from .config.settings import PIECES_DIR, WS_HOST, WS_PORT, WS_URI
from .config.input_maps import P1_MAP, P2_MAP

async def run_local():
    game = create_game(PIECES_DIR, ImgFactory())
    game.run()

async def run_server(host=None, port=None):
    from .server.ws_server import serve_and_tick
    game = create_game(PIECES_DIR, ImgFactory())
    
    # Use provided arguments or fall back to config/environment
    server_host = host or WS_HOST
    server_port = port or WS_PORT
    
    print(f"Starting KFC Game Server on {server_host}:{server_port}")
    print(f"Clients can connect to: ws://{server_host}:{server_port}")
    
    await serve_and_tick(game, host=server_host, port=server_port)

async def run_client(host=None, port=None):
    from .client.ws_client import WSClient
    from .client.event_bridge import EventBridge
    from .input.keyboard_input import KeyboardProducer, KeyboardProcessor

    img_factory = ImgFactory()
    game = create_game(PIECES_DIR, img_factory)
    
    logging.debug("Game created successfully with all pieces")
    
    # Use provided arguments or fall back to config/environment
    server_host = host or WS_HOST
    server_port = port or WS_PORT
    ws_uri = f"ws://{server_host}:{server_port}"
    
    player = os.getenv("PLAYER", "W")
    print(f"Connecting to server at {ws_uri} as player {player}")
    
    ws = await WSClient(ws_uri).connect(player=player)

    class _ToWSQueue:
        def __init__(self, ws_client, loop):
            self.ws = ws_client
            self.loop = loop

        def put(self, cmd):
            # Schedule the coroutine to run in the main event loop from another thread
            future = asyncio.run_coroutine_threadsafe(self.ws.send_command(cmd), self.loop)

    player_num = 1 if player == "W" else 2
    keymap = P1_MAP if player_num == 1 else P2_MAP
    kp = KeyboardProcessor(8, 8, keymap)
    
    EventBridge(ws, game.bus).start()
    
    mirror = BoardMirror()
    subscribe_state_sync(game.bus, mirror)
    
    kb = KeyboardProducer(game, _ToWSQueue(ws, asyncio.get_event_loop()), kp, player=player_num, board_mirror=mirror)
    kb.start()
    
    renderer = ClientRenderer(game.board, PIECES_DIR, ImgFactory())
    subscribe_render(game.bus, renderer)

    headless = os.getenv("KFC_HEADLESS", "0") == "1"
    display = NullDisplay() if headless else Cv2Display("Kung Fu Chess")

    render_loop = ClientRenderLoop(renderer, hz=60.0, display=display)
    render_loop.start()

    try:
        while True:
            await asyncio.sleep(0.1)
    except KeyboardInterrupt:
        pass
    finally:
        await render_loop.stop()
        display.close()

async def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='KFC Game - Kung Fu Chess')
    parser.add_argument('--mode', choices=['local', 'server', 'client'], 
                       default=os.getenv("KFC_MODE", "local").lower(),
                       help='Game mode (default: local, or from KFC_MODE env var)')
    parser.add_argument('--host', type=str, 
                       default=None,
                       help=f'Server host address (default: {WS_HOST}, or from KFC_HOST env var)')
    parser.add_argument('--port', type=int, 
                       default=None,
                       help=f'Server port (default: {WS_PORT}, or from KFC_PORT env var)')
    parser.add_argument('--player', choices=['W', 'B'], 
                       default=os.getenv("PLAYER", "W"),
                       help='Player color for client mode (default: W, or from PLAYER env var)')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Enable verbose logging')
    
    args = parser.parse_args()
    
    # Configure logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(level=log_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    
    # Set player environment for client mode
    if args.mode == 'client':
        os.environ['PLAYER'] = args.player
    
    # Run the appropriate mode
    if args.mode == "local":  
        await run_local()
    elif args.mode == "server": 
        await run_server(host=args.host, port=args.port)
    elif args.mode == "client": 
        await run_client(host=args.host, port=args.port)
    else: 
        raise SystemExit(f"Unknown mode: {args.mode}")

if __name__ == "__main__":
    asyncio.run(main())
