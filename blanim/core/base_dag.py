# blanim/blockDAGs/base_dag.py

from __future__ import annotations

"""Base class for DAG/Chain structures with universal traversal and highlighting.  

This module provides shared functionality for both Bitcoin chains and Kaspa DAGs,  
including graph traversal algorithms and visual highlighting effects.  
"""

from manim import *
from manim.animation.updaters.mobject_update_utils import cycle_animation
import numpy as np
from typing import List, Optional, Set

__all__ = ["BaseDAG"]


class BaseDAG:
    """Base class for DAG/Chain with universal traversal and highlighting.

    This class provides:
    - Graph traversal methods (past cone, future cone, anticone)
    - Visual highlighting effects (pulsing, flashing, fading)
    - Block registry management

    Attributes:
        blocks: Dictionary mapping block names to block objects (registry)
        all_blocks: List of all blocks in the DAG/chain
    """

    def __init__(self):
        """Initialize the BaseDAG with an empty block registry."""
        self.blocks = {}  # Block registry: name -> block object
        self.all_blocks = []  # List of all blocks

    # ============================================================================
    # BLOCK REGISTRY METHODS
    # ============================================================================

    def register_block(self, name: str, block):
        """Register a block in the DAG registry.

        Args:
            name: Unique identifier for the block
            block: The block object to register
        """
        self.blocks[name] = block
        if block not in self.all_blocks:
            self.all_blocks.append(block)

    def get_block(self, name: str):
        """Retrieve a block by name from the registry.

        Args:
            name: The block's unique identifier

        Returns:
            The block object, or None if not found
        """
        return self.blocks.get(name)

        # ============================================================================

    # GRAPH TRAVERSAL METHODS
    # ============================================================================

    def get_past_cone(self, block) -> List:
        """Get all blocks in the past cone (ancestors) via recursive traversal.

        Works for both chains (single parent) and DAGs (multiple parents).
        Uses depth-first search to find all reachable ancestors.

        Args:
            block: The block whose past cone to compute

        Returns:
            List of all ancestor blocks
        """
        past = set()
        to_visit = [block]

        while to_visit:
            current = to_visit.pop()
            for parent in current.parents:
                if parent not in past:
                    past.add(parent)
                    to_visit.append(parent)

        return list(past)

    def get_future_cone(self, block) -> List:
        """Get all blocks in the future cone (descendants) via recursive traversal.

        Works for both chains (single child) and DAGs (multiple children).
        Uses direct child links instead of building a children mapping.

        Args:
            block: The block whose future cone to compute

        Returns:
            List of all descendant blocks
        """
        future = set()
        to_visit = [block]

        while to_visit:
            current = to_visit.pop()
            for child in current.children:  # Direct child links
                if child not in future:
                    future.add(child)
                    to_visit.append(child)

        return list(future)

    def get_anticone(self, block) -> List:
        """Get blocks in the anticone (neither past nor future).

        The anticone consists of blocks that are parallel to the given block:
        - Not in its past (not ancestors)
        - Not in its future (not descendants)
        - Not the block itself

        For chains with single parents: always empty (no parallel branches possible)
        For DAGs with multiple parents: returns parallel branches

        Args:
            block: The block whose anticone to compute

        Returns:
            List of blocks in the anticone
        """
        past = set(self.get_past_cone(block))
        future = set(self.get_future_cone(block))

        anticone = [
            b for b in self.all_blocks
            if b != block and b not in past and b not in future
        ]

        return anticone


        # ============================================================================

    # HIGHLIGHTING METHODS
    # ============================================================================

    def create_pulse_updater(self, block, original_width: Optional[float] = None,
                             highlighted_width: float = 8):
        """Create a pulsing stroke width updater for a block.

        Args:
            block: The LOGICAL block to pulse
            original_width: Original stroke width (defaults to block._visual.config.stroke_width)
            highlighted_width: Maximum stroke width during pulse
        """
        if original_width is None:
            original_width = block._visual.config.stroke_width  # Changed

        def pulse_stroke(mob, dt):
            t = getattr(mob, 'time', 0) + dt
            mob.time = t
            width = original_width + (highlighted_width - original_width) * (np.sin(t * np.pi) + 1) / 2
            mob.set_stroke(WHITE, width=width)

        return pulse_stroke

    def highlight_block_with_context(
            self,
            scene,
            focused_block,  # Now expects LOGICAL block
            context_blocks: Optional[List] = None,
            highlight_color: ParsableManimColor = YELLOW,
            fade_opacity: float = 0.1,
            flash_connections: bool = True
    ) -> Optional[List]:
        """Highlight a block and its context (past/future/anticone).

        Args:
            focused_block: The LOGICAL block to pulse (white flashing)
            context_blocks: List of LOGICAL blocks to highlight (defaults to past cone)
        """
        # Default to past cone if no context specified
        if context_blocks is None:
            context_blocks = self.get_past_cone(focused_block)

            # Build fade animations for non-relevant blocks
        fade_animations = []
        for block in self.all_blocks:
            if block not in [focused_block] + context_blocks:
                # Access visual through ._visual
                fade_animations.append(block._visual.square.animate.set_fill(opacity=fade_opacity))
                for line in block._visual.parent_lines:
                    fade_animations.append(line.animate.set_stroke(opacity=0.25))

                    # Restore context blocks and their connections
        restore_animations = []
        for block in context_blocks:
            restore_animations.append(
                block._visual.square.animate.set_fill(opacity=block._visual.config.fill_opacity)
            )
            for line in block._visual.parent_lines:
                restore_animations.append(line.animate.set_stroke(opacity=1.0))

                # Apply fading and restoration
        if fade_animations or restore_animations:
            scene.play(*fade_animations, *restore_animations)

            # Add pulsing to focused block
        focused_block._visual.square.time = 0
        pulse_updater = self.create_pulse_updater(focused_block)
        focused_block._visual.square.add_updater(pulse_updater)

        # Flash connections if requested
        flash_lines = []
        if flash_connections:
            for block in context_blocks:
                for line in block._visual.parent_lines:
                    flash_line = line.copy().set_color(highlight_color)
                    scene.add(flash_line)
                    flash_lines.append(flash_line)
                    cycle_animation(ShowPassingFlash(flash_line, time_width=0.3, run_time=1.5))

                    # Highlight context blocks
        highlight_animations = [
            block._visual.square.animate.set_stroke(highlight_color, width=8)
            for block in context_blocks
        ]
        if highlight_animations:
            scene.play(*highlight_animations)

        return flash_lines if flash_connections else None

    def reset_highlighting(
            self,
            scene,
            focused_block,  # Now expects LOGICAL block
            context_blocks: Optional[List] = None,
            flash_lines: Optional[List] = None
    ):
        """Reset all highlighting effects to original state.

        Args:
            focused_block: The LOGICAL block that was pulsing
            context_blocks: List of LOGICAL blocks that were highlighted
        """
        # Remove flash lines
        if flash_lines:
            scene.remove(*flash_lines)

            # Remove pulse updater
        if focused_block._visual.square.updaters:
            focused_block._visual.square.remove_updater(focused_block._visual.square.updaters[-1])

            # Default to past cone if no context specified
        if context_blocks is None:
            context_blocks = self.get_past_cone(focused_block)

            # Reset all blocks to original state
        reset_animations = []
        for block in self.all_blocks:
            reset_animations.extend([
                block._visual.square.animate.set_fill(opacity=block._visual.config.fill_opacity),
                block._visual.square.animate.set_stroke(
                    block._visual.config.stroke_color,
                    width=block._visual.config.stroke_width
                )
            ])
            for line in block._visual.parent_lines:
                reset_animations.append(line.animate.set_stroke(opacity=1.0))

        if reset_animations:
            scene.play(*reset_animations)

    def highlight_block_context(
            self,
            scene,
            focused_block,
            show_past: bool = True,
            show_future: bool = False,
            show_anticone: bool = False,
            highlight_color: ParsableManimColor = YELLOW,
            fade_opacity: float = 0.1
    ) -> Optional[List]:
        """Convenience method to highlight a block with its graph context.

        This is a higher-level wrapper around highlight_block_with_context that
        automatically computes the context blocks based on graph relationships.

        Args:
            scene: The HUD2DScene to play animations on
            focused_block: The block to highlight
            show_past: Whether to highlight past cone (default True)
            show_future: Whether to highlight future cone (default False)
            show_anticone: Whether to highlight anticone (default False)
            highlight_color: Color for context blocks (default YELLOW)
            fade_opacity: Opacity for faded blocks (default 0.1)

        Returns:
            List of flash line objects (for cleanup)
        """
        context_blocks = []

        if show_past:
            context_blocks.extend(self.get_past_cone(focused_block))

        if show_future:
            context_blocks.extend(self.get_future_cone(focused_block))

        if show_anticone:
            context_blocks.extend(self.get_anticone(focused_block))

            # Remove duplicates while preserving order
        seen = set()
        context_blocks = [
            b for b in context_blocks
            if not (b in seen or seen.add(b))
        ]

        return self.highlight_block_with_context(
            scene=scene,
            focused_block=focused_block,
            context_blocks=context_blocks,
            highlight_color=highlight_color,
            fade_opacity=fade_opacity,
            flash_connections=True
        )