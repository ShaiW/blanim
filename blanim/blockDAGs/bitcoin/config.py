# blanim\blanim\blockDAGs\bitcoin\config.py

from dataclasses import dataclass
from manim import BLUE, WHITE, ParsableManimColor

__all__ = ["DEFAULT_BITCOIN_CONFIG", "BitcoinBlockConfig"]

@dataclass
class BitcoinBlockConfig:
    """Configuration for Bitcoin block visualization."""
    # Visual styling
    block_color: ParsableManimColor = BLUE
    fill_opacity: float = 0.2
    stroke_color: ParsableManimColor = BLUE
    stroke_width: float = 3
    side_length: float = 0.7

    # Label styling
    label_font_size: int = 24
    label_color: ParsableManimColor = WHITE

    # Animation timing
    create_run_time: float = 2.0
    label_change_run_time: float = 1.0
    movement_run_time: float = 1.0

    # Line styling (Bitcoin-specific: single parent)
    line_color: ParsableManimColor = BLUE
    line_stroke_width: float = 5

# Default configuration instance
DEFAULT_BITCOIN_CONFIG = BitcoinBlockConfig()