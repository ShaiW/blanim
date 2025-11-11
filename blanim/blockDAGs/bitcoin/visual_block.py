# blanim\blanim\blockDAGs\bitcoin\visual_block.py

from __future__ import annotations

__all__ = ["BitcoinVisualBlock"]

import copy
from typing import Optional, TYPE_CHECKING

from manim import Create, AnimationGroup

from .config import BitcoinConfig, DEFAULT_BITCOIN_CONFIG
from ... import BaseVisualBlock, ParentLine

if TYPE_CHECKING:
    from .logical_block import BitcoinLogicalBlock

# noinspection PyProtectedMember
class BitcoinVisualBlock(BaseVisualBlock):
    """Bitcoin block visualization with single-parent chain structure.

    Represents a block in Bitcoin's longest-chain consensus mechanism where
    each block has exactly one parent, forming a linear blockchain. The
    parent connection is visualized with a line whose color is determined
    by the block configuration.

    The block uses 2D coordinates (x, y) for positioning, with the z-coordinate
    set to 0 by the base class to align with coordinate grids. The parent line uses
    z_index=1 to render in front of regular lines (z_index=0) but behind blocks
    (z_index=2).

    Parameters
    ----------
    label_text : str
        Text to display on the block (typically block height or number).
    position : tuple[float, float]
        2D coordinates (x, y) for block placement. The z-coordinate is
        set to 0 to align with coordinate grids. Rendering order is controlled
        via z_index (blocks at z_index=2, parent line at z_index=1).
    parent : BitcoinVisualBlock, optional
        The parent block in the chain. If None, this is a genesis block.
    bitcoin_config : BitcoinBlockConfig, optional
        Configuration object containing all visual and animation settings.
        Default is DEFAULT_BITCOIN_CONFIG.

    Attributes
    ----------
    bitcoin_config : BitcoinBlockConfig
        Stored configuration object for the block.
    parent_line : ParentLine or None
        Single ParentLine connecting to parent block. None for genesis blocks.
        Uses z_index=1 for rendering order (in front of regular lines at z_index=0,
        behind blocks at z_index=2).
     : list[BitcoinVisualBlock]
        List of child blocks that have this block as their parent.

    Examples
    --------
    Creating a simple chain::

        genesis = BitcoinVisualBlock("Gen", (0, 0))
        block1 = BitcoinVisualBlock("1", (2, 0), parent=genesis)

        # Add with lines
        self.play(genesis.create_with_lines())
        self.play(block1.create_with_lines())

    Using custom configuration::

        custom_config = BitcoinBlockConfig(
            block_color=RED,
            line_color=YELLOW,
            create_run_time=3.0
        )
        block = BitcoinVisualBlock("Custom", (0, 0), bitcoin_config=custom_config)
        self.play(block.create_with_lines())

    Moving a block with line updates::

        self.play(block1.create_movement_animation(
            block1.animate.shift(RIGHT)
        ))

    Notes
    -----
    The parent line uses z_index=1 to ensure proper rendering order: regular
    lines (z_index=0) render behind parent lines, which render behind blocks
    (z_index=2). This creates a clear visual hierarchy without affecting 3D
    positioning, avoiding projection issues in HUD2DScene.

    The children list is automatically maintained when blocks are created
    with parents, enabling automatic line updates when parent blocks move.

    See Also
    --------
    KaspaVisualBlock : Multi-parent DAG alternative
    BaseVisualBlock : Base class for all visual blocks
    BitcoinBlockConfig : Configuration object for Bitcoin blocks
    """
    bitcoin_config: BitcoinConfig
    parent_line: ParentLine | None
    logical_block: BitcoinLogicalBlock

    def __init__(
            self,
            label_text: str,
            position: tuple[float, float],
            parent: Optional[BitcoinVisualBlock] = None,
            bitcoin_config: BitcoinConfig = DEFAULT_BITCOIN_CONFIG
    ) -> None:
        # Pass config values to BaseVisualBlock
        super().__init__(label_text, position, bitcoin_config)

