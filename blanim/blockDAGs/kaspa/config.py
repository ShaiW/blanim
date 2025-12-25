# blanim\blanim\blockDAGs\kaspa\config.py

from dataclasses import dataclass
from typing import TypedDict

from manim import BLUE, WHITE, ParsableManimColor, YELLOW, GREEN, PURPLE, RED, logger
from ...core.base_config import BaseBlockConfig

__all__ = ["DEFAULT_KASPA_CONFIG", "KaspaConfig", "_KaspaConfigInternal"]

#TODO finish refactoring kaspa to use this consistently
#TODO ensure parameters are identical in both

# Public TypedDict for user type hints
class KaspaConfig(TypedDict, total=False):
    """Typed configuration for Kaspa blockDAG visualization."""
    # GHOSTDAG Parameters
    k: int

    # Visual Styling - Block Appearance
    block_color: ParsableManimColor
    fill_opacity: float
    stroke_color: ParsableManimColor
    stroke_width: float
    stroke_opacity: float
    side_length: float

    # Visual Styling - Label Appearance
    label_font_size: int
    label_color: ParsableManimColor
    label_opacity: float
    label_type: str #TODO figure out how to typehint this

    # Visual Styling - Line Appearance
    selected_parent_line_color: ParsableManimColor
    other_parent_line_color: ParsableManimColor
    line_stroke_width: float
    line_stroke_opacity: float

    # Animation Timing
    create_run_time: float
    label_change_run_time: float
    movement_run_time: float
    camera_follow_time: float

    # Highlighting Behavior
    context_block_color: ParsableManimColor
    context_block_cycle_time: float
    context_block_stroke_width: float
    highlight_block_color: ParsableManimColor
    highlight_line_color: ParsableManimColor
    highlight_stroke_width: float
    fade_opacity: float
    flash_connections: bool
    highlight_line_cycle_time: float

    # Spatial Layout
    genesis_x: float
    genesis_y: float
    horizontal_spacing: float
    vertical_spacing: float

    # GHOSTDAG-specific colors
    ghostdag_parent_stroke_highlight_color: ParsableManimColor
    ghostdag_parent_line_highlight_color: ParsableManimColor
    ghostdag_selected_parent_stroke_color: ParsableManimColor
    ghostdag_parent_stroke_highlight_width: int
    ghostdag_selected_parent_fill_color: ParsableManimColor
    ghostdag_mergeset_color: ParsableManimColor
    ghostdag_order_color: ParsableManimColor
    ghostdag_blue_color: ParsableManimColor
    ghostdag_red_color: ParsableManimColor
    ghostdag_highlight_width: int
    ghostdag_selected_parent_stroke_width: int
    ghostdag_mergeset_stroke_width: int
    ghostdag_selected_parent_opacity: float
    ghostdag_blue_opacity: float
    ghostdag_red_opacity: float
    ghostdag_selected_fill: ParsableManimColor

@dataclass
class _KaspaConfigInternal(BaseBlockConfig):
    """Complete configuration for Kaspa blockDAG visualization.

    Combines visual styling and spatial layout into a single config.
    Each section is clearly separated for maintainability.

    WARNING opacity must ALWAYS be > 0
    """

    # ========================================
    # GHOSTDAG - Parameter
    # ========================================
    k: int = 18

    # ========================================
    # GHOSTDAG - GhostDAG-specific colors and styling
    # ========================================

    ghostdag_parent_stroke_highlight_color = YELLOW
    ghostdag_parent_line_highlight_color = YELLOW
    ghostdag_selected_parent_stroke_color = GREEN
    ghostdag_parent_stroke_highlight_width = 6
    ghostdag_selected_parent_fill_color = BLUE #SP becomes BLUE by default in GHOSTDAG, rec leaving this alone.

    ghostdag_mergeset_color = PURPLE
    ghostdag_order_color = GREEN
    ghostdag_blue_color = BLUE
    ghostdag_red_color = RED

    ghostdag_highlight_width = 4
#    ghostdag_line_width = 3
    ghostdag_selected_parent_stroke_width = 6
    ghostdag_mergeset_stroke_width = 3

    ghostdag_selected_parent_opacity = 0.6
    ghostdag_blue_opacity = 0.6
    ghostdag_red_opacity = 0.6
    ghostdag_selected_fill = BLUE

    # ========================================
    # VISUAL STYLING - Block Appearance
    # ========================================
    block_color: ParsableManimColor = WHITE  #NOTE if block color is BLUE, the is no visible change during GHOSTDAG coloring animation.
    fill_opacity: float = 0.3
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
    label_type: str = 'bluescore'

    # ========================================
    # VISUAL STYLING - Line Appearance
    # ========================================
    selected_parent_line_color: ParsableManimColor = BLUE
    other_parent_line_color: ParsableManimColor = WHITE
    line_stroke_width: float = 4
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
    context_block_color: ParsableManimColor = YELLOW # Color of pulsing stroke
    context_block_cycle_time: float = 2.0  # Seconds per complete pulse cycle
    context_block_stroke_width: float = 8

    # Highlight blocks with relationships to the Context Block
    highlight_block_color: ParsableManimColor = YELLOW
    highlight_line_color = YELLOW
    highlight_stroke_width: float = 8

    fade_opacity: float = 0.1 # Opacity to fade unrelated blocks(and lines) to during a highlight animation

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

    def __post_init__(self):
        """Validate and auto-correct values with warnings."""
        # Auto-correct opacity values
        if self.fill_opacity <= 0:
            logger.warning("fill_opacity must be > 0, auto-correcting to 0.01")
            self.fill_opacity = 0.01
        elif self.fill_opacity > 1.0:
            logger.warning("fill_opacity must be <= 1.0, auto-correcting to 1.0")
            self.fill_opacity = 1.0

        if self.stroke_opacity <= 0:
            logger.warning("stroke_opacity must be > 0, auto-correcting to 0.01")
            self.stroke_opacity = 0.01
        elif self.stroke_opacity > 1.0:
            logger.warning("stroke_opacity must be <= 1.0, auto-correcting to 1.0")
            self.stroke_opacity = 1.0

        if self.fade_opacity < 0:
            logger.warning("fade_opacity must be >= 0, auto-correcting to 0")
            self.fade_opacity = 0
        elif self.fade_opacity > 1.0:
            logger.warning("fade_opacity must be <= 1.0, auto-correcting to 1.0")
            self.fade_opacity = 1.0

            # Auto-correct other critical values
        if self.stroke_width < 1:
            logger.warning("stroke_width must be >= 1, auto-correcting to 0")
            self.stroke_width = 1

        if self.k < 0:
            logger.warning("k must be >= 0, auto-correcting to 0")
            self.k = 0

        # Default configuration instance
DEFAULT_KASPA_CONFIG = _KaspaConfigInternal()