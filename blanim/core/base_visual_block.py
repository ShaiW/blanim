from __future__ import annotations

__all__ = ["BaseVisualBlock"]

from manim import VMobject, ParsableManimColor, Square, Text, BLUE, WHITE, Transform, BLACK, Create, AnimationGroup
from manim.typing import Point3DLike

#TODO test this (base_visual_block), kaspa/visual_block, and bitcoin/visual_block to verify they work as expected
class BaseVisualBlock(VMobject):
    """Base class for blockchain block visualization with primer pattern.

    This class handles only visual elements and animations for blockchain blocks,
    following the separation of concerns principle where visual rendering is
    independent of blockchain logic (consensus, parent selection, etc.).

    The block consists of a colored square with a text label. The label uses
    the "primer pattern" - initialized with an invisible 5-character primer
    that enables smooth text transformations without recreating the mobject.
    When the block is created, the label fades in and grows from invisible
    (size 1, BLACK) to visible (size 24, WHITE) simultaneously with the block.

    Architecture Notes
    ------------------
    - Parent lines are NOT submobjects and must be added to scenes separately
    - Lines use UpdateFromFunc to avoid automatic movement propagation
    - Position is inherited from the square submobject
    - Label and square are sibling submobjects for independent animation
    - Primer pattern maintains 5-character capacity for all label transformations

    Parameters
    ----------
    label_text : str
        Text to display on the block. Maximum 5 characters recommended.
    position : Point3DLike
        3D coordinates [x, y, z] where the block should be positioned.
    block_color : ParsableManimColor, optional
        Color of the block square. Default is BLUE.

    Attributes
    ----------
    square : Square
        The main square visual element (0.7 side length, full opacity).
    label : Text
        Text label displayed on the square using primer pattern.
        Initialized as invisible 5-character primer ("00000" at size 1, BLACK).
    max_label_chars : int
        Maximum safe character count for label transformations (default: 5).
    label_font_size : int
        Font size for visible label text (default: 24).
    label_color : ParsableManimColor
        Color for visible label text (default: WHITE).
    _label_text : str
        Stored label text for primer transformation.

    Examples
    --------
    Creating and animating a block::

        block = BaseVisualBlock("Gen", [0, 0, 0])
        self.play(block.create_with_label())  # Label fades in as block draws
        self.play(block.change_label("New"))  # Safe transform up to 5 chars

    See Also
    --------
    BitcoinVisualBlock : Single-parent chain visualization
    KaspaVisualBlock : Multi-parent DAG visualization
    """
    def __init__(self, label_text: str, position: Point3DLike, block_color: ParsableManimColor = BLUE) -> None:
        super().__init__()

        #####Square#####
        self.square = Square(
            color=block_color,
            fill_opacity=1,
            side_length=0.7
        )

        self.square.move_to(position)
        self.add(self.square)

        #####Label (Primer Pattern)#####
        self._label_text = label_text

        self.max_label_chars = 5  #note primer is set up for max 5 characters, exceeding 5 characters in your label could cause problems
        self.label_font_size = 24
        self.label_color: ParsableManimColor = WHITE

        # Create invisible primer with maximum capacity
        primer_string = "0" * self.max_label_chars
        self.label = Text(
            primer_string,
            font_size=1,  # Invisible size
            color=BLACK  # Invisible color
        )

        self.label.move_to(self.square.get_center())
        self.add(self.label)

    def create_with_label(self, **kwargs):
        """Create animation with label fade-in/grow effect.

        Generates an AnimationGroup that simultaneously creates the block
        (square and invisible primer label) and transforms the primer to
        visible text. The label fades in and grows from size 1/BLACK to
        size 24/WHITE as the block is drawn.

        This method is designed to be extended by child classes (e.g.,
        BitcoinVisualBlock, KaspaVisualBlock) which can extract the
        animations list and append additional elements like parent lines.

        Parameters
        ----------
        **kwargs
            Keyword arguments passed to Create and Transform animations.
            Common options include `run_time` (default: 1.0).

        Returns
        -------
        AnimationGroup
            Combined animation for block creation and label transformation.
            Both animations use the same run_time for synchronized effect.

        Examples
        --------
        Basic usage::

            block = BaseVisualBlock("Gen", [0, 0, 0])
            self.play(block.create_with_label(run_time=1.5))

        Extended by child classes::

            # In BitcoinVisualBlock.create_with_lines()
            base_group = super().create_with_label(**kwargs)
            animations = list(base_group.animations)
            animations.append(Create(self.parent_line))
            return AnimationGroup(*animations)

        Notes
        -----
        The primer pattern ensures the label has 5-character capacity for
        all future transformations via change_label(). The fade-in/grow
        effect is achieved by using matching run_time values for both
        Create(self) and Transform(label) animations in an AnimationGroup.

        See Also
        --------
        change_label : Transform label to new text after creation
        """
        # Get run_time from kwargs or use default
        run_time = kwargs.get('run_time', 1.0)

        # Create the block (square + invisible primer)
        create_anim = Create(self, run_time=run_time)

        # Transform primer to actual label (same run_time)
        actual_label = self._get_label(self._label_text)
        label_transform = Transform(self.label, actual_label, run_time=run_time)

        return AnimationGroup(create_anim, label_transform)

    def _get_label(self, text: str) -> Text:
        """Create a new label mobject at the primer location.

        This internal method generates a new Text mobject positioned at the
        current label's center, enabling smooth Transform animations.

        Parameters
        ----------
        text : str
            The text content for the new label.

        Returns
        -------
        Text
            A new Text mobject positioned at the primer location.

        Notes
        -----
        Similar to UniversalNarrationManager.get_narration() pattern.
        """
        label = Text(
            text,
            font_size=self.label_font_size,
            color=self.label_color
        )
        label.move_to(self.label.get_center())
        return label

    def change_label(self, text: str, run_time: float = 0.5, **kwargs):
        """Change the block's label text with animation.

        Uses the primer pattern to transform the label smoothly without
        recreating the entire block mobject. The label is transformed
        in-place using Manim's Transform animation.

        Parameters
        ----------
        text : str
            New text to display on the block.
        run_time : float, optional
            Duration of the transform animation in seconds. Default is 0.5.
        **kwargs
            Additional keyword arguments passed to Transform animation.

        Returns
        -------
        Transform
            The Transform animation to be played via scene.play().

        Examples
        --------
        In a scene::

            block = BaseVisualBlock("1", [0, 0, 0])
            self.add(block)
            self.play(block.change_label("42"))
        """
        new_label = self._get_label(text)
        self._label_text = text
        return Transform(self.label, new_label, run_time=run_time, **kwargs)