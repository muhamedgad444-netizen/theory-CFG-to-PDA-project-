# CFG to PDA Converter

A Context-Free Grammar (CFG) to Pushdown Automaton (PDA) converter, built as **Project 02** for the **CSCI419 - Theory of Computation** course. 

This application takes a Context-Free Grammar as input and automatically converts it into an equivalent Pushdown Automaton, providing a step-by-step breakdown, a formal definition of the resulting PDA, a transition table, and an interactive state diagram.

## Features

- **Standard Conversion Algorithm:** Implements the classic 5-step CFG-to-PDA conversion algorithm as taught in Tutorial 08.
- **Pure Python GUI:** Built entirely with Python's standard `tkinter` library. **No external dependencies** or third-party libraries (like PyQt, CustomTkinter, or Matplotlib) are used, adhering strictly to the project guidelines.
- **Dynamic State Diagram:** Renders a clear, auto-scaled visual diagram of the PDA states (`q_start`, `q1`, `q_loop`, `q_accept`) and their transitions directly on a Canvas.
- **Detailed Output:** 
  - Parsed CFG
  - Conversion Steps
  - PDA Formal Definition
  - Full Transition Table
- **Pre-loaded Examples:** Includes quick buttons to load common grammar examples.

## Requirements

- Python 3.x
- `tkinter` (comes pre-installed with standard Python distributions)

## How to Run

1. Clone the repository or download the source code.
2. Run the main script from your terminal or command prompt:

```bash
python cfg_to_pda.py
```

## Input Format

When entering a grammar in the application:
- Use `→` or `->` for productions (e.g., `S -> aTb`).
- Use `|` to separate alternative bodies (e.g., `S -> aTb | b`).
- Use `ε` or `eps` for epsilon/empty string.
- Variables must be single uppercase letters (`A-Z`).
- Terminals can be lowercase letters or digits (`a-z`, `0-9`).
