from __future__ import annotations

__all__ = ["ParentLine"]

import numpy as np
from manim import Line, WHITE, CapStyleType, UpdateFromFunc

#TODO ensure lines have their own properties preserved so animations can be created by accessing lines properties
class ParentLine(Line):
    """Uses no updater, update from func during movement anims on either parent or child block.square"""
    def __init__(self, this_block, parent_block, line_color=WHITE):
        """REQUIREMENT pass the blocks square NOT the block"""
        super().__init__(
            start=this_block.get_left(),
            end=parent_block.get_right(),
            buff=0.1,
            color=line_color,
            stroke_width=5,
            cap_style = CapStyleType.ROUND
        )

        self.this_block = this_block
        self.parent_block = parent_block

        self.shade_in_3d = True

        self.z = 0.01  # Lines behind blocks

        self.shift(np.array([0, 0, self.z]))

    def _update_position_and_size(self, mobject):
        new_start = self.this_block.get_left()
        new_end = self.parent_block.get_right()
#        self.set_stroke(width=self._fixed_stroke_width)
        # Push endpoints backward in z

        new_start[2] = self.z
        new_end[2] = self.z

        self.set_points_by_ends(new_start, new_end, buff=self.buff)

    def create_update_animation(self):
        return UpdateFromFunc(
            self,
            update_function=self._update_position_and_size,
            suspend_mobject_updating=False
        )