import pathlib

from GameFactory import create_game
from client.renderer import ClientRenderer
from GraphicsFactory import MockImgFactory
from mock_img import MockImg

PIECES_DIR = pathlib.Path(__file__).parent.parent.parent / "pieces"

def px_for_cell(board, cell):
    x_m, y_m = board.cell_to_m(cell)
    return board.m_to_pix((x_m, y_m))

def find_draw_on(traj, x, y):
    return any(
        (isinstance(r, tuple) and len(r) == 2 and r == (x, y)) or
        (isinstance(r, tuple) and len(r) >= 3 and r[-2] == x and r[-1] == y)
        for r in traj
    )

def test_client_full_board_rendering_centered_and_with_piece():
    # --- Arrange ---
    game = create_game(PIECES_DIR, MockImgFactory())
    game._update_cell2piece_map()
    MockImg.reset()

    renderer = ClientRenderer(game.board, PIECES_DIR, MockImgFactory())

    pawn_white = game.pos[(6, 0)][0]
    payload = {
        "version": 1,
        "pieces": [{"id": pawn_white.id, "cell": (6, 0)}],
    }

    # --- Act ---
    renderer.render_snapshot(payload)

    # --- Assert 1:
    assert getattr(renderer, "_frame", None) is not None, "Renderer did not create a final _frame"

    # --- Assert 2:
    canvas_width = game.board.W_cells * game.board.cell_W_pix
    canvas_height = game.board.H_cells * game.board.cell_H_pix

    assert getattr(renderer, "_frame", None) is not None, "Renderer did not create a final _frame"
    bg_height, bg_width = renderer._frame.shape[:2]

    expected_x0 = (bg_width - canvas_width) // 2
    expected_y0 = (bg_height - canvas_height) // 2

    assert find_draw_on(MockImg.traj, expected_x0, expected_y0), \
        f"Did not find canvas overlay draw_on at ({expected_x0}, {expected_y0}); traj={MockImg.traj}"

    # --- Assert 3:
    x_px, y_px = px_for_cell(game.board, (6, 0))
    assert find_draw_on(MockImg.traj, x_px, y_px), \
        f"Did not find sprite draw_on call on canvas at ({x_px}, {y_px}); traj={MockImg.traj}"
