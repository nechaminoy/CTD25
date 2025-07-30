# engine/sound_handler.py
import logging
from pathlib import Path
from typing import List
try:
    import pygame  # type: ignore
except Exception:
    pygame = None  # type: ignore

from ..shared.event import Event, EventType

played_sounds: List[str] = []

# Init mixer once
def init_mixer():
    """Call this once in real application startup."""
    if not pygame:
        return
    try:
        if not pygame.mixer.get_init():
            pygame.mixer.init()
    except pygame.error:
        # No audio device / headless test env – ignore
        pass

def play_sound_file(filename: str) -> None:
    """
    Create and play a pygame Sound object for the given file.
    Path is resolved relative to this module (not current working directory).
    In tests/CI (no audio device or missing file), skip gracefully.
    """
    log = logging.getLogger(__name__)

    path = Path(filename)
    if not path.is_absolute():
        base = Path(__file__).resolve().parent
        candidates = [
            base / filename,  # תיקיית המודול (engine/ או KFC_Py/)
            base.parent / filename,  # הורה (KFC_Py/)
            base.parents[1] / filename if len(base.parents) > 1 else None,  # סבא (game_logic/)
        ]
        path = next((p.resolve() for p in candidates if p and p.exists()), Path())
    if not pygame:
        log.warning("pygame not available; skipping playback")
        return
    try:
        if not path.exists():
            log.warning("Sound file not found: %s; skipping playback", path)
            return

        if not pygame.mixer.get_init():
            pygame.mixer.init()

        sound = pygame.mixer.Sound(str(path))
        sound.play()

    except (FileNotFoundError, pygame.error) as e:
        # Headless/CI/No audio device – don't crash tests
        logging.getLogger(__name__).warning("Skipping sound playback: %s", e)


def on_sound_play(event: Event) -> None:
    """
    EventBus callback for SOUND_PLAY events:
    - Chooses the correct file based on whether it's a capture
    - Records it in played_sounds
    - Calls play_sound_file to actually play it
    """
    is_capture = (event.payload or {}).get('capture', False)
    sound_file = "capture.wav" if is_capture else "move.mp3"

    played_sounds.append(sound_file)
    play_sound_file(sound_file)


def get_played_sounds() -> List[str]:
    """
    Return a copy of the list of played sound filenames.
    """
    return list(played_sounds)

def clear_played_sounds() -> None:
    """
    Clear the played_sounds list (to reset state between tests).
    """
    played_sounds.clear()

def subscribe_to_events_sound_play(bus) -> None:
    """
    Subscribe the on_sound_play handler to SOUND_PLAY events on the given bus.
    """
    bus.subscribe(EventType.SOUND_PLAY, on_sound_play)
