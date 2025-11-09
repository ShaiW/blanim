# blanim\blanim\blockDAGs\bitcoin\chain.py
"""
BitcoinDAG: Blockchain Visualization System
===========================================

Architecture Overview:
---------------------
This class manages Bitcoin blockchain visualization using a DAG (Directed Acyclic Graph)
structure where each block has at most one parent, forming a linear chain. The system
uses a shared configuration pattern where all blocks reference DEFAULT_BITCOIN_CONFIG
for consistent visual styling across the entire chain.

Key Design Principles:
- Config-driven styling: All visual properties (colors, opacities, stroke widths) are
  read from BitcoinBlockConfig to maintain a single source of truth for "neutral state"
- List-based parent lines: Following Kaspa's pattern, parent_lines is a list attribute
  (containing 0-1 elements for Bitcoin) for API consistency across DAG types
- Separation of concerns: BitcoinLogicalBlock handles graph structure/relationships,
  BitcoinVisualBlock handles Manim rendering, and BitcoinDAG orchestrates both

Highlighting System:
-------------------
The highlight_block_with_context() method visualizes block relationships by:
1. Fading unrelated blocks and their parent lines to fade_opacity
2. Highlighting context blocks (past/future cone) with colored strokes
3. Adding a pulsing white stroke to the focused block via updater
4. Flashing parent lines that connect blocks within the highlighted context

Reset is achieved by reading original values from config, ensuring blocks always
return to their defined neutral state without needing to store temporary state.

TODO / Future Improvements:
---------------------------
1. **Config-driven line properties**: Currently, some line operations use hardcoded
   parameters (e.g., opacity=1.0). These should read from config.line_stroke_opacity
   for consistency. This requires:
   - Ensuring all line creation/reset uses config values
   - Adding any missing line-related config fields (already have line_stroke_opacity)

2. **Label fading during highlighting**: Block labels currently don't fade with their
   parent blocks during highlighting. To implement:
   - In highlight_block_with_context(), add label fade animations:
     ```python
     block._visual.label.animate.set_fill(opacity=fade_opacity)
     ```
   - In reset_highlighting(), restore label opacity from config
   - May need to add label_opacity to BitcoinBlockConfig if not present

3. **Focused block parent line fading**: The focused block's parent line now correctly
   fades when the parent is outside the context (e.g., showing B1's future doesn't
   fade Genesis→B1 line). This was achieved by checking:
   ```python
   if focused_block.parent not in context_blocks:
       fade_animations.append(focused_block._visual.parent_lines[0].animate...)
"""

from __future__ import annotations

from typing import Optional, List, TYPE_CHECKING

import numpy as np
from manim import ParsableManimColor, YELLOW, ShowPassingFlash, cycle_animation, WHITE, Wait

from .logical_block import BitcoinLogicalBlock
from .layout_config import BitcoinLayoutConfig, DEFAULT_BITCOIN_LAYOUT_CONFIG

if TYPE_CHECKING:
    from ...core.hud_2d_scene import HUD2DScene

