import os, asyncio, logging
from GameFactory import create_game
from GraphicsFactory import ImgFactory, MockImgFactory
from config.settings import PIECES_DIR, WS_HOST, WS_PORT, WS_URI
from config.input_maps import P1_MAP

async def run_local():
    game = create_game(PIECES_DIR, ImgFactory())
    game.run()

async def run_server():
    from server.ws_server import serve
    game = create_game(PIECES_DIR, MockImgFactory())
    await serve(game, host=WS_HOST, port=WS_PORT)

async def run_client():
    from client.ws_client import WSClient
    from client.event_bridge import EventBridge
    from KeyboardInput import KeyboardProducer, KeyboardProcessor

    game = create_game(PIECES_DIR, ImgFactory())
    ws = await WSClient(WS_URI).connect()
    EventBridge(ws, game.bus).start()

    kp = KeyboardProcessor(game.board.H_cells, game.board.W_cells, P1_MAP, initial_pos=(7, 0))
    kb = KeyboardProducer(game, game.user_input_queue, kp, player=1, send_command=ws.send_command)
    kb.start()

    try:
        while True:
            await asyncio.sleep(0.05)
    except KeyboardInterrupt:
        pass

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
