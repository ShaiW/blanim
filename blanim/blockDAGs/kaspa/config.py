# blanim\blanim\blockDAGs\kaspa\config.py

from dataclasses import dataclass
from manim import BLUE, WHITE, ParsableManimColor, PURE_BLUE, YELLOW, GREEN
from ...core.base_config import BaseBlockConfig

__all__ = ["DEFAULT_KASPA_CONFIG", "KaspaBlockConfig"]


@dataclass
class KaspaBlockConfig(BaseBlockConfig):
    """Configuration for Kaspa block visualization."""
    # Visual styling (same as Bitcoin)
    block_color: ParsableManimColor = "#49EACB"
    fill_opacity: float = 0.7
    stroke_color: ParsableManimColor = PURE_BLUE
    stroke_width: float = 3
    side_length: float = 0.7

    # Label styling
    label_font_size: int = 24
    label_color: ParsableManimColor = WHITE

    # Animation timing
    create_run_time: float = 2.0
    label_change_run_time: float = 1.0
    movement_run_time: float = 1.0

    # Highlighting parameters
    highlight_color: ParsableManimColor = GREEN
    highlight_stroke_width: float = 8
    highlight_run_time: float = 0.5

    # Line styling (Kaspa-specific: multiple parents)
    selected_parent_color: ParsableManimColor = PURE_BLUE  # First parent
    other_parent_color: ParsableManimColor = BLUE  # Other parents
    line_stroke_width: float = 5

# Default configuration instance
DEFAULT_KASPA_CONFIG = KaspaBlockConfig()