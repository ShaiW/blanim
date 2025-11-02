# blanim\blanim\blockDAGs\bitcoin\visual_block.py

from __future__ import annotations

__all__ = ["BitcoinVisualBlock"]

from typing import Optional

from .config import BitcoinBlockConfig, DEFAULT_BITCOIN_CONFIG

from blanim import *

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
    block_config : BitcoinBlockConfig, optional
        Configuration object containing all visual and animation settings.
        Default is DEFAULT_BITCOIN_CONFIG.

    Attributes
    ----------
    config : BitcoinBlockConfig
        Stored configuration object for the block.
    parent_line : ParentLine or None
        Single ParentLine connecting to parent block. None for genesis blocks.
        Uses z_index=1 for rendering order (in front of regular lines at z_index=0,
        behind blocks at z_index=2).
    children : list[BitcoinVisualBlock]
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
        block = BitcoinVisualBlock("Custom", (0, 0), block_config=custom_config)
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

    def __init__(
            self,
            label_text: str,
            position: tuple[float, float],
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
            self.parent_line.set_z_index(1)
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
            Keyword arguments passed to Create animations. Supports 'run_time'
            to control animation duration. If not provided, uses
            self.config.create_run_time.

        Returns
        -------
        AnimationGroup
            Combined animation for block, label, and line creation. If no
            parent line exists (genesis block), returns only the base
            animation group.

        Examples
        --------
        Creating a Bitcoin chain::

            genesis = BitcoinVisualBlock("Gen", (0, 0))
            block1 = BitcoinVisualBlock("1", (2, 0), parent=genesis)
            block2 = BitcoinVisualBlock("2", (4, 0), parent=block1)

            # Draw blocks with their parent lines
            self.play(genesis.create_with_lines())
            self.play(block1.create_with_lines())
            self.play(block2.create_with_lines())

        With custom run time::

            self.play(block1.create_with_lines(run_time=3.0))

        Notes
        -----
        This method demonstrates the extension pattern where child classes
        reuse parent animation logic by calling super().create_with_label()
        and extending the returned AnimationGroup, avoiding code duplication.

        For genesis blocks (no parent), this method returns the same result
        as create_with_label() from the base class.

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

        When a block moves, its parent line and all child lines must update
        to maintain their connections. This method wraps any movement animation
        with UpdateFromFunc animations that continuously update the line
        endpoints during the movement.

        Parameters
        ----------
        animation : Animation
            The movement animation to wrap (typically block.animate.shift()).

        Returns
        -------
        AnimationGroup or Animation
            If parent_line or children exist, returns AnimationGroup with
            line updates. Otherwise, returns the original animation unchanged.

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
        if self.parent_line:
            animations.append(self.parent_line.create_update_animation())

        # Update child lines (lines from children pointing to this block)
        for child in self.children:
            if child.parent_line:
                animations.append(child.parent_line.create_update_animation())

        return AnimationGroup(*animations) if len(animations) > 1 else animation