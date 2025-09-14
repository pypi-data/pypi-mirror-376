import random
from collections import deque
from typing import List, Tuple

from .models import Board, GameConfig, GameState


def get_adjacent_positions(
    row: int, col: int, width: int, height: int
) -> List[Tuple[int, int]]:
    """Get list of valid adjacent positions for a given cell."""
    adjacent = []

    # Check all 8 directions: top-left, top, top-right, left, right, bottom-left, bottom, bottom-right
    for dr in [-1, 0, 1]:
        for dc in [-1, 0, 1]:
            if dr == 0 and dc == 0:  # Skip the cell itself
                continue

            new_row = row + dr
            new_col = col + dc

            # Check if position is within board bounds
            if 0 <= new_row < height and 0 <= new_col < width:
                adjacent.append((new_row, new_col))

    return adjacent


def place_mines(board: Board, total_mines: int):
    """Randomly place mines on the board."""
    # Create list of all possible positions
    all_positions = []
    for row in range(board.height):
        for col in range(board.width):
            all_positions.append((row, col))

    # Randomly select positions for mines
    mine_positions = random.sample(all_positions, total_mines)

    # Place mines at selected positions
    for row, col in mine_positions:
        cell = board.get_cell(row, col)
        if cell:
            cell.has_mine = True


def calculate_adjacent_mines(board: Board):
    """Calculate adjacent mine count for each non-mine cell."""
    for row in range(board.height):
        for col in range(board.width):
            cell = board.get_cell(row, col)

            if cell and not cell.has_mine:
                # Count mines in adjacent positions
                mine_count = 0
                adjacent_positions = get_adjacent_positions(
                    row, col, board.width, board.height
                )

                for adj_row, adj_col in adjacent_positions:
                    adjacent_cell = board.get_cell(adj_row, adj_col)
                    if adjacent_cell and adjacent_cell.has_mine:
                        mine_count += 1

                cell.adjacent_mines = mine_count


def reveal_cell(game_state: GameState, row: int, col: int) -> bool:
    """Reveal a cell and handle mine explosion or cascade reveal.

    Returns True if successful, False if invalid move.
    """
    board = game_state.board
    cell = board.get_cell(row, col)

    # Check if cell exists and is not already revealed
    if cell is None or cell.is_revealed:
        return False

    # If cell has flag, remove it and update counter
    if cell.has_flag:
        cell.has_flag = False
        game_state.flags_placed -= 1

    # Reveal the cell
    cell.is_revealed = True

    # Check if cell has a mine
    if cell.has_mine:
        # Game over - player hit a mine
        game_state.mark_game_over()
        game_state.won = False
        return True

    # If cell has no adjacent mines, trigger cascade reveal
    if cell.adjacent_mines == 0:
        reveal_cascade(game_state, row, col)

    return True


def reveal_cascade(game_state: GameState, row: int, col: int) -> None:
    """Reveal all connected empty cells in a cascade effect."""
    board = game_state.board

    # Use BFS with a queue to reveal adjacent empty cells
    queue = deque([(row, col)])

    while queue:
        current_row, current_col = queue.popleft()

        # Get all adjacent positions
        adjacent_positions = get_adjacent_positions(
            current_row, current_col, board.width, board.height
        )

        for adj_row, adj_col in adjacent_positions:
            adjacent_cell = board.get_cell(adj_row, adj_col)

            # Skip if cell doesn't exist, is already revealed, or has a mine
            if (
                adjacent_cell is None
                or adjacent_cell.is_revealed
                or adjacent_cell.has_mine
            ):
                continue

            # Remove flag if present
            if adjacent_cell.has_flag:
                adjacent_cell.has_flag = False
                game_state.flags_placed -= 1

            # Reveal the adjacent cell
            adjacent_cell.is_revealed = True

            # If this cell also has no adjacent mines, add it to queue for further expansion
            if adjacent_cell.adjacent_mines == 0:
                queue.append((adj_row, adj_col))


def check_victory(game_state: GameState) -> None:
    """Check if the player has won the game by revealing all non-mine cells."""
    board = game_state.board
    unrevealed_count = 0

    # Count unrevealed cells
    for row in range(board.height):
        for col in range(board.width):
            cell = board.get_cell(row, col)
            if cell and not cell.is_revealed:
                unrevealed_count += 1

    # Player wins if the number of unrevealed cells equals the number of mines
    if unrevealed_count == board.total_mines:
        game_state.mark_game_over()
        game_state.won = True


def toggle_flag(game_state: GameState, row: int, col: int) -> bool:
    """Toggle flag on/off for a cell.

    Returns True if successful, False if invalid move.
    """
    board = game_state.board
    cell = board.get_cell(row, col)

    # Check if cell exists and is not already revealed
    if cell is None or cell.is_revealed:
        return False

    # Toggle flag state
    if cell.has_flag:
        cell.has_flag = False
        game_state.flags_placed -= 1
    else:
        cell.has_flag = True
        game_state.flags_placed += 1

    return True


def reveal_all_mines(game_state: GameState) -> None:
    """Reveal all mines on the board when game is over."""
    board = game_state.board

    for row in range(board.height):
        for col in range(board.width):
            cell = board.get_cell(row, col)
            if cell and cell.has_mine:
                cell.is_revealed = True


def initialize_game(level: str) -> GameState:
    """Initialize a new game with the specified difficulty level."""
    # Get configuration for the level
    width, height, total_mines = GameConfig.get_config(level)

    # Create board with dimensions
    board = Board(width, height, total_mines)

    # Place mines randomly
    place_mines(board, total_mines)

    # Calculate adjacent mine counts
    calculate_adjacent_mines(board)

    # Create and return game state
    return GameState(board)
