import queue, time, logging
from typing import List, Dict, Tuple, Optional
from collections import defaultdict

import cv2

from ..shared.board import Board
from ..shared.command import Command
from ..graphics.overlay_manager import render_overlay
from ..shared.event import EventType
from ..shared.publisher import PublisherMixin
from ..graphics.canvas import board_img
from ..shared.piece import Piece
from ..shared.bus import EventBus, event_bus as default_event_bus

from ..input.keyboard_input import KeyboardProcessor, KeyboardProducer

# set up a module-level logger – real apps can configure handlers/levels
logger = logging.getLogger(__name__)


class InvalidBoard(Exception): ...


class Game(PublisherMixin):
    def __init__(self, pieces: List[Piece], board: Board, event_bus: EventBus | None = None, *, validate_setup: bool = True,):
        bus = event_bus or default_event_bus
        super().__init__(bus)
        self.pieces = pieces
        self.board = board
        self.bus = bus
        self.curr_board = None
        self.user_input_queue = queue.Queue()
        self.piece_by_id = {p.id: p for p in pieces}
        self.pos: Dict[Tuple[int, int], List[Piece]] = defaultdict(list)
        self.START_NS = time.monotonic_ns()
        self._time_factor = 1
        self._validate_initial_setup()
        self._deferred_after_cooldown = {}
        self.kp1: Optional[KeyboardProcessor] = None
        self.kp2: Optional[KeyboardProcessor] = None
        self.kb_prod_1: Optional[KeyboardProducer] = None
        self.kb_prod_2: Optional[KeyboardProducer] = None
        self.selected_id_1: Optional[str] = None
        self.selected_id_2: Optional[str] = None
        self.last_cursor1 = (0, 0)
        self.last_cursor2 = (0, 0)
        self._window_ready = False
        self._did_reset = False
        self.state_version = 0
        self._snapshot_dirty = True
        if validate_setup:
            self._validate_initial_setup()

    # ──────────────────────────────────────────────────────────────
    def game_time_ms(self) -> int:
        delta_ms = (time.monotonic_ns() - self.START_NS) // 1_000_000
        return int(delta_ms * self._time_factor)

    def clone_board(self) -> Board:
        return self.board.clone()

    # ──────────────────────────────────────────────────────────────
    def start_user_input_thread(self):
        # player 1 key‐map
        p1_map = {
            "up": "up", "down": "down", "left": "left", "right": "right",
            "enter": "select", "space": "select", "+": "jump"
        }
        # player 2 key‐map
        p2_map = {
            "w": "up", "s": "down", "a": "left", "d": "right",
            "f": "select", "space": "select", "g": "jump"
        }

        # Player 1 (white) starts at bottom (row 7), Player 2 (black) at top (row 0)
        self.kp1 = KeyboardProcessor(self.board.H_cells,
                                     self.board.W_cells,
                                     keymap=p1_map,
                                     initial_pos=(7, 0))
        self.kp2 = KeyboardProcessor(self.board.H_cells,
                                     self.board.W_cells,
                                     keymap=p2_map,
                                     initial_pos=(0, 0))

        self.kb_prod_1 = KeyboardProducer(self, self.user_input_queue, self.kp1, player=1)
        self.kb_prod_2 = KeyboardProducer(self, self.user_input_queue, self.kp2, player=2)

        self.kb_prod_1.start()
        self.kb_prod_2.start()

    def snapshot(self) -> dict:
        cursors = []
        
        # Add player cursors to snapshot
        if hasattr(self, 'kp1') and self.kp1:
            cursor_pos = self.kp1.get_cursor()
            cursors.append({"player": 1, "cell": cursor_pos})
            
        if hasattr(self, 'kp2') and self.kp2:
            cursor_pos = self.kp2.get_cursor()
            cursors.append({"player": 2, "cell": cursor_pos})
        
        return {
            "version": self.state_version,
            "pieces": [
                {
                    "id": p.id,
                    "cell": p.current_cell(),
                    "color": p.id[1],
                    "state": p.state.name,
                }
                for p in self.pieces
            ],
            "cursors": cursors,
        }

    def _bump_version(self) -> None:
        self.state_version += 1
        self._snapshot_dirty = True

    def _publish_snapshot(self) -> None:
        payload = self.snapshot()
        self.publish_event(
            et=EventType.STATE_SNAPSHOT,
            timestamp=self.game_time_ms(),
            **payload
        )
        self._snapshot_dirty = False

    # ──────────────────────────────────────────────────────────────
    def _update_cell2piece_map(self):
        self.pos.clear()
        for p in self.pieces:
            self.pos[p.current_cell()].append(p)

    def _run_game_loop(self, num_iterations=None, is_with_graphics=True):
        if not self._did_reset:
            start_ms = self.game_time_ms()
            for p in self.pieces:
                p.reset(start_ms)
            self._did_reset = True
            self._snapshot_dirty = True
        it_counter = 0
        prev_now = -1
        while not self._is_win():
            now = self.game_time_ms()
            if num_iterations is not None and now == prev_now:
                self.START_NS -= 1_000_000  # להזיז את ההתחלה אחורה ב־1ms
                now = self.game_time_ms()
            prev_now = now

            self._update_cell2piece_map()
            # 1) drain and apply ALL pending commands first
            while not self.user_input_queue.empty():
                cmd: Command = self.user_input_queue.get()
                self._process_input(cmd)

            # 2) advance piece animations / physics for current tick
            for p in self.pieces:
                p.update(now)

            for pid, pending_cmd in list(self._deferred_after_cooldown.items()):
                p = self.piece_by_id.get(pid)
                if not p:
                    del self._deferred_after_cooldown[pid]
                    continue

                if p.state.name.startswith("idle"):
                    before = p.current_cell()
                    p.on_command(pending_cmd, self.pos)
                    setattr(p, "_last_cmd_ts", pending_cmd.timestamp)
                    after = p.current_cell()

                    from_cell = pending_cmd.params[0] if pending_cmd.params else before
                    to_cell = pending_cmd.params[1] if len(pending_cmd.params) > 1 else after

                    if (from_cell != to_cell) or (len(pending_cmd.params) > 1):
                        self._bump_version()
                        logging.debug("state_version=%s", self.state_version)
                        self.publish_event(
                            et=EventType.PIECE_MOVED,
                            timestamp=pending_cmd.timestamp,
                            piece=pending_cmd.piece_id[0],
                            **{'from': from_cell},
                            to=to_cell,
                            player="white" if pending_cmd.piece_id[1] == "W" else "black",
                            capture=False,
                            timestamp_ms=pending_cmd.timestamp,
                        )
                    del self._deferred_after_cooldown[pid]

            # 3) rebuild cell→piece map *after* moves and updates
            self._update_cell2piece_map()

            # 4) resolve collisions based on the fresh board state
            self._resolve_collisions()

            if self._snapshot_dirty:
                self._publish_snapshot()

            # 5) render (optional)
            if is_with_graphics:
                self._draw()
                self._show()

            # stop early for tests
            if num_iterations is not None:
                it_counter += 1
                if it_counter >= num_iterations:
                    return

    def run(self, num_iterations=None, is_with_graphics=True):
        self.start_user_input_thread()
        start_ms = self.game_time_ms()
        for p in self.pieces:
            p.reset(start_ms)
        self._did_reset = True

        self.publish_event(
            et=EventType.GAME_STARTED,
            timestamp=start_ms,
            message="Game Start!"
            # white="Alice", black="Bob"
        )

        self._run_game_loop(num_iterations, is_with_graphics)

        self._announce_win()
        if self.kb_prod_1:
            self.kb_prod_1.stop()
            self.kb_prod_2.stop()

    # ──────────────────────────────────────────────────────────────
    def _draw(self):
        self.curr_board = self.clone_board()
        for p in self.pieces:
            p.draw_on_board(self.curr_board, now_ms=self.game_time_ms())

        # overlay both players' cursors, but only log on change
        if self.kp1 and self.kp2:
            for player, kp, last in (
                (1, self.kp1, 'last_cursor1'),
                (2, self.kp2, 'last_cursor2')
            ):
                r, c = kp.get_cursor()
                # draw rectangle
                y1 = r * self.board.cell_H_pix
                x1 = c * self.board.cell_W_pix
                y2 = y1 + self.board.cell_H_pix - 1
                x2 = x1 + self.board.cell_W_pix - 1
                color = (0, 255, 0) if player == 1 else (255, 0, 0)
                self.curr_board.img.draw_rect(x1, y1, x2, y2, color)

                # only print if moved
                prev = getattr(self, last)
                if prev != (r, c):
                    logger.debug("Marker P%s moved to (%s, %s)", player, r, c)
                    setattr(self, last, (r, c))

    def _show(self):
        bg = board_img.img.copy()

        board_np = self.curr_board.img.img

        if board_np.shape[2] == 4:
            # strip alpha if exists (canvas is BGR)
            board_np = board_np[..., :3]

        h_bg, w_bg = bg.shape[:2]
        h_b, w_b = board_np.shape[:2]
        x_off = (w_bg - w_b) // 2
        y_off = (h_bg - h_b) // 2

        bg[y_off:y_off + h_b, x_off:x_off + w_b] = board_np

        from types import SimpleNamespace
        render_overlay(now_ms=self.game_time_ms(), board=SimpleNamespace(img=bg))
        if not self._window_ready:
            try:
                cv2.namedWindow("Game", cv2.WINDOW_NORMAL)
                cv2.resizeWindow("Game", 1920, 1080)
            except Exception as e:
                logger.debug("Skipping window creation (headless?): %s", e)
            self._window_ready = True

        try:
            cv2.imshow("Game", bg)
            cv2.waitKey(1)
        except Exception as e:
            logger.debug("imshow skipped (headless?): %s", e)

    # ──────────────────────────────────────────────────────────────
    def _side_of(self, piece_id: str) -> str:
        return piece_id[1]

    def _process_input(self, cmd: Command):
        """
        Apply the command to the addressed piece and (if it actually changes squares)
        PUBLISH a PIECE_MOVED event immediately with capture=False.
        Actual captures (and their events) are handled inside _resolve_collisions().

        Robust to commands that provide only a single param (e.g., jump with just the
        current cell) by deriving the `to` square from the piece's post-command state.
        """
        mover = self.piece_by_id.get(cmd.piece_id)
        if not mover:
            logger.debug("Unknown piece id %s", cmd.piece_id)
            return

        if not mover.state.name.startswith("idle"):
            self._deferred_after_cooldown[mover.id] = cmd
            self.publish_event(et=EventType.SOUND_PLAY, timestamp=self.game_time_ms(), capture=False)
            logger.debug("Queued command for %s until it becomes idle: %s", mover.id, cmd)
            return

        # Track position before/after to safely infer from/to when params are partial
        before = mover.current_cell()
        mover.on_command(cmd, self.pos)
        setattr(mover, "_last_cmd_ts", cmd.timestamp)
        after = mover.current_cell()

        # Derive from/to safely:
        # - if no params → from=before, to=after
        # - if one param  → from=params[0], to=after
        # - if two params → from=params[0], to=params[1]
        from_cell = cmd.params[0] if cmd.params else before
        to_cell = cmd.params[1] if len(cmd.params) > 1 else after

        # Publish PIECE_MOVED only if a real square change happened
        #   OR if caller explicitly supplied both from/to (to keep their intent).
        if (from_cell != to_cell) or (len(cmd.params) > 1):
            self._bump_version()
            logging.debug("state_version=%s", self.state_version)
            self.publish_event(
                et=EventType.PIECE_MOVED,
                timestamp=cmd.timestamp,  # wall-clock-ish for ordering
                piece=cmd.piece_id[0],
                **{'from': from_cell},
                to=to_cell,
                player="white" if cmd.piece_id[1] == "W" else "black",
                capture=False,
                timestamp_ms=cmd.timestamp,  # relative game-time for history UI/tests
            )

        # Optional UX cue: play a non-capture move sound regardless
        self.publish_event(
            et=EventType.SOUND_PLAY,
            timestamp=self.game_time_ms(),
            capture=False
        )

        logger.info(f"Processed command: {cmd} for piece {cmd.piece_id} (from {from_cell} to {to_cell})")

    def _resolve_collisions(self):
        """
        Detect multiple pieces on same cell.
        Decide winner by 'most recently started moving' heuristic,
        skip captures when a jumper/knight-in-air is involved,
        and PUBLISH CAPTURE immediately when we actually remove a piece.
        """
        self._update_cell2piece_map()
        occupied = self.pos

        for cell, plist in occupied.items():
            if len(plist) < 2:
                continue

            logger.debug(f"Collision detected at {cell}: {[p.id for p in plist]}")

            def _start_key(p: Piece):
                last_cmd = getattr(p, "_last_cmd_ts", -1)
                start_ms = self._piece_start_ms(p)
                return (last_cmd, start_ms)

            moving_pieces = [p for p in plist if p.state.name != 'idle']
            pool = moving_pieces if moving_pieces else plist
            winner = max(pool, key=_start_key)
            logger.debug(f"Winner: {winner.id} by key={_start_key(winner)}")
            # prefer pieces that are moving over idle; then by newest start_ms
            # moving_pieces = [p for p in plist if p.state.name != 'idle']
            # if moving_pieces:
            #     winner = max(moving_pieces, key=lambda p: p.state.physics.get_start_ms())
            #     logger.debug(f"Winner (moving): {winner.id} (state: {winner.state.name})")
            # else:
            #     winner = max(plist, key=lambda p: p.state.physics.get_start_ms())
            #     logger.debug(f"Winner (idle): {winner.id} (state: {winner.state.name})")

            # remove every other piece (respect jump/knight-in-air rules)
            to_remove: List[Piece] = []
            for p in plist:
                if p is winner:
                    continue

                # ---- in-air exceptions: ALWAYS skip removal ----
                if p.state.name == 'jump':
                    logger.debug(f"Piece {p.id} is jumping - not removing")
                    continue
                if winner.state.name == 'jump':
                    logger.debug(f"Winner {winner.id} is jumping - not removing {p.id}")
                    continue
                # knights moving are considered 'in air'
                if p.id.startswith(('NW', 'NB')) and p.state.name == 'move':
                    logger.debug(f"Knight {p.id} is moving (jumping) - not removing")
                    continue
                if winner.id.startswith(('NW', 'NB')) and winner.state.name == 'move':
                    logger.debug(f"Winner knight {winner.id} is moving (jumping) - not removing {p.id}")
                    continue

                # ---- same-color: resolve overlap WITHOUT CAPTURE (no score) ----
                if winner.id[1] == p.id[1]:
                    logger.debug(f"Same-color overlap {winner.id} vs {p.id} – removing loser WITHOUT CAPTURE")
                    to_remove.append(p)
                    continue

                # ---- opponents: perform real capture and publish events ----
                self._bump_version()
                logger.info(f"CAPTURE: {winner.id} captures {p.id} at {cell}")
                self.publish_event(
                    et=EventType.CAPTURE,
                    timestamp=self.game_time_ms(),
                    player='white' if winner.id[1] == 'W' else 'black',
                    piece=p.id[0],
                )
                self.publish_event(
                    et=EventType.SOUND_PLAY,
                    timestamp=self.game_time_ms(),
                    capture=True
                )
                to_remove.append(p)

            # physically remove losers from the game state
            # NEW — remove by identity, keep indices stable, and drop from lookup
            if to_remove and not any(evt for evt in []):
                self._bump_version()
            for p in to_remove:
                pid = p.id
                self.pieces = [x for x in self.pieces if x.id != pid]
                self.piece_by_id.pop(pid, None)

            # Rebuild occupancy after removals in this cell so next checks are accurate
            self._update_cell2piece_map()

    # ──────────────────────────────────────────────────────────────
    def _validate(self, pieces):
        """Ensure both kings present and no two pieces share a cell (unless opposite sides)."""
        has_white_king = has_black_king = False
        seen_cells: Dict[Tuple[int, int], str] = {}
        for p in pieces:
            cell = p.current_cell()
            if cell in seen_cells:
                # Allow overlap only if piece is from opposite side
                if seen_cells[cell] == p.id[1]:
                    return False
            else:
                seen_cells[cell] = p.id[1]
            if p.id.startswith("KW"):
                has_white_king = True
            elif p.id.startswith("KB"):
                has_black_king = True
        return has_white_king and has_black_king

    def _is_win(self) -> bool:
        kings = [p for p in self.pieces if p.id.startswith(('KW', 'KB'))]
        return len(kings) < 2

    def _announce_win(self):
        # text = 'Black wins!' if any(p.id.startswith('KB') for p in self.pieces) else 'White wins!'
        winner_is_black = any(p.id.startswith('KB') for p in self.pieces)
        winner = 'black' if winner_is_black else 'white'
        text = 'Black wins!' if winner_is_black else 'White wins!'
        logger.info(text)

        self.publish_event(
            et=EventType.GAME_ENDED,
            timestamp=self.game_time_ms(),
            winner=winner,
            reason="king captured"
        )

    def _validate_initial_setup(self):
        w = sum(1 for p in self.pieces if p.id.startswith("KW"))
        b = sum(1 for p in self.pieces if p.id.startswith("KB"))
        if w != 1 or b != 1:
            raise InvalidBoard(f"Missing or duplicate king(s): white={w}, black={b}")

        seen: Dict[Tuple[int, int], str] = {}
        for p in self.pieces:
            cell = p.current_cell()
            if cell in seen:
                raise InvalidBoard(f"Duplicate initial positions at {cell}: {seen[cell]} and {p.id}")
            seen[cell] = p.id

    def _piece_start_ms(self, piece: Piece) -> int:
        phys = getattr(piece.state, "physics", None)
        if phys is None:
            return 0
        get_ms = getattr(phys, "get_start_ms", None)
        if callable(get_ms):
            try:
                return int(get_ms())
            except Exception:
                return int(getattr(phys, "_start_ms", 0))
        return int(getattr(phys, "_start_ms", 0))
