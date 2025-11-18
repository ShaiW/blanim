# blanim\blanim\blockDAGs\kaspa\config.py

from dataclasses import dataclass
from manim import BLUE, WHITE, ParsableManimColor
from ...core.base_config import BaseBlockConfig

__all__ = ["DEFAULT_KASPA_CONFIG", "KaspaConfig"]


@dataclass
class KaspaConfig(BaseBlockConfig):
    """Complete configuration for Kaspa blockDAG visualization.

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
    selected_parent_line_color: ParsableManimColor = WHITE
    other_parent_line_color: ParsableManimColor = WHITE
    line_stroke_width: float = 5
    line_stroke_opacity: float = 1.0

    # ========================================
    # ANIMATION TIMING
    # ========================================
    create_run_time: float = 2.0
    label_change_run_time: float = 1.0
    movement_run_time: float = 1.0
    camera_follow_time: float = 1.0

    # ========================================
    # HIGHLIGHTING BEHAVIOR
    # ========================================
    # Context Block is the block we show relationships of during highlighting
    context_block_color: ParsableManimColor = WHITE # Color of pulsing stroke
    context_block_cycle_time: float = 2.0  # Seconds per complete pulse cycle
    context_block_stroke_width: float = 8

    # Highlight blocks with relationships to the Context Block
    highlight_color: ParsableManimColor = "#70C7BA"
    highlight_stroke_width: float = 8

    fade_opacity: float = 0.3 # Opacity to fade unrelated blocks to during a highlight animation

    flash_connections: bool = True # Directional flash animation cycling on lines
    highlight_line_cycle_time = 1 # Time for a single flash to pass on lines

    # ========================================
    # SPATIAL LAYOUT - Genesis Position
    # ========================================
    genesis_x: float = -5.5
    genesis_y: float = 0.0

    # ========================================
    # SPATIAL LAYOUT - Block Spacing
    # ========================================
    horizontal_spacing: float = 2.0
    vertical_spacing: float = 1.0  # For parallel blocks during forks

# Default configuration instance
DEFAULT_KASPA_CONFIG = KaspaBlockConfig()