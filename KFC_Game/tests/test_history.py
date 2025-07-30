from time import time
import pytest
from unittest.mock import MagicMock, patch
from ..shared.event import Event, EventType
from ..shared.move_history import (
    format_time,
    coords_to_algebraic,
    to_algebraic_notation,
    add_move_to_history,
    clear_move_histories,
    get_move_history,
    update_history_panels,
    on_piece_moved,
    subscribe_to_events
)

# 1. format_time
@pytest.mark.parametrize("ms,expected", [
    (65000, "01:05.000"),
    (0, "00:00.000"),
    (1234567, "20:34.567"),
])
def test_format_time(ms, expected):
    assert format_time(ms) == expected

# 2. coords_to_algebraic
@pytest.mark.parametrize("coord,expected", [
    ((0, 0), "a8"),
    ((7, 7), "h1"),
    ((4, 3), "d4"),
])
def test_coords_to_algebraic(coord, expected):
    assert coords_to_algebraic(coord) == expected

@pytest.mark.parametrize("coord", [
    (8, 8),
    (-1, -1),
])
def test_coords_to_algebraic_invalid(coord):
    with pytest.raises(IndexError):
        coords_to_algebraic(coord)

# 3. to_algebraic_notation
@pytest.mark.parametrize("mv,expected", [
    ({"piece":"P", "from":(6,4), "to":(4,4)}, "e4"),
    ({"piece":"P", "from":(3,3), "to":(2,4), "capture":True}, "dxe6"),
    ({"piece":"N", "from":(7,6), "to":(5,5)}, "Nf3"),
    ({"castling":"O-O"}, "O-O"),
    ({"castling":"O-O-O"}, "O-O-O"),
    ({"piece":"P", "from":(1,0), "to":(0,0), "promotion":"queen"}, "a8=Q"),
    ({"piece":"Q", "from":(3,3), "to":(1,5), "check":True}, "Qf7+"),
    ({"piece":"R", "from":(1,7), "to":(0,7), "checkmate":True}, "Rh8#"),
])
def test_to_algebraic_notation(mv, expected):
    assert to_algebraic_notation(mv) == expected

# 4. add_move_to_history
def test_add_move_to_history():
    clear_move_histories()
    add_move_to_history('white', '00:01.000', 'e4')
    add_move_to_history('black', '00:01.500', 'd5')

    assert get_move_history('white') == [('00:01.000', 'e4')]
    assert get_move_history('black') == [('00:01.500', 'd5')]

# 5. on_piece_moved
def test_on_piece_moved():
    clear_move_histories()
    event = Event(EventType.PIECE_MOVED, {
        'piece':'P', 'from':(6,4), 'to':(4,4),
        'player':'white', 'timestamp_ms':1000
    }, timestamp=int(time() * 1000))

    with patch('KFC_Game.shared.move_history.update_history_panels') as mock_update_history_panels:
        on_piece_moved(event)

        assert get_move_history('white') == [('00:01.000', 'e4')]
        mock_update_history_panels.assert_called_once()
        
# 6. update_history_panels
def test_update_history_panels():
    mock_board = MagicMock()
    mock_board.img.shape.__getitem__.return_value = 800

    mock_template = MagicMock()
    mock_template.clone.return_value = mock_template

    black_history = [('00:01.500', 'd5')] * 21
    white_history = [('00:01.000', 'e4')] * 19

    update_history_panels(board=mock_board,
                          black_template=mock_template,
                          white_template=mock_template,
                          black_history=black_history,
                          white_history=white_history)

    assert mock_template.put_text.call_count == (20+19)*2
    assert mock_template.draw_on.call_count == 2

# 7. subscribe_to_events
def test_subscribe_to_events():
    mock_bus = MagicMock()
    subscribe_to_events(mock_bus)
    mock_bus.subscribe.assert_called_once_with(EventType.PIECE_MOVED, on_piece_moved)
