import pytest
from unittest.mock import MagicMock, patch
from ..shared.event import Event, EventType
from ..shared.score_handler import (
    add_capture_score,
    reset_scores,
    get_score,
    update_score_panels,
    on_capture,
    subscribe_to_events_capture
)

@pytest.fixture(autouse=True)
def run_before_each_test():
    reset_scores()

def test_add_capture_score():
    add_capture_score('white', 'pawn')
    add_capture_score('black', 'queen')

    assert get_score('white') == 1
    assert get_score('black') == 9

def test_on_capture():
    reset_scores()
    evt = Event(EventType.CAPTURE, {
        'player': 'white',
        'piece': 'bishop',
    }, timestamp=0)

    with patch('KFC_Game.shared.score_handler.update_score_panels') as mock_update:
        on_capture(evt)
        assert get_score('white') == 3
        mock_update.assert_called_once()

def test_update_score_panels():
    mock_board = MagicMock()
    mock_board.img.shape = (800, 800, 3)
    mock_template = MagicMock()
    mock_template.clone.return_value = mock_template

    update_score_panels(board=mock_board, template=mock_template)

    assert mock_template.put_text.call_count == 2
    assert mock_template.draw_on.call_count == 2

def test_subscribe_to_events():
    mock_bus = MagicMock()
    subscribe_to_events_capture(mock_bus)
    mock_bus.subscribe.assert_called_once_with(EventType.CAPTURE, on_capture)
