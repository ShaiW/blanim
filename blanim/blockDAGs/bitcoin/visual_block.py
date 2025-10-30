# blanim\blanim\blockDAGs\bitcoin\visual_block.py

from __future__ import annotations

__all__ = ["BitcoinVisualBlock"]

from typing import Optional

from .config import BitcoinBlockConfig, DEFAULT_BITCOIN_CONFIG

from manim.typing import Point3DLike

from blanim import *

class BitcoinVisualBlock(BaseVisualBlock):
    """Bitcoin block visualization with single-parent chain structure.

    Represents a block in Bitcoin's longest-chain consensus mechanism where
    each block has exactly one parent, forming a linear blockchain. The
    parent connection is visualized with a BLUE line.

    Parameters
    ----------
    label_text : str
        Text to display on the block (typically block height or number).
    position : Point3DLike
        3D coordinates [x, y, z] for block placement.
    block_color : ParsableManimColor, optional
        Color of the block square. Default is BLUE.
    parent : BitcoinVisualBlock, optional
        The parent block in the chain. If None, this is a genesis block.

    Attributes
    ----------
    parent_line : ParentLine or None
        Single ParentLine connecting to parent block. None for genesis blocks.

    Examples
    --------
    Creating a chain::

        genesis = BitcoinVisualBlock("Gen", [0, 0, 0])
        block1 = BitcoinVisualBlock("1", [2, 0, 0], parent=genesis)

        # Add with lines
        self.play(genesis.create_with_lines())
        self.play(block1.create_with_lines())

    Moving a block with line updates::

        self.play(block1.create_movement_animation(
            block1.animate.shift(RIGHT)
        ))

    See Also
    --------
    KaspaVisualBlock : Multi-parent DAG alternative
    BaseVisualBlock : Base class for all visual blocks
    """

    def __init__(
            self,
            label_text: str,
            position: Point3DLike,
            parent: Optional[BitcoinVisualBlock] = None,
            block_config: BitcoinBlockConfig = DEFAULT_BITCOIN_CONFIG
    ) -> None:
        # Store config
        self.config = block_config

        # Pass config values to BaseVisualBlock
        super().__init__(
            label_text=label_text,
            position=position,
            block_color=self.config.block_color,
            fill_opacity=self.config.fill_opacity,
            stroke_color=self.config.stroke_color,
            stroke_width=self.config.stroke_width,
            side_length=self.config.side_length,
            label_font_size=self.config.label_font_size,
            label_color=self.config.label_color,
            create_run_time=self.config.create_run_time,
            label_change_run_time=self.config.label_change_run_time
        )

        self.children = []

        # Handle parent line with config
        if parent:
            self.parent_line = ParentLine(
                self.square,
                parent.square,
                line_color=self.config.line_color
            )
            parent.children.append(self)
        else:
            self.parent_line = None


    def create_with_lines(self, **kwargs):
        """Create animation for block, label, and parent line.

        Extends the base class's create_with_label() method by adding
        the parent line creation animation. All animations (block creation,
        label fade-in/grow, and line drawing) run simultaneously with
        matching run_time for synchronized visual effects.

        Parameters
        ----------
        **kwargs
            Keyword arguments passed to Create animations (e.g., run_time).

        Returns
        -------
        AnimationGroup
            Combined animation for block, label, and line creation.

        Examples
        --------
        Creating a Bitcoin chain::

            genesis = BitcoinVisualBlock("Gen", [0, 0, 0])
            block1 = BitcoinVisualBlock("1", [2, 0, 0], parent=genesis)
            block2 = BitcoinVisualBlock("2", [4, 0, 0], parent=block1)

            # Draw blocks with their parent lines
            self.play(genesis.create_with_lines())
            self.play(block1.create_with_lines())
            self.play(block2.create_with_lines())

        Notes
        -----
        This method demonstrates the extension pattern where child classes
        reuse parent animation logic by calling super().create_with_label()
        and extending the returned AnimationGroup, avoiding code duplication.

        See Also
        --------
        BaseVisualBlock.create_with_label : Base animation method
        create_movement_animation : Animate block movement with line updates
        """
        # Get the base animation group from parent class
        base_animation_group = super().create_with_label(**kwargs)

        # If there's a parent line, add it to the animations
        if self.parent_line:
            run_time = kwargs.get('run_time', self.config.create_run_time)
            # Extract animations from base group and add line creation
            animations = list(base_animation_group.animations)
            animations.append(Create(self.parent_line, run_time=run_time))
            return AnimationGroup(*animations)

        # No parent line, just return base animation
        return base_animation_group

    def create_movement_animation(self, animation):
        """Wrap movement animation with automatic line updates.

        When a block moves, its parent line must update to maintain the
        connection. This method wraps any movement animation with an
        UpdateFromFunc animation that continuously updates the line endpoints.

        Parameters
        ----------
        animation : Animation
            The movement animation to wrap (typically block.animate.shift()).

        Returns
        -------
        AnimationGroup or Animation
            If parent_line exists, returns AnimationGroup with line update.
            Otherwise, returns the original animation unchanged.

        Examples
        --------
        ::

            # Move block right while updating its parent line
            self.play(block.create_movement_animation(
                block.animate.shift(RIGHT * 2)
            ))

        Notes
        -----
        The line update uses UpdateFromFunc to avoid automatic movement
        propagation that would occur if lines were submobjects.
        """
        animations = [animation]

        # Update this block's parent line
        if self.parent_line:
            animations.append(self.parent_line.create_update_animation())

        # Update child lines (lines from children pointing to this block)
        for child in self.children:
            if child.parent_line:
                animations.append(child.parent_line.create_update_animation())

        return AnimationGroup(*animations) if len(animations) > 1 else animation