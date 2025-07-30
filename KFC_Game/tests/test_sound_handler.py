# tests/test_sound_handler.py
import pytest
from unittest.mock import patch, MagicMock
from ..shared.event import Event, EventType
from ..audio.sound_handler import (
    on_sound_play,
    play_sound_file,
    get_played_sounds,
    clear_played_sounds,
    subscribe_to_events_sound_play
)

@pytest.fixture(autouse=True)
def clear_sounds_fixture():
    """Automatically clear the played_sounds list before each test."""
    clear_played_sounds()

@patch('KFC_Game.audio.sound_handler.play_sound_file')
def test_play_move_sound(mock_play_sound):
    """When capture=False, we should record and attempt to play 'move.mp3'."""
    event = Event(EventType.SOUND_PLAY, {'capture': False}, timestamp=0)
    on_sound_play(event)

    assert get_played_sounds() == ["move.mp3"]
    mock_play_sound.assert_called_once_with("move.mp3")

@patch('KFC_Game.audio.sound_handler.play_sound_file')
def test_play_capture_sound(mock_play_sound):
    """When capture=True, we should record and attempt to play 'capture.wav'."""
    event = Event(EventType.SOUND_PLAY, {'capture': True}, timestamp=0)
    on_sound_play(event)

    assert get_played_sounds() == ["capture.wav"]
    mock_play_sound.assert_called_once_with("capture.wav")

def test_clear_and_get_played_sounds():
    """clear_played_sounds should empty the list; get_played_sounds returns current list."""
    # ensure starting from empty
    clear_played_sounds()
    assert get_played_sounds() == []

    # simulate manual additions
    from ..audio.sound_handler import played_sounds
    played_sounds.extend(["a.mp3", "b.wav"])
    assert get_played_sounds() == ["a.mp3", "b.wav"]

def test_subscribe_to_events():
    """subscribe_to_events should register our handler on the bus."""
    mock_bus = MagicMock()
    subscribe_to_events_sound_play(mock_bus)
    mock_bus.subscribe.assert_called_once_with(EventType.SOUND_PLAY, on_sound_play)

def test_eventbus_integration(monkeypatch):
    """
    Simulate EventBus.publish calling our handler,
    and ensure play_sound_file is invoked via the handler logic.
    """
    mock_play = MagicMock()
    monkeypatch.setattr('KFC_Game.audio.sound_handler.play_sound_file', mock_play)

    from ..audio import sound_handler
    mock_bus = MagicMock()
    sound_handler.subscribe_to_events_sound_play(mock_bus)

    # Find the registered handler and invoke it manually
    # call_args_list holds tuples like ((EventType, handler),)
    # but MagicMock.subscribe call_args_list entries are (args, kwargs)
    handler = mock_bus.subscribe.call_args_list[0][0][1]
    event = Event(EventType.SOUND_PLAY, {'capture': False}, timestamp=0)
    handler(event)

    assert get_played_sounds() == ["move.mp3"]
    mock_play.assert_called_once_with("move.mp3")
