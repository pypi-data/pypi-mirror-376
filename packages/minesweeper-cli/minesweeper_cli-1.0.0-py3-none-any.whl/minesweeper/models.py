from datetime import datetime
from typing import List, Optional, Tuple


class Cell:
    """Represents a single cell in the minesweeper grid."""

    def __init__(self):
        self.has_mine: bool = False
        self.is_revealed: bool = False
        self.has_flag: bool = False
        self.adjacent_mines: int = 0

    def __repr__(self) -> str:
        flags = []
        if self.has_mine:
            flags.append("MINE")
        if self.is_revealed:
            flags.append("REVEALED")
        if self.has_flag:
            flags.append("FLAG")
        if self.adjacent_mines > 0:
            flags.append(f"ADJ:{self.adjacent_mines}")

        return f"Cell({', '.join(flags) if flags else 'EMPTY'})"


class Board:
    """Represents the minesweeper game board."""

    def __init__(self, width: int, height: int, total_mines: int):
        self.width = width
        self.height = height
        self.total_mines = total_mines
        self.cells: List[List[Cell]] = []

        # Initialize empty grid
        for row in range(height):
            cell_row = []
            for col in range(width):
                cell_row.append(Cell())
            self.cells.append(cell_row)

    def get_cell(self, row: int, col: int) -> Optional[Cell]:
        """Get cell at given position, returns None if position invalid."""
        if not self.is_valid_position(row, col):
            return None
        return self.cells[row][col]

    def is_valid_position(self, row: int, col: int) -> bool:
        """Check if the given position is within board bounds."""
        return 0 <= row < self.height and 0 <= col < self.width


class GameState:
    """Represents the current state of a minesweeper game."""

    def __init__(self, board: Board):
        self.board = board
        self.is_game_over: bool = False
        self.won: bool = False
        self.start_time: datetime = datetime.now()
        self.end_time: Optional[datetime] = None
        self.flags_placed: int = 0

    def elapsed_time(self) -> float:
        """Returns elapsed time in seconds since game start."""
        if self.is_game_over and self.end_time:
            # If game is over and we have end_time, use that for consistent time display
            return (self.end_time - self.start_time).total_seconds()
        else:
            return (datetime.now() - self.start_time).total_seconds()

    def mark_game_over(self):
        """Mark the game as over and record the end time."""
        if not self.is_game_over:
            self.is_game_over = True
            self.end_time = datetime.now()


class GameConfig:
    """Configuration for different game difficulty levels."""

    LEVELS = {
        "easy": (8, 8, 10),  # width, height, mines
        "medium": (16, 16, 40),
        "hard": (30, 16, 99),
    }

    @classmethod
    def get_config(cls, level: str) -> Tuple[int, int, int]:
        """Get configuration for given level. Returns (width, height, mines)."""
        if level not in cls.LEVELS:
            raise ValueError(
                f"Unknown level: {level}. Available: {list(cls.LEVELS.keys())}"
            )
        return cls.LEVELS[level]
