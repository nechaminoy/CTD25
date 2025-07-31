"""
Input handler setup for client mode.
"""
from ..input.keyboard_input import KeyboardProcessor, KeyboardProducer
from ..config.input_maps import P1_MAP, P2_MAP


class ToWSQueue:
    """Adapter to send commands via WebSocket client."""
    def __init__(self, ws_client, loop):
        self.ws = ws_client
        self.loop = loop

    def put(self, cmd):
        import asyncio
        # Schedule the coroutine to run in the main event loop from another thread
        future = asyncio.run_coroutine_threadsafe(self.ws.send_command(cmd), self.loop)

    async def send_command(self, cmd):
        """Direct async method for sending commands."""
        await self.ws.send_command(cmd)


def setup_input_handling(game, ws_client, player, board_mirror=None):
    """
    Setup input handling for client mode.
    
    Args:
        game: Game instance
        ws_client: WebSocket client
        player: Player color ("W" or "B")
        board_mirror: BoardMirror instance for accurate state
    
    Returns:
        KeyboardProducer instance
    """
    import asyncio
    
    player_num = 1 if player == "W" else 2
    keymap = P1_MAP if player_num == 1 else P2_MAP
    kp = KeyboardProcessor(8, 8, keymap)
    
    kb = KeyboardProducer(
        game, 
        ToWSQueue(ws_client, asyncio.get_event_loop()), 
        kp, 
        player=player_num, 
        board_mirror=board_mirror
    )
    
    return kb
