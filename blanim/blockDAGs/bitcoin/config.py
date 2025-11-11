# blanim/blanim/blockDAGs/bitcoin/config.py

from __future__ import annotations

from dataclasses import dataclass
from manim import BLUE, WHITE, PURPLE, ParsableManimColor

from ...core.base_config import BaseBlockConfig

__all__ = ["DEFAULT_BITCOIN_CONFIG", "BitcoinConfig"]


@dataclass
class BitcoinConfig(BaseBlockConfig):
    """Complete configuration for Bitcoin blockchain visualization.

    Combines visual styling and spatial layout into a single config.
    Each section is clearly separated for maintainability.
    """

    # ========================================
    # VISUAL STYLING - Block Appearance
    # ========================================
    block_color: ParsableManimColor = BLUE
    fill_opacity: float = 0.2
    stroke_color: ParsableManimColor = BLUE
    stroke_width: float = 3
    stroke_opacity: float = 1.0
    side_length: float = 0.7

    # ========================================
    # VISUAL STYLING - Label Appearance
    # ========================================
    label_font_size: int = 24
    label_color: ParsableManimColor = WHITE
    label_opacity: float = 1.0

    # ========================================
    # VISUAL STYLING - Line Appearance
    # ========================================
    line_color: ParsableManimColor = BLUE
    line_stroke_width: float = 5
    line_stroke_opacity: float = 1.0

    # ========================================
    # ANIMATION TIMING
    # ========================================
    create_run_time: float = 2.0
    label_change_run_time: float = 1.0
    movement_run_time: float = 1.0

    # ========================================
    # HIGHLIGHTING BEHAVIOR
    # ========================================
    highlight_color: ParsableManimColor = PURPLE
    highlight_stroke_width: float = 8
    highlight_run_time: float = 0.5
    fade_opacity: float = 0.3
    context_block_color: ParsableManimColor = WHITE
    flash_connections: bool = True

    # ========================================
    # SPATIAL LAYOUT - Genesis Position
    # ========================================
    genesis_x: float = -6.5
    genesis_y: float = 0.0

    # ========================================
    # SPATIAL LAYOUT - Block Spacing
    # ========================================
    horizontal_spacing: float = 2.0
    vertical_spacing: float = 1.0  # For parallel blocks during forks

# Default configuration instance
DEFAULT_BITCOIN_CONFIG = BitcoinConfig()