# blanim/blanim/blockDAGs/bitcoin/visual_block.py

from __future__ import annotations

from typing import Optional

from manim.typing import Point3DLike

from blanim import *

class BitcoinVisualBlock(BaseVisualBlock):
    """
    Bitcoin block visualization with single-parent chain structure.

    Bitcoin uses a longest-chain consensus where each block has exactly
    one parent, forming a linear chain. The parent line is colored BLUE.

    Attributes:
        parent_line: Single ParentLine to the parent block (if exists)
    """
    def __init__(self, label_text: str, position: Point3DLike,
                 block_color: ParsableManimColor = BLUE,
                 parent: Optional[BitcoinVisualBlock] = None) -> None:
        super().__init__(label_text, position, block_color)

        if parent:
            self.parent_line = ParentLine(
                this_block=self.square,
                parent_block=parent.square,
                line_color=BLUE
            )
            self.parent_lines = [self.parent_line]