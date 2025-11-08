from __future__ import annotations

__all__ = ["ParentLine"]

from manim import Line, WHITE, CapStyleType, UpdateFromFunc

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
        self._fixed_stroke_width = 5

    def _update_position_and_size(self, mobject):
        new_start = self.this_block.get_left()
        new_end = self.parent_block.get_right()
#        self.set_stroke(width=self._fixed_stroke_width)
        self.set_points_by_ends(new_start, new_end, buff=self.buff)

    def create_update_animation(self):
        return UpdateFromFunc(
            self,
            update_function=self._update_position_and_size,
            suspend_mobject_updating=False
        )