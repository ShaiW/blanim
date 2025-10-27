# blanim/blanim/blockDAGs/kaspa/visual_block.py

from __future__ import annotations

from typing import Optional

from manim.typing import Point3DLike

from blanim import *

class KaspaVisualBlock(BaseVisualBlock):
    """
    Kaspa block visualization with multi-parent DAG structure.

    Kaspa uses GHOSTDAG consensus where blocks can have multiple parents.
    The first parent in the list is the selected parent (BLUE line),
    while other parents have WHITE lines.

    Attributes:
        parent_lines: List of ParentLine objects to all parent blocks

    Note: First parent in constructor's parents list is the selected parent.
    """
    parent_lines: list[ParentLine]

    def __init__(self, label_text: str, position: Point3DLike,
                 block_color: ParsableManimColor = BLUE,
                 parents: Optional[list[KaspaVisualBlock]] = None) -> None:
        super().__init__(label_text, position, block_color)

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