import threading, logging
import keyboard  # pip install keyboard
from ..shared.command import Command
import asyncio


logger = logging.getLogger(__name__)


class KeyboardProcessor:
    """
    Maintains a cursor on an R×C grid and maps raw key names
    into logical actions via a user‑supplied keymap.
    """

    def __init__(self, rows: int, cols: int, keymap: dict[str, str], initial_pos: tuple[int, int] = (0, 0)):
        self.rows = rows
        self.cols = cols
        self.keymap = keymap
        self._cursor = list(initial_pos)  # Start at specified position
        self._lock = threading.Lock()

    def process_key(self, event):
        # Only care about key‑down events
        if event.event_type != "down":
            return None

        key = event.name
        
        # Translate Hebrew keys to English
        hebrew_to_english = {
            'ש': 'a',  # ש = a
            'ד': 's',  # ד = s  
            'ג': 'd',  # ו = d
            '\'': 'w',  # ' = w
            'כ': 'f',  # כ = f
            'ע': 'g',  # ג = g
        }
        
        # Convert Hebrew key to English
        if key in hebrew_to_english:
            key = hebrew_to_english[key]
        
        action = self.keymap.get(key)
        
        if key in ['up', 'down', 'left', 'right'] or action in ['up', 'down', 'left', 'right']:
            logger.info(f"[KEY] Key pressed: '{key}' -> Action: '{action}'")
        
        logger.debug("Key '%s' → action '%s'", key, action)

        if action in ("up", "down", "left", "right"):
            with self._lock:
                r, c = self._cursor
                old_pos = (r, c)
                if action == "up":
                    r = max(0, r - 1)
                elif action == "down":
                    r = min(self.rows - 1, r + 1)
                elif action == "left":
                    c = max(0, c - 1)
                elif action == "right":
                    c = min(self.cols - 1, c + 1)
                self._cursor = [r, c]
                
                if old_pos != (r, c):
                    logger.info(f"[CURSOR] Player moved from {old_pos} to ({r},{c}) - action: {action}")
                else:
                    logger.info(f"[CURSOR] No movement - at edge, action: {action}, position: ({r},{c})")
                
                logger.debug("Cursor moved to (%s,%s)", r, c)

        return action

    def get_cursor(self) -> tuple[int, int]:
        with self._lock:
            return tuple(self._cursor)


class KeyboardProducer(threading.Thread):

    def __init__(self, game, queue, processor: KeyboardProcessor, player: int, send_command=None, board_mirror=None):
        super().__init__(daemon=True)
        self.game = game
        self.queue = queue
        self.proc = processor
        self.player = player
        self.selected_id = None
        self.selected_cell = None
        # Define which color each player controls
        self.my_color = "W" if player == 1 else "B"
        self._send_cmd = send_command
        self.board_mirror = board_mirror  # For client mode - holds server state
        # Check if queue is a ToWSQueue (client mode)
        self._is_client_mode = hasattr(queue, 'send_command')

    def set_sender(self, fn):
        self._send_cmd = fn

    def _emit(self, cmd: Command):
        if self._is_client_mode:
            # In client mode, send via WebSocket
            if hasattr(self.queue, 'send_command'):
                # Schedule it properly on the event loop
                import asyncio
                try:
                    loop = asyncio.get_event_loop()
                    if loop.is_running():
                        asyncio.create_task(self.queue.send_command(cmd))
                    else:
                        self.queue.put(cmd)
                except RuntimeError:
                    self.queue.put(cmd)
            else:
                self.queue.put(cmd)
        elif self._send_cmd is None:
            return
        elif asyncio.iscoroutinefunction(self._send_cmd):
            asyncio.get_running_loop().create_task(self._send_cmd(cmd))
        else:
            self._send_cmd(cmd)

    def run(self):
        # Install our hook; it stays active until we call keyboard.unhook_all()
        keyboard.hook(self._on_event)
        keyboard.wait()

    def _find_piece_at(self, cell):
        # If we have a board mirror (client mode), use it for accurate state
        if self.board_mirror:
            for piece_data in self.board_mirror.pieces:
                piece_cell = tuple(piece_data.get('cell', []))
                if piece_cell == cell:
                    # Create a simple object with the properties we need
                    class PieceProxy:
                        def __init__(self, piece_data):
                            self.id = piece_data.get('id', '')
                            self._cell = piece_data.get('cell', [])
                        def current_cell(self):
                            return tuple(self._cell)
                    return PieceProxy(piece_data)
            return None
        
        # Fallback to local game pieces (local mode)
        for p in self.game.pieces:
            if p.current_cell() == cell:
                return p
        return None

    def _on_event(self, event):
        action = self.proc.process_key(event)
        
        # Send cursor update if it's a movement action and we're in client mode
        if action in ("up", "down", "left", "right") and self._is_client_mode:
            cursor_pos = self.proc.get_cursor()
            # Create a special cursor update command
            cursor_cmd = Command(
                timestamp=self.game.game_time_ms() if hasattr(self.game, 'game_time_ms') else 0,
                piece_id="",  # Empty piece_id for cursor commands
                type="cursor_update",
                params=[self.player, cursor_pos]
            )
            self._emit(cursor_cmd)
            logger.debug(f"Player{self.player} cursor moved to {cursor_pos}")
        
        # only interpret select/jump
        if action not in ("select", "jump"):
            return

        cell = self.proc.get_cursor()
        
        if action == "select":
            if self.selected_id is None:
                # first press = pick up the piece under the cursor
                piece = self._find_piece_at(cell)
                if not piece:
                    print(f"[WARN] No piece at {cell}")
                    return

                # Check if the piece belongs to this player's color
                piece_color = piece.id[1]  # W or B
                if piece_color != self.my_color:
                    print(f"[WARN] Player{self.player} ({self.my_color}) cannot select {piece.id} (color {piece_color})")
                    return

                self.selected_id = piece.id
                self.selected_cell = cell
                
                # Update selected_id_X in Game
                if self.player == 1:
                    self.game.selected_id_1 = self.selected_id
                else:
                    self.game.selected_id_2 = self.selected_id
                    
                print(f"[KEY] Player{self.player} selected {piece.id} at {cell}")
                return

            elif cell == self.selected_cell:  # selected same place
                self.selected_id = None
                # Update in Game
                if self.player == 1:
                    self.game.selected_id_1 = None
                else:
                    self.game.selected_id_2 = None
                return

            else:
                cmd = Command(
                    self.game.game_time_ms(),
                    self.selected_id,
                    "move",
                    [self.selected_cell, cell]
                )
                self.queue.put(cmd)
                logger.info(f"Player{self.player} queued {cmd}")
                self.selected_id = None
                self.selected_cell = None
                
                # Update in Game
                if self.player == 1:
                    self.game.selected_id_1 = None
                else:
                    self.game.selected_id_2 = None

        elif action == "jump":
            if self.selected_id is None:
                print(f"[WARN] Player{self.player} tried to jump but no piece selected")
                return
            
            cmd = Command(
                self.game.game_time_ms(),
                self.selected_id,
                "jump",
                [self.selected_cell]  # Pass current cell to the command
            )
            self.queue.put(cmd)
            logger.info(f"Player{self.player} queued {cmd}")
            # We don't deselect the piece after a jump


    def stop(self):
        keyboard.unhook_all()


class ToWSQueue:
    def __init__(self, ws_client):
        self.ws = ws_client
    
    def put(self, cmd):
        import asyncio
        asyncio.create_task(self.ws.send_command(cmd))
    
    async def send_command(self, cmd):
        """Send command directly via WebSocket"""
        await self.ws.send_command(cmd)
