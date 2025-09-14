import os
import string
from typing import List

from colorama import Fore, Style, init

from .models import Cell, GameState

# Initialize colorama
init(autoreset=True)

# Color configuration according to PRD
COLORS = {
    "unrevealed": Fore.BLUE,
    "empty": Fore.WHITE,
    "mine": Fore.RED,
    "flag": Fore.YELLOW,
    "explosion": Fore.RED,
    "border": Fore.LIGHTBLACK_EX,
    "number_1": Fore.CYAN,
    "number_2": Fore.GREEN,
    "number_3": Fore.YELLOW,
    "number_4": Fore.MAGENTA,
    "number_5": Fore.RED,
    "number_6": Fore.CYAN,
    "number_7": Fore.WHITE,
    "number_8": Fore.RED,
    "error": Fore.RED,
    "success": Fore.GREEN,
    "info": Fore.CYAN,
}


def colorize(text: str, color: str) -> str:
    """Apply color to text and reset afterward."""
    return f"{color}{text}{Style.RESET_ALL}"


def clear_screen():
    """Clear the terminal screen."""
    os.system("clear" if os.name == "posix" else "cls")


def get_column_labels(width: int) -> List[str]:
    """Generate column labels A-Z, AA-AZ, etc. for given width."""
    labels = []

    for i in range(width):
        if i < 26:
            # A-Z for first 26 columns with extra space
            labels.append(string.ascii_uppercase[i] + " ")
        else:
            # AA, AB, AC, ... for columns beyond 26
            first_letter = string.ascii_uppercase[(i - 26) // 26]
            second_letter = string.ascii_uppercase[i % 26]
            labels.append(first_letter + second_letter)

    return labels


def render_cell(
    cell: Cell,
    game_over: bool = False,
    exploded_position: tuple = None,
    current_position: tuple = None,
) -> str:
    """Render a single cell based on its state with colors."""
    if cell.has_flag and not cell.is_revealed:
        return colorize("🚩", COLORS["flag"])

    if not cell.is_revealed:
        return colorize("⬛", COLORS["unrevealed"])

    # Show explosion symbol if this is where the mine exploded
    if exploded_position and current_position == exploded_position:
        return colorize("💥", COLORS["explosion"])

    if cell.has_mine and game_over:
        return colorize("💣", COLORS["mine"])

    if cell.adjacent_mines > 0:
        color_key = f"number_{cell.adjacent_mines}"
        return colorize(str(cell.adjacent_mines), COLORS[color_key])

    return colorize("·", COLORS["empty"])


def is_emoji(text: str) -> bool:
    """Check if text contains actual emoji characters (not just Unicode)."""
    # Check for actual emojis used in the game
    emoji_chars = {"⬛", "🚩", "💣", "💥"}
    return any(char in emoji_chars for char in text)


def render_board(game_state: GameState, exploded_position: tuple = None):
    """Render the complete game board with appropriate spacing."""
    board = game_state.board
    width = board.width
    height = board.height

    # Get column labels
    column_labels = get_column_labels(width)

    # Print header with column labels using single space separator
    print("     " + " ".join(column_labels))

    # Calculate border length for mixed content
    border_length = width * 3 - 1 + 2
    print(colorize("   ┌" + "─" * border_length + "┐", COLORS["border"]))

    # Print each row
    for row in range(height):
        row_display = f"{row + 1:2d}"  # Right-align row numbers
        print(f"{row_display} {colorize('│', COLORS['border'])} ", end="")

        # Print cells with spacing: 1 space after emoji, 2 spaces after ASCII
        for col in range(width):
            cell = board.get_cell(row, col)
            cell_content = render_cell(
                cell, game_state.is_game_over, exploded_position, (row, col)
            )
            print(cell_content, end="")

            if col < width - 1:  # Add space between columns except last
                if is_emoji(cell_content):
                    print(" ", end="")  # 1 space after emoji (emoji is visually wider)
                else:
                    print("  ", end="")  # 2 spaces after ASCII (numbers, dots)
            else:  # Last column
                if is_emoji(cell_content):
                    print("", end="")  # No extra space after emoji in last column
                else:
                    print(" ", end="")  # 1 space after ASCII in last column

        print(colorize(" │", COLORS["border"]))

    # Print bottom border
    print(colorize("   └" + "─" * border_length + "┘", COLORS["border"]))


def render_game_info(game_state: GameState):
    """Render game information below the board."""
    board = game_state.board

    # Format elapsed time as MM:SS
    elapsed_seconds = int(game_state.elapsed_time())
    minutes = elapsed_seconds // 60
    seconds = elapsed_seconds % 60
    time_str = f"{minutes:02d}:{seconds:02d}"

    print(
        f"  Banderas: {game_state.flags_placed}/{board.total_mines}  Tiempo: {time_str}"
    )
    print()  # Empty line for spacing


def render_game_over(game_state: GameState, last_move: tuple = None):
    """Render game over screen with statistics and options."""
    board = game_state.board

    # Format elapsed time as MM:SS
    elapsed_seconds = int(game_state.elapsed_time())
    minutes = elapsed_seconds // 60
    seconds = elapsed_seconds % 60
    time_str = f"{minutes:02d}:{seconds:02d}"

    if game_state.won:
        print(colorize("¡GANASTE! 🎉", COLORS["success"]))
        print()
        print("Todas las minas encontradas")
        print(f"Tiempo: {time_str}")
    else:
        print(colorize("¡BOOM!", COLORS["error"]))
        if last_move:
            # Convert coordinates back to user format
            row, col = last_move
            col_letters = ""
            temp_col = col + 1  # Convert to 1-based
            while temp_col > 0:
                temp_col -= 1
                col_letters = chr(ord("A") + temp_col % 26) + col_letters
                temp_col //= 26
            coord_str = f"{col_letters}{row + 1}"
            print(colorize(f"Pisaste una mina en {coord_str}", COLORS["error"]))
        print()
        print(f"Banderas encontradas: {game_state.flags_placed}/{board.total_mines}")
        print(f"Tiempo total: {time_str}")

    print()
    print("[N]ueva partida")
    print("[S]alir")
