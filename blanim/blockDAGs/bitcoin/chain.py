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
- Unified config: All visual properties (colors, opacities, stroke widths) and layout
  parameters (genesis position, spacing) are read from BitcoinConfig
- List-based parent lines: Following Kaspa's pattern, parent_lines is a list attribute
  (containing 0-1 elements for Bitcoin) for API consistency across DAG types
- Separation of concerns: BitcoinLogicalBlock handles graph structure/relationships,
  BitcoinVisualBlock handles Manim rendering, and BitcoinDAG orchestrates both
- Animation delegation: DAG methods call visual block animation methods rather than
  directly manipulating Manim objects, ensuring consistent animation behavior

Block Lifecycle:
---------------
1. **Creation**: add_block() creates a BitcoinLogicalBlock and plays its
   create_with_lines() animation, which handles block, label, and parent line creation
2. **Movement**: move() delegates to visual block's create_movement_animation(), which
   automatically updates connected parent and child lines
3. **Highlighting**: Highlighting methods use visual block's animation methods for
   consistent fade/highlight/pulse effects

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
1. **Refactor highlighting to use visual block methods**: Currently, _highlight_with_context()
   manually constructs fade/highlight animations. Should use:
   - BaseVisualBlock.create_fade_animation() for fading blocks
   - BaseVisualBlock.create_reset_animation() for resetting to neutral state
   - BaseVisualBlock.create_pulsing_highlight() instead of _create_pulse_updater()
   This requires adding these methods to BaseVisualBlock first.

2. **Add line fade methods to visual block**: Parent line fading logic should move to
   visual block layer with a create_line_fade_animation() method.

3. **Config-driven line properties**: Ensure all line operations read from config
   (line_stroke_opacity, line_color, etc.) rather than using any hardcoded values.
"""

from __future__ import annotations

from typing import Optional, List, TYPE_CHECKING

import numpy as np
from manim import ShowPassingFlash, cycle_animation, WHITE, Wait

from .logical_block import BitcoinLogicalBlock
from .config import BitcoinConfig, DEFAULT_BITCOIN_CONFIG

if TYPE_CHECKING:
    from ...core.hud_2d_scene import HUD2DScene

# noinspection PyProtectedMember
class BitcoinDAG:
    def __init__(self, scene: HUD2DScene, config: BitcoinConfig = DEFAULT_BITCOIN_CONFIG):
        self.scene = scene
        self.config = config
        self.blocks: dict[str, BitcoinLogicalBlock] = {}
        self.all_blocks: List[BitcoinLogicalBlock] = []
        self.genesis: Optional[BitcoinLogicalBlock] = None
        self.currently_highlighted_block: Optional[BitcoinLogicalBlock] = None

    ########################################
    # Block Handling
    ########################################

    def add_block(
            self,
            parent: Optional[BitcoinLogicalBlock] = None,
            name: Optional[str] = None
    ) -> BitcoinLogicalBlock:
        """Add a new block to the DAG with automatic positioning."""
        # Auto-generate name only if not provided
        if name is None:
            name = self._generate_block_name(parent)

        # Auto-calculate position if not provided
        position = self._calculate_position(parent)

        # Create the block with calculated position
        block = BitcoinLogicalBlock(
            name=name,
            parent=parent,
            position=position,
            bitcoin_config=self.config,
        )

        # Register and add to scene
        self.blocks[name] = block
        self.all_blocks.append(block)

        if parent is None:
            self.genesis = block

        # Play the creation animation
        self.scene.play(block._visual.create_with_lines())

        return block

    def _calculate_position(self, parent: Optional[BitcoinLogicalBlock]) -> tuple[float, float]:
        """Calculate position for a block based on parent and siblings.

        This method can be called both during initial block creation and
        when repositioning blocks after chain length changes.
        """
        if parent is None:
            # Genesis block
            return self.config.genesis_x, self.config.genesis_y

            # Calculate horizontal position
        parent_pos = parent._visual.square.get_center()
        x_position = parent_pos[0] + self.config.horizontal_spacing

        # Calculate vertical offset for parallel blocks
        new_block_weight = parent.weight + 1
        same_height_blocks = [b for b in self.all_blocks if b.weight == new_block_weight]
        sibling_index = len(same_height_blocks)
        y_position = self.config.genesis_y + (sibling_index * self.config.vertical_spacing)

        return x_position, y_position

    def generate_chain(self, num_blocks: int) -> List[BitcoinLogicalBlock]:
        """Generate a linear chain of blocks.

        Args:
            num_blocks: Total number of blocks to create (including genesis)

        Returns:
            List of all created blocks
        """
        created_blocks = []

        # Create genesis if it doesn't exist
        if self.genesis is None:
            genesis = self.add_block()
            created_blocks.append(genesis)
            num_blocks -= 1

            # Create remaining blocks in sequence
        parent = self.genesis
        for i in range(num_blocks):
            block = self.add_block(parent=parent)
            created_blocks.append(block)
            parent = block

        return created_blocks

    def _generate_block_name(self, parent: Optional[BitcoinLogicalBlock]) -> str:
        """Generate human-readable block name based on weight (height)."""
        if parent is None:
            return "Gen"

            # Use weight - 1 for block number since Genesis has weight 1
        height = parent.weight + 1
        block_number = height - 1

        # Find existing blocks at this height
        blocks_at_height = [
            b for b in self.all_blocks
            if b.weight == height
        ]

        # Generate name with suffix for parallel blocks
        if not blocks_at_height:
            return f"B{block_number}"
        else:
            # First parallel block gets 'a', second gets 'b', etc.
            suffix = chr(ord('a') + len(blocks_at_height) - 1)
            return f"B{block_number}{suffix}"

    def get_block(self, name: str) -> Optional[BitcoinLogicalBlock]:
        """Retrieve a block by name with automatic fuzzy matching."""
        # Try exact match first
        if name in self.blocks:
            return self.blocks[name]

        if not self.all_blocks:
            return None

            # Extract height and find closest
        import re
        match = re.search(r'B?(\d+)', name)
        if not match:
            return self.all_blocks[-1]

        target_height = int(match.group(1))
        max_height = max(b.weight for b in self.all_blocks)
        actual_height = min(target_height, max_height)

        # Find first block at this height
        for block in self.all_blocks:
            if block.weight == actual_height:
                return block

        return self.all_blocks[-1]

    ########################################
    # Moving Blocks
    ########################################

    def move(
            self,
            blocks: List[BitcoinLogicalBlock],
            positions: List[tuple[float, float]]
    ):
        """Move multiple blocks using their visual block's movement animation.

        Args:
            blocks: List of blocks to move
            positions: Corresponding (x, y) positions
        """
        if len(blocks) != len(positions):
            raise ValueError("Number of blocks must match number of positions")

        animations = []
        for block, pos in zip(blocks, positions):
            target = np.array([pos[0], pos[1], 0])
            animations.append(
                block._visual.create_movement_animation(
                    block._visual.animate.move_to(target)
                )
            )

        if animations:
            self.scene.play(*animations)

    ########################################
    # Get Past/Future/Anticone Blocks
    ########################################

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

    ########################################
    # Highlighting Blocks
    ########################################

    def highlight_past(self, focused_block: BitcoinLogicalBlock) -> List:
        """Highlight a block's past cone (ancestors).

        All styling comes from focused_block._visual.config.
        """
        context_blocks = self.get_past_cone(focused_block)
        return self._highlight_with_context(focused_block, context_blocks)

    def highlight_future(self, focused_block: BitcoinLogicalBlock) -> List:
        """Highlight a block's future cone (descendants).

        All styling comes from focused_block._visual.config.
        """
        context_blocks = self.get_future_cone(focused_block)
        return self._highlight_with_context(focused_block, context_blocks)

    def highlight_anticone(self, focused_block: BitcoinLogicalBlock) -> List:
        """Highlight a block's anticone (neither ancestors nor descendants).

        All styling comes from focused_block._visual.config.
        """
        context_blocks = self.get_anticone(focused_block)
        return self._highlight_with_context(focused_block, context_blocks)

    @staticmethod
    def _create_pulse_updater(block: BitcoinLogicalBlock):
        """Create pulsing stroke width updater using config values."""
        # Read ALL values from config
        original_width = block._visual.config.stroke_width
        highlighted_width = block._visual.config.highlight_stroke_width

        def pulse_stroke(mob, dt):
            t = getattr(mob, 'time', 0) + dt
            mob.time = t
            width = original_width + (highlighted_width - original_width) * (
                    np.sin(t * np.pi) + 1
            ) / 2
            mob.set_stroke(WHITE, width=width)

        return pulse_stroke

    def _highlight_with_context(
            self,
            focused_block: BitcoinLogicalBlock,
            context_blocks: Optional[List[BitcoinLogicalBlock]] = None
    ) -> List:
        """Highlight a block and its context with optional connection flashing.

        Returns:
            List of flash line copies that were added to the scene (for cleanup)
        """
        # Store the currently highlighted block
        self.currently_highlighted_block = focused_block
        # Read ALL styling from config
        fade_opacity = focused_block._visual.config.fade_opacity
        highlight_color = focused_block._visual.config.highlight_color
        flash_connections = focused_block._visual.config.flash_connections

        if context_blocks is None:
            context_blocks = []

        # Fade non-context blocks (always fade unrelated blocks)
        fade_animations = []
        for block in self.all_blocks:
            if block not in context_blocks and block != focused_block:
                fade_animations.extend([
                    block._visual.square.animate.set_fill(opacity=fade_opacity),
                    block._visual.square.animate.set_stroke(opacity=fade_opacity),
                    block._visual.label.animate.set_fill(opacity=fade_opacity)
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
        pulse_updater = self._create_pulse_updater(focused_block)
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

    def reset_highlighting(self):
        """Reset all blocks to neutral state from config."""
        # Remove pulse updater from currently highlighted block
        if self.currently_highlighted_block and self.currently_highlighted_block._visual.square.updaters:
            self.currently_highlighted_block._visual.square.remove_updater(
                self.currently_highlighted_block._visual.square.updaters[-1]
            )

            # Reset ALL blocks to original styling from config
        reset_animations = []
        for block in self.all_blocks:
            reset_animations.extend([
                block._visual.square.animate.set_fill(opacity=block._visual.config.fill_opacity),
                block._visual.square.animate.set_stroke(
                    block._visual.config.stroke_color,
                    width=block._visual.config.stroke_width,
                    opacity=block._visual.config.stroke_opacity
                ),
                block._visual.label.animate.set_fill(opacity=block._visual.config.label_opacity)
            ])
            for line in block._visual.parent_lines:
                reset_animations.append(
                    line.animate.set_stroke(
                        block._visual.config.line_color,
                        width=block._visual.config.line_stroke_width,
                        opacity=block._visual.config.line_stroke_opacity
                    )
                )

                # Clear the tracked state
        self.currently_highlighted_block = None

        if reset_animations:
            self.scene.play(*reset_animations)