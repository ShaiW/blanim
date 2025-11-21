# blanim\blanim\core\base_visual_block.py

from __future__ import annotations

__all__ = ["BaseVisualBlock"]

from typing import TYPE_CHECKING

import numpy as np
from manim import (
    Square,
    Text,
    WHITE,
    Transform,
    BLACK,
    Create,
    AnimationGroup,
    VGroup, BackgroundRectangle
)

if TYPE_CHECKING:
    from ..core.base_config import BaseBlockConfig

class BaseVisualBlock(VGroup):
    """Base class for blockchain block visualization.

    This is an abstract base class - do not instantiate directly.
    Child classes MUST set self.config in their __init__ before calling
    any highlighting methods.
    """

    config: BaseBlockConfig
    square: Square
    label: Text

    def __init__(
            self,
            label_text: str,
            position: tuple[float, float],
            config: BaseBlockConfig,
    ) -> None:
        super().__init__()

        self.config = config
        self._label_text = label_text

        # Define z-coordinates for all components
        self.square_z = 0.0      # Front
        self.bg_rect_z = 0.005   # Behind square  (but infront of lines at 0.01)
        self.label_z = -0.005    # In front of square

        #####Square#####
        self.square = Square(
            fill_color=config.block_color,
            fill_opacity=config.fill_opacity,
            stroke_color=config.stroke_color,
            stroke_width=config.stroke_width,
            stroke_opacity=config.stroke_opacity,
            side_length=config.side_length,
            shade_in_3d=True
        )

        self.square.move_to((position[0], position[1], self.square_z))

        self.background_rect = BackgroundRectangle(
            self.square,
            color=None,  # None uses scene background color
            fill_opacity=0.75,  # Allows slight line visibility
            buff=0  # No buffer, exact size of square
        )

        self.background_rect.shade_in_3d = True
        # Position background BEHIND square
        self.background_rect.move_to((position[0], position[1], self.bg_rect_z))

        #####Label (Primer Pattern)#####
        # Create invisible primer with 5-character capacity
        self.label = Text(
            "00000",  # 5 0's for default capacity
            font_size=1,
            color=BLACK
        )
#        self.label.move_to(self.square.get_center())
        self.label.move_to((position[0], position[1], self.label_z))
        self.label.shade_in_3d = True

        # Add to VGroup
        self.add(self.background_rect, self.square, self.label)

        self.parent_lines = []
        self.child_lines = []

    def _get_label(self, text: str) -> Text:

        new_label = Text(
            text,
            font_size=self.config.label_font_size,
            color=self.config.label_color
        )
        center = self.square.get_center()
        new_label.move_to((center[0], center[1], self.label_z))
        return new_label

    def create_with_label(self):

        run_time = self.config.create_run_time

        # Create the square only (not the entire self)
        create_anim = Create(self.square, run_time=run_time)

        # Transform primer to actual label (same run_time)
        actual_label = self._get_label(self._label_text)
        label_transform = Transform(self.label, actual_label, run_time=run_time)

        return AnimationGroup(create_anim, label_transform)

    def change_label(self, text: str):

        run_time = self.config.label_change_run_time

        new_label = self._get_label(text)
        self._label_text = text
        return Transform(self.label, new_label, run_time=run_time)

    def create_with_lines(self):
        """Returns AnimationGroup of block + label + lines creation."""
        run_time = self.config.create_run_time

        # Create animations for square AND background_rect together
        create_square = Create(self.square, run_time=run_time)
        create_bg = Create(self.background_rect, run_time=run_time)

        actual_label = self._get_label(self._label_text)
        label_transform = Transform(self.label, actual_label, run_time=run_time)

        anims = [create_square, create_bg, label_transform]
        for line in self.parent_lines:
            anims.append(Create(line, run_time=run_time))

        return AnimationGroup(*anims)
    # def create_with_lines(self):  # CHANGE 3: Added new method
    #     """Returns AnimationGroup of block + label + lines creation."""
    #     run_time = self.config.create_run_time
    #     create_anim = Create(self.square, run_time=run_time)
    #     actual_label = self._get_label(self._label_text)
    #     label_transform = Transform(self.label, actual_label, run_time=run_time)
    #
    #     anims = [create_anim, label_transform]
    #     for line in self.parent_lines:
    #         anims.append(Create(line, run_time=run_time))
    #
    #     return AnimationGroup(*anims)

#TODO remove all references to config and use properties, the config should only exist at the DAG level and pass parameters to everything
    def create_highlight_animation(self, color=None, stroke_width=None):
        """Returns animation for highlighting this block's stroke."""
        if color is None:
            color = self.config.highlight_color
        if stroke_width is None:
            stroke_width = self.config.highlight_stroke_width

        return self.square.animate.set_stroke(color, width=stroke_width)

    def create_unhighlight_animation(self):
        """Returns animation to reset stroke to original config."""
        return self.square.animate.set_stroke(
            self.config.stroke_color,
            width=self.config.stroke_width
        )

    def create_pulsing_highlight(self, color=None, min_width=None, max_width=None):
        """Returns updater function for pulsing stroke effect."""
        if color is None:
            color = WHITE
        if min_width is None:
            min_width = self.config.stroke_width
        if max_width is None:
            max_width = self.config.highlight_stroke_width

        def pulse_stroke(mob, dt):
            import numpy as np
            t = getattr(mob, 'time', 0) + dt
            mob.time = t
            width = min_width + (max_width - min_width) * (np.sin(t * np.pi) + 1) / 2
            mob.set_stroke(color, width=width)

        return pulse_stroke