#        self.children = []

        # Handle parent line with config
        if parent:
            self.parent_lines = []
            parent_line = ParentLine(
                self.square,
                parent.square,
                line_color=bitcoin_config.line_color
            )
            parent_line.set_z_index(1)
            self.parent_lines.append(parent_line)
        else:
            self.parent_lines = []

    def __deepcopy__(self, memo):
        logical_block = self.logical_block
        self.logical_block = None

        cls = self.__class__
        result = cls.__new__(cls)
        memo[id(self)] = result
        for k, v in self.__dict__.items():
            setattr(result, k, copy.deepcopy(v, memo))

        self.logical_block = logical_block  # Restore original
        result.logical_block = logical_block  # Set on copy

        return result

    def create_with_lines(self) -> AnimationGroup:
        """Create animation for block with its parent line.

        Returns
        -------
        :class:`~.AnimationGroup`
            Animation group containing block creation and parent line creation.

        Examples
        --------
        Creating a genesis block (no parent line)::

            genesis = BitcoinVisualBlock("Gen", (0, 0))
            self.play(genesis.create_with_lines())

        Creating a block with parent line::

            block1 = BitcoinVisualBlock("1", (2, 0), parent=genesis)
            self.play(block1.create_with_lines())

        Notes
        -----
        This method combines the base block creation animation with the
        parent line creation animation. For genesis blocks (no parent),
        only the block creation animation is returned.

        The parent line is created with the same run_time as the block
        to ensure synchronized animation.

        See Also
        --------
        create_movement_animation : Animation for moving blocks
        """
        # Get base animation (block + label)
        base_animation_group = super().create_with_label()

        # If there's a parent line, add it to the animations
        if self.parent_lines:  # Fixed: check if list is non-empty
            run_time = self.config.create_run_time
            # Extract animations from base group and add line creation
            animations = list(base_animation_group.animations)
            animations.append(Create(self.parent_lines[0], run_time=run_time))  # Fixed: access first element
            return AnimationGroup(*animations)
        else:
            return base_animation_group

    def create_movement_animation(self, animation) -> AnimationGroup:
        """Create movement animation that updates connected lines.

        Parameters
        ----------
        animation
            The base movement animation (e.g., block.animate.shift(RIGHT))

        Returns
        -------
        :class:`~.AnimationGroup`
            Animation group containing movement and line updates

        Examples
        --------
        Moving a single block::

            block = BitcoinVisualBlock("1", (0, 0), parent=genesis)
            self.play(block.create_movement_animation(
                block.animate.shift(RIGHT * 2)
            ))

        Moving multiple blocks simultaneously::

            self.play(
                block1.create_movement_animation(block1.animate.shift(UP)),
                block2.create_movement_animation(block2.animate.shift(DOWN))
            )

        Moving a parent block (updates all child lines)::

            # Genesis has multiple children
            self.play(genesis.create_movement_animation(
                genesis.animate.shift(LEFT)
            ))  # All child lines update automatically

        Notes
        -----
        The line update uses UpdateFromFunc to avoid automatic movement
        propagation that would occur if lines were submobjects. This gives
        precise control over which lines update during movement.

        This method updates both:
        - The block's own parent line (if it exists)
        - All lines from children pointing to this block

        This ensures the entire chain remains visually connected during
        any block movement.

        See Also
        --------
        create_with_lines : Initial block and line creation
        ParentLine.create_update_animation : Line update mechanism
        """
        animations = [animation]

        # Update this block's parent line
        if self.parent_lines:  # Fixed: check if list is non-empty
            animations.append(self.parent_lines[0].create_update_animation())  # Fixed: access first element

        # Update child lines (lines from children pointing to this block)
        for logical_child in self.logical_block.children:
            if logical_child._visual.parent_lines:  # Fixed: check if list is non-empty
                animations.append(
                    logical_child._visual.parent_lines[0].create_update_animation())  # Fixed: access first element

        return AnimationGroup(*animations) if len(animations) > 1 else animation
