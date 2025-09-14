# Minesweeper CLI 💣

Classic Minesweeper game for the terminal, built with Python. Features colorful interface, multiple difficulty levels, and intuitive commands.

## 🎮 Game Preview

```
    A  B  C  D  E  F  G  H
  ┌─────────────────────────┐
1 │ ⬛ ⬛ ⬛ ⬛ ⬛ ⬛ ⬛ ⬛ │
2 │ ·  1  1  2  ⬛ ⬛ ⬛ ⬛ │
3 │ ·  1  🚩 2  ⬛ ⬛ ⬛ ⬛ │
4 │ ·  1  1  2  ⬛ ⬛ ⬛ ⬛ │
5 │ ·  ·  ·  1  ⬛ ⬛ ⬛ ⬛ │
6 │ 1  1  ·  ·  ⬛ ⬛ ⬛ ⬛ │
7 │ ⬛ 1  ·  ·  ⬛ ⬛ ⬛ ⬛ │
8 │ ⬛ 1  ·  ·  ⬛ ⬛ ⬛ ⬛ │
  └─────────────────────────┘

Banderas: 1/10  Tiempo: 2:34

> reveal D5
```

## 🚀 Installation

### Use [uv](https://github.com/astral-sh/uv)

```bash
uv tool install minesweeper-cli
```

## 🎯 Usage

### Basic Commands

```bash
# Run with default easy level
minesweeper

# Run with specific difficulty
minesweeper --level medium
minesweeper --level hard

# Show version
minesweeper --version

# Show help
minesweeper --help
```

### Difficulty Levels

| Level | Grid Size | Mines | Description |
|-------|-----------|-------|-------------|
| **Easy** | 8×8 | 10 | Perfect for beginners |
| **Medium** | 16×16 | 40 | Balanced challenge |
| **Hard** | 30×16 | 99 | Expert level |

## 🎮 How to Play

### In-Game Commands

| Command | Aliases | Example | Description |
|---------|---------|---------|-------------|
| `reveal <coord>` | `r <coord>` | `reveal A1` | Reveal a cell |
| `flag <coord>` | `f <coord>` | `flag B3` | Place/remove flag |
| `help` | `h`, `?` | `help` | Show help screen |
| `quit` | `q` | `quit` | Exit game |
| `new` | `n` | `new` | New game (end game only) |

### Coordinate System

- **Columns**: Letters (A-Z, then AA-AZ, BA-BZ, etc.)
- **Rows**: Numbers (1, 2, 3, ...)
- **Format**: Letter + Number

**Examples**: `A1`, `B3`, `AA15`, `AD30`

### Game Symbols

| Symbol | Meaning | Color |
|--------|---------|-------|
| ⬛ | Unrevealed cell | Blue |
| · | Empty revealed cell | White |
| 🚩 | Flag | - |
| 💥 | Exploded mine | - |
| 💣 | Mine (shown when game ends) | Red |
| 1-8 | Adjacent mine count | Various* |

*Number colors: 1=Cyan, 2=Green, 3=Yellow, 4=Magenta, 5=Red, 6=Cyan, 7=White, 8=Red

### Gameplay Rules

1. **Goal**: Reveal all cells that don't contain mines
2. **Numbers**: Show how many mines are adjacent to that cell
3. **Flags**: Use to mark suspected mine locations
4. **Cascade**: Empty cells automatically reveal adjacent empty areas
5. **Game Over**: Revealing a mine ends the game
6. **Victory**: Reveal all non-mine cells to win

## 📋 Game Examples

### Easy Game Session

```
    A  B  C  D  E  F  G  H
  ┌─────────────────────────┐
1 │ 1  1  ·  ·  ·  ·  1  ⬛ │
2 │ 💣 1  ·  ·  ·  ·  1  ⬛ │
3 │ 1  1  ·  ·  ·  ·  1  ⬛ │
4 │ ·  ·  ·  ·  ·  ·  1  ⬛ │
5 │ ·  ·  ·  ·  ·  ·  1  ⬛ │
6 │ ·  ·  ·  ·  ·  ·  1  ⬛ │
7 │ 1  1  1  1  1  1  2  ⬛ │
8 │ ⬛ ⬛ ⬛ ⬛ ⬛ ⬛ ⬛ ⬛│
  └─────────────────────────┘

¡BOOM! 
Pisaste una mina en A2

Banderas encontradas: 0/10
Tiempo total: 1:23

[N]ueva partida
[S]alir
```

### Victory Screen

```
¡GANASTE! 🎉

Todas las minas encontradas
Tiempo: 5:23

[N]ueva partida
[S]alir
```

## 🛠️ Development

### Setup Development Environment

```bash
# Clone repository
git clone <repository-url>
cd minesweeper-cli

# Setup with uv (recommended)
uv venv
source .venv/bin/activate
uv pip install -e .

# Or setup with pip
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

### Install using uv (recommended)

```bash
# Install uv if you haven't already
curl -LsSf https://astral.sh/uv/install.sh | sh

# Create virtual environment and install
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
uv pip install -e .
```

### Using pip

```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install in development mode
pip install -e .
```

### Run Tests

```bash
# When tests are implemented
uv run pytest tests/

# Code quality checks
uv run ruff src/ --check
uv run black src/ --check
uv run mypy src/
```

### Project Structure

```
minesweeper-cli/
├── src/
│   └── minesweeper/
│       ├── __init__.py
│       ├── main.py          # CLI entry point and main game loop
│       ├── game.py          # Game logic and state management
│       ├── models.py        # Data structures (Cell, Board, GameState)
│       ├── renderer.py      # Display and visualization
│       └── commands.py      # Command parsing and validation
├── examples/
│   └── play_example.py      # Programmatic usage examples
├── tests/                   # Test files (to be implemented)
├── docs/                    # Design documents
├── pyproject.toml          # Project configuration
├── README.md               # This file
└── LICENSE                 # GPLv3 License
```

## 🧩 Examples

See `examples/play_example.py` for programmatic usage:

```bash
python examples/play_example.py
```

This shows how to:
- Create games programmatically
- Make automated moves
- Integrate game logic into other applications

## 🔧 Requirements

- Python 3.9 or higher
- Click 8.0+ (CLI framework)
- Colorama 0.4+ (terminal colors)

## 📜 License

This project is licensed under the GPLv3 License - see the [LICENSE](LICENSE) file for details.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

### Current Features ✅

- [x] Three difficulty levels (Easy, Medium, Hard)
- [x] Colorful terminal interface
- [x] Intuitive command system
- [x] Flag placement and removal
- [x] Cascade reveal for empty areas
- [x] Win/lose detection
- [x] Game timer
- [x] Cross-platform support

### Future Enhancements 🚀

- [ ] Improvements on UX (revealing a number should auto-reveal adjacent free cells and other numbers)
- [ ] Save/load game state
- [ ] Statistics and best times
- [ ] Custom difficulty levels
- [ ] Hint system

## 📞 Support

If you encounter any issues or have questions:

1. Check the in-game help: `help` command
2. Review this README
3. Check the examples in `examples/`
4. Open an issue on Gitlab

---

**Happy Minesweeping! 💣🎮**
