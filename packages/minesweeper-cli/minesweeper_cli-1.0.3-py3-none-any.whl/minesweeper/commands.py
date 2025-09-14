import re
from enum import Enum
from typing import Optional, Tuple

from .models import GameState


class Command(Enum):
    """Available game commands."""

    REVEAL = "reveal"
    FLAG = "flag"
    HELP = "help"
    QUIT = "quit"
    NEW = "new"
    INVALID = "invalid"


def parse_coordinate(coord_str: str) -> Optional[Tuple[int, int]]:
    """
    Parse coordinate string like 'A1' or 'AA15' to (row, col) tuple.
    Returns None if format is invalid.
    """
    if not coord_str:
        return None

    # Validate format: letters followed by numbers
    match = re.match(r"^([A-Z]+)([0-9]+)$", coord_str.upper())
    if not match:
        return None

    letters, numbers = match.groups()

    # Convert letters to column index using Excel-style column naming
    # A=0, B=1, ..., Z=25, AA=26, AB=27, ..., AZ=51, BA=52, BB=53, etc.
    col = 0
    for letter in letters:
        col = col * 26 + (ord(letter) - ord("A") + 1)
    col -= 1  # Adjust to 0-based indexing (A=0, not A=1)

    # Convert numbers to row index (1=0, 2=1, ...)
    try:
        row = int(numbers) - 1
    except ValueError:
        return None

    # Basic bounds check (negative values)
    if row < 0 or col < 0:
        return None

    return (row, col)


def parse_command(input_str: str) -> Tuple[Command, Optional[Tuple[int, int]]]:
    """
    Parse user input string into command and coordinate.
    Returns (Command, coordinate) tuple.
    """
    if not input_str:
        return (Command.INVALID, None)

    # Convert to lowercase and split
    parts = input_str.strip().lower().split()

    if not parts:
        return (Command.INVALID, None)

    command_str = parts[0]

    # Identify command
    if command_str in ["reveal", "r"]:
        if len(parts) < 2:
            return (Command.INVALID, None)
        coordinate = parse_coordinate(parts[1])
        return (Command.REVEAL, coordinate)

    elif command_str in ["flag", "f"]:
        if len(parts) < 2:
            return (Command.INVALID, None)
        coordinate = parse_coordinate(parts[1])
        return (Command.FLAG, coordinate)

    elif command_str in ["help", "h", "?"]:
        return (Command.HELP, None)

    elif command_str in ["quit", "q", "exit"]:
        return (Command.QUIT, None)

    elif command_str in ["new", "n"]:
        return (Command.NEW, None)

    else:
        return (Command.INVALID, None)


def validate_command(
    command: Command, coordinate: Optional[Tuple[int, int]], game_state: GameState
) -> Optional[str]:
    """
    Validate command and coordinate against current game state.
    Returns error message string if invalid, None if valid.
    """
    board = game_state.board

    # Commands that require coordinates
    if command in [Command.REVEAL, Command.FLAG]:
        if coordinate is None:
            return "Formato de coordenada inválido. Use letra+número (ej: B3)"

        row, col = coordinate

        # Check if coordinate is within board bounds
        if not board.is_valid_position(row, col):
            return "Coordenada fuera del tablero"

        # Check if cell is already revealed for REVEAL command
        if command == Command.REVEAL:
            cell = board.get_cell(row, col)
            if cell and cell.is_revealed and not cell.has_flag:
                return "Esa casilla ya está revelada"

    # NEW command only allowed when game is over
    if command == Command.NEW and not game_state.is_game_over:
        return "Solo puedes iniciar una nueva partida cuando el juego termine"

    # REVEAL and FLAG only allowed when game is not over
    if command in [Command.REVEAL, Command.FLAG] and game_state.is_game_over:
        return "El juego ha terminado. Use 'new' para nueva partida o 'quit' para salir"

    return None  # Valid command
