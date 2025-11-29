# blanim\blanim\core\base_config.py

from dataclasses import dataclass
from manim import BLUE, WHITE, YELLOW, ParsableManimColor, PURE_BLUE

__all__ = ["BaseBlockConfig"]

@dataclass
class BaseBlockConfig:
    """Base configuration for blockchain block visualization.

    All blockchain-specific configs (Bitcoin, Kaspa, etc.) should inherit
    from this class to ensure compatibility with BaseVisualBlock.
    """
    # Visual styling
    block_color: ParsableManimColor = BLUE
    fill_opacity: float = 0.2
    stroke_color: ParsableManimColor = PURE_BLUE
    stroke_width: float = 3
    stroke_opacity: float = 1.0
    side_length: float = 0.7
    line_stroke_opacity: float = 1.0  #TODO add config support for parent lines

    # Label styling
    label_font_size: int = 24
    label_color: ParsableManimColor = WHITE
    label_opacity: float = 1.0

    # Animation timing
    create_run_time: float = 2.0
    label_change_run_time: float = 1.0
    movement_run_time: float = 1.0

    # Highlighting parameters
    highlight_color: ParsableManimColor = YELLOW
    highlight_stroke_width: float = 8
    highlight_run_time: float = 0.5
    fade_opacity: float = 0.3
    context_block_color: ParsableManimColor = WHITE
    flash_connections: bool = True
