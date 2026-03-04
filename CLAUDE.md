# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

`mj-agent` is a Python 3.13 project managed with `uv`.

## Commands

```bash
# Install dependencies / sync environment
uv sync

# Run the project
uv run python main.py

# Add a dependency
uv add <package>

# Run a script or tool in the project environment
uv run <command>
```

## Architecture

The project is a minimal scaffold. `main.py` is the entry point containing a `main()` function. As the project grows, structure should be added here.
