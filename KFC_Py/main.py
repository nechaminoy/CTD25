import os, asyncio, logging
from pathlib import Path
from GameFactory import create_game
from GraphicsFactory import ImgFactory, MockImgFactory
from client.display import NullDisplay, Cv2Display
from client.render_loop import ClientRenderLoop
from client.renderer import ClientRenderer
from client.ui_state_sync import BoardMirror, subscribe_state_sync, subscribe_render
from config.settings import PIECES_DIR, WS_HOST, WS_PORT, WS_URI
from config.input_maps import P1_MAP, P2_MAP

async def run_local():
    game = create_game(PIECES_DIR, ImgFactory())
    game.run()

async def run_server():
    from server.ws_server import serve_and_tick
    game = create_game(PIECES_DIR, ImgFactory())
    await serve_and_tick(game, host=WS_HOST, port=WS_PORT)

async def run_client():
    from client.ws_client import WSClient
    from client.event_bridge import EventBridge
    from KeyboardInput import KeyboardProducer, KeyboardProcessor

    img_factory = ImgFactory()
    game = create_game(PIECES_DIR, img_factory)
    
    # Load the background image first
    bg_path = str(Path(__file__).resolve().parent.parent / "table_bg_13in.png")
    if not Path(bg_path).exists():
        raise FileNotFoundError(f"Cannot load background image: {bg_path}")
    board_img = img_factory(bg_path, (1920, 1080))
    game.board.img = board_img
    
    player = os.getenv("PLAYER", "W")
    ws = await WSClient(WS_URI).connect(player=player)

    class _ToWSQueue:
        def __init__(self, ws_client):
            self.ws = ws_client

        def put(self, cmd):
            asyncio.create_task(self.ws.send_command(cmd))

    player_num = 1 if player == "W" else 2
    keymap = P1_MAP if player_num == 1 else P2_MAP
    kp = KeyboardProcessor(8, 8, keymap)
    kb = KeyboardProducer(game, _ToWSQueue(ws), kp, player=player_num)
    kb.start()

    EventBridge(ws, game.bus).start()
    
    mirror = BoardMirror()
    subscribe_state_sync(game.bus, mirror)
    
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
    logging.basicConfig(level=logging.DEBUG,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    mode = os.getenv("KFC_MODE", "local").lower()
    if mode == "local":  await run_local()
    elif mode == "server": await run_server()
    elif mode == "client": await run_client()
    else: raise SystemExit(f"Unknown KFC_MODE={mode}")

if __name__ == "__main__":
    asyncio.run(main())