# noinspection PyProtectedMember
class BitcoinDAG:
    def __init__(self, scene: HUD2DScene, layout_config: BitcoinLayoutConfig = DEFAULT_BITCOIN_LAYOUT_CONFIG):
        self.scene = scene
        self.layout_config = layout_config
        self.blocks: dict[str, BitcoinLogicalBlock] = {}
        self.all_blocks: List[BitcoinLogicalBlock] = []
        self.genesis: Optional[BitcoinLogicalBlock] = None

    def add_block(
            self,
            name: str,
            parent: Optional[BitcoinLogicalBlock] = None,
            position: Optional[tuple[float, float]] = None
    ) -> BitcoinLogicalBlock:
        """Create and register a new block in the chain.

        Args:
            name: Unique identifier for the block
            parent: Parent block (None for genesis)
            position: (x, y) coordinates. If None, auto-calculated from layout_config

        Returns:
            The created BitcoinLogicalBlock
        """
        # Auto-calculate position if not provided
        if position is None:
            if parent is None:
                # Genesis block
                position = (self.layout_config.genesis_x, self.layout_config.genesis_y)
            else:
                # Calculate based on parent position + horizontal_spacing
                parent_pos = parent._visual.square.get_center()
                position = (
                    parent_pos[0] + self.layout_config.horizontal_spacing,
                    parent_pos[1]
                )

                # Create logical block (parent-child relationship auto-derived in __init__)
        block = BitcoinLogicalBlock(name=name, parent=parent, position=position)

        # Register in DAG
        self.blocks[name] = block
        self.all_blocks.append(block)

        # Track genesis
        if parent is None:
            self.genesis = block

        return block

    def get_block(self, name: str) -> Optional[BitcoinLogicalBlock]:
        """Retrieve a block by name."""
        return self.blocks.get(name)

    def play(self, *animations):
        """Wrapper around scene.play() for animation orchestration."""
        self.scene.play(*animations)

    def move(
            self,
            blocks: List[BitcoinLogicalBlock],
            positions: List[tuple[float, float]]
    ):
        """Move multiple blocks with deduplicated line updates.

        Args:
            blocks: List of blocks to move
            positions: Corresponding (x, y) positions
        """
        if len(blocks) != len(positions):
            raise ValueError("Number of blocks must match number of positions")

            # Collect affected lines (deduplicate)
        affected_lines = set()
        for block in blocks:
            # Collect parent line if it exists
            if block._visual.parent_lines:  # Fixed: check if list is non-empty
                affected_lines.add(block._visual.parent_lines[0])

                # Collect child lines
            for child in block.children:
                if child._visual.parent_lines:  # Fixed: check if list is non-empty
                    affected_lines.add(child._visual.parent_lines[0])

                    # Create movement animations
        move_animations = []
        for block, pos in zip(blocks, positions):
            target = np.array([pos[0], pos[1], 0])
            move_animations.append(
                block._visual.animate.move_to(target)
            )

            # Create line update animations (deduplicated)
        line_animations = [
            line.create_update_animation()
            for line in affected_lines
        ]

        # Combine and play
        all_animations = move_animations + line_animations
        if all_animations:
            self.scene.play(*all_animations)

    @staticmethod
    def get_past_cone(block: BitcoinLogicalBlock) -> List[BitcoinLogicalBlock]:
        """Get all ancestors via depth-first search."""
        past = set()
        to_visit = [block]

        while to_visit:
            current = to_visit.pop()
            if current.parent and current.parent not in past:
                past.add(current.parent)
                to_visit.append(current.parent)

        return list(past)

    @staticmethod
    def get_future_cone(block: BitcoinLogicalBlock) -> List[BitcoinLogicalBlock]:
        """Get all descendants via depth-first search."""
        future = set()
        to_visit = [block]

        while to_visit:
            current = to_visit.pop()
            for child in current.children:
                if child not in future:
                    future.add(child)
                    to_visit.append(child)

        return list(future)

    def get_anticone(self, block: BitcoinLogicalBlock) -> List[BitcoinLogicalBlock]:
        """Get blocks that are neither ancestors nor descendants."""
        past = set(self.get_past_cone(block))
        future = set(self.get_future_cone(block))

        return [
            b for b in self.all_blocks
            if b != block and b not in past and b not in future
        ]

    @staticmethod
    def create_pulse_updater(
            block: BitcoinLogicalBlock,
            original_width: Optional[float] = None,
            highlighted_width: float = 8
    ):
        """Create pulsing stroke width updater."""
        if original_width is None:
            original_width = block._visual.config.stroke_width

        def pulse_stroke(mob, dt):
            t = getattr(mob, 'time', 0) + dt
            mob.time = t
            width = original_width + (highlighted_width - original_width) * (
                    np.sin(t * np.pi) + 1
            ) / 2
            mob.set_stroke(WHITE, width=width)

        return pulse_stroke

    def highlight_block_with_context(
            self,
            focused_block: BitcoinLogicalBlock,
            context_blocks: Optional[List[BitcoinLogicalBlock]] = None,
            highlight_color: ParsableManimColor = YELLOW,
            fade_opacity: float = 0.3,
            flash_connections: bool = True
    ) -> List:
        """Highlight a block and its context with optional connection flashing.

        Returns:
            List of flash line copies that were added to the scene (for cleanup)
        """
        if context_blocks is None:
            context_blocks = []

            # Fade non-context blocks (always fade unrelated blocks)
        fade_animations = []
        for block in self.all_blocks:
            if block not in context_blocks and block != focused_block:
                fade_animations.extend([
                    block._visual.square.animate.set_fill(opacity=fade_opacity),
                    block._visual.square.animate.set_stroke(opacity=fade_opacity)
                ])
                for line in block._visual.parent_lines:
                    fade_animations.append(line.animate.set_stroke(opacity=fade_opacity))

                    # Fade focused block's parent line if parent is not in context
        if focused_block._visual.parent_lines:
            parent_block = focused_block.parent
            if parent_block and parent_block not in context_blocks:
                fade_animations.append(
                    focused_block._visual.parent_lines[0].animate.set_stroke(opacity=fade_opacity)
                )

        if fade_animations:
            self.scene.play(*fade_animations)

            # Add pulsing white stroke to focused block (using updater)
        pulse_updater = self.create_pulse_updater(focused_block)
        focused_block._visual.square.add_updater(pulse_updater)

        # Highlight context blocks with yellow stroke and increased width
        context_animations = []
        for block in context_blocks:
            context_animations.extend([
                block._visual.square.animate.set_stroke(
                    highlight_color,
                    width=block._visual.config.highlight_stroke_width
                )
            ])

        if context_animations:
            self.scene.play(*context_animations)
        else:
            # Play a minimal wait to commit the fade state
            self.scene.play(Wait(0.01))

            # Flash connections using cycle_animation (non-blocking)
        flash_lines = []
        if flash_connections:
            for block in context_blocks:
                if block._visual.parent_lines:
                    # Create a copy of the line with highlight color
                    flash_line = block._visual.parent_lines[0].copy().set_color(highlight_color)
                    self.scene.add(flash_line)
                    flash_lines.append(flash_line)

                    # Apply cycle_animation to make it flash
                    cycle_animation(
                        ShowPassingFlash(flash_line, time_width=0.5, run_time=1.5)
                    )

                    # Flash focused block's parent line only if parent is in context
            if focused_block._visual.parent_lines and focused_block.parent in context_blocks:
                flash_line = focused_block._visual.parent_lines[0].copy().set_color(highlight_color)
                self.scene.add(flash_line)
                flash_lines.append(flash_line)
                cycle_animation(
                    ShowPassingFlash(flash_line, time_width=0.5, run_time=1.5)
                )

                # Return the flash line copies (not originals) for cleanup
        return flash_lines

    def reset_highlighting(
            self,
            focused_block: BitcoinLogicalBlock,
            context_blocks: Optional[List[BitcoinLogicalBlock]] = None,
            flash_lines: Optional[List] = None
    ):
        """Reset all highlighting effects."""
        # Remove flash lines from scene
        if flash_lines:
            self.scene.remove(*flash_lines)

            # Remove pulse updater from focused block
        if focused_block._visual.square.updaters:
            focused_block._visual.square.remove_updater(
                focused_block._visual.square.updaters[-1]
            )

            # Get context blocks if not provided
        if context_blocks is None:
            context_blocks = []

            # Reset all blocks to original styling
        reset_animations = []
        for block in self.all_blocks:
            reset_animations.extend([
                block._visual.square.animate.set_fill(
                    opacity=block._visual.config.fill_opacity
                ),
                block._visual.square.animate.set_stroke(
                    block._visual.config.stroke_color,
                    width=block._visual.config.stroke_width,
                    opacity=block._visual.config.stroke_opacity
                )
            ])
            for line in block._visual.parent_lines:
                reset_animations.append(
                    line.animate.set_stroke(
                        block._visual.config.line_color,
                        width=block._visual.config.line_stroke_width,
                        opacity=block._visual.config.line_stroke_opacity
                    )
                )

        if reset_animations:
            self.scene.play(*reset_animations)

    def highlight_block_context(
            self,
            focused_block: BitcoinLogicalBlock,
            show_past: bool = True,
            show_future: bool = False,
            show_anticone: bool = False,
            highlight_color: ParsableManimColor = YELLOW,
            fade_opacity: float = 0.1
    ) -> Optional[List]:
        """Convenience method to highlight block with graph context."""
        context_blocks = []

        if show_past:
            context_blocks.extend(self.get_past_cone(focused_block))
        if show_future:
            context_blocks.extend(self.get_future_cone(focused_block))
        if show_anticone:
            context_blocks.extend(self.get_anticone(focused_block))

        # Remove duplicates
        seen = set()
        context_blocks = [
            b for b in context_blocks if not (b in seen or seen.add(b))
        ]

        return self.highlight_block_with_context(
            focused_block=focused_block,
            context_blocks=context_blocks,
            highlight_color=highlight_color,
            fade_opacity=fade_opacity,
            flash_connections=True
        )