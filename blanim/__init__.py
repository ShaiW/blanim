"""Blanim: Blockchain Animation Library

This module extends Manim with blockchain-specific visualization tools.

IMPORT STRATEGY:
----------------
We re-export all Manim classes (from manim import *) to provide a unified
import experience. Users only need `from blanim import *` to access both:
- All Manim primitives (Circle, Square, Create, Transform, etc.)
- All blanim blockchain classes (BitcoinVisualBlock, KaspaVisualBlock, etc.)

WHY RE-EXPORT MANIM:
--------------------
This eliminates the need for double imports (`from manim import *` +
`from blanim import *`) in scene files. While this creates namespace overlap,
it provides better developer experience by treating blanim as a complete
animation framework rather than just an extension library.

STRUCTURE:
----------
- core/: Base infrastructure (HUD2DScene, BaseVisualBlock, etc.)
- blockDAGs/: Blockchain-specific implementations (bitcoin/, kaspa/, etc.)
- utils/: Shared utilities

USAGE:
------
    from blanim import *

    class MyScene(HUD2DScene):
        def construct(self):
            # Access Manim classes directly
            circle = Circle()
            # Access blanim classes directly
            block = BitcoinVisualBlock()
            self.play(Create(circle), Create(block))
"""

# blanim/__init__.py
from manim import *  # Re-export all Manim classes  # noqa: F401, F403
from .core import *
from .blockDAGs.bitcoin import *
from .blockDAGs.kaspa import *