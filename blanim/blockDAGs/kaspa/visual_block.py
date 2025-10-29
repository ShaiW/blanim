# blanim/blanim/blockDAGs/kaspa/visual_block.py

from __future__ import annotations

from typing import Optional

from manim.typing import Point3DLike

from blanim import *

class KaspaVisualBlock(BaseVisualBlock):
    """Kaspa block visualization with multi-parent DAG structure.

    Represents a block in Kaspa's GHOSTDAG consensus where blocks can have
    multiple parents, forming a Directed Acyclic Graph (DAG). The first
    parent in the list is the "selected parent" (BLUE line), while other
    parents have WHITE lines.

    Parameters
    ----------
    label_text : str
        Text to display on the block (typically blue score or block number).
    position : Point3DLike
        3D coordinates [x, y, z] for block placement.
    block_color : ParsableManimColor, optional
        Color of the block square. Default is BLUE.
    parents : list[KaspaVisualBlock], optional
        List of parent blocks. First parent is the selected parent.
        If None or empty, this is a genesis block.

    Attributes
    ----------
    parent_lines : list[ParentLine]
        List of ParentLine objects connecting to all parent blocks.
        First line (to selected parent) is BLUE, others are WHITE.

    Examples
    --------
    Creating a DAG with multiple parents::

        genesis = KaspaVisualBlock("Gen", [0, 0, 0])
        block1 = KaspaVisualBlock("1", [1, 1, 0], parents=[genesis])
        block2 = KaspaVisualBlock("2", [1, -1, 0], parents=[genesis])

        # Block with multiple parents (selected parent first)
        merge = KaspaVisualBlock("3", [2, 0, 0], parents=[block1, block2])

        self.play(genesis.create_with_lines())
        self.play(block1.create_with_lines(), block2.create_with_lines())
        self.play(merge.create_with_lines())  # Shows BLUE and WHITE lines

    Moving a block with multiple line updates::

        self.play(merge.create_movement_animation(
            merge.animate.shift(UP)
        ))  # All parent lines update automatically

    See Also
    --------
    BitcoinVisualBlock : Single-parent chain alternative
    BaseVisualBlock : Base class for all visual blocks

    Notes
    -----
    The selected parent (first in list) determines the block's position in
    the GHOSTDAG ordering and receives special visual treatment (BLUE line).
    """
    parent_lines: list[ParentLine]

    def __init__(self, label_text: str, position: Point3DLike,
                 block_color: ParsableManimColor = BLUE,
                 parents: Optional[list[KaspaVisualBlock]] = None) -> None:
        super().__init__(label_text, position, block_color)

        self.parent_lines = []

        if parents:
            for i, parent in enumerate(parents):
                is_selected = (i == 0)  # First parent is selected
                line_color = BLUE if is_selected else WHITE
                line = ParentLine(
                    this_block=self.square,
                    parent_block=parent.square,
                    line_color=line_color
                )
                self.parent_lines.append(line)

    def create_with_lines(self, **kwargs):
        """Create animation for block, label, and parent lines."""
        base_animation_group = super().create_with_label(**kwargs)

        if self.parent_lines:
            run_time = kwargs.get('run_time', 1.0)
            animations = list(base_animation_group.animations)

            # Add all parent line creations
            for line in self.parent_lines:
                animations.append(Create(line, run_time=run_time))

            return AnimationGroup(*animations)

        return base_animation_group

    def create_movement_animation(self, animation):
        """Wrap movement animation with automatic updates for all parent lines.

        When a block moves, all its parent lines must update to maintain
        connections. This method wraps any movement animation with
        UpdateFromFunc animations for each line.

        Parameters
        ----------
        animation : Animation
            The movement animation to wrap (typically block.animate.shift()).

        Returns
        -------
        AnimationGroup
            Animation group containing the movement and all line updates.

        Examples
        --------
        ::

            # Move block with multiple parents
            self.play(merge_block.create_movement_animation(
                merge_block.animate.shift(RIGHT * 2)
            ))  # All parent lines update simultaneously

        Notes
        -----
        Each line update uses UpdateFromFunc to avoid automatic movement
        propagation. This is critical for DAG structures where blocks may
        have complex parent-child relationships.
        """
        line_updates = [line.create_update_animation() for line in self.parent_lines]
        return AnimationGroup(animation, *line_updates)