# blanim\blanim\blockDAGs\bitcoin\config.py

from dataclasses import dataclass
from manim import BLUE, WHITE, ParsableManimColor
from manim.utils.color.X11 import PURPLE

from ...core.base_config import BaseBlockConfig

__all__ = ["DEFAULT_BITCOIN_CONFIG", "BitcoinBlockConfig"]

@dataclass
class BitcoinBlockConfig(BaseBlockConfig):
    """Configuration for Bitcoin block visualization."""
    # Visual styling
    block_color: ParsableManimColor = BLUE
    fill_opacity: float = 0.2
    stroke_color: ParsableManimColor = BLUE
    stroke_width: float = 3
    stroke_opacity: float = 1.0
    side_length: float = 0.7
    line_stroke_opacity: float = 1.0

    # Label styling
    label_font_size: int = 24
    label_color: ParsableManimColor = WHITE

    # Animation timing
    create_run_time: float = 2.0
    label_change_run_time: float = 1.0
    movement_run_time: float = 1.0

    # Highlighting parameters
    highlight_color: ParsableManimColor = PURPLE
    highlight_stroke_width: float = 8
    highlight_run_time: float = 0.5

    # Line styling (Bitcoin-specific: single parent)
    line_color: ParsableManimColor = BLUE
    line_stroke_width: float = 5

# Default configuration instance
DEFAULT_BITCOIN_CONFIG = BitcoinBlockConfig()