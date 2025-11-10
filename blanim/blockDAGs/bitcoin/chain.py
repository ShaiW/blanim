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

TODO / Future Improvements: UPDATE THIS
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
from manim import ShowPassingFlash, cycle_animation, WHITE, Wait

from .logical_block import BitcoinLogicalBlock
from .layout_config import BitcoinLayoutConfig, DEFAULT_BITCOIN_LAYOUT_CONFIG
from ... import BitcoinBlockConfig, DEFAULT_BITCOIN_CONFIG

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
        self.currently_highlighted_block: Optional[BitcoinLogicalBlock] = None

    ########################################
    # Block Handling
    ########################################

#TODO blocks added to scene without create and without labels, need to create
    def add_block(
            self,
            parent: Optional[BitcoinLogicalBlock] = None,
            position: Optional[np.ndarray] = None,
            config: Optional[BitcoinBlockConfig] = None,
            name: Optional[str] = None
    ) -> BitcoinLogicalBlock:
        """Add a new block to the DAG with automatic positioning."""
        # Auto-generate name only if not provided
        if name is None:
            name = self._generate_block_name(parent)
            # Auto-calculate position if not provided
        if position is None:
            if parent is None:
                # Genesis block: use genesis_y from layout_config
                position = np.array([0, self.layout_config.genesis_y, 0])
            else:
                # Child block: position to the right of parent
                parent_pos = parent._visual.square.get_center()
                position = parent_pos + np.array([self.layout_config.horizontal_spacing, 0, 0])

                # Create the block with calculated position
        block = BitcoinLogicalBlock(
            name=name,
            parent=parent,
            position=position,
            bitcoin_config=config or DEFAULT_BITCOIN_CONFIG,
        )

        # Register and add to scene
        self.blocks[name] = block
        self.all_blocks.append(block)

        if parent is None:
            self.genesis = block

            # Automatically add visual components to scene
        self.scene.add(block._visual)
        for line in block._visual.parent_lines:
            self.scene.add(line)

        return block

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
            return "Genesis"

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