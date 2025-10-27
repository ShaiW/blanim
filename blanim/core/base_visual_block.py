from __future__ import annotations

__all__ = ["BaseVisualBlock"]

from manim import VMobject, ParsableManimColor, Square, Text, Create, AnimationGroup, BLUE, WHITE
from manim.typing import Point3DLike


#TODO change label to follow primer pattern similar to NarrationManager or selfish_mining_bitcoin.py
class BaseVisualBlock(VMobject):
    """
    Base class handling only visual elements and animations for blockchain blocks.

    IMPORTANT: Lines are NOT submobjects and must be added to the scene separately:
        block = VisualBlock("Label", [0,0,0], selected_parent=parent)
        self.add(block)  # Adds square and label only
        self.add(*block.parent_lines)  # Must manually add lines

    Lines update independently using UpdateFromFunc to avoid automatic movement
    propagation. Use create_with_lines() or create_movement_animation() to handle
    line animations properly.

    Attributes:
        square: The main square visual element
        label: Text label displayed on the square
        parent_lines: List of ParentLine objects (NOT submobjects)

    Note: The children list should be managed at the logical Block level,
    not in VisualBlock. This class handles only visual rendering.
    """
    def __init__(self, label_text: str, position: Point3DLike, block_color: ParsableManimColor = BLUE) -> None:
        super().__init__()

        #####Sqaure#####
        self.square = Square(
            color=block_color,
            fill_opacity=1,
            side_length=0.7
        )
        self.square.move_to(position)
        self.add(self.square)

        #####Label#####
        self.label = Text(
            label_text,
            font_size=24,
            color=WHITE
        )
        self.label.move_to(self.square.get_center())
        self._label_text = label_text
        self.add(self.label)

        #####Parent Relationship#####
        self.parent_lines = []

    def create_with_lines(self, **kwargs):
        """Create animation including block and all lines"""
        block_creation = Create(self, **kwargs)
        line_creations = [Create(line, **kwargs) for line in self.parent_lines]
        return AnimationGroup(block_creation, *line_creations)

    def create_movement_animation(self, animation):
        """
        Wrap movement animation with line updates.

        Usage:
            self.play(block.create_movement_animation(block.animate.shift(RIGHT)))
        """
        line_updates = [line.create_update_animation() for line in self.parent_lines]
        return AnimationGroup(animation, *line_updates)