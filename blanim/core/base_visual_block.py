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
    VGroup
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

        #####Square#####
        self.square = Square(
            fill_color=config.block_color,
            fill_opacity=config.fill_opacity,
            stroke_color=config.stroke_color,
            stroke_width=config.stroke_width,
            stroke_opacity=config.stroke_opacity,
            side_length=config.side_length,
        )

        self.square.move_to((position[0], position[1], 0))

        self.background_rect = Square(
            side_length=config.side_length,
            fill_color=BLACK,
            fill_opacity=0.9,  # Allows slight line visibility
            stroke_width=0,
        )

        # Position background BEHIND square
        self.background_rect.move_to(self.square.get_center())

        #####Label (Primer Pattern)#####
        # Create invisible primer with 5-character capacity
        self.label = Text(
            "00000",  # 5 0's for default capacity
            font_size=1,
            color=BLACK,
        )
        self.label.move_to(self.square.get_center())

        # Add to VGroup
        self.add(self.background_rect, self.square, self.label)

        self.parent_lines = []
        self.child_lines = []

        # Set z_index at the end
        self.background_rect.set_z_index(11)
        self.square.set_z_index(12)
        self.label.set_z_index(13)

    def _get_label(self, text: str) -> Text:
        if not text or text.isspace():
            text = "\u200B"  # Zero-width space maintains position #TODO verify(this does not appear to maintain position)

        new_label = Text(
            text,
            font_size=self.config.label_font_size,
            color=self.config.label_color
        )
        new_label.move_to(self.square.get_center())
        return new_label

#TODO creates label by default but setting "" or " " breaks positioning of get_center on vgroup, figure out how to create invisible label that does not break positioning,
#   similar to narrate/caption  (Pretty sure positioning is fixed by overriding get_center() to return center of square, need to test label after setting to empty)
    def create_with_label(self):

        run_time = self.config.create_run_time

        # Create the square only (not the entire self)
        create_anim = Create(self.square, run_time=run_time)
        bgsquare_anim = Create(self.background_rect, run_time=run_time)

        # Transform primer to actual label (same run_time)
        actual_label = self._get_label(self._label_text)
        label_transform = Transform(self.label, actual_label, run_time=run_time)

        return AnimationGroup(create_anim, bgsquare_anim, label_transform)

    def change_label(self, text: str):

        run_time = self.config.label_change_run_time

        new_label = self._get_label(text)
        self._label_text = text
        return Transform(self.label, new_label, run_time=run_time)

    #TODO this is used in Bitcoin DAG only, REMOVE/REPLACE with create with label for consitency?
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
            t = getattr(mob, 'time', 0) + dt
            mob.time = t
            width = min_width + (max_width - min_width) * (np.sin(t * np.pi) + 1) / 2
            mob.set_stroke(color, width=width)

        return pulse_stroke

    ####################
    # Override Functions
    ####################

    # Override get_center() so it returns the center of the visual block
    def get_center(self) -> np.ndarray:
        """Override to return only the square's center, ignoring label positioning."""
        return self.square.get_center()