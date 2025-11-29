# blanim/blanim/__main__.py

from __future__ import annotations

from manim.__main__ import main as manim_main
from manim import config

def main():
    """Blanim CLI - blockchain animation with Manim.

    Wrapper around Manim's CLI with blockchain-optimized defaults.
    """
    # Optional: Set blanim-specific defaults
    # config.background_color = "#1a1a1a"  # Example default

    # Delegate to Manim's CLI
    manim_main()

if __name__ == "__main__":
    main()