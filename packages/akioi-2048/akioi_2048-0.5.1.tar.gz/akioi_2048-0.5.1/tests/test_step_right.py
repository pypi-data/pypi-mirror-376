import akioi_2048 as ak


def test_right_number_merges_and_positive_score() -> None:
    board = [
        [0, 0, 0, 0],
        [0, 0, 0, 0],
        [0, 0, 0, 0],
        [2, 2, 4, 4],
    ]
    new_board, delta, _ = ak.step(board, ak.Direction.Right)
    assert new_board[3][3] == 8
    assert new_board[3][2] == 4
    assert delta == 12


def test_right_multiplier_merges_and_negative_score() -> None:
    board = [
        [0, 0, 0, 0],
        [0, 0, 0, 0],
        [0, 0, 0, 0],
        [-1, -1, -2, -2],
    ]
    new_board, delta, _ = ak.step(board, ak.Direction.Right)
    assert new_board[3][3] == -4
    assert new_board[3][2] == -2
    assert delta == -6


def test_right_number_multiplier_merges() -> None:
    board = [
        [0, 0, 0, 0],
        [0, 0, 0, 0],
        [0, 0, 0, 0],
        [0, 0, 2, -2],
    ]
    new_board, delta, _ = ak.step(board, ak.Direction.Right)
    assert new_board[3][3] == 4
    assert delta == 4


def test_right_number_and_multiplier_do_not_merge_without_tiles_right() -> None:
    board = [
        [0, 0, 0, 0],
        [0, 0, 0, 0],
        [0, 0, 0, 0],
        [2, -2, 0, 0],
    ]
    new_board, delta, _ = ak.step(board, ak.Direction.Right)
    assert new_board[3][2] == 2
    assert new_board[3][3] == -2
    assert delta == 0


def test_right_number_and_multiplier_no_merge_with_gap() -> None:
    board = [
        [0, 0, 0, 0],
        [0, 0, 0, 0],
        [0, 0, 0, 0],
        [2, -2, 0, 16],
    ]
    new_board, delta, _ = ak.step(board, ak.Direction.Right)
    assert new_board[3][1] == 2
    assert new_board[3][2] == -2
    assert new_board[3][3] == 16
    assert delta == 0
