from enum import Enum
from dataclasses import dataclass
from typing import Any, Dict


class EventType(str, Enum):
    # ─── Game lifecycle ───
    GAME_STARTED   = "game_started"
    GAME_ENDED     = "game_ended"

    # ─── Piece / move events ───
    MOVE_STARTED   = "move_started"
    MOVE_FINISHED  = "move_finished"
    CAPTURE        = "capture"
    ILLEGAL_MOVE   = "illegal_move"
    PIECE_MOVED    = "piece_moved"

    # ─── UI / FX helpers (optional) ───
    ANNOUNCEMENT_SHOW = "announcement_show"
    ANNOUNCEMENT_HIDE = "announcement_hide"
    SOUND_PLAY        = "sound_play"
    ANIMATION_DONE    = "animation_done"

    # ─── Misc / debug (optional) ───
    PIECE_SELECTED = "piece_selected"
    PIECE_DROPPED  = "piece_dropped"
    TIMER_TICK     = "timer_tick"

    STATE_SNAPSHOT = "state_snapshot"
    ASSIGN_PLAYER = "assign_player"
    ILLEGAL_COMMAND = "illegal_command"
    COMMAND_RESULT = "command_result"


@dataclass(frozen=True)
class Event:
    """Generic event object passed through the bus."""
    type: EventType
    payload: Dict[str, Any]
    timestamp: int  # milliseconds since game start or epoch
