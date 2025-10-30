# blanim\blanim\core\base_visual_block.py

from __future__ import annotations

__all__ = ["BaseVisualBlock"]

from manim import VMobject, ParsableManimColor, Square, Text, BLUE, WHITE, Transform, BLACK, Create, AnimationGroup, \
    PURE_BLUE
from manim.typing import Point3DLike

#TODO test this (base_visual_block), kaspa/visual_block, and bitcoin/visual_block to verify they work as expected
class BaseVisualBlock(VMobject):
    """Base class for blockchain block visualization with primer pattern.

    This class handles only visual elements and animations for blockchain blocks,
    following the separation of concerns principle where visual rendering is
    independent of blockchain logic (consensus, parent selection, etc.).

    The block consists of a colored square with a text label. The label uses
    the "primer pattern" where an invisible placeholder is created first,
    then transformed to visible text. This ensures the label reference remains
    constant across transformations.

    Parameters
    ----------
    label_text : str
        Text to display on the block.
    position : Point3DLike
        3D coordinates [x, y, z] for block placement.
    block_color : ParsableManimColor, optional
        DEPRECATED: Use fill_color and stroke_color instead.
        Fallback color if fill_color/stroke_color not specified.
    fill_color : ParsableManimColor, optional
        Interior color of the square. Default is BLUE.
    fill_opacity : float, optional
        Opacity of the square fill (0=transparent, 1=opaque). Default is 0.2.
    stroke_color : ParsableManimColor, optional
        Border color of the square. Default is PURE_BLUE.
    stroke_width : float, optional
        Width of the square border. Default is 3.
    side_length : float, optional
        Length of each side of the square. Default is 0.7.
    label_font_size : int, optional
        Font size for the label text. Default is 24.
    label_color : ParsableManimColor, optional
        Color of the label text. Default is WHITE.

    Attributes
    ----------
    square : Square
        The visual square representing the block.
    label : Text
        The text label (uses primer pattern).
    _label_text : str
        Current text content of the label.

    Examples
    --------
    Basic usage::

        block = BaseVisualBlock("Genesis", [0, 0, 0])
        self.add(block)

    With custom styling::

        block = BaseVisualBlock(
            "Block 1",
            [1, 0, 0],
            fill_color=RED,
            fill_opacity=0.3,
            stroke_color=ORANGE,
            stroke_width=5
        )
    """

    def __init__(
            self,
            label_text: str,
            position: Point3DLike,
            block_color: ParsableManimColor = BLUE,
            fill_color: ParsableManimColor | None = None,
            fill_opacity: float = 0.2,
            stroke_color: ParsableManimColor | None = None,
            stroke_width: float = 3,
            side_length: float = 0.7,
            label_font_size: int = 24,
            label_color: ParsableManimColor = WHITE,
            create_run_time: float = 2.0,
            label_change_run_time: float = 1.0,
            **kwargs
    ) -> None:
        super().__init__(**kwargs)

        # Handle color parameters with fallback to block_color
        if fill_color is None:
            fill_color = block_color
        if stroke_color is None:
            stroke_color = PURE_BLUE

        # Store label text
        self._label_text = label_text

        #####Square#####
        self.square = Square(
            fill_color=fill_color,
            fill_opacity=fill_opacity,
            stroke_color=stroke_color,
            stroke_width=stroke_width,
            side_length=side_length
        )
        self.square.move_to(position)
        self.add(self.square)

        #####Label (Primer Pattern)#####
        # Create invisible primer with 5-character capacity
        self.label = Text(
            "00000",  # 5 0's for default capacity
            font_size=1,
            color=BLACK
        )
        self.label.move_to(self.square.get_center())
        self.add(self.label)

        # Store label styling parameters for _get_label
        self._label_font_size = label_font_size
        self._label_color = label_color

        self._create_run_time = create_run_time
        self._label_change_run_time = label_change_run_time

    def _get_label(self, text: str) -> Text:
        """Create a label Text object positioned at the square's center.

        This is an internal helper method used by create_with_label() and
        change_label() to generate properly positioned label objects.

        Parameters
        ----------
        text : str
            Text content for the label.

        Returns
        -------
        Text
            A Text mobject positioned at the square's center.

        Notes
        -----
        The label is positioned relative to self.square.get_center() rather
        than self.label.get_center() to ensure correct positioning during
        simultaneous movement and label change animations.
        """
        new_label = Text(
            text,
            font_size=self._label_font_size,
            color=self._label_color
        )
        new_label.move_to(self.square.get_center())
        return new_label

    def create_with_label(self, **kwargs):
        """Create animation with label fade-in/grow effect.

        Generates an AnimationGroup that creates the block (square and
        invisible primer label) and transforms the primer to visible text.
        The label fades in and grows from size 1/BLACK to the configured
        size and color as the block is drawn.

        This method is designed to be extended by child classes (e.g.,
        BitcoinVisualBlock, KaspaVisualBlock) which can extract the
        animations list and append additional elements like parent lines.

        Parameters
        ----------
        **kwargs
            Keyword arguments passed to Create animation.
            Supports 'run_time' to control animation duration.

        Returns
        -------
        AnimationGroup
            Group containing square creation and label transformation.

        Notes
        -----
        The primer pattern ensures the label has 5-character capacity for
        all future transformations via change_label(). The fade-in/grow
        effect is achieved by using matching run_time values for both
        Create(square) and Transform(label) animations in an AnimationGroup.

        See Also
        --------
        change_label : Transform label to new text after creation
        """
        # Get run_time from kwargs or use default
        run_time = kwargs.get('run_time', self._create_run_time)

        # Create the square only (not the entire self)
        create_anim = Create(self.square, run_time=run_time)

        # Transform primer to actual label (same run_time)
        actual_label = self._get_label(self._label_text)
        label_transform = Transform(self.label, actual_label, run_time=run_time)

        return AnimationGroup(create_anim, label_transform)

    def change_label(self, text: str, run_time: float | None = None, **kwargs):
        """Change the block's label text with animation.

        """
        if run_time is None:
            run_time = self._label_change_run_time

        new_label = self._get_label(text)
        self._label_text = text
        return Transform(self.label, new_label, run_time=run_time, **kwargs)