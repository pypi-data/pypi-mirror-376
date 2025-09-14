import click

from .commands import Command, parse_command, validate_command
from .game import (
    check_victory,
    initialize_game,
    reveal_all_mines,
    reveal_cell,
    toggle_flag,
)
from .renderer import (
    COLORS,
    clear_screen,
    colorize,
    render_board,
    render_game_info,
    render_game_over,
)


def game_loop(level: str) -> None:
    """Main game loop with command input and processing."""
    # Initialize game with mines and adjacent counts
    game_state = initialize_game(level)
    message = ""
    last_mine_position = None

    try:
        while True:
            # Clear screen and render game state
            clear_screen()

            # If game is over, reveal all mines and show exploded position
            if game_state.is_game_over and not game_state.won:
                reveal_all_mines(game_state)
                render_board(game_state, last_mine_position)
            else:
                render_board(game_state)

            render_game_info(game_state)

            # Show message if there's one
            if message:
                print(f"\n{message}")
                message = ""  # Clear message after showing

            # Handle end game state
            if game_state.is_game_over:
                print()
                render_game_over(game_state, last_mine_position)
                user_input = input("> ").strip().lower()

                if user_input in ["n", "nueva", "new"]:
                    game_state = initialize_game(level)  # Start new game
                    last_mine_position = None
                    message = colorize("Nueva partida iniciada", COLORS["success"])
                    continue
                elif user_input in ["s", "salir", "quit", "exit"]:
                    break
                else:
                    message = colorize(
                        "Opción no válida. Use [N]ueva o [S]alir", COLORS["error"]
                    )
                    continue
            else:
                # Normal game input
                print(
                    "\nComandos disponibles: reveal <coord>, flag <coord>, help, quit"
                )
                user_input = input("> ").strip()

            # Parse and validate command
            command, coordinate = parse_command(user_input)
            error_message = validate_command(command, coordinate, game_state)

            if error_message:
                message = colorize(error_message, COLORS["error"])
                continue

            # Process valid commands
            if command == Command.QUIT:
                break
            elif command == Command.HELP:
                # Show comprehensive help that stays on screen
                clear_screen()
                print(colorize("=== AYUDA DEL JUEGO BUSCAMINAS ===", COLORS["info"]))
                print()
                print(colorize("COMANDOS DISPONIBLES:", COLORS["success"]))
                print("  reveal <coord> o r <coord> - Revelar casilla")
                print("    Ejemplo: reveal A1, r B3")
                print("  flag <coord> o f <coord>   - Colocar/quitar bandera")
                print("    Ejemplo: flag C2, f A5")
                print("  help o h o ?               - Mostrar esta ayuda")
                print("  quit o q                   - Salir del juego")
                print()
                print(colorize("FORMATO DE COORDENADAS:", COLORS["success"]))
                print("  Use Letra+Número: A1, B3, AA15, etc.")
                print("  Columnas: A-Z, luego AA-AZ, BA-BZ, etc.")
                print("  Filas: 1, 2, 3, ...")
                print()
                print(colorize("CÓMO JUGAR:", COLORS["success"]))
                print("  - Revelar todas las casillas que no tienen minas")
                print("  - Los números indican cuántas minas hay alrededor")
                print("  - Usa banderas para marcar donde crees que hay minas")
                print("  - ¡Cuidado! Si revelas una mina, pierdes")
                print()
                input(colorize("Presiona Enter para continuar...", COLORS["info"]))
                message = ""  # Clear message since we showed help screen
            elif command == Command.REVEAL:
                row, col = coordinate
                if reveal_cell(game_state, row, col):
                    if game_state.is_game_over:
                        if not game_state.won:
                            # Store the position where the mine exploded
                            last_mine_position = (row, col)
                    else:
                        # Check for victory after revealing
                        check_victory(game_state)
                        if game_state.won:
                            message = colorize("¡GANASTE! 🎉", COLORS["success"])
                        else:
                            message = ""  # Don't show message for successful reveals
                else:
                    # This case should be caught by validation now
                    message = colorize("Esa casilla ya está revelada", COLORS["error"])
            elif command == Command.FLAG:
                row, col = coordinate
                if toggle_flag(game_state, row, col):
                    cell = game_state.board.get_cell(row, col)
                    if cell.has_flag:
                        message = colorize("Bandera colocada", COLORS["info"])
                    else:
                        message = colorize("Bandera quitada", COLORS["info"])
                else:
                    message = colorize(
                        "No se puede colocar bandera en esa casilla", COLORS["error"]
                    )
            elif command == Command.NEW:
                if game_state.is_game_over:
                    game_state = initialize_game(level)
                    message = colorize("Nueva partida iniciada", COLORS["success"])
            elif command == Command.INVALID:
                message = colorize(
                    "Comando no reconocido. Use 'help' para ver comandos",
                    COLORS["error"],
                )

    except KeyboardInterrupt:
        print("\n\nJuego interrumpido. ¡Hasta pronto!")


@click.command()
@click.option(
    "--level",
    type=click.Choice(["easy", "medium", "hard"]),
    default="easy",
    help="Difficulty level (easy=8x8/10 minas, medium=16x16/40 minas, hard=30x16/99 minas)",
)
@click.version_option(version="1.0.0", prog_name="minesweeper-cli")
def cli(level):
    """Buscaminas CLI - Classic Minesweeper for the terminal"""
    level_info = {
        "easy": "8x8, 10 minas",
        "medium": "16x16, 40 minas",
        "hard": "30x16, 99 minas",
    }

    print(colorize("=== BUSCAMINAS CLI ===", COLORS["info"]))
    print(f"Nivel: {level.capitalize()} ({level_info[level]})")
    print("Presiona Ctrl+C en cualquier momento para salir")
    print()
    game_loop(level)


if __name__ == "__main__":
    cli()
