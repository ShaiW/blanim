# blanim\blanim\blockDAGs\kaspa\visual_block.py

from __future__ import annotations

__all__ = ["KaspaVisualBlock"]

import copy
from typing import TYPE_CHECKING

from manim import AnimationGroup, Create

from .config import DEFAULT_KASPA_CONFIG, KaspaConfig
from ... import BaseVisualBlock, ParentLine

if TYPE_CHECKING:
    from .logical_block import KaspaLogicalBlock

# noinspection PyProtectedMember
#TODO instead of using a config for every single block, we can pass parameters from the DAG - low priority
class KaspaVisualBlock(BaseVisualBlock):
    """Kaspa block visualization with multi-parent DAG structure.

    Represents a block in Kaspa's GHOSTDAG consensus where blocks can have
    multiple parents, forming a Directed Acyclic Graph (DAG). The first
    parent in the list is the "selected parent" with special visual treatment,
    while other parents are regular parent connections.

    The block uses 2D coordinates (x, y) for positioning, with the z-coordinate
    set to 0 by the base class to align with coordinate grids. Parent lines use
    different z_index values: the selected parent line (first in list) at z_index=1,
    and other parent lines at z_index=0, creating a visual hierarchy where regular
    lines (z_index=0) render behind selected parent lines (z_index=1), which render
    behind blocks (z_index=2).

    Parameters
    ----------
    label_text : str
        Text to display on the block (typically blue score or block number).
    position : tuple[float, float]
        2D coordinates (x, y) for block placement. The z-coordinate is
        set to 0 to align with coordinate grids. Rendering order is controlled
        via z_index (blocks at z_index=2, selected parent line at z_index=1,
        other parent lines at z_index=0).
    parents : list[KaspaVisualBlock], optional
        List of parent blocks. First parent is the selected parent.
        If None or empty, this is a genesis block.

    Attributes
    ----------
    kaspa_config : KaspaBlockConfig
        Stored configuration object for the block.
    parent_lines : list[ParentLine]
        List of ParentLine objects connecting to all parent blocks.
        First line (to selected parent) uses selected_parent_color and z_index=1.
        Other lines use other_parent_color and z_index=0.
     : list[KaspaVisualBlock]
        List of child blocks that have this block as one of their parents.

    Examples
    --------
    Creating a simple DAG::

        genesis = KaspaVisualBlock("Gen", (0, 0))
        block1 = KaspaVisualBlock("1", (1, 1), parents=[genesis])
        block2 = KaspaVisualBlock("2", (1, -1), parents=[genesis])

        self.play(genesis.create_with_lines())
        self.play(block1.create_with_lines(), block2.create_with_lines())

    Creating a block with multiple parents::

        # Block with multiple parents (selected parent first)
        merge = KaspaVisualBlock("3", (2, 0), parents=[block1, block2])
        self.play(merge.create_with_lines())  # Shows different colored lines

    Using custom configuration::

        custom_config = KaspaBlockConfig(
            block_color=GREEN,
            selected_parent_color=PINK,
            other_parent_color=LIGHT_GRAY,
            create_run_time=2.5
        )
        block = KaspaVisualBlock("Custom", (0, 0), kaspa_config=custom_config)
        self.play(block.create_with_lines())

    Moving a block with multiple line updates::

        self.play(merge.create_movement_animation(
            merge.animate.shift(UP)
        ))  # All parent lines update automatically

    Notes
    -----
    The selected parent (first in list) determines the block's position in
    the GHOSTDAG ordering and receives special visual treatment through both
    color (configured via selected_parent_color) and z_index (z_index=1).

    The z_index creates a clear visual hierarchy:
    - Regular lines and non-selected parent lines: z_index=0 (back)
    - Selected parent line: z_index=1 (middle)
    - Blocks: z_index=2 (front)

    All objects remain at z-coordinate 0 to avoid 3D projection issues in HUD2DScene.

    The children list is automatically maintained when blocks are created
    with parents, enabling automatic line updates when parent blocks move.

    See Also
    --------
    BitcoinVisualBlock : Single-parent chain alternative
    BaseVisualBlock : Base class for all visual blocks
    KaspaBlockConfig : Configuration object for Kaspa blocks
    """

    kaspa_config: KaspaConfig
    parent_lines: list[ParentLine]
    logical_block: KaspaLogicalBlock

    def __init__(
            self,
            label_text: str,
            position: tuple[float, float],
            parents: list[KaspaVisualBlock] | None = None,
            kaspa_config: KaspaConfig = DEFAULT_KASPA_CONFIG
    ) -> None:
        # Pass config directly to BaseVisualBlock
        super().__init__(label_text, position, kaspa_config)

        # Handle parent lines with config
        #TODO confirm z-index on SP lines vs other lines
        if parents:
            self.parent_lines = []
            for i, parent in enumerate(parents):
                line_color = self.kaspa_config.selected_parent_line_color if i == 0 else self.kaspa_config.other_parent_line_color
                parent_line = ParentLine(
                    self.square,
                    parent.square,
                    line_color=line_color
                )
                parent_line.set_z_index(1 if i == 0 else 0)
                self.parent_lines.append(parent_line)
        else:
            self.parent_lines = []

#TODO verify this is correct to avoid breaking manim
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

    def create_with_lines(self):
        """Create animation for block, label, and all parent lines.

        Extends the base class's create_with_label() method by adding
        animations for all parent line creations. All animations (block creation,
        label fade-in/grow, and line drawing) run simultaneously with
        matching run_time for synchronized visual effects.

        Parameters
        ----------


        Returns
        -------
        AnimationGroup
            Combined animation for block, label, and all line creations. If no
            parent lines exist (genesis block), returns only the base
            animation group.

        Examples
        --------
        Creating a Kaspa DAG::

            genesis = KaspaVisualBlock("Gen", (0, 0))
            block1 = KaspaVisualBlock("1", (1, 1), parents=[genesis])
            block2 = KaspaVisualBlock("2", (1, -1), parents=[genesis])
            merge = KaspaVisualBlock("3", (2, 0), parents=[block1, block2])

            # Draw blocks with their parent lines
            self.play(genesis.create_with_lines())
            self.play(block1.create_with_lines(), block2.create_with_lines())
            self.play(merge.create_with_lines())  # Creates 2 parent lines

        With custom run time::

            self.play(merge.create_with_lines(run_time=3.0))

        Notes
        -----
        This method demonstrates the extension pattern where child classes
        reuse parent animation logic by calling super().create_with_label()
        and extending the returned AnimationGroup, avoiding code duplication.

        For genesis blocks (no parents), this method returns the same result
        as create_with_label() from the base class.

        All parent lines are created simultaneously, with the selected parent
        line (first in list) using a different color and z-ordering than
        other parent lines.

        See Also
        --------
        BaseVisualBlock.create_with_label : Base animation method
        create_movement_animation : Animate block movement with line updates
        """
        base_animation_group = super().create_with_label()

        if self.parent_lines:
            run_time = self.kaspa_config.create_run_time
            animations = list(base_animation_group.animations)

            # Add all parent line creations
            for line in self.parent_lines:
                animations.append(Create(line, run_time=run_time))

            return AnimationGroup(*animations)

        return base_animation_group

    def create_movement_animation(self, animation):
        """Wrap movement animation with automatic updates for all parent lines.

        When a block moves, all its parent lines and all child lines must update
        to maintain their connections. This method wraps any movement animation
        with UpdateFromFunc animations for each line, ensuring the entire DAG
        structure remains visually connected during movement.

        Parameters
        ----------
        animation : Animation
            The movement animation to wrap (typically block.animate.shift()).

        Returns
        -------
        AnimationGroup or Animation
            If parent_lines or children exist, returns AnimationGroup with
            line updates. Otherwise, returns the original animation unchanged.

        Examples
        --------
        Moving a single block::

            block = KaspaVisualBlock("1", (0, 0), parents=[genesis])
            self.play(block.create_movement_animation(
                block.animate.shift(RIGHT * 2)
            ))

        Moving multiple blocks simultaneously::

            self.play(
                block1.create_movement_animation(block1.animate.shift(UP)),
                block2.create_movement_animation(block2.animate.shift(DOWN))
            )

        Moving a parent block with multiple children::

            # Genesis has multiple children in a DAG
            self.play(genesis.create_movement_animation(
                genesis.animate.shift(LEFT)
            ))  # All child lines update automatically

        Moving a merge block with multiple parents::

            # Merge block has multiple parent lines
            self.play(merge.create_movement_animation(
                merge.animate.shift(UP * 2)
            ))  # All parent lines update simultaneously

        Notes
        -----
        The line update uses UpdateFromFunc to avoid automatic movement
        propagation that would occur if lines were submobjects. This gives
        precise control over which lines update during movement.

        This method updates:
        - All of the block's own parent lines (if they exist)
        - All lines from children pointing to this block

        This is critical for DAG structures where blocks may have complex
        parent-child relationships with multiple connections. The method
        ensures the entire DAG remains visually connected during any block
        movement.

        See Also
        --------
        create_with_lines : Initial block and line creation
        ParentLine.create_update_animation : Line update mechanism
        """
        animations = [animation]

        # Update this block's parent lines
        animations.extend([line.create_update_animation() for line in self.parent_lines])

        # Update child lines (lines from children pointing to this block)
        for logical_child in self.logical_block.children:
            for line in logical_child._visual.parent_lines:
                if line.parent_block == self.square:
                    animations.append(line.create_update_animation())

        return AnimationGroup(*animations) if len(animations) > 1 else animation