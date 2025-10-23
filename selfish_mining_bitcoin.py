from __future__ import annotations

from manim.typing import Point3DLike
from common import *
import random
from typing import TYPE_CHECKING, Literal

if TYPE_CHECKING:
    from typing_extensions import TypeAlias

##########WARNINGS##########
# README: !!!Lines are stored in block objects BUT do not reference the block, lines use the square(visual block) for end points.
# README: !!!Do NOT cache any Mobject that gets removed with ReplacementTransform (e.g. state/transition/caption text), create new Mobjects instead.

##########NOTES##########

"""  
MANUAL RACE RESOLUTION IMPLEMENTATION PLAN  
===========================================  

This plan outlines the changes needed to add manual control over race resolution  
for educational animations explaining selfish mining step-by-step.  

PROBLEM  
-------  
Currently, `_check_if_race_continues()` automatically triggers race resolution at  
the end of every `advance_selfish_chain()` and `advance_honest_chain()` call.  
This prevents:  
1. Pausing between blocks to add narration  
2. Manually revealing the selfish chain at specific moments  
3. Demonstrating individual steps without triggering automatic resolution  

IMPLEMENTATION CHECKLIST  
-------------------------  

[ ] 1. Add `auto_resolve` Parameter  
    - Add to `SelfishMiningSquares.__init__()`:  
      ```python  
      def __init__(self, scene: HUD2DScene, alpha=0.3, gamma=0.5,   
                   enable_narration=False, auto_resolve=True):  
          # ... existing code ...  
          self.auto_resolve = auto_resolve  
      ```
[ ] 2. Modify `_check_if_race_continues()`  
    - Make race resolution conditional:  
      ```python  
      def _check_if_race_continues(self) -> None:  
          '''Evaluate race conditions and trigger resolution if needed.'''  
          if not self.auto_resolve:  
              return  # Skip automatic resolution  
          # ... existing resolution logic ...  
      ```
[ ] 3. Break Down `_animate_race_resolution()` into Steps  
    - Extract three separate public methods:  

    a) `vertical_shift_chains(caption: str = None) -> None`  
       - Extracts vertical shift logic from `_animate_race_resolution()`  
       - Aligns winning chain with genesis y-position  
       - Accepts optional caption parameter  

    b) `horizontal_shift_camera(caption: str = None) -> None`  
       - Extracts horizontal camera shift logic  
       - Positions winning block at genesis x-position  
       - Accepts optional caption parameter  

    c) `finalize_race_winner(caption: str = None) -> None`  
       - Extracts state transition logic  
       - Updates state to "0" (without changing label to "Gen")  
       - Accepts optional caption parameter  

[ ] 4. Create Composite `resolve_race()` Method  
    - High-level method for backward compatibility:  
      ```python  
      def resolve_race(self, winner: str, caption: str = None,  
                       vertical_caption: str = None,  
                       horizontal_caption: str = None,  
                       finalize_caption: str = None) -> None:  
          '''Manually trigger race resolution with optional per-step captions.  

          Parameters  
          ----------  
          winner : str  
              Either "honest" or "selfish"  
          caption : str, optional  
              Overall caption for the resolution  
          vertical_caption : str, optional  
              Caption for vertical shift step  
          horizontal_caption : str, optional  
              Caption for horizontal camera shift step  
          finalize_caption : str, optional  
              Caption for finalization step  
          '''  
          if caption:  
              self.update_caption(caption)  
          self.vertical_shift_chains(vertical_caption)  
          self.horizontal_shift_camera(horizontal_caption)  
          self.finalize_race_winner(finalize_caption)  
      ```
[ ] 5. Fix `reveal_selfish_chain()` Method  
    - Create general reveal method (NOT tied to tie scenario):  
      ```python  
      def reveal_selfish_chain(self, caption: str = None,  
                              reposition: bool = False,  
                              target_y: float = None) -> None:  
          '''Manually reveal the selfish chain.  

          Makes selfish chain visible without assuming tie state.  
          Does NOT automatically transition to state 0'.  
          Works regardless of chain lengths (1 vs 2, 3 vs 1, etc.).  

          Parameters  
          ----------  
          caption : str, optional  
              Caption to display during reveal  
          reposition : bool, optional  
              Whether to reposition chain (default: False)  
          target_y : float, optional  
              Target y-position if repositioning  
          '''  
          if not self.selfish_chain.blocks:  
              return  
          if caption:  
              self.update_caption(caption)  
          # Implementation depends on hiding mechanism (opacity/position)  
      ```  
    - Keep `_reveal_selfish_chain_for_tie()` as PRIVATE method  
    - Only called internally when automatic tie detection triggers  

[ ] 6. Make `advance_honest_on_selfish_chain()` Public  
    - Rename from `_advance_honest_on_selfish_chain()` (remove underscore)  
    - Update docstring to indicate it's now public API  

[ ] 7. Add `update_captions()` for Sequential Narrations  
    ```python  
    def update_captions(self, captions: list[str],   
                       wait_between: float = None) -> None:  
        '''Update caption multiple times with waits in between.  

        Parameters  
        ----------  
        captions : list[str]  
            List of caption texts to display sequentially  
        wait_between : float, optional  
            Time to wait between captions.   
            If None, uses AnimationTimingConfig.WAIT_TIME  
        '''  
        if wait_between is None:  
            wait_between = AnimationTimingConfig.WAIT_TIME  
        for caption in captions:  
            self.update_caption(caption)  
            self.scene.wait(wait_between)  
    ```
[ ] 8. Update All Docstrings  
    - Document new public methods  
    - Add examples showing manual control usage  
    - Note backward compatibility (auto_resolve defaults to True)  

EXAMPLE USAGE  
-------------  
```python  
class SelfishMiningManualExplanation(HUD2DScene):  
    def construct(self):  
        # Disable automatic resolution  
        sm = SelfishMiningSquares(self, 0.33, 0.5,   
                                  enable_narration=True,   
                                  auto_resolve=False)  

        # Build up to resolution  
        sm.advance_selfish_chain("Selfish miner builds lead")  
        sm.advance_selfish_chain()  
        sm.advance_honest_chain("Honest miners catch up")  
        sm.advance_honest_chain()  

        # Multiple narrations before revealing  
        sm.update_captions([  
            "Both chains are now tied",  
            "The selfish miner must reveal their chain",  
            "Network propagation determines the winner"  
        ])  

        # Manual resolution with narration at each step  
        sm.reveal_selfish_chain("Selfish chain revealed!")  
        sm.vertical_shift_chains("Aligning chains vertically...")  
        sm.horizontal_shift_camera("Repositioning camera...")  
        sm.finalize_race_winner("Race complete!")  

        # Or use composite method with per-step captions  
        sm.resolve_race(  
            "selfish",  
            vertical_caption="Aligning chains...",  
            horizontal_caption="Repositioning camera...",  
            finalize_caption="New race begins!"  
        )
"""

##########End Notes##########

class Block:
    """A blockchain block visualization composed of Manim mobjects.

    Represents a single block in a blockchain, consisting of a square shape,
    text label, and optional connecting line to a parent block. Blocks can
    form a tree structure through parent-child relationships.

    .. warning::
        **Animation Conflicts**: When animating blocks with FollowLines, the line uses
        :class:`~.UpdateFromFunc` animations and will conflict with transform animations
        (`.animate.shift()`, `.animate.scale()`, etc.) if included in the same
        :meth:`~.Scene.play` call. Use :meth:`get_transform_safe_mobjects` for transform
        animations, or manually exclude lines.

    Parameters
    ----------
    label_text : str
        The text label displayed in the center of the block
    position : Point3DLike
        The initial position of the block in the scene
    block_color : ParsableManimColor
        The color of the block's square (e.g., BLUE, "#FF0000")
    parent_block : Block, optional
        The parent block to connect to. If provided, a :class:`FollowLine` is created
        and this block is added to the parent's children list. Default is None (genesis block).

    Attributes
    ----------
    square : Square
        The visual square representing the block (configured via LayoutConfig)
    label : Text
        The text label displayed on the block (configured via LayoutConfig)
    line : FollowLine or None
        Connection line to parent block, or None for genesis blocks
    children : list[Block]
        List of child blocks connected to this block
    next_genesis : bool
        Flag indicating if this block will become the next genesis block
    parent_block : Block or None
        Reference to the parent block, or None for genesis blocks

    Examples
    --------

    .. code-block:: python

        # Create a genesis block (no parent)
        genesis = Block("0", position=ORIGIN, block_color=BLUE)
        scene.add(*genesis.get_mobjects())

        # Create child blocks forming a chain
        block1 = Block("1", position=RIGHT * 2, block_color=GREEN, parent_block=genesis)
        block2 = Block("2", position=RIGHT * 4, block_color=GREEN, parent_block=block1)

        scene.add(*block1.get_mobjects())
        scene.add(*block2.get_mobjects())

    .. code-block:: python

        # Animate block movement (transform-safe)
        blocks = [genesis, block1, block2]

        # Correct: Separate block mobjects from lines
        self.play(
            *[mob.animate.shift(UP) for block in blocks
              for mob in block.get_transform_safe_mobjects()],
            *[block.line.create_update_animation() for block in blocks if block.has_line()]
        )

    See Also
    --------
    :class:`FollowLine` : Dynamic line that connects blocks
    :class:`~.Square` : Manim square mobject used for block visualization
    :class:`~.Text` : Manim text mobject used for block labels
    :class:`~.Transform` : Animation used by :meth:`change_label_to`

    Notes
    -----
    - Block styling is controlled by `LayoutConfig` constants:
      - `BLOCK_SIDE_LENGTH`: Size of the square
      - `BLOCK_FILL_OPACITY`: Opacity of the square fill
      - `LABEL_FONT_SIZE`: Font size of the label text
      - `LABEL_COLOR`: Color of the label text
    - The `FollowLine` connects `self.square` to `parent_block.square`, not the Block objects directly
    - Use :meth:`get_transform_safe_mobjects` when animating with `.animate` syntax
    - Use :meth:`get_mobjects` for non-transform animations (FadeIn, Create, etc.)
    - Label text is stored separately in `_label_text` for retrieval via :meth:`get_label_text`
    """

    def __init__(self, label_text: str, position: Point3DLike, block_color: str, parent_block: 'Block' = None) -> None:
        """Initialize a Block with visual components and optional parent connection.

        Creates a square, label, and optional connecting line. If a parent block is provided,
        this block is automatically added to the parent's children list.

        Parameters
        ----------
        label_text : str
            The text label displayed in the center of the block
        position : Point3DLike
            The initial position of the block in the scene
        block_color : str
            The color of the block's square
        parent_block : Block, optional
            The parent block to connect to. If provided, a FollowLine is created
            and this block is added to the parent's children list.
        """
        # Visual components (existing Manim objects)
        self.square = Square(
            side_length=LayoutConfig.BLOCK_SIDE_LENGTH,
            color=block_color,
            fill_opacity=LayoutConfig.BLOCK_FILL_OPACITY
        )
        self.square.move_to(position)

        self.label = Text(
            label_text,
            font_size=LayoutConfig.LABEL_FONT_SIZE,
            color=LayoutConfig.LABEL_COLOR
        )
        self.label.move_to(self.square.get_center())

        # Store the label text
        self._label_text = label_text

        self.children = []
        self.next_genesis = False

        self.parent_block = parent_block
        if parent_block:
            parent_block.children.append(self)

        # Store line directly - but it references squares, not Blocks
        if parent_block:
            self.line = FollowLine(
                start_mobject=self.square,  # ← References Square, not Block
                end_mobject=parent_block.square  # ← References Square, not Block
            )
        else:
            self.line = None

    def change_label_to(self, new_text: str, run_time: float = None) -> Animation:
        """Create a Transform animation to change the label text.

        The label mobject remains the same object in memory, but its appearance
        is transformed to display the new text. This is similar to the HUD primer
        pattern used for state/caption text.

        Parameters
        ----------
        new_text : str
            The new text to display on the label
        run_time : float, optional
            Animation duration. If None, uses `AnimationTimingConfig.FADE_IN_TIME`

        Returns
        -------
        Animation
            :class:`~.Transform` animation that morphs the current label to the new text

        Examples
        --------

        .. code-block:: python

            block = Block("0", ORIGIN, BLUE)
            scene.add(*block.get_mobjects())

            # Change label from "0" to "1"
            scene.play(block.change_label_to("1"))

            # Custom run time
            scene.play(block.change_label_to("2", run_time=0.5))

        Notes
        -----
        - Uses :class:`~.Transform`, not :class:`~.ReplacementTransform`
        - Updates internal `_label_text` attribute
        - Label position remains centered on the square
        """
        target_label = Text(
            new_text,
            font_size=LayoutConfig.LABEL_FONT_SIZE,
            color=LayoutConfig.LABEL_COLOR
        )
        target_label.move_to(self.square.get_center())
        self._label_text = new_text

        if run_time is None:
            run_time = AnimationTimingConfig.FADE_IN_TIME

        return Transform(self.label, target_label, run_time=run_time)

    def get_mobjects(self):
        """Return list of Manim mobjects for rendering.

        Returns all visual components (square, label, and line if present)
        that need to be added to the scene.

        .. warning::
            If using transform animations (`.animate.shift()`, `.animate.scale()`, etc.),
            use :meth:`get_transform_safe_mobjects` instead to avoid animation conflicts
            with the FollowLine's :class:`~.UpdateFromFunc` animation. Safe to use with
            :class:`~.FadeIn`, :class:`~.FadeOut`, :class:`~.Create`, :class:`~.Uncreate`,
            and style animations.

        Returns
        -------
        list[Mobject]
            List containing square, label, and optionally the connecting line

        See Also
        --------
        :meth:`get_transform_safe_mobjects` : Get mobjects safe for transform animations
        """
        mobjects = [self.square, self.label]
        if self.line:
            mobjects.append(self.line)
        return mobjects

    def get_label_text(self) -> str:
        """Get the text content of the block's label.

        Returns
        -------
        str
            The text displayed on the block's label
        """
        return self._label_text

    def get_transform_safe_mobjects(self) -> list:
        """Get mobjects safe for transform animations without conflicts.

        Returns square and label only, excluding the FollowLine which uses
        :class:`~.UpdateFromFunc` and would conflict with transform animations like
        `.animate.shift()`, `.animate.scale()`, `.animate.rotate()`, etc.

        Use this method when animating block positions or transformations.
        The line should be animated separately using `line.create_update_animation()`.

        Returns
        -------
        list[Mobject]
            List containing only square and label (excludes line)

        Examples
        --------

        .. code-block:: python

            # Correct usage for transform animations
            all_mobjects = []
            for block in chain.blocks:
                all_mobjects.extend(block.get_transform_safe_mobjects())

            self.play(
                *[mob.animate.shift(RIGHT) for mob in all_mobjects],
                *[block.line.create_update_animation()
                  for block in chain.blocks if block.has_line()]
            )

        See Also
        --------
        :meth:`get_mobjects` : Get all mobjects including line
        :class:`FollowLine` : Documentation for line animation conflicts
        """
        return [self.square, self.label]

    def move_to(self, position):
        """Move block to a new position.

        Updates both the square and label positions. The line position
        must be updated separately by playing its UpdateFromFunc animation
        via `line.create_update_animation()`.

        Parameters
        ----------
        position : Point3DLike
            The new position for the block's center

        Notes
        -----
        - Does not return self (not chainable)
        - Line does NOT update automatically - must play `line.create_update_animation()`
        - Label stays centered on square

        Examples
        --------

        .. code-block:: python

            # Move block and update line
            block.move_to(RIGHT * 2)
            if block.has_line():
                self.play(block.line.create_update_animation())
        """
        self.square.move_to(position)
        self.label.move_to(self.square.get_center())

    def get_center(self):
        """Get the center position of the block.

        Returns
        -------
        Point3D
            The center coordinates of the block's square
        """
        return self.square.get_center()

    def get_left(self):
        """Get the left edge position of the block.

        Returns
        -------
        Point3D
            The coordinates of the block's left edge
        """
        return self.square.get_left()

    def get_right(self):
        """Get the right edge position of the block.

        Returns
        -------
        Point3D
            The coordinates of the block's right edge
        """
        return self.square.get_right()

    def set_as_next_genesis(self):
        """Mark this block as the next genesis block.

        Sets the `next_genesis` flag to True, indicating this block will
        become a genesis block in the next epoch or chain split.

        See Also
        --------
        :meth:`is_next_genesis` : Check if block is marked as next genesis
        :meth:`is_genesis` : Check if block is currently a genesis block
        """
        self.next_genesis = True

    def is_next_genesis(self) -> bool:
        """Check if this block is marked as the next genesis block.

        Returns
        -------
        bool
            True if this block is marked as next genesis, False otherwise

        See Also
        --------
        :meth:`set_as_next_genesis` : Mark block as next genesis
        """
        return self.next_genesis

    def is_genesis(self) -> bool:
        """Check if this block is a genesis block.

        A genesis block is one with no parent (the first block in a chain).

        Returns
        -------
        bool
            True if this block has no parent, False otherwise

        See Also
        --------
        :meth:`is_next_genesis` : Check if block will become genesis
        """
        return self.parent_block is None

    def has_line(self) -> bool:
        """Check if this block has a connecting line to a parent.

        Returns
        -------
        bool
            True if a connecting line exists, False otherwise

        Notes
        -----
        Equivalent to checking `self.line is not None` or `not self.is_genesis()`
        """
        return self.line is not None

    def __repr__(self) -> str:
        """String representation for debugging.

        Returns
        -------
        str
            A string showing the block's label, parent, children, and genesis status

        Examples
        --------

        .. code-block:: python

            genesis = Block("0", ORIGIN, BLUE)
            block1 = Block("1", RIGHT * 2, GREEN, parent_block=genesis)
            print(repr(block1))
            # Output: Block(label=1, parent=0, children=[], next_genesis=False)
        """
        parent_label = self.parent_block.get_label_text() if self.parent_block else "None"
        children_labels = [child.get_label_text() for child in self.children]
        return f"Block(label={self.get_label_text()}, parent={parent_label}, children={children_labels}, next_genesis={self.next_genesis})"


class FollowLine(Line):
    """A Line that dynamically connects two mobjects via animation.

    This line does NOT use automatic updaters. Instead, it provides a method
    to create an UpdateFromFunc animation that must be explicitly played
    to update the line's position.

    Parameters
    ----------
    start_mobject : Mobject
        The mobject to connect from (line starts at its left edge)
    end_mobject : Mobject
        The mobject to connect to (line ends at its right edge)

    Attributes
    ----------
    start_mobject : Mobject
        Reference to the starting mobject for position tracking
    end_mobject : Mobject
        Reference to the ending mobject for position tracking
    buff : float
        Buffer distance from mobject edges (inherited from Line)

    Examples
    --------

    .. code-block:: python

        # Create two blocks
        block1 = Block("A", LEFT * 2, BLUE)
        block2 = Block("B", RIGHT * 2, GREEN, parent_block=block1)

        # Line is created automatically in Block.__init__
        # To animate block movement with line update:
        self.play(
            block2.square.animate.shift(UP),
            block2.line.create_update_animation()
        )

    .. code-block:: python

        # Manual FollowLine creation
        square1 = Square().shift(LEFT * 2)
        square2 = Square().shift(RIGHT * 2)
        line = FollowLine(square1, square2)

        self.add(square1, square2, line)

        # Animate with line update
        self.play(
            square1.animate.shift(DOWN),
            square2.animate.shift(UP),
            line.create_update_animation()
        )

    See Also
    --------
    :class:`Block` : Uses FollowLine for parent-child connections
    :class:`~.UpdateFromFunc` : Animation class used for line updates
    :class:`~.Line` : Parent class providing root line functionality

    Notes
    -----
    - Line updates via :class:`~.UpdateFromFunc` conflict with transform animations
    - Always use :meth:`create_update_animation` when animating connected mobjects
    - The ``suspend_mobject_updating=False`` parameter ensures line updates during animation
    - Stroke width is preserved via ``_fixed_stroke_width`` to prevent scaling issues
    - Configuration controlled by ``LayoutConfig.LINE_BUFFER``, ``LayoutConfig.LINE_COLOR``,
      and ``LayoutConfig.LINE_STROKE_WIDTH``
    """

    def __init__(self, start_mobject, end_mobject):
        """Initialize FollowLine connecting two mobjects.

        Parameters
        ----------
        start_mobject : Mobject
            The mobject to connect from (line starts at its left edge)
        end_mobject : Mobject
            The mobject to connect to (line ends at its right edge)
        """
        # Initialize Line with current positions of the mobjects
        super().__init__(
            start=start_mobject.get_left(),
            end=end_mobject.get_right(),
            buff=LayoutConfig.LINE_BUFFER,
            color=LayoutConfig.LINE_COLOR,
            stroke_width=LayoutConfig.LINE_STROKE_WIDTH,
        )
        # Store references to mobjects for animation-based updates
        self.start_mobject = start_mobject
        self.end_mobject = end_mobject
        self._fixed_stroke_width = LayoutConfig.LINE_STROKE_WIDTH

    def _update_position_and_size(self, _mobject):
        """Update function called by UpdateFromFunc animation.

        This is NOT an automatic updater - it only runs when the
        UpdateFromFunc animation created by :meth:`create_update_animation`
        is played via :meth:`~.Scene.play`.

        Parameters
        ----------
        _mobject : Mobject
            The mobject being updated (unused, required by UpdateFromFunc signature)

        Notes
        -----
        Updates line endpoints to match current positions of start and end mobjects.
        Preserves stroke width to prevent scaling issues.
        """
        new_start = self.start_mobject.get_left()
        new_end = self.end_mobject.get_right()
        self.set_stroke(width=self._fixed_stroke_width)
        self.set_points_by_ends(new_start, new_end, buff=self.buff)

    def create_update_animation(self):
        """Create an UpdateFromFunc animation to play alongside other animations.

        The animation duration automatically matches other animations in the same
        :meth:`~.Scene.play` call.

        Returns
        -------
        UpdateFromFunc
            Animation that updates line position each frame

        Examples
        --------

        .. code-block:: python

            # Line updates while block moves
            self.play(
                block.animate.shift(RIGHT),
                line.create_update_animation()
            )

        .. code-block:: python

            # Multiple blocks moving simultaneously
            self.play(
                block1.square.animate.shift(UP),
                block2.square.animate.shift(DOWN),
                block1.line.create_update_animation(),
                block2.line.create_update_animation()
            )

        See Also
        --------
        :class:`~.UpdateFromFunc` : The animation class used
        :meth:`Block.get_transform_safe_mobjects` : Get mobjects safe for transform animations

        Notes
        -----
        - Must be played in the same :meth:`~.Scene.play` call as the mobject movements
        - Uses ``suspend_mobject_updating=False`` to allow updates during animation
        - Animation duration matches the longest animation in the play() call
        """
        return UpdateFromFunc(
            self,
            update_function=self._update_position_and_size,
            suspend_mobject_updating=False
        )


class ChainBranch:
    """Container for blockchain branch visualization with automatic block coloring.

    Manages a collection of blocks that form a single branch (honest or selfish chain).
    Automatically assigns block colors based on label prefixes: 'H' for honest (blue),
    'S' for selfish (red), or genesis color for blocks without these prefixes.

    Parameters
    ----------
    chain_type : str
        Type identifier for this chain branch (e.g., "honest", "selfish")

    Attributes
    ----------
    chain_type : str
        The type identifier for this branch
    blocks : list[Block]
        Ordered list of blocks in this branch

    Examples
    --------

    .. code-block:: python

        # Create honest chain branch
        honest_chain = ChainBranch("honest")

        # Add genesis block
        genesis = Block("0", ORIGIN, LayoutConfig.GENESIS_BLOCK_COLOR)

        # Add blocks with automatic coloring
        block1, line1 = honest_chain.add_block("H1", RIGHT * 2, genesis)
        block2, line2 = honest_chain.add_block("H2", RIGHT * 4, block1)

        # Get all mobjects for scene
        self.add(*honest_chain.get_all_mobjects())

    .. code-block:: python

        # Create selfish chain branch
        selfish_chain = ChainBranch("selfish")

        # Add selfish blocks (automatically colored red)
        s_block1, s_line1 = selfish_chain.add_block("S1", RIGHT * 2, genesis)
        s_block2, s_line2 = selfish_chain.add_block("S2", RIGHT * 4, s_block1)

    See Also
    --------
    :class:`Block` : Individual block visualization
    :class:`FollowLine` : Line connecting blocks
    :class:`LayoutConfig` : Color configuration constants

    Notes
    -----
    - Block colors determined by label prefix:
      - 'H' prefix → ``LayoutConfig.HONEST_CHAIN_COLOR`` (blue)
      - 'S' prefix → ``LayoutConfig.SELFISH_CHAIN_COLOR`` (red)
      - No prefix → ``LayoutConfig.GENESIS_BLOCK_COLOR`` (blue)
    - Each block creates its own :class:`FollowLine` internally via :class:`Block.__init__`
    - Blocks are stored in order of addition in the ``blocks`` list
    - Use :meth:`get_all_mobjects` to retrieve all visual elements for scene rendering
    """
    def __init__(self, chain_type: str):
        """Initialize chain branch with type identifier.

        Parameters
        ----------
        chain_type : str
            Type identifier for this chain branch (e.g., "honest", "selfish")
        """
        self.chain_type = chain_type
        self.blocks = []

    def add_block(self, label: str, position: Point3DLike, parent_block: Block):
        """Add a block to this chain with automatic color assignment.

        Creates a new block with color determined by label prefix and adds it to
        the branch. The block automatically creates its own connecting line to the
        parent block via :class:`Block.__init__`.

        Parameters
        ----------
        label : str
            Block label text. Prefix determines color: 'H' for honest (blue),
            'S' for selfish (red), or genesis color for others
        position : Point3DLike
            Position for the new block in the scene
        parent_block : Block
            Parent block to connect to (creates line automatically)

        Returns
        -------
        tuple[Block, FollowLine | None]
            Tuple of (created block, its connecting line). Line is None for genesis blocks.

        Examples
        --------

        .. code-block:: python

            chain = ChainBranch("honest")
            genesis = Block("0", ORIGIN, LayoutConfig.GENESIS_BLOCK_COLOR)

            # Add honest block (blue)
            h_block, h_line = chain.add_block("H1", RIGHT * 2, genesis)

            # Add selfish block (red)
            s_block, s_line = chain.add_block("S1", RIGHT * 4, genesis)

        See Also
        --------
        :class:`Block` : Block class that handles line creation
        :class:`LayoutConfig` : Contains color constants

        Notes
        -----
        - Block is automatically appended to ``self.blocks`` list
        - Line is extracted from ``block.line`` for separate tracking
        - Color assignment is case-sensitive (must be uppercase 'H' or 'S')
        """
        # Determine color based on block label prefix
        if label.startswith("H"):
            block_color = LayoutConfig.HONEST_CHAIN_COLOR
        elif label.startswith("S"):
            block_color = LayoutConfig.SELFISH_CHAIN_COLOR
        else:
            block_color = LayoutConfig.GENESIS_BLOCK_COLOR

            # Block constructor now handles line creation
        block = Block(label, position, block_color, parent_block=parent_block)
        self.blocks.append(block)

        # Extract line from block for separate tracking
        line = block.line

        return block, line

    def get_all_mobjects(self) -> list:
        """Get all mobjects including blocks and lines for scene rendering.

        Collects all visual elements (squares, labels, and lines) from all blocks
        in this chain branch. Use this method to add the entire chain to a scene.

        Returns
        -------
        list
            List of all mobjects from all blocks (squares, labels, and lines)

        Examples
        --------

        .. code-block:: python

            chain = ChainBranch("honest")
            # ... add blocks to chain ...

            # Add entire chain to scene
            self.add(*chain.get_all_mobjects())

        .. code-block:: python

            # Animate entire chain
            chain_mobjects = chain.get_all_mobjects()
            self.play(*[FadeIn(mob) for mob in chain_mobjects])

        See Also
        --------
        :meth:`Block.get_mobjects` : Returns mobjects for a single block

        Notes
        -----
        - Iterates through all blocks in ``self.blocks`` list
        - Calls :meth:`Block.get_mobjects` for each block
        - Returns flattened list of all mobjects (not grouped by block)
        - Includes squares, labels, and lines from all blocks
        """
        mobjects = []
        for block in self.blocks:
            mobjects.extend(block.get_mobjects())

        return mobjects


class NarrationTextFactory:
    """Factory for creating HUD text mobjects with primer-based Transform support.

    Creates text mobjects for state labels, transitions, and captions in blockchain
    visualizations. Designed to work with :class:`HUD2DScene`'s primer pattern where
    invisible text is created first, then transformed to visible text.

    .. warning::
        **Text Type Compatibility**: The primer pattern works with :class:`~.Text`,
        :class:`~.MathTex`, and :class:`~.Tex` individually, but mixing types
        (e.g., Text → MathTex) fails due to incompatible submobject structures.
        Pick ONE text type and stick with it throughout the scene.

    Parameters
    ----------
    No parameters required.

    Attributes
    ----------
    state_text_position : Vector3D
        Position for state text (default: DOWN)
    caption_text_position : Vector3D
        Position for caption text (default: UP)
    max_state_chars : int
        Maximum character capacity for state text primers (default: 20)
    max_caption_chars : int
        Maximum character capacity for caption text primers (default: 100)

    Examples
    --------

    .. code-block:: python

        # Create factory and primers
        factory = NarrationTextFactory()
        state_primer = factory.create_primer_text(
            factory.max_state_chars,
            factory.state_text_position
        )
        caption_primer = factory.create_primer_text(
            factory.max_caption_chars,
            factory.caption_text_position
        )

        # Register primers as fixed in frame
        self.add_fixed_in_frame_mobjects(state_primer, caption_primer)

        # Create visible text for Transform
        state_text = factory.get_state("1")
        self.play(Transform(state_primer, state_text))

    .. code-block:: python

        # Create transition text
        transition = factory.get_transition("1", "0prime")
        self.play(Transform(state_primer, transition))

        # Create caption text
        caption = factory.get_caption("Honest miner finds block")
        self.play(Transform(caption_primer, caption))

    See Also
    --------
    :class:`HUD2DScene` : Scene class that uses this factory
    :class:`NarrationManager` : Manager that wraps this factory
    :class:`~.Text` : Manim text mobject class used
    :class:`~.Transform` : Animation used with factory output

    Notes
    -----
    **Text Type Compatibility**:

    Tested combinations:
    - Text → Text: ✅ Works
    - MathTex → MathTex: ✅ Works
    - Tex → Tex: ✅ Works
    - Text → MathTex → Tex: ❌ Fails

    Untested combinations:
    - MathTex ↔ Tex: Unknown (both inherit from :class:`~.SingleStringMathTex`)
    - Text with different fonts: Unknown
    - MarkupText: Unknown

    **Character Counting**:
    - Spaces do NOT count toward character capacity
    - Only visible characters (letters, numbers, symbols) count
    - LaTeX commands do not count as characters

    **Configuration Dependencies**:
    - Uses ``LayoutConfig.STATE_FONT_SIZE`` for state text
    - Uses ``LayoutConfig.CAPTION_FONT_SIZE`` for caption text
    - Uses ``LayoutConfig.STATE_TEXT_COLOR`` for state text color
    - Uses ``LayoutConfig.CAPTION_TEXT_COLOR`` for caption text color

    **Future Expansion**:
    To support multiple text types:
    1. Test MathTex ↔ Tex compatibility
    2. Consider separate primer pools per compatible type group
    3. Document character counting differences per type
    """

    def __init__(self):
        """Initialize factory with default positions and character capacities.

        Sets up default positions (DOWN for state, UP for caption) and maximum
        character capacities (20 for state, 100 for caption).
        """
        self.state_text_position = DOWN
        self.caption_text_position = UP
        self.max_state_chars = 20
        self.max_caption_chars = 100

    @staticmethod
    def create_primer_text(max_chars: int, position) -> Text:
        """Create invisible primer text with maximum character capacity.

        Creates a black (invisible) text mobject filled with '0' characters to
        establish the maximum capacity for Transform animations. This primer must
        be added to fixed-in-frame before any transforms.

        Parameters
        ----------
        max_chars : int
            Maximum number of characters (spaces excluded) this primer can support
        position : Vector3D
            Edge position for the text (e.g., UP, DOWN, LEFT, RIGHT)

        Returns
        -------
        Text
            Invisible primer text mobject positioned at specified edge

        Examples
        --------

        .. code-block:: python

            # Create 20-character primer at bottom of screen
            primer = NarrationTextFactory.create_primer_text(20, DOWN)
            self.add_fixed_in_frame_mobjects(primer)

        See Also
        --------
        :meth:`get_state` : Create state text for Transform
        :meth:`get_caption` : Create caption text for Transform

        Notes
        -----
        - Primer string is '0' repeated ``max_chars`` times
        - Color is BLACK (invisible on black background)
        - Font size is 1 (minimal size)
        - Must be registered with ``add_fixed_in_frame_mobjects()`` before use
        - Character capacity excludes spaces
        """
        primer_string = "0" * max_chars
        primer = Text(primer_string, color=BLACK, font_size=1)
        primer.to_edge(position)
        return primer

    def get_state(self, state_name: str) -> Mobject:
        """Get or create state text dynamically based on state name.

        Creates text for blockchain state labels (e.g., "State 1", "State 0'").
        Handles special state names like "0prime" which maps to "State 0'".

        Parameters
        ----------
        state_name : str
            State identifier (e.g., "1", "2", "0prime")

        Returns
        -------
        Mobject
            Text mobject for Transform animation, positioned at state_text_position

        Examples
        --------

        .. code-block:: python

            factory = NarrationTextFactory()

            # Regular state
            state1 = factory.get_state("1")  # "State 1"

            # Special state with prime notation
            state0p = factory.get_state("0prime")  # "State 0'"

            # Transform primer to visible state
            self.play(Transform(state_primer, state1))

        See Also
        --------
        :meth:`get_transition` : Create transition text between states
        :meth:`create_primer_text` : Create primer for this text

        Notes
        -----
        - Uses ``LayoutConfig.STATE_FONT_SIZE`` for font size
        - Uses ``LayoutConfig.STATE_TEXT_COLOR`` for text color
        - Positioned at ``self.state_text_position`` (default: DOWN)
        - Special mapping: "0prime" → "State 0'"
        - Default format: "State {state_name}"
        """
        text_map = {
            "0prime": "State 0'"
        }
        text = text_map.get(state_name, f"State {state_name}")

        state = Text(
            text,
            font_size=LayoutConfig.STATE_FONT_SIZE,
            color=LayoutConfig.STATE_TEXT_COLOR
        )
        state.to_edge(self.state_text_position)
        return state

    def get_transition(self, from_state: str, to_state: str) -> Mobject:
        """Get or create transition text between states.

        Creates text showing state transitions (e.g., "1 → 0'", "2 → 0").
        Handles special state names like "0prime" which maps to "0'".

        Parameters
        ----------
        from_state : str
            Starting state identifier (e.g., "1", "2", "0prime")
        to_state : str
            Ending state identifier (e.g., "0", "0prime")

        Returns
        -------
        Mobject
            Text mobject for Transform animation, positioned at state_text_position

        Examples
        --------

        .. code-block:: python

            factory = NarrationTextFactory()

            # Regular transition
            trans1 = factory.get_transition("1", "0")  # "1 → 0"

            # Transition with prime notation
            trans2 = factory.get_transition("2", "0prime")  # "2 → 0'"

            # Transform primer to show transition
            self.play(Transform(state_primer, trans1))

        See Also
        --------
        :meth:`get_state` : Create state text
        :meth:`create_primer_text` : Create primer for this text

        Notes
        -----
        - Uses ``LayoutConfig.STATE_FONT_SIZE`` for font size
        - Uses ``LayoutConfig.STATE_TEXT_COLOR`` for text color
        - Positioned at ``self.state_text_position`` (default: DOWN)
        - Special mapping: "0prime" → "0'"
        - Arrow symbol: "→" (Unicode U+2192)
        """
        state_text_map = {
            "0prime": "0'"
        }
        from_text = state_text_map.get(from_state, from_state)
        to_text = state_text_map.get(to_state, to_state)

        transition = Text(
            f"{from_text} → {to_text}",
            font_size=LayoutConfig.STATE_FONT_SIZE,
            color=LayoutConfig.STATE_TEXT_COLOR
        )
        transition.to_edge(self.state_text_position)
        return transition

    def get_caption(self, caption_text: str) -> Mobject:
        """Get or create caption text for narration.

        Creates text for narration captions describing blockchain events
        (e.g., "Honest miner finds block", "Selfish miner releases chain").

        Parameters
        ----------
        caption_text : str
            Caption text to display

        Returns
        -------
        Mobject
            Text mobject for Transform animation, positioned at caption_text_position

        Examples
        --------

        .. code-block:: python

            factory = NarrationTextFactory()

            # Create caption
            caption = factory.get_caption("Honest miner finds block")

            # Transform primer to show caption
            self.play(Transform(caption_primer, caption))

        .. code-block:: python

            # Clear caption with invisible text
            empty = factory.get_caption(".....")
            empty.set_color(BLACK)
            self.play(Transform(caption_primer, empty))

        See Also
        --------
        :meth:`get_state` : Create state text
        :meth:`create_primer_text` : Create primer for this text
        :class:`NarrationManager` : Uses this method for captions

        Notes
        -----
        - Uses ``LayoutConfig.CAPTION_FONT_SIZE`` for font size
        - Uses ``LayoutConfig.CAPTION_TEXT_COLOR`` for text color
        - Positioned at ``self.caption_text_position`` (default: UP)
        - Character count excludes spaces
        - Must not exceed ``max_caption_chars`` capacity
        """
        caption = Text(
            caption_text,
            font_size=LayoutConfig.CAPTION_FONT_SIZE,
            color=LayoutConfig.CAPTION_TEXT_COLOR
        )
        caption.to_edge(self.caption_text_position)
        return caption


class AnimationTimingConfig:
    """Centralized animation timing configuration for blockchain visualizations.

    Provides class-level constants for all animation durations and wait times used
    throughout blockchain scenes. All timing values are in seconds and can be scaled
    globally using :meth:`set_speed_multiplier`.

    This configuration class follows a similar pattern to Manim's :class:`~.ManimConfig`
    system, providing a single source of truth for timing-related settings.

    Attributes
    ----------
    WAIT_TIME : float
        Standard wait time between animations (default: 1.0 seconds)
    FADE_IN_TIME : float
        Duration for fade-in animations (default: 1.0 seconds)
    FADE_OUT_TIME : float
        Duration for fade-out animations (default: 1.0 seconds)
    BLOCK_CREATION_TIME : float
        Duration for creating new blocks (default: 1.0 seconds)
    CHAIN_RESOLUTION_TIME : float
        Duration for resolving chain conflicts (default: 2.0 seconds)
    SHIFT_TO_NEW_GENESIS_TIME : float
        Duration for shifting chains to new genesis position (default: 3.0 seconds)
    INITIAL_SCENE_WAIT_TIME : float
        Pause duration at scene start before animations begin (default: 3.0 seconds)
    VERTICAL_SHIFT_TIME : float
        Duration for vertical chain movements (default: 2.0 seconds)
    CHAIN_REVEAL_ANIMATION_TIME : float
        Duration for revealing hidden chains (default: 2.0 seconds)
    FOLLOW_LINE_UPDATE_TIME : float
        Duration for :class:`FollowLine` update animations (default: 2.0 seconds)

    Examples
    --------

    .. code-block:: python

        # Use timing constants in animations
        self.play(
            FadeIn(block),
            run_time=AnimationTimingConfig.FADE_IN_TIME
        )
        self.wait(AnimationTimingConfig.WAIT_TIME)

    .. code-block:: python

        # Speed up all animations by 2x
        AnimationTimingConfig.set_speed_multiplier(0.5)

        # Now all animations run at half duration
        self.play(
            FadeIn(block),
            run_time=AnimationTimingConfig.FADE_IN_TIME  # Now 0.5 seconds
        )

    .. code-block:: python

        # Slow down all animations by 2x for detailed presentation
        AnimationTimingConfig.set_speed_multiplier(2.0)

    See Also
    --------
    :class:`LayoutConfig` : Centralized layout and styling configuration
    :class:`~.ManimConfig` : Manim's global configuration system

    Notes
    -----
    - All timing values are class attributes, not instance attributes
    - :meth:`set_speed_multiplier` modifies class attributes in-place
    - Multiplier is cumulative - calling it twice multiplies the effect
    - To reset timings, you must manually set each constant back to defaults
    - ``SHIFT_TO_NEW_GENESIS_TIME`` may become dynamic in future versions
      to adjust based on the number of blocks being moved (up to 4 blocks)
    """
    # Scene timing
    WAIT_TIME = 1.0

    # Animation durations
    FADE_IN_TIME = 1.0
    FADE_OUT_TIME = 1.0
    BLOCK_CREATION_TIME = 1.0
    CHAIN_RESOLUTION_TIME = 2.0
    SHIFT_TO_NEW_GENESIS_TIME = 3.0
    INITIAL_SCENE_WAIT_TIME = 3.0  # pause at the beginning before any animations are added
    VERTICAL_SHIFT_TIME = 2.0
    CHAIN_REVEAL_ANIMATION_TIME = 2.0
    FOLLOW_LINE_UPDATE_TIME = 2.0

    @classmethod
    def set_speed_multiplier(cls, multiplier: float):
        """Scale all timing constants by a multiplier for faster/slower animations.

        Multiplies all class-level timing constants by the given factor. Values less
        than 1.0 speed up animations, values greater than 1.0 slow them down.

        .. warning::
            This method modifies class attributes in-place and is **cumulative**.
            Calling it multiple times will compound the effect. There is no built-in
            reset mechanism - you must manually restore defaults if needed.

        Parameters
        ----------
        multiplier : float
            Factor to multiply all timing constants by. Must be positive.
            - ``multiplier < 1.0``: Speeds up animations (e.g., 0.5 = 2x faster)
            - ``multiplier = 1.0``: No change
            - ``multiplier > 1.0``: Slows down animations (e.g., 2.0 = 2x slower)

        Examples
        --------

        .. code-block:: python

            # Original timing
            print(AnimationTimingConfig.FADE_IN_TIME)  # 1.0

            # Speed up by 2x
            AnimationTimingConfig.set_speed_multiplier(0.5)
            print(AnimationTimingConfig.FADE_IN_TIME)  # 0.5

            # Cumulative effect - now 4x faster than original
            AnimationTimingConfig.set_speed_multiplier(0.5)
            print(AnimationTimingConfig.FADE_IN_TIME)  # 0.25

        .. code-block:: python

            # Slow down for detailed presentation
            AnimationTimingConfig.set_speed_multiplier(2.0)

            # All animations now take twice as long
            self.play(
                FadeIn(block),
                run_time=AnimationTimingConfig.FADE_IN_TIME  # 2.0 seconds
            )

        See Also
        --------
        :class:`~.ChangeSpeed` : Manim's animation speed modifier

        Notes
        -----
        - Modifies all timing constants: ``WAIT_TIME``, ``FADE_IN_TIME``,
          ``FADE_OUT_TIME``, ``BLOCK_CREATION_TIME``, ``CHAIN_RESOLUTION_TIME``,
          ``SHIFT_TO_NEW_GENESIS_TIME``, ``INITIAL_SCENE_WAIT_TIME``,
          ``VERTICAL_SHIFT_TIME``, ``CHAIN_REVEAL_ANIMATION_TIME``,
          ``FOLLOW_LINE_UPDATE_TIME``
        - Does not validate that multiplier is positive - negative values will
          cause undefined behavior
        - Unlike Manim's :class:`~.ChangeSpeed`, this affects the configuration
          constants themselves, not individual animation playback
        """
        cls.WAIT_TIME *= multiplier
        cls.FADE_IN_TIME *= multiplier
        cls.FADE_OUT_TIME *= multiplier
        cls.BLOCK_CREATION_TIME *= multiplier
        cls.CHAIN_RESOLUTION_TIME *= multiplier
        cls.SHIFT_TO_NEW_GENESIS_TIME *= multiplier
        cls.INITIAL_SCENE_WAIT_TIME *= multiplier
        cls.VERTICAL_SHIFT_TIME *= multiplier
        cls.CHAIN_REVEAL_ANIMATION_TIME *= multiplier
        cls.FOLLOW_LINE_UPDATE_TIME *= multiplier


class LayoutConfig:
    """Centralized layout and visual configuration for blockchain visualizations.

    Provides class-level constants for all positioning, sizing, and color settings used
    throughout blockchain scenes. All values are in Manim coordinate units unless otherwise
    specified.

    This configuration class follows a similar pattern to :class:`AnimationTimingConfig`,
    providing a single source of truth for visual layout settings.

    Attributes
    ----------
    GENESIS_X : float
        X-coordinate for genesis block position (default: -4)
    GENESIS_Y : float
        Y-coordinate for genesis block position (default: 0)
    BLOCK_HORIZONTAL_SPACING : float
        Horizontal distance between consecutive blocks (default: 2)
    HONEST_Y_OFFSET : float
        Y-offset for honest chain from genesis (default: 0)
    SELFISH_Y_OFFSET : float
        Y-offset for selfish chain from genesis (default: -1.2)
    LINE_BUFFER : float
        Buffer distance from block edges for connecting lines (default: 0.1)
    LINE_STROKE_WIDTH : float
        Stroke width for :class:`FollowLine` connections (default: 2)
    BLOCK_SIDE_LENGTH : float
        Side length of block squares (default: 0.8)
    BLOCK_FILL_OPACITY : float
        Fill opacity for block squares (default: 0, transparent)
    LABEL_FONT_SIZE : int
        Font size for block labels (default: 24)
    STATE_FONT_SIZE : int
        Font size for state text in HUD (default: 24)
    CAPTION_FONT_SIZE : int
        Font size for caption text in HUD (default: 24)
    LABEL_COLOR : ParsableManimColor
        Color for block labels (default: WHITE)
    LINE_COLOR : ParsableManimColor
        Color for connecting lines (default: WHITE)
    SELFISH_CHAIN_COLOR : str
        Color for selfish chain blocks (default: "#FF0000", pure red)
    HONEST_CHAIN_COLOR : str
        Color for honest chain blocks (default: "#0000FF", pure blue)
    GENESIS_BLOCK_COLOR : str
        Color for genesis blocks (default: "#0000FF", pure blue)
    STATE_TEXT_COLOR : ParsableManimColor
        Color for state text in HUD (default: WHITE)
    CAPTION_TEXT_COLOR : ParsableManimColor
        Color for caption text in HUD (default: WHITE)
    SELFISH_BLOCK_OPACITY : float
        Opacity for selfish chain blocks (default: 0.5)

    Examples
    --------

    .. code-block:: python

        # Use layout constants for block creation
        genesis = Block(
            "0",
            [LayoutConfig.GENESIS_X, LayoutConfig.GENESIS_Y, 0],
            LayoutConfig.GENESIS_BLOCK_COLOR
        )

    .. code-block:: python

        # Calculate next block position
        next_x = LayoutConfig.GENESIS_X + LayoutConfig.BLOCK_HORIZONTAL_SPACING
        next_y = LayoutConfig.HONEST_Y_OFFSET
        block1 = Block("H1", [next_x, next_y, 0], LayoutConfig.HONEST_CHAIN_COLOR)

    .. code-block:: python

        # Use tie positions for chain conflicts
        honest_y, selfish_y = LayoutConfig.get_tie_positions(LayoutConfig.GENESIS_Y)
        # honest_y = 0.6, selfish_y = -0.6

    See Also
    --------
    :class:`AnimationTimingConfig` : Centralized timing configuration
    :class:`Block` : Uses these constants for visual properties
    :class:`FollowLine` : Uses LINE_BUFFER, LINE_COLOR, LINE_STROKE_WIDTH
    :class:`ChainBranch` : Uses color constants for automatic block coloring
    :class:`NarrationTextFactory` : Uses font size and color constants

    Notes
    -----
    **Coordinate System**:
    - Genesis block at (GENESIS_X, GENESIS_Y) = (-4, 0)
    - Honest chain at Y = HONEST_Y_OFFSET = 0 (same as genesis)
    - Selfish chain at Y = SELFISH_Y_OFFSET = -1.2 (below genesis)
    - Blocks spaced horizontally by BLOCK_HORIZONTAL_SPACING = 2

    **Color Scheme**:
    - Honest chain: Pure blue (#0000FF)
    - Selfish chain: Pure red (#FF0000) with 0.5 opacity
    - Genesis blocks: Pure blue (#0000FF)

    **Configuration Pattern**:
    - All attributes are class-level constants (not instance-level)
    - Values can be modified directly: ``LayoutConfig.GENESIS_X = -5``
    - No validation or reset mechanism provided
    - Changes affect all subsequent block/line creations
    """
    GENESIS_X = -4
    GENESIS_Y = 0
    BLOCK_HORIZONTAL_SPACING = 2
    HONEST_Y_OFFSET = 0
    SELFISH_Y_OFFSET = -1.2

    LINE_BUFFER = 0.1
    LINE_STROKE_WIDTH = 2

    BLOCK_SIDE_LENGTH = 0.8
    BLOCK_FILL_OPACITY = 0

    LABEL_FONT_SIZE = 24
    STATE_FONT_SIZE = 24
    CAPTION_FONT_SIZE = 24

    LABEL_COLOR = WHITE
    LINE_COLOR = WHITE
    SELFISH_CHAIN_COLOR = "#FF0000"  # PURE_RED
    HONEST_CHAIN_COLOR = "#0000FF"  # PURE_BLUE
    GENESIS_BLOCK_COLOR = "#0000FF"  # PURE_BLUE
    STATE_TEXT_COLOR = WHITE
    CAPTION_TEXT_COLOR = WHITE

    SELFISH_BLOCK_OPACITY = 0.5

    @staticmethod
    def get_tie_chain_spacing() -> float:
        """Calculate tie chain spacing as half the distance between chains.

        Returns the vertical spacing used when chains are in a tie state,
        calculated as half the distance between honest and selfish chain offsets.

        Returns
        -------
        float
            Half the vertical distance between honest and selfish chains

        Examples
        --------

        .. code-block:: python

            spacing = LayoutConfig.get_tie_chain_spacing()
            # spacing = abs(0 - (-1.2)) / 2 = 0.6

        .. code-block:: python

            # Use spacing to position tied chains symmetrically
            spacing = LayoutConfig.get_tie_chain_spacing()
            honest_y = LayoutConfig.GENESIS_Y + spacing
            selfish_y = LayoutConfig.GENESIS_Y - spacing

        See Also
        --------
        :meth:`get_tie_positions` : Get both tie positions at once

        Notes
        -----
        - Uses absolute value to ensure positive spacing regardless of offset order
        - Spacing is symmetric around genesis Y-coordinate
        - Default spacing: abs(0 - (-1.2)) / 2 = 0.6
        """
        return abs(LayoutConfig.SELFISH_Y_OFFSET - LayoutConfig.HONEST_Y_OFFSET) / 2

    @staticmethod
    def get_tie_positions(genesis_y: float) -> tuple[float, float]:
        """Calculate Y-positions for both chains in tie state.

        When chains are tied, they are positioned symmetrically above and below
        the genesis Y-coordinate, separated by the tie chain spacing.

        Parameters
        ----------
        genesis_y : float
            The Y-coordinate of the genesis block to center the tie positions around

        Returns
        -------
        tuple[float, float]
            A tuple of (honest_y, selfish_y) positions for tie state

        Examples
        --------

        .. code-block:: python

            # Get tie positions centered on genesis
            honest_y, selfish_y = LayoutConfig.get_tie_positions(LayoutConfig.GENESIS_Y)
            # honest_y = 0 + 0.6 = 0.6
            # selfish_y = 0 - 0.6 = -0.6

        .. code-block:: python

            # Position chains in tie state
            honest_y, selfish_y = LayoutConfig.get_tie_positions(genesis.get_center()[1])
            self.play(
                honest_chain.animate.shift(UP * (honest_y - current_honest_y)),
                selfish_chain.animate.shift(UP * (selfish_y - current_selfish_y))
            )

        See Also
        --------
        :meth:`get_tie_chain_spacing` : Get the spacing value used

        Notes
        -----
        - Honest chain positioned above genesis: ``genesis_y + spacing``
        - Selfish chain positioned below genesis: ``genesis_y - spacing``
        - Spacing calculated by :meth:`get_tie_chain_spacing`
        - Default positions with GENESIS_Y=0: (0.6, -0.6)
        """
        spacing = LayoutConfig.get_tie_chain_spacing()
        return genesis_y + spacing, genesis_y - spacing


class AnimationManager:
    """Facade for Manim animations with consistent timing configuration.

    Wraps Manim's animation system to provide centralized animation creation with
    timing values from :class:`AnimationTimingConfig`. All animations in the
    SelfishMiningSquares system use this manager for consistent timing and prevent
    duplicate creation animations.

    .. warning::
        **Module-level Singleton**: Use the module-level `animations` singleton instead
        of instantiating this class directly. All methods are static and stateless.

    .. warning::
        **Duplicate Creation Prevention**: All draw methods check for duplicate
        creation attempts using the `is_in_scene` attribute. Attempting to draw
        a mobject that's already in the scene will raise :class:`ValueError`.

    Parameters
    ----------
    No parameters required.

    Attributes
    ----------
    This class has no instance attributes. All methods are static.

    Examples
    --------

    .. code-block:: python

        from selfish_mining_bitcoin import animations

        # Draw block body (square)
        block = Block("1", RIGHT * 2, BLUE)
        self.play(animations.draw_block_body(block.square))

        # Draw block label (text)
        self.play(animations.draw_block_label(block.label))

        # Draw connection line
        self.play(animations.draw_line(block.line))

        # Transform text
        new_text = Text("State 1")
        self.play(animations.transform_text(old_text, new_text))

    See Also
    --------
    :class:`AnimationTimingConfig` : Timing constants used by this manager
    :class:`~.Create` : Manim animation class wrapped by draw methods
    :class:`~.Transform` : Manim animation class wrapped by transform_text

    Notes
    -----
    - All draw methods use :class:`~.Create` animation with configured timing
    - All draw methods set ``mobject.is_in_scene = True`` to track scene membership
    - Duplicate creation attempts raise :class:`ValueError` to prevent unexpected behavior
    - ``draw_block_body`` uses ``AnimationTimingConfig.BLOCK_CREATION_TIME``
    - ``draw_block_label`` and ``draw_line`` use ``AnimationTimingConfig.FADE_IN_TIME``
    - ``transform_text`` uses :class:`~.Transform` instead of :class:`~.ReplacementTransform`
    - Transform preserves original mobject properties (critical for HUD primer pattern)
    - Module-level singleton pattern eliminates parameter passing
    """

    @staticmethod
    def draw_block_body(mobject) -> Animation:
        """Draw a block body (square) onto the scene.

        Sets ``mobject.is_in_scene = True`` before returning the animation.
        Raises :class:`ValueError` if mobject is already in scene.

        Parameters
        ----------
        mobject : Square
            The block's square mobject to animate

        Returns
        -------
        Animation
            Create animation with configured block creation time

        Raises
        ------
        ValueError
            If mobject is already in the scene (has ``is_in_scene = True``)

        Examples
        --------

        .. code-block:: python

            block = Block("1", RIGHT * 2, BLUE)
            self.play(animations.draw_block_body(block.square))

        Notes
        -----
        - Uses ``AnimationTimingConfig.BLOCK_CREATION_TIME`` for run_time
        - Automatically sets ``mobject.is_in_scene = True``
        - Prevents duplicate creation by checking existing ``is_in_scene`` attribute
        """
        if getattr(mobject, 'is_in_scene', False):
            raise ValueError(
                f"Cannot create animation for {mobject} - already in scene. "
                "This would cause unexpected animation behavior."
            )
        mobject.is_in_scene = True
        return Create(mobject, run_time=AnimationTimingConfig.BLOCK_CREATION_TIME)

    @staticmethod
    def draw_block_label(mobject) -> Animation:
        """Draw a block label (text) onto the scene.

        Sets ``mobject.is_in_scene = True`` before returning the animation.
        Raises :class:`ValueError` if mobject is already in scene.

        Parameters
        ----------
        mobject : Text
            The block's label mobject to animate

        Returns
        -------
        Animation
            Create animation with configured fade-in time

        Raises
        ------
        ValueError
            If mobject is already in the scene (has ``is_in_scene = True``)

        Examples
        --------

        .. code-block:: python

            block = Block("1", RIGHT * 2, BLUE)
            self.play(animations.draw_block_label(block.label))

        Notes
        -----
        - Uses ``AnimationTimingConfig.FADE_IN_TIME`` for run_time
        - Automatically sets ``mobject.is_in_scene = True``
        - Prevents duplicate creation by checking existing ``is_in_scene`` attribute
        """
        if getattr(mobject, 'is_in_scene', False):
            raise ValueError(
                f"Cannot create animation for {mobject} - already in scene. "
                "This would cause unexpected animation behavior."
            )
        mobject.is_in_scene = True
        return Create(mobject, run_time=AnimationTimingConfig.FADE_IN_TIME)

    @staticmethod
    def draw_line(mobject) -> Animation:
        """Draw a connection line onto the scene.

        Sets ``mobject.is_in_scene = True`` before returning the animation.
        Raises :class:`ValueError` if mobject is already in scene.

        Parameters
        ----------
        mobject : FollowLine
            The line mobject to animate

        Returns
        -------
        Animation
            Create animation with configured fade-in time

        Raises
        ------
        ValueError
            If mobject is already in the scene (has ``is_in_scene = True``)

        Examples
        --------

        .. code-block:: python

            block = Block("1", RIGHT * 2, BLUE, parent_block=genesis)
            self.play(animations.draw_line(block.line))

        Notes
        -----
        - Uses ``AnimationTimingConfig.FADE_IN_TIME`` for run_time
        - Automatically sets ``mobject.is_in_scene = True``
        - Prevents duplicate creation by checking existing ``is_in_scene`` attribute
        """
        if getattr(mobject, 'is_in_scene', False):
            raise ValueError(
                f"Cannot create animation for {mobject} - already in scene. "
                "This would cause unexpected animation behavior."
            )
        mobject.is_in_scene = True
        return Create(mobject, run_time=AnimationTimingConfig.FADE_IN_TIME)

    @staticmethod
    def transform_text(old_mobject, new_mobject) -> Animation:
        """Transform one text mobject to another.

        Uses :class:`~.Transform` to preserve the original mobject's properties,
        which is critical for the HUD primer pattern.

        Parameters
        ----------
        old_mobject : Mobject
            The current text mobject to transform from
        new_mobject : Mobject
            The new text mobject to transform to

        Returns
        -------
        Animation
            Transform animation with configured fade-in time

        Examples
        --------

        .. code-block:: python

            old_text = Text("State 0")
            new_text = Text("State 1")
            self.play(animations.transform_text(old_text, new_text))

        Notes
        -----
        - Uses ``AnimationTimingConfig.FADE_IN_TIME`` for run_time
        - Uses :class:`~.Transform` instead of :class:`~.ReplacementTransform`
        - Transform preserves ``old_mobject``'s properties (including ``is_in_scene`` flag)
        - Does not set ``is_in_scene`` because it transforms existing mobject
        """
        return Transform(old_mobject, new_mobject, run_time=AnimationTimingConfig.FADE_IN_TIME)


animations = AnimationManager()


class NarrationManager:
    """Scene-aware HUD text manager with primer-based Transform support.

    Manages HUD text elements for blockchain/DAG visualizations using the primer
    pattern. Creates invisible primer text mobjects once during initialization,
    then provides methods to generate visible text for :class:`~.Transform` animations.
    All primers are automatically registered as fixed-in-frame with the scene.

    .. warning::
        **Primer Pattern Requirements**: This class uses :class:`~.Transform` (not
        :class:`~.ReplacementTransform`) to update text. The primer mobjects must
        never be removed from the scene, and character capacity is fixed at
        initialization. Exceeding capacity causes text to detach from the HUD.

    Parameters
    ----------
    scene : HUD2DScene
        Scene instance with :meth:`add_fixed_in_frame_mobjects` support. Must be
        a :class:`~.ThreeDScene` subclass with fixed-in-frame capabilities.
    narration_factory : NarrationTextFactory
        Factory for creating text mobjects. Provides text creation methods and
        configuration (max character counts, positions, styling).

    Attributes
    ----------
    scene : HUD2DScene
        Reference to the scene instance
    factory : NarrationTextFactory
        Text factory used for creating mobjects
    current_state_text : Text
        Primer mobject for state/transition text (bottom of screen)
    current_caption_text : Text
        Primer mobject for caption text (top of screen)
    current_state_name : str
        Tracks the current state identifier (default: "0")

    Examples
    --------

    .. code-block:: python

        # Initialize manager with scene and factory
        factory = NarrationTextFactory()
        manager = NarrationManager(self, factory)

        # Display state text
        state_text = manager.get_state("1")
        self.play(Transform(manager.current_state_text, state_text))

    .. code-block:: python

        # Show transition between states
        transition = manager.get_transition("1", "2")
        self.play(Transform(manager.current_state_text, transition))

        # Add caption narration
        caption = manager.get_narration("Honest miner finds block")
        self.play(Transform(manager.current_caption_text, caption))

    .. code-block:: python

        # Clear caption with invisible text
        empty = manager.get_empty_narration()
        self.play(Transform(manager.current_caption_text, empty))

    See Also
    --------
    :class:`NarrationTextFactory` : Factory for creating text mobjects
    :class:`~.ThreeDScene` : Base scene class with fixed-in-frame support
    :class:`~.Transform` : Animation used to update primer text
    :meth:`~.ThreeDScene.add_fixed_in_frame_mobjects` : Method for HUD registration

    Notes
    -----
    **Primer Pattern**:
    - Primers are created once in :meth:`__init__` with maximum character capacity
    - Primers start invisible (BLACK color, font_size=1)
    - First :class:`~.Transform` makes primer visible
    - All subsequent :class:`~.Transform` calls reuse the same primer mobject
    - Character capacity is fixed at initialization (from factory configuration)

    **Character Capacity**:
    - State text: Configured via ``factory.max_state_chars`` (default: 20)
    - Caption text: Configured via ``factory.max_caption_chars`` (default: 100)
    - Exceeding capacity causes characters to detach from fixed-in-frame

    **Text Type Compatibility**:
    - Current implementation uses :class:`~.Text` exclusively
    - Cannot mix text types (Text → MathTex fails due to incompatible submobjects)
    - For MathTex/Tex support, use separate primer pools per text type

    **Dependencies**:
    - Requires scene with :meth:`add_fixed_in_frame_mobjects` method
    - Uses factory's ``max_state_chars``, ``max_caption_chars`` configuration
    - Uses factory's ``state_text_position``, ``caption_text_position`` configuration
    """
    def __init__(self, scene: HUD2DScene, narration_factory: NarrationTextFactory):
        """Initialize manager with scene and factory, creating fixed-in-frame primers.

        Creates two invisible primer text mobjects (state and caption) with maximum
        character capacity, then registers them as fixed-in-frame with the scene.
        These primers are reused for all subsequent text updates via :class:`~.Transform`.

        Parameters
        ----------
        scene : HUD2DScene
            Scene instance with :meth:`add_fixed_in_frame_mobjects` support
        narration_factory : NarrationTextFactory
            Factory for creating text mobjects with configuration

        Notes
        -----
        - Primers are positioned using factory's ``state_text_position`` (DOWN)
          and ``caption_text_position`` (UP)
        - Primer capacity uses factory's ``max_state_chars`` (20) and
          ``max_caption_chars`` (100)
        - Primers are registered once and never removed from scene
        - Initial state name is set to "0"
        """
        self.scene = scene
        self.factory = narration_factory

        # Create primers with maximum capacity
        state_primer = self.factory.create_primer_text(
            self.factory.max_state_chars,
            self.factory.state_text_position
        )
        caption_primer = self.factory.create_primer_text(
            self.factory.max_caption_chars,
            self.factory.caption_text_position
        )

        # Register primers as fixed in frame ONCE
        self.scene.add_fixed_in_frame_mobjects(state_primer, caption_primer)

        # Track the primer mobjects (these will be transformed)
        self.current_state_text = state_primer
        self.current_caption_text = caption_primer
        self.current_state_name = "0"

    def get_state(self, state: str):
        """Create state text for Transform animation.

        Generates text for blockchain state labels (e.g., "State 1", "State 0'")
        positioned at the state primer's center. Updates internal state tracking.

        Parameters
        ----------
        state : str
            State identifier (e.g., "1", "2", "0prime")

        Returns
        -------
        Mobject
            Text mobject positioned at primer center, ready for :class:`~.Transform`

        Examples
        --------

        .. code-block:: python

            # Display state 1
            state_text = manager.get_state("1")
            self.play(Transform(manager.current_state_text, state_text))

            # Display state with prime notation
            state_text = manager.get_state("0prime")  # "State 0'"
            self.play(Transform(manager.current_state_text, state_text))

        See Also
        --------
        :meth:`get_transition` : Create transition text between states
        :meth:`NarrationTextFactory.get_state` : Factory method for state text

        Notes
        -----
        - Text is positioned at ``current_state_text.get_center()``
        - No scene registration needed (primer already registered)
        - Updates ``current_state_name`` attribute
        - Special mapping: "0prime" → "State 0'" (handled by factory)
        """
        text = self.factory.get_state(state)
        text.move_to(self.current_state_text.get_center())
        # No registration needed - primer already registered
        self.current_state_name = state
        return text

    def get_transition(self, from_state: str, to_state: str):
        """Create transition text for Transform animation.

        Generates text showing state transitions (e.g., "1 → 2", "2 → 0'")
        positioned at the state primer's center.

        Parameters
        ----------
        from_state : str
            Starting state identifier (e.g., "1", "2", "0prime")
        to_state : str
            Ending state identifier (e.g., "0", "2", "0prime")

        Returns
        -------
        Mobject
            Text mobject positioned at primer center, ready for :class:`~.Transform`

        Examples
        --------

        .. code-block:: python

            # Show transition from state 1 to state 2
            transition = manager.get_transition("1", "2")
            self.play(Transform(manager.current_state_text, transition))

            # Transition with prime notation
            transition = manager.get_transition("2", "0prime")  # "2 → 0'"
            self.play(Transform(manager.current_state_text, transition))

        See Also
        --------
        :meth:`get_state` : Create state text
        :meth:`NarrationTextFactory.get_transition` : Factory method for transitions

        Notes
        -----
        - Text is positioned at ``current_state_text.get_center()``
        - No scene registration needed (primer already registered)
        - Arrow symbol: "→" (Unicode U+2192)
        - Special mapping: "0prime" → "0'" (handled by factory)
        """
        text = self.factory.get_transition(from_state, to_state)
        text.move_to(self.current_state_text.get_center())
        # No registration needed - primer already registered
        return text

    def get_narration(self, narration: str):
        """Create caption text for Transform animation.

        Generates narration caption text (e.g., "Honest miner finds block")
        positioned at the caption primer's center.

        Parameters
        ----------
        narration : str
            Caption text to display

        Returns
        -------
        Mobject
            Text mobject positioned at primer center, ready for :class:`~.Transform`

        Examples
        --------

        .. code-block:: python

            # Display narration caption
            caption = manager.get_narration("Honest miner finds block")
            self.play(Transform(manager.current_caption_text, caption))

            # Update with new caption
            caption = manager.get_narration("Selfish miner releases chain")
            self.play(Transform(manager.current_caption_text, caption))

        See Also
        --------
        :meth:`get_empty_narration` : Create invisible text to clear caption
        :meth:`NarrationTextFactory.get_caption` : Factory method for captions

        Notes
        -----
        - Text is positioned at ``current_caption_text.get_center()``
        - No scene registration needed (primer already registered)
        - Character count must not exceed ``factory.max_caption_chars``
        - Uses factory's ``CAPTION_FONT_SIZE`` and ``CAPTION_TEXT_COLOR``
        """
        text = self.factory.get_caption(narration)
        text.move_to(self.current_caption_text.get_center())
        # No registration needed - primer already registered
        return text

    def get_empty_narration(self):
        """Create invisible placeholder text to clear caption.

        Generates invisible text (BLACK color) positioned at the caption primer's
        center. Used to clear/hide caption text while maintaining primer state.

        Returns
        -------
        Mobject
            Invisible text mobject positioned at primer center

        Examples
        --------

        .. code-block:: python

            # Clear caption by transforming to invisible text
            empty = manager.get_empty_narration()
            self.play(Transform(manager.current_caption_text, empty))

        See Also
        --------
        :meth:`get_narration` : Create visible caption text

        Notes
        -----
        - Text content is "....." (5 periods)
        - Color is BLACK (invisible on black background)
        - Positioned at ``current_caption_text.get_center()``
        - No scene registration needed (primer already registered)
        """
        text = self.factory.get_caption(".....")
        text.set_color(BLACK)  # Invisible against black background
        text.move_to(self.current_caption_text.get_center())
        return text


# TiebreakDecision = Literal["honest_on_honest", "honest_on_selfish", "selfish_on_selfish"]
if TYPE_CHECKING:
    TiebreakDecision: TypeAlias = Literal["honest_on_honest", "honest_on_selfish", "selfish_on_selfish"]


class SelfishMiningSquares:
    """Animated selfish mining simulation for blockchain visualization.

    Simulates the selfish mining attack strategy in blockchain systems, where a malicious
    mining pool withholds blocks to gain unfair advantages. Manages two competing chains
    (honest and selfish), handles probabilistic block generation, race resolution, and
    provides animated visualizations with optional HUD narration.

    .. warning::
        **Scene Type Requirement**: This class requires a :class:`HUD2DScene` instance.
        Passing any other scene type will raise a :class:`TypeError` during initialization.

    Parameters
    ----------
    scene : HUD2DScene
        Scene instance for rendering animations. Must be a :class:`HUD2DScene` subclass
        with fixed-in-frame support for HUD elements.
    alpha : float, optional
        Adversarial hash power (selfish pool's mining percentage). Default: 0.3 (30%)
    gamma : float, optional
        Network connectivity (proportion of honest miners who see selfish chain first
        during ties). Default: 0.5 (50%)
    enable_narration : bool, optional
        Enable HUD text narration showing state transitions and captions. Default: False

    Attributes
    ----------
    scene : HUD2DScene
        Reference to the scene instance
    narration : NarrationManager
        Manager for HUD text elements (state labels, captions)
    alpha : float
        Adversarial hash power percentage
    gamma : float
        Network connectivity percentage
    enable_narration : bool
        Whether narration is enabled
    genesis : Block
        Current genesis block (updated after each race resolution)
    original_genesis : Block
        Reference to the very first genesis block
    selfish_chain : ChainBranch
        Container for selfish miner's blocks
    honest_chain : ChainBranch
        Container for honest miner's blocks
    selfish_blocks_created : int
        Total count of selfish blocks created (resets each race)
    honest_blocks_created : int
        Total count of honest blocks created (resets each race)
    previous_selfish_lead : int
        Selfish lead from previous block addition (for state tracking)

    Examples
    --------

    .. code-block:: python

        class MyScene(HUD2DScene):
            def construct(self):
                # Initialize simulation with 30% adversarial power
                sim = SelfishMiningSquares(self, alpha=0.3, gamma=0.5, enable_narration=True)

                # Generate blocks probabilistically
                for _ in range(10):
                    sim.generate_next_block_probabilistic()

    .. code-block:: python

        # Manual block creation with custom captions
        sim = SelfishMiningSquares(self, alpha=0.4, enable_narration=True)

        sim.advance_selfish_chain(caption="Selfish miner finds block")
        sim.advance_honest_chain(caption="Honest miner finds block")

        # Update caption without advancing chains
        sim.update_caption("Analyzing blockchain state...")

    .. code-block:: python

        # Manual tiebreak control
        sim = SelfishMiningSquares(self, alpha=0.3, gamma=0.5)

        # Force specific tiebreak outcome
        sim.advance_honest_chain(tiebreak="honest_on_honest")

        # Zoom out to show multiple races
        sim.zoom_out_to_show_races(max_races=5, animation_time=3.0)

    See Also
    --------
    :class:`HUD2DScene` : Required scene type for this simulation
    :class:`Block` : Individual blockchain block visualization
    :class:`ChainBranch` : Container for blockchain branches
    :class:`NarrationManager` : HUD text management

    Notes
    -----
    **Selfish Mining Strategy**:
    - Selfish pool withholds blocks to create a private chain
    - When honest miners catch up, selfish pool reveals blocks strategically
    - Goal: Gain more than fair share of blocks (more than alpha percentage)

    **Probability Model**:
    - Block generation: P(selfish) = alpha, P(honest) = 1 - alpha
    - Tiebreak outcomes (state 0'):
      - P(selfish_on_selfish) = alpha
      - P(honest_on_selfish) = gamma * (1 - alpha)
      - P(honest_on_honest) = (1 - gamma) * (1 - alpha)

    **State Machine**:
    - State 0: Equal chains (initial state)
    - State 0': Tie revealed (both chains visible, equal length)
    - State N (N > 0): Selfish lead of N blocks
    - Transitions trigger automatic race resolution when appropriate

    **Race Resolution**:
    - Honest wins: selfish_lead = -1
    - Selfish wins: selfish_lead = 1 after previous lead of 2
    - Tie resolution: Determined by tiebreak probabilities

    **Camera Behavior**:
    - Automatically scrolls right when chains exceed 4 blocks
    - Shifts by one block spacing per new maximum length
    - Recenters on genesis position after race resolution

    **Configuration Dependencies**:
    - Uses ``LayoutConfig`` for block positioning and styling
    - Uses ``AnimationTimingConfig`` for animation durations
    - Requires ``animations`` module for draw/transform helpers
    """
    def __init__(self, scene: HUD2DScene, alpha=0.3, gamma=0.5, enable_narration=False):
        """Initialize selfish mining simulation with genesis block.

        Creates genesis block, initializes chain containers, sets up narration manager
        (if enabled), and displays initial scene with optional state/caption text.

        Parameters
        ----------
        scene : HUD2DScene
            Scene instance for rendering. Must be :class:`HUD2DScene` subclass.
        alpha : float, optional
            Adversarial hash power (0.0 to 1.0). Default: 0.3
        gamma : float, optional
            Network connectivity (0.0 to 1.0). Default: 0.5
        enable_narration : bool, optional
            Enable HUD text narration. Default: False

        Raises
        ------
        TypeError
            If scene is not an instance of :class:`HUD2DScene`

        Notes
        -----
        - Genesis block is positioned at ``(LayoutConfig.GENESIS_X, LayoutConfig.GENESIS_Y, 0)``
        - Initial wait time: ``AnimationTimingConfig.INITIAL_SCENE_WAIT_TIME``
        - If narration enabled, displays "State 0" and "Selfish Mining in Bitcoin"
        - Camera tracking starts at threshold of 4 blocks
        """
        # Validate scene type
        if not isinstance(scene, HUD2DScene):
            raise TypeError(
                f"SelfishMiningSquares requires a HUD2DScene instance, "
                f"got {type(scene).__name__} instead. "
                f"Please change your scene class to inherit from HUD2DScene."
            )
        # Scene to bypass manim limitations and use play in SelfishMiningSquares
        self.scene = scene

        # Create scene-specific narration manager
        narration_factory = NarrationTextFactory()
        self.narration = NarrationManager(scene, narration_factory)

        # Adversary % and Connectedness
        self.alpha = alpha
        self.gamma = gamma

        # Narration control
        self.enable_narration = enable_narration
        self._pending_tiebreak = None

        # Camera tracking for long races
        self._previous_max_chain_len = 4  # Track maximum chain length for camera scrolling

        self.genesis_position = (LayoutConfig.GENESIS_X, LayoutConfig.GENESIS_Y, 0)

        self.selfish_miner_block_opacity = LayoutConfig.SELFISH_BLOCK_OPACITY

        self.selfish_blocks_created = 0
        self.honest_blocks_created = 0
        self.previous_selfish_lead = 0

        # Create blockchains
        self.selfish_chain = ChainBranch("selfish")
        self.honest_chain = ChainBranch("honest")

        # Create Genesis block
        self.genesis = Block("Gen", self.genesis_position, LayoutConfig.GENESIS_BLOCK_COLOR)
        self.original_genesis = self.genesis

        self.scene.wait(AnimationTimingConfig.INITIAL_SCENE_WAIT_TIME)

        # Add genesis block to scene
        genesis_animations = [
            animations.draw_block_body(self.genesis.square),
            animations.draw_block_label(self.genesis.label)
        ]

        # Show initial state if narration enabled
        if self.enable_narration:
            initial_state = self.narration.get_state("0")
            genesis_animations.append(animations.transform_text(
                self.narration.current_state_text, initial_state))

            initial_caption = self.narration.get_narration("Selfish Mining in Bitcoin")
            genesis_animations.append(animations.transform_text(
                self.narration.current_caption_text, initial_caption))

        self.scene.play(*genesis_animations)

        self.scene.wait(AnimationTimingConfig.WAIT_TIME)

    ####################
    # Public API
    # Probabilistic Block Generation
    ####################

    def generate_next_block_probabilistic(self):
        """Generate next block based on alpha and gamma probabilities.

        Determines whether to create selfish or honest block using probabilistic
        model. Handles both normal states and tie states (0') with appropriate
        probability distributions.

        Notes
        -----
        **Normal State Logic**:
        - P(selfish) = alpha
        - P(honest) = 1 - alpha

        **Tie State Logic (0')**:
        - Uses :meth:`_decide_next_block_in_tie` for three-way decision
        - Automatically triggers race resolution after tiebreak

        **Automatic Behaviors**:
        - Checks for race resolution after each block
        - Updates camera position if chains grow beyond threshold
        - Manages state transitions and narration (if enabled)

        Examples
        --------

        .. code-block:: python

            sim = SelfishMiningSquares(self, alpha=0.3, gamma=0.5)

            # Generate 20 blocks probabilistically
            for _ in range(20):
                sim.generate_next_block_probabilistic()

        See Also
        --------
        :meth:`advance_selfish_chain` : Manual selfish block creation
        :meth:`advance_honest_chain` : Manual honest block creation
        :meth:`_decide_next_block_in_tie` : Tiebreak probability logic
        """
        honest_blocks, selfish_blocks, selfish_lead, is_tied = self._get_race_state()

        if is_tied:
            decision = self._decide_next_block_in_tie()

            if decision == "selfish_on_selfish":
                self.advance_selfish_chain()
            elif decision == "honest_on_honest":
                self.advance_honest_chain()
            else:  # "honest_on_selfish"
                self._advance_honest_on_selfish_chain()
        else:
            decision = self._decide_next_block_normal()

            if decision == "selfish":
                self.advance_selfish_chain()
            else:
                self.advance_honest_chain()

    ####################
    # Public API
    # Manual Block Creation
    ####################

    def advance_selfish_chain(self, caption: str | None = None, tiebreak: "TiebreakDecision | None" = None) -> None:
        """Create next selfish block with animated create.

        Adds a new selfish block to the selfish chain, animates its appearance,
        updates state tracking, and checks for race resolution conditions.

        Parameters
        ----------
        caption : str | None, optional
            Caption text to display in HUD (if narration enabled). Default: None
        tiebreak : Literal["honest_on_honest", "honest_on_selfish", "selfish_on_selfish"] | None, optional
            Manual override for next tiebreak decision. Invalid values are silently
            ignored (converted to None). Default: None

        Notes
        -----
        - Block label format: "S{count}" (e.g., "S1", "S2", "S3")
        - Position: Calculated based on parent block and chain type
        - Color: ``LayoutConfig.SELFISH_BLOCK_COLOR``
        - Automatically triggers race resolution if conditions met

        **Animation Sequence**:
        1. Draw block body and label
        2. Draw connecting line (if parent exists)
        3. Transform caption text (if provided and narration enabled)
        4. Show state transition (if narration enabled)
        5. Wait, then show final state
        6. Check camera scrolling and race resolution

        Examples
        --------

        .. code-block:: python

            sim = SelfishMiningSquares(self, enable_narration=True)

            # Create selfish block with caption
            sim.advance_selfish_chain(caption="Selfish miner finds block")

            # Force specific tiebreak outcome
            sim.advance_selfish_chain(tiebreak="selfish_on_selfish")

        See Also
        --------
        :meth:`advance_honest_chain` : Create honest block
        :meth:`_advance_honest_on_selfish_chain` : Create honest block on selfish parent
        """
        # Validate tiebreak - silently convert invalid strings to None
        if tiebreak is not None and tiebreak not in ("honest_on_honest", "honest_on_selfish", "selfish_on_selfish"):
            tiebreak = None

        self._pending_tiebreak = tiebreak

        self._store_previous_lead()

        previous_state = self._capture_state_before_block()

        self.selfish_blocks_created += 1

        label = f"S{self.selfish_blocks_created}"

        parent = self._get_parent_block("selfish")

        position = self._calculate_block_position(parent, "selfish")

        block, line = self.selfish_chain.add_block(label, position, parent_block=parent)

        self._animate_block_and_line(block, line, caption, previous_state)

        self._check_if_race_continues()

    def advance_honest_chain(self, caption: str | None = None, tiebreak: "TiebreakDecision | None" = None) -> None:
        """Create next honest block with animated create.

        Adds a new honest block to the honest chain, animates its appearance,
        updates state tracking, and checks for race resolution conditions.

        Parameters
        ----------
        caption : str | None, optional
            Caption text to display in HUD (if narration enabled). Default: None
        tiebreak : Literal["honest_on_honest", "honest_on_selfish", "selfish_on_selfish"] | None, optional
            Manual override for next tiebreak decision. Invalid values are silently
            ignored (converted to None). Default: None

        Notes
        -----
        - Block label format: "H{count}" (e.g., "H1", "H2", "H3")
        - Position: Calculated based on parent block and chain type
        - Color: ``LayoutConfig.HONEST_BLOCK_COLOR``
        - Automatically triggers race resolution if conditions met

        **Animation Sequence**:
        Same as :meth:`advance_selfish_chain`

        Examples
        --------

        .. code-block:: python

            sim = SelfishMiningSquares(self, enable_narration=True)

            # Create honest block with caption
            sim.advance_honest_chain(caption="Honest miner finds block")

        See Also
        --------
        :meth:`advance_selfish_chain` : Create selfish block
        """
        # Validate tiebreak - silently convert invalid strings to None
        if tiebreak is not None and tiebreak not in ("honest_on_honest", "honest_on_selfish", "selfish_on_selfish"):
            tiebreak = None

        self._pending_tiebreak = tiebreak

        self._store_previous_lead()

        previous_state = self._capture_state_before_block()

        self.honest_blocks_created += 1

        label = f"H{self.honest_blocks_created}"

        parent = self._get_parent_block("honest")

        position = self._calculate_block_position(parent, "honest")

        block, line = self.honest_chain.add_block(label, position, parent_block=parent)

        self._animate_block_and_line(block, line, caption, previous_state)

        self._check_if_race_continues()

    def update_caption(self, caption_text: str) -> None:
        """Update caption text without advancing any chain.

        Transforms the caption text and waits for the same duration as a normal
        block addition. Useful for displaying narrative text between block events.

        Parameters
        ----------
        caption_text : str
            Text to display in caption area. Pass empty string or None to clear.

        Notes
        -----
        - Does nothing if ``enable_narration`` is False
        - Wait duration matches block addition: 2 * WAIT_TIME + FADE_IN_TIME
        - Uses invisible placeholder ("....." in BLACK) to clear caption

        Examples
        --------

        .. code-block:: python

            sim = SelfishMiningSquares(self, enable_narration=True)

            # Display narrative text
            sim.update_caption("Analyzing blockchain state...")

            # Clear caption
            sim.update_caption("")

        See Also
        --------
        :meth:`NarrationManager.get_narration` : Caption text creation
        :meth:`NarrationManager.get_empty_narration` : Clear caption helper
        """
        if not self.enable_narration:
            return

            # Transform caption text
        if caption_text:
            caption_mobject = self.narration.get_narration(caption_text)
        else:
            caption_mobject = self.narration.get_empty_narration()

        self.scene.play(
            animations.transform_text(
                self.narration.current_caption_text,
                caption_mobject
            )
        )

        # Wait for the same duration as a block addition
        # This matches: initial wait + state transition + final wait
        total_wait_time = (AnimationTimingConfig.WAIT_TIME * 2) + AnimationTimingConfig.FADE_IN_TIME
        self.scene.wait(total_wait_time)

    ####################
    # Public API
    # Camera Control
    ####################

    def zoom_out_to_show_races(self, max_races: int = 10, animation_time: float = 3.0, margin: float = 1.0):
        """Zoom camera to show multiple races by calculating bounding box.

        Collects blocks from up to ``max_races`` complete races (traversing backward
        from current block), calculates bounding box, and animates camera to fit
        all blocks in frame.

        Parameters
        ----------
        max_races : int, optional
            Maximum number of complete races to display. Default: 10
        animation_time : float, optional
            Duration of zoom animation in seconds. Default: 3.0
        margin : float, optional
            Extra space around blocks in bounding box. Default: 1.0

        Notes
        -----
        - Uses backward traversal to find genesis blocks, then forward BFS
        - Ensures current race is always included
        - Calculates zoom factor based on frame aspect ratio
        - Preserves aspect ratio (no distortion)

        **Algorithm**:
        1. Find most recent block (current race tip)
        2. Traverse backward to find N genesis blocks
        3. Use Nth genesis as starting point
        4. Forward BFS to collect all descendant blocks
        5. Calculate bounding box and zoom factor
        6. Animate camera movement

        Examples
        --------

        .. code-block:: python

            sim = SelfishMiningSquares(self, alpha=0.3)

            # Generate multiple races
            for _ in range(50):
                sim.generate_next_block_probabilistic()

            # Zoom out to show last 5 races
            sim.zoom_out_to_show_races(max_races=5, animation_time=2.0)

        See Also
        --------
        :meth:`_collect_blocks_for_zoom_out` : Block collection logic
        :meth:`_find_most_recent_block` : Find current race tip
        """
        # Step 1: Collect blocks
        all_blocks = self._collect_blocks_for_zoom_out(max_races)
        if not all_blocks:
            return

        # Step 2: Calculate bounding box manually
        all_block_mobjects = []
        for block in all_blocks:
            all_block_mobjects.extend([block.square, block.label])

        # Calculate bounding box
        min_x = min(mob.get_critical_point(LEFT)[0] for mob in all_block_mobjects)
        max_x = max(mob.get_critical_point(RIGHT)[0] for mob in all_block_mobjects)
        min_y = min(mob.get_critical_point(DOWN)[1] for mob in all_block_mobjects)
        max_y = max(mob.get_critical_point(UP)[1] for mob in all_block_mobjects)

        # Calculate center and dimensions
        center_x = (min_x + max_x) / 2
        center_y = (min_y + max_y) / 2
        width = max_x - min_x + margin
        height = max_y - min_y + margin

        # Calculate zoom factor
        frame_aspect = config.frame_width / config.frame_height
        content_aspect = width / height

        if content_aspect > frame_aspect:
            zoom_factor = config.frame_width / width
        else:
            zoom_factor = config.frame_height / height

            # Step 3: Animate camera movement
        self.scene.move_camera(
            frame_center=[center_x, center_y, 0],
            zoom=zoom_factor,
            run_time=animation_time
        )
        self.scene.wait(AnimationTimingConfig.WAIT_TIME)

    ####################
    # Private
    # Probabilistic Decision Logic
    ####################

    def _get_race_state(self) -> tuple[int, int, int, bool]:
        """Get current race state from chain lengths.

        Retrieves the current state of the blockchain race by calculating chain
        lengths and determining if chains are tied. Used by probabilistic block
        generation to decide which decision logic to apply.

        Returns
        -------
        tuple[int, int, int, bool]
            A 4-tuple containing:
            - honest_len (int): Number of blocks in honest chain
            - selfish_len (int): Number of blocks in selfish chain
            - selfish_lead (int): Difference (selfish_len - honest_len)
            - is_tied (bool): True if chains are equal length and both non-empty

        Notes
        -----
        - Tie condition: ``selfish_lead == 0 and honest_len > 0``
        - Initial state (no blocks): ``honest_len == 0`` returns ``is_tied = False``
        - Uses :meth:`_get_current_chain_lengths` to calculate lengths

        See Also
        --------
        :meth:`_get_current_chain_lengths` : Calculates chain lengths
        :meth:`generate_next_block_probabilistic` : Uses this to determine decision logic
        """
        honest_len, selfish_len, selfish_lead = self._get_current_chain_lengths()
        is_tied = (selfish_lead == 0 and honest_len > 0)
        return honest_len, selfish_len, selfish_lead, is_tied

    def _decide_next_block_in_tie(self) -> "TiebreakDecision":
        """Decide which chain gets the next block during a tie (state 0').

        Determines tiebreak outcome using either manual override (if set via
        ``_pending_tiebreak``) or probabilistic distribution based on alpha
        (adversarial hash power) and gamma (network connectivity).

        Returns
        -------
        TiebreakDecision
            One of three outcomes:
            - ``"selfish_on_selfish"``: Selfish pool mines on selfish chain
            - ``"honest_on_selfish"``: Honest miner builds on selfish chain
            - ``"honest_on_honest"``: Honest miner builds on honest chain

        Notes
        -----
        **Manual Override**:
        - If ``self._pending_tiebreak`` is not None, returns that value immediately
        - Override is set via ``tiebreak`` parameter in :meth:`advance_selfish_chain`
          or :meth:`advance_honest_chain`

        **Probability Distribution** (from selfish mining paper state 0'):

        - P(selfish_on_selfish) = α

          Selfish pool mines next block with probability equal to their hash power

        - P(honest_on_selfish) = γ(1-α)

          Honest miners build on selfish chain: honest hash power × connectivity advantage

        - P(honest_on_honest) = (1-γ)(1-α)

          Honest miners build on honest chain: honest hash power × (1 - connectivity)

        Where:

        - α = ``self.alpha`` (selfish pool's hash power)
        - γ = ``self.gamma`` (network connectivity)
        - (1-α) = honest miners' hash power

        Total probability: α + γ(1-α) + (1-γ)(1-α) = 1

        **Implementation**:

        Uses cumulative probability ranges:

        - [0, α): selfish_on_selfish
        - [α, α + γ(1-α)): honest_on_selfish
        - [α + γ(1-α), 1]: honest_on_honest

        Examples
        --------

        .. code-block:: python

            # Probabilistic tiebreak (alpha=0.3, gamma=0.5)
            # P(selfish_on_selfish) = 0.3
            # P(honest_on_selfish) = 0.5 * 0.7 = 0.35
            # P(honest_on_honest) = 0.5 * 0.7 = 0.35
            decision = self._decide_next_block_in_tie()

        .. code-block:: python

            # Manual override via pending_tiebreak
            self._pending_tiebreak = "honest_on_honest"
            decision = self._decide_next_block_in_tie()
            # Returns: "honest_on_honest" (ignores probabilities)

        See Also
        --------
        :meth:`generate_next_block_probabilistic` : Calls this during tie states
        :meth:`advance_selfish_chain` : Can set manual tiebreak override
        :meth:`advance_honest_chain` : Can set manual tiebreak override
        """
        # Check for manual tiebreak override
        if self._pending_tiebreak is not None:
            return self._pending_tiebreak

        rand = random.random()

        if rand < self.alpha:
            return "selfish_on_selfish"
        elif rand < self.alpha + self.gamma * (1 - self.alpha):
            return "honest_on_selfish"
        else:
            return "honest_on_honest"

    def _decide_next_block_normal(self) -> str:
        """Decide which type of block to create during normal (non-tie) state.

        Determines whether to create a selfish or honest block using simple
        probabilistic distribution based on alpha (adversarial hash power).

        Returns
        -------
        str
            Either ``"selfish"`` or ``"honest"``

        Notes
        -----
        **Probability Distribution**:

        - P(selfish) = α (``self.alpha``)
        - P(honest) = 1 - α

        This represents the basic mining power distribution where the selfish
        pool has α fraction of total hash power.

        **Implementation**:

        - Generates random value in [0, 1)
        - If random < alpha: returns ``"selfish"``
        - Otherwise: returns ``"honest"``

        Examples
        --------

        .. code-block:: python

            # With alpha=0.3 (30% adversarial power)
            # 30% chance of "selfish", 70% chance of "honest"
            block_type = self._decide_next_block_normal()

        See Also
        --------
        :meth:`generate_next_block_probabilistic` : Calls this during normal states
        :meth:`_decide_next_block_in_tie` : Tiebreak decision logic
        """
        return "selfish" if random.random() < self.alpha else "honest"

    ####################
    # Private
    # Block Creation Helpers
    ####################

    def _advance_honest_on_selfish_chain(self, caption: str = None) -> None:
        """Create honest block on selfish chain during tiebreak.

        Adds an honest block to the selfish chain when an honest miner builds on
        the selfish parent block. This occurs during tiebreak scenarios (state 0')
        when the network connectivity parameter determines block placement.

        Parameters
        ----------
        caption : str | None, optional
            Caption text to display in HUD (if narration enabled). Default: None

        Notes
        -----
        - Block label format: "H{count}" (e.g., "H1", "H2", "H3")
        - Parent: Last block in selfish chain (or genesis if empty)
        - Position: Calculated using selfish chain's Y-offset
        - Automatically triggers race resolution check after animation

        **Animation Sequence**:
        Same as :meth:`advance_honest_chain` but adds to selfish chain instead

        **Typical Usage**:
        Called by :meth:`generate_next_block_probabilistic` when tiebreak
        decision is "honest_on_selfish"

        See Also
        --------
        :meth:`advance_honest_chain` : Create honest block on honest chain
        :meth:`_decide_next_block_in_tie` : Determines when this is called
        """

        self._store_previous_lead()

        previous_state = self._capture_state_before_block()

        self.honest_blocks_created += 1

        label = f"H{self.honest_blocks_created}"

        parent = self._get_parent_block("selfish")

        position = self._calculate_block_position(parent, "selfish")

        block, line = self.selfish_chain.add_block(label, position, parent_block=parent)

        self._animate_block_and_line(block, line, caption, previous_state)

        self._check_if_race_continues()

    def _store_previous_lead(self) -> None:
        """Store current selfish lead before block creation.

        Captures the selfish lead value before any chain modifications. Used to
        detect state transitions that trigger race resolution (e.g., lead changing
        from 2 to 1).

        Notes
        -----
        - Updates ``self.previous_selfish_lead`` attribute
        - Called at the start of every block creation method
        - Used by :meth:`_had_selfish_lead_of_exactly_two` for resolution detection

        See Also
        --------
        :meth:`_get_current_chain_lengths` : Calculates current lead
        :meth:`_had_selfish_lead_of_exactly_two` : Checks stored value
        """
        _, _, self.previous_selfish_lead = self._get_current_chain_lengths()

    def _get_parent_block(self, chain_type: str) -> Block:
        """Get parent block for next block in specified chain.

        Retrieves the last block in the specified chain to use as parent for
        the next block. Returns genesis block if chain is empty.

        Parameters
        ----------
        chain_type : str
            Chain identifier: either ``"selfish"`` or ``"honest"``

        Returns
        -------
        Block
            Last block in chain, or genesis block if chain is empty

        Notes
        -----
        - Selfish chain: ``self.selfish_chain.blocks[-1]`` or genesis
        - Honest chain: ``self.honest_chain.blocks[-1]`` or genesis
        - Genesis block: ``self.genesis`` (updated after each race resolution)

        See Also
        --------
        :meth:`_calculate_block_position` : Uses parent to calculate position
        """
        chain = self.selfish_chain if chain_type == "selfish" else self.honest_chain

        if not chain.blocks:
            return self.genesis
        else:
            return chain.blocks[-1]

    def _calculate_block_position(self, parent: Block, chain_type: str) -> Point3DLike:
        """Calculate position for new block based on parent and chain type.

        Determines the (x, y, z) coordinates for a new block. X-position is always
        one block spacing to the right of parent. Y-position depends on whether
        parent is genesis (uses chain-specific offset) or not (inherits parent's Y).

        Parameters
        ----------
        parent : Block
            Parent block to position relative to
        chain_type : str
            Chain identifier: either ``"selfish"`` or ``"honest"``

        Returns
        -------
        Point3DLike
            3D coordinates tuple (x, y, z) for new block position

        Notes
        -----
        **X-Position**:
        - Always: ``parent.x + LayoutConfig.BLOCK_HORIZONTAL_SPACING``

        **Y-Position**:
        - If parent is genesis:
          - Selfish: ``LayoutConfig.SELFISH_Y_OFFSET``
          - Honest: ``LayoutConfig.HONEST_Y_OFFSET``
        - If parent is not genesis:
          - Inherits parent's Y-coordinate (maintains chain alignment)

        **Z-Position**:
        - Always: 0 (2D visualization in 3D scene)

        Examples
        --------

        .. code-block:: python

            # First block in selfish chain (parent is genesis)
            parent = self.genesis
            pos = self._calculate_block_position(parent, "selfish")
            # Returns: (genesis.x + spacing, SELFISH_Y_OFFSET, 0)

            # Second block in selfish chain (parent is S1)
            parent = self.selfish_chain.blocks[-1]
            pos = self._calculate_block_position(parent, "selfish")
            # Returns: (S1.x + spacing, S1.y, 0)

        See Also
        --------
        :meth:`_get_parent_block` : Gets parent block for positioning
        """
        parent_pos = parent.get_center()
        x_position = float(parent_pos[0]) + LayoutConfig.BLOCK_HORIZONTAL_SPACING

        if parent == self.genesis:
            y_position = LayoutConfig.SELFISH_Y_OFFSET if chain_type == "selfish" else LayoutConfig.HONEST_Y_OFFSET
        else:
            y_position = float(parent_pos[1])

        return x_position, y_position, 0

    def _animate_block_and_line(self, block: Block, line: Line | FollowLine, caption: str = None,
                                previous_state: str = None) -> None:
        """Animate block and line creation with HUD text updates.

        Orchestrates the complete animation sequence for adding a block to the scene,
        including block/line drawing, caption updates, state transitions, and camera
        adjustments. Uses primer-based :class:`~.Transform` for HUD text.

        Parameters
        ----------
        block : Block
            Block to animate (already created, not yet added to scene)
        line : Line | FollowLine | None
            Connecting line to parent block, or None for genesis blocks
        caption : str | None, optional
            Caption text to display (if narration enabled). Default: None
        previous_state : str | None, optional
            State before block creation (for transition animation). Default: None

        Notes
        -----
        **Animation Sequence**:

        1. **Initial Play Call**:
           - Draw block body (square)
           - Draw block label (text)
           - Draw connecting line (if exists)
           - Transform caption (if provided and narration enabled)
           - Show state transition (if narration enabled)

        2. **Camera Check**:
           - Calls :meth:`_check_and_shift_camera_if_needed`
           - Shifts camera right if chains exceed threshold

        3. **Wait**:
           - Duration: ``AnimationTimingConfig.WAIT_TIME``

        4. **Final State Play Call** (conditional):
           - Transform transition text to final state text
           - Skipped for special cases (race resolution, tie reveal)

        5. **Final Wait**:
           - Duration: ``AnimationTimingConfig.WAIT_TIME``

        **Special Cases** (skip final state transformation):

        - ``2 → 0``: Honest catches up from -2 to -1 (triggers resolution)
        - ``0 → 0``: Honest wins (triggers resolution)
        - ``X → 0'``: Tie reveal (handled by :meth:`_reveal_selfish_chain_for_tie`)
        - ``0' → 0/1``: Tiebreak resolution (handled by resolution logic)

        **Caption Handling**:

        - If caption provided: Transform to visible caption text
        - If caption is None: Transform to invisible placeholder (clears caption)
        - Uses :meth:`NarrationManager.get_narration` and :meth:`NarrationManager.get_empty_narration`

        **State Transition Logic**:

        - Calculates current state using :meth:`_calculate_current_state`
        - Passes ``in_tiebreak=True`` if previous state was "0prime"
        - Shows transition animation (e.g., "1 → 2")
        - Shows final state animation (e.g., "State 2") unless special case

        Examples
        --------

        .. code-block:: python

            # Typical usage in block creation methods
            block, line = self.selfish_chain.add_block(label, position, parent_block=parent)
            self._animate_block_and_line(block, line, caption, previous_state)

        See Also
        --------
        :meth:`_check_and_shift_camera_if_needed` : Camera scrolling logic
        :meth:`_calculate_current_state` : State calculation
        :meth:`NarrationManager.get_transition` : Transition text creation
        :meth:`NarrationManager.get_state` : Final state text creation
        """
        ########## Block Anims ##########
        anims = [
            animations.draw_block_body(block.square),
            animations.draw_block_label(block.label),
        ]

        ########## Line Anims ##########
        if line:
            anims.append(animations.draw_line(line))

        ########## Caption Anims ##########
        if self.enable_narration:
            if caption:
                # Transform to new caption text
                caption_mobject = self.narration.get_narration(caption)
            else:
                # Transform to invisible placeholder (clears the caption)
                caption_mobject = self.narration.get_empty_narration()

            anims.append(animations.transform_text(
                self.narration.current_caption_text, caption_mobject))

        ########## State Anims ##########
        current_state = None
        is_special_case_2_to_0 = False
        is_special_case_0_to_0 = False
        is_special_case_to_0prime = False
        is_special_case_from_0prime = False

        # Always calculate current state when narration is enabled
        if self.enable_narration:
            in_tiebreak = (previous_state == "0prime")
            current_state = self._calculate_current_state(in_tiebreak=in_tiebreak)

            # SPECIAL CASE: Check if this triggers the "honest catches up from -2 to -1" resolution
            if previous_state == "2" and current_state == "1":
                current_state = "0"
                is_special_case_2_to_0 = True

                # SPECIAL CASE: Check if this is a 0→0 transition (honest wins, triggers race resolution)
            if previous_state == "0" and current_state == "0":
                is_special_case_0_to_0 = True

                # SPECIAL CASE: Check if this is a transition to 0' (tie reveal situation)
            if current_state == "0prime":
                is_special_case_to_0prime = True

                # SPECIAL CASE: Check if transitioning from 0prime during tiebreak resolution
            if previous_state == "0prime" and current_state in ["0", "1"]:
                is_special_case_from_0prime = True

                # Show transition if we have a previous state
            # Always transform the primer - no need to check if it exists
            if previous_state is not None and current_state is not None:
                transition_text_ref = self.narration.get_transition(previous_state, current_state)
                anims.append(animations.transform_text(
                    self.narration.current_state_text, transition_text_ref))

        ########## PLAY Anims ##########
        self.scene.play(*anims)

        # Check if camera needs to shift AFTER block is created but BEFORE state transition
        self._check_and_shift_camera_if_needed()

        ########## WAIT Anims ##########
        self.scene.wait(AnimationTimingConfig.WAIT_TIME)

        ########## ANOTHER PLAY Anims ##########
        # Skip the second transformation for special cases - let race resolution/tie reveal handle it
        if self.enable_narration and previous_state is not None and current_state is not None and not is_special_case_2_to_0 and not is_special_case_0_to_0 and not is_special_case_to_0prime and not is_special_case_from_0prime:
            final_state_text = self.narration.get_state(current_state)
            # Always transform the primer - it's already registered as fixed-in-frame
            self.scene.play(
                animations.transform_text(self.narration.current_state_text, final_state_text)
            )

        ########## WAIT Anims ##########
        self.scene.wait(AnimationTimingConfig.WAIT_TIME)

    def _check_and_shift_camera_if_needed(self) -> None:
        """Shift camera right if chains exceed previous maximum length.

        Automatically scrolls the camera to the right when either chain grows
        beyond the tracked maximum length and exceeds the threshold of 4 blocks.
        Shifts by exactly one block spacing per new maximum length.

        Notes
        -----
        **Threshold Behavior**:
        - No scrolling until max chain length > 4
        - Only scrolls when exceeding previous maximum

        **Shift Amount**:
        - Exactly ``LayoutConfig.BLOCK_HORIZONTAL_SPACING`` per new maximum
        - Maintains consistent spacing as chains grow

        **Camera Movement**:
        - Uses :meth:`Scene.move_camera` with frame_center update
        - Duration: ``AnimationTimingConfig.WAIT_TIME``
        - Updates ``self._previous_max_chain_len`` after shift

        **Tracking**:
        - ``self._previous_max_chain_len`` initialized to 4 in :meth:`__init__`
        - Reset to 4 in :meth:`_transition_to_next_race` after race resolution

        Examples
        --------

        .. code-block:: python

            # Chain lengths: honest=3, selfish=5
            # Previous max: 4
            # Result: Shift right by one block spacing, update max to 5

            # Chain lengths: honest=5, selfish=5
            # Previous max: 5
            # Result: No shift (max unchanged)

        See Also
        --------
        :meth:`_get_current_chain_lengths` : Gets current chain lengths
        :meth:`_transition_to_next_race` : Resets tracking after race
        """
        honest_len, selfish_len, _ = self._get_current_chain_lengths()
        max_chain_len = max(honest_len, selfish_len)

        # Only shift if we've exceeded the previous maximum
        if max_chain_len > 4 and max_chain_len > self._previous_max_chain_len:
            # Shift by exactly one block spacing
            shift_amount = LayoutConfig.BLOCK_HORIZONTAL_SPACING

            current_center = self.scene.camera.frame_center
            new_center = [current_center[0] + shift_amount, current_center[1], current_center[2]]

            self.scene.move_camera(
                frame_center=new_center,
                run_time=AnimationTimingConfig.WAIT_TIME
            )

            # Update the tracked maximum
            self._previous_max_chain_len = max_chain_len

    ####################
    # Private
    # Chain State Tracking
    ####################

    def _get_current_chain_lengths(self) -> tuple[int, int, int]:
        """Get current chain lengths and selfish lead.

        Calculates the number of blocks in each chain and the selfish miner's
        lead (positive if selfish ahead, negative if honest ahead, zero if tied).

        Returns
        -------
        tuple[int, int, int]
            A 3-tuple containing:
            - honest_len (int): Number of blocks in honest chain
            - selfish_len (int): Number of blocks in selfish chain
            - selfish_lead (int): Difference (selfish_len - honest_len)

        Notes
        -----
        - Directly counts blocks in ``self.honest_chain.blocks`` and ``self.selfish_chain.blocks``
        - Selfish lead calculation: ``selfish_len - honest_len``
        - Positive lead: Selfish chain is ahead
        - Negative lead: Honest chain is ahead
        - Zero lead: Chains are equal length (may indicate tie state)

        Examples
        --------

        .. code-block:: python

            # Honest: 3 blocks, Selfish: 5 blocks
            honest_len, selfish_len, selfish_lead = self._get_current_chain_lengths()
            # Returns: (3, 5, 2)

            # Honest: 4 blocks, Selfish: 2 blocks
            honest_len, selfish_len, selfish_lead = self._get_current_chain_lengths()
            # Returns: (4, 2, -2)

        See Also
        --------
        :meth:`_get_race_state` : Uses this to determine tie state
        :meth:`_store_previous_lead` : Stores lead before block creation
        """
        honest_len = len(self.honest_chain.blocks)
        selfish_len = len(self.selfish_chain.blocks)
        selfish_lead = selfish_len - honest_len
        return honest_len, selfish_len, selfish_lead

    def _get_winning_and_losing_chains(self, winner: str) -> tuple[ChainBranch, ChainBranch]:
        """Get winning and losing chains based on winner identifier.

        Returns the chain objects in order (winning chain, losing chain) based
        on the winner string. Used during race resolution to identify which
        chain to keep and which to discard.

        Parameters
        ----------
        winner : str
            Winner identifier: either ``"honest"`` or ``"selfish"``

        Returns
        -------
        tuple[ChainBranch, ChainBranch]
            A 2-tuple containing:
            - winning_chain (ChainBranch): The chain that won the race
            - losing_chain (ChainBranch): The chain that lost the race

        Notes
        -----
        - If winner is ``"honest"``: Returns ``(self.honest_chain, self.selfish_chain)``
        - Otherwise: Returns ``(self.selfish_chain, self.honest_chain)``
        - No validation of winner string (assumes valid input)

        Examples
        --------

        .. code-block:: python

            # Get chains when honest wins
            winning, losing = self._get_winning_and_losing_chains("honest")
            # winning = self.honest_chain, losing = self.selfish_chain

            # Get chains when selfish wins
            winning, losing = self._get_winning_and_losing_chains("selfish")
            # winning = self.selfish_chain, losing = self.honest_chain

        See Also
        --------
        :meth:`_animate_race_resolution` : Uses this to identify chains for animation
        :meth:`_get_winning_block` : Gets the winning block from winner string
        """
        if winner == "honest":
            return self.honest_chain, self.selfish_chain
        else:
            return self.selfish_chain, self.honest_chain

    def _get_winning_block(self, winner: str) -> Block | None:
        """Get the winning block based on winner identifier.

        Returns the last block in the winning chain, or None if the chain is empty.
        Used to identify which block becomes the next genesis after race resolution.

        Parameters
        ----------
        winner : str
            Winner identifier: either ``"honest"`` or ``"selfish"``

        Returns
        -------
        Block | None
            Last block in winning chain, or None if chain is empty

        Notes
        -----
        - If winner is ``"honest"``: Returns ``self.honest_chain.blocks[-1]`` or None
        - Otherwise: Returns ``self.selfish_chain.blocks[-1]`` or None
        - Returns None only if winning chain has no blocks (edge case)
        - No validation of winner string (assumes valid input)

        Examples
        --------

        .. code-block:: python

            # Get winning block when honest wins
            winning_block = self._get_winning_block("honest")
            # Returns: Last block in honest chain

            # Get winning block when selfish wins
            winning_block = self._get_winning_block("selfish")
            # Returns: Last block in selfish chain

            # Edge case: Empty chain
            winning_block = self._get_winning_block("honest")
            # Returns: None (if honest_chain.blocks is empty)

        See Also
        --------
        :meth:`_transition_to_next_race` : Uses this to set next genesis block
        :meth:`_get_winning_and_losing_chains` : Gets chain objects instead of blocks
        """
        if winner == "honest":
            return self.honest_chain.blocks[-1] if self.honest_chain.blocks else None
        else:
            return self.selfish_chain.blocks[-1] if self.selfish_chain.blocks else None

    ####################
    # Race Resolution Detection
    # Private
    ####################

    def _check_if_race_continues(self) -> None:
        """Evaluate race conditions and trigger resolution if needed.

        Checks three resolution conditions in priority order: honest wins (lead = -1),
        tie state (lead = 0), and honest catch-up (lead = 1 after being 2). If any
        condition is met, triggers appropriate resolution or tiebreak handling.

        Notes
        -----
        **Resolution Strategy Priority**:

        1. **Honest Wins**: Checked via :meth:`_check_does_honest_win`
           - Condition: ``selfish_lead == -1``
           - Action: Trigger resolution with honest as winner

        2. **Tie State**: Checked via :meth:`_check_if_tied`
           - Condition: ``selfish_lead == 0 and honest_len > 0``
           - Action: Reveal selfish chain, resolve tiebreak, check final lead

        3. **Honest Catch-Up**: Checked via :meth:`_check_if_honest_caught_up`
           - Condition: ``selfish_lead == 1`` and previous lead was 2
           - Action: Trigger resolution with selfish as winner

        **Strategy Pattern**:
        - Uses lambda functions to defer execution until needed
        - Each strategy returns ``True`` if resolution triggered, ``False`` otherwise
        - First strategy that returns ``True`` stops further checks

        **Called By**:
        - :meth:`advance_selfish_chain` (after block creation)
        - :meth:`advance_honest_chain` (after block creation)
        - :meth:`_advance_honest_on_selfish_chain` (after tiebreak block)

        See Also
        --------
        :meth:`_check_does_honest_win` : Check if honest chain wins
        :meth:`_check_if_tied` : Check and handle tie state
        :meth:`_check_if_honest_caught_up` : Check if honest caught up from -2
        :meth:`_get_current_chain_lengths` : Get chain state
        """

        honest_len, selfish_len, selfish_lead = self._get_current_chain_lengths()

        # Define resolution strategies in priority order
        strategies = [
            lambda sl, hb: self._check_does_honest_win(sl),
            lambda sl, hb: self._check_if_tied(sl, hb),
            lambda sl, hb: self._check_if_honest_caught_up(sl),
        ]

        for strategy in strategies:
            if strategy(selfish_lead, honest_len):
                return

    def _check_does_honest_win(self, selfish_lead: int) -> bool:
        """Check if honest chain wins by overtaking selfish chain.

        Detects when honest chain is one block ahead of selfish chain (lead = -1),
        indicating honest miners have overtaken and won the race.

        Parameters
        ----------
        selfish_lead : int
            Current selfish lead (selfish_len - honest_len)

        Returns
        -------
        bool
            True if honest wins (triggers resolution), False otherwise

        Notes
        -----
        **Win Condition**:
        - ``selfish_lead == -1``: Honest chain is 1 block ahead
        - This means honest miners have overtaken the selfish chain

        **Action on Win**:
        - Calls :meth:`_trigger_resolution` with ``"honest"`` as winner
        - Resolution will fade out selfish chain and transition to next race

        **Priority**:
        - Checked first in :meth:`_check_if_race_continues` strategy list
        - Takes precedence over tie and catch-up checks

        Examples
        --------

        .. code-block:: python

            # Honest: 5 blocks, Selfish: 4 blocks
            # selfish_lead = 4 - 5 = -1
            result = self._check_does_honest_win(-1)
            # Returns: True (triggers honest win resolution)

            # Honest: 3 blocks, Selfish: 3 blocks
            # selfish_lead = 3 - 3 = 0
            result = self._check_does_honest_win(0)
            # Returns: False (not a win condition)

        See Also
        --------
        :meth:`_trigger_resolution` : Executes race resolution
        :meth:`_check_if_race_continues` : Calls this as first strategy
        """
        if selfish_lead == -1:
            self._trigger_resolution("honest")
            return True
        return False

    def _check_if_tied(self, selfish_lead: int, honest_blocks: int) -> bool:
        """Check and handle tie state (state 0').

        Detects when chains are equal length with both having blocks (tie state),
        reveals selfish chain, resolves tiebreak, and checks final lead to determine
        race winner.

        Parameters
        ----------
        selfish_lead : int
            Current selfish lead (selfish_len - honest_len)
        honest_blocks : int
            Number of blocks in honest chain

        Returns
        -------
        bool
            True if tie detected and handled, False otherwise

        Notes
        -----
        **Tie Condition**:
        - ``selfish_lead == 0``: Chains are equal length
        - ``honest_blocks > 0``: Both chains have blocks (not initial state)

        **Tie Resolution Sequence**:

        1. **Reveal Selfish Chain**: :meth:`_reveal_selfish_chain_for_tie`
           - Makes hidden selfish blocks visible
           - Animates opacity change

        2. **Wait**: ``AnimationTimingConfig.WAIT_TIME``

        3. **Tiebreak Decision**: :meth:`_decide_next_block_in_tie`
           - Returns: ``"selfish_on_selfish"``, ``"honest_on_honest"``, or ``"honest_on_selfish"``

        4. **Create Tiebreak Block**:
           - ``selfish_on_selfish``: :meth:`advance_selfish_chain`
           - ``honest_on_honest``: :meth:`advance_honest_chain`
           - ``honest_on_selfish``: :meth:`_advance_honest_on_selfish_chain`

        5. **Wait**: ``AnimationTimingConfig.WAIT_TIME``

        6. **Check Final Lead**:
           - If ``new_lead > 0``: Selfish wins → :meth:`_trigger_resolution("selfish")`
           - If ``new_lead < 0``: Honest wins → :meth:`_trigger_resolution("honest")`
           - If ``new_lead == 0``: Tie persists (no resolution)

        **Priority**:
        - Checked second in :meth:`_check_if_race_continues` strategy list
        - After honest win check, before catch-up check

        Examples
        --------

        .. code-block:: python

            # Honest: 3 blocks, Selfish: 3 blocks
            # selfish_lead = 0, honest_blocks = 3
            result = self._check_if_tied(0, 3)
            # Returns: True (tie detected, tiebreak executed)

            # Honest: 0 blocks, Selfish: 0 blocks (initial state)
            # selfish_lead = 0, honest_blocks = 0
            result = self._check_if_tied(0, 0)
            # Returns: False (not a tie, just initial state)

        See Also
        --------
        :meth:`_reveal_selfish_chain_for_tie` : Makes selfish chain visible
        :meth:`_decide_next_block_in_tie` : Determines tiebreak outcome
        :meth:`_trigger_resolution` : Executes race resolution
        :meth:`_get_current_chain_lengths` : Gets updated lead after tiebreak
        """
        if selfish_lead == 0 and honest_blocks > 0:
            self._reveal_selfish_chain_for_tie()
            self.scene.wait(AnimationTimingConfig.WAIT_TIME)

            decision = self._decide_next_block_in_tie()

            if decision == "selfish_on_selfish":
                self.advance_selfish_chain()
            elif decision == "honest_on_honest":
                self.advance_honest_chain()
            else:
                self._advance_honest_on_selfish_chain()

            self.scene.wait(AnimationTimingConfig.WAIT_TIME)

            _, _, new_lead = self._get_current_chain_lengths()

            if new_lead > 0:
                self._trigger_resolution("selfish")
            elif new_lead < 0:
                self._trigger_resolution("honest")

            return True
        return False

    def _check_if_honest_caught_up(self, selfish_lead: int) -> bool:
        """Check if honest caught up from 2-block deficit (state 2 → 1).

        Detects when selfish lead drops from 2 to 1, triggering selfish win resolution
        according to selfish mining strategy (release private chain before being caught).

        Parameters
        ----------
        selfish_lead : int
            Current selfish lead (selfish_len - honest_len)

        Returns
        -------
        bool
            True if catch-up detected (triggers resolution), False otherwise

        Notes
        -----
        **Catch-Up Condition**:
        - ``selfish_lead == 1``: Selfish currently 1 block ahead
        - :meth:`_had_selfish_lead_of_exactly_two()` returns True: Previous lead was 2

        **Selfish Mining Strategy**:
        - When lead drops from 2 to 1, selfish pool releases private chain
        - This prevents honest miners from catching up completely
        - Selfish pool wins the race by revealing their longer chain

        **Action on Catch-Up**:
        - Calls :meth:`_trigger_resolution` with ``"selfish"`` as winner
        - Resolution will fade out honest chain and transition to next race

        **Priority**:
        - Checked third (last) in :meth:`_check_if_race_continues` strategy list
        - After honest win and tie checks

        Examples
        --------

        .. code-block:: python

            # Previous: Honest=2, Selfish=4 (lead=2)
            # Current: Honest=3, Selfish=4 (lead=1)
            # Honest just caught up from -2 to -1
            result = self._check_if_honest_caught_up(1)
            # Returns: True (triggers selfish win resolution)

            # Previous: Honest=1, Selfish=2 (lead=1)
            # Current: Honest=2, Selfish=3 (lead=1)
            # Lead stayed at 1 (not a catch-up from 2)
            result = self._check_if_honest_caught_up(1)
            # Returns: False (previous lead was not 2)

        See Also
        --------
        :meth:`_had_selfish_lead_of_exactly_two` : Checks previous lead
        :meth:`_trigger_resolution` : Executes race resolution
        :meth:`_store_previous_lead` : Stores lead before block creation
        """
        if selfish_lead == 1 and self._had_selfish_lead_of_exactly_two():
            self._trigger_resolution("selfish")
            return True
        return False

    ####################
    # Private
    # Race Resolution Execution
    ####################

    def _trigger_resolution(self, winner: str):
        """Trigger race resolution and transition to next race.

        Orchestrates the complete race resolution process: identifies winning block,
        animates resolution, updates genesis reference, and resets state for the
        next race.

        Parameters
        ----------
        winner : str
            Winner identifier: either ``"honest"`` or ``"selfish"``

        Notes
        -----
        **Resolution Sequence**:

        1. Get winning block via :meth:`_get_winning_block`
        2. Animate resolution via :meth:`_animate_race_resolution`
        3. Mark winning block as next genesis
        4. Transition to next race via :meth:`_transition_to_next_race`
        5. Reset counters via :meth:`_finalize_race_and_start_next`

        **State Updates**:
        - ``self.genesis`` updated to winning block
        - Chain lists cleared
        - Block counters reset to 0
        - Camera tracking reset to threshold (4)

        See Also
        --------
        :meth:`_animate_race_resolution` : Handles animation sequence
        :meth:`_get_winning_block` : Identifies winning block
        :meth:`_transition_to_next_race` : Updates genesis and clears chains
        :meth:`_finalize_race_and_start_next` : Resets counters
        """
        # Use helper method instead of inline logic
        winning_block = self._get_winning_block(winner)

        # Run resolution animation
        self._animate_race_resolution(winner)

        # Update genesis reference to winning block
        if winning_block:
            winning_block.set_as_next_genesis()
            self._transition_to_next_race(winning_block)

        # Reset for next race
        self._finalize_race_and_start_next()

    def _animate_race_resolution(self, winner: str):
        """Animate the resolution of a blockchain race.

        Performs three-step animation sequence: vertical shift to align winning block
        with genesis Y-position, horizontal camera shift to position winning block at
        genesis screen position, and optional state transition to "0".

        Parameters
        ----------
        winner : str
            Winner identifier: either ``"honest"`` or ``"selfish"``

        Notes
        -----
        **Animation Sequence**:

        **Step 1: Vertical Shift** (only if selfish chain has blocks)
        - Calculate vertical distance: ``genesis_y - winning_block_y``
        - Create VGroups for winning and losing chain mobjects
        - Shift both chains vertically using ``.animate.shift(UP * vertical_shift)``
        - Update FollowLines via :meth:`_collect_follow_line_animations`
        - Duration: ``AnimationTimingConfig.SHIFT_TO_NEW_GENESIS_TIME``

        **Step 2: Horizontal Camera Shift**
        - Calculate winning block's current screen position
        - Calculate required camera shift to align with ``self.genesis_position[0]``
        - Move camera horizontally using :meth:`Scene.move_camera`
        - Duration: ``AnimationTimingConfig.SHIFT_TO_NEW_GENESIS_TIME``

        **Step 3: State Transition** (if narration enabled)
        - Transform state text to "0" using :meth:`NarrationManager.get_state`
        - Only plays if ``state_animations`` list is non-empty
        - Wait: ``AnimationTimingConfig.WAIT_TIME``

        **Early Exit**:
        - Returns immediately if winning chain has no blocks

        **Mobject Handling**:
        - Uses :meth:`Block.get_transform_safe_mobjects` to exclude FollowLines
        - FollowLines updated separately via :meth:`_collect_follow_line_animations`

        Examples
        --------

        .. code-block:: python

            # Honest wins: shift honest chain to genesis position
            self._animate_race_resolution("honest")

            # Selfish wins: shift selfish chain to genesis position
            self._animate_race_resolution("selfish")

        See Also
        --------
        :meth:`_get_winning_and_losing_chains` : Gets chain objects
        :meth:`_collect_follow_line_animations` : Creates line update animations
        :meth:`Block.get_transform_safe_mobjects` : Gets mobjects excluding lines
        :meth:`Block.set_as_next_genesis` : Marks block as next genesis
        """
        winning_chain, losing_chain = self._get_winning_and_losing_chains(winner)
        winning_block = winning_chain.blocks[-1] if winning_chain.blocks else None

        if not winning_block:
            return

        winning_block.set_as_next_genesis()

        # Step 1: Vertical shift (only if selfish chain has blocks)
        if self.selfish_chain.blocks:
            genesis_y = self.genesis_position[1]
            winning_block_current_y = winning_block.get_center()[1]
            vertical_shift = genesis_y - winning_block_current_y

            winning_group = VGroup(*[mob for block in winning_chain.blocks
                                     for mob in block.get_transform_safe_mobjects()])
            losing_group = VGroup(*[mob for block in losing_chain.blocks
                                    for mob in block.get_transform_safe_mobjects()])

            follow_line_animations = self._collect_follow_line_animations([winning_chain, losing_chain])

            self.scene.play(
                winning_group.animate.shift(UP * vertical_shift),
                losing_group.animate.shift(UP * vertical_shift),
                *follow_line_animations,
                run_time=AnimationTimingConfig.SHIFT_TO_NEW_GENESIS_TIME
            )

            # Step 2: Horizontal shift - position winning block at genesis screen position
        winning_block_x = winning_block.get_center()[0]
        current_camera_x = self.scene.camera.frame_center[0]

        # Where does winning block appear on screen right now?
        winning_block_screen_x = winning_block_x - current_camera_x

        # Where should genesis appear on screen?
        target_screen_x = self.genesis_position[0]

        # How far to shift camera?
        camera_shift = winning_block_screen_x - target_screen_x

        # Move camera
        new_camera_x = current_camera_x + camera_shift

        self.scene.move_camera(
            frame_center=[new_camera_x, self.scene.camera.frame_center[1], self.scene.camera.frame_center[2]],
            run_time=AnimationTimingConfig.SHIFT_TO_NEW_GENESIS_TIME
        )

#        # Step 3: Update label to "Gen"
#        state_animations = [winning_block.change_label_to("Gen")]
        # try without changing label
        state_animations = []

        if self.enable_narration and self.narration.current_state_text:
            final_state = self.narration.get_state("0")
            state_animations.append(animations.transform_text(self.narration.current_state_text, final_state))

#        self.scene.play(*state_animations)
        # trying to ensure empty animation does not crash when testing without changing block label(and narration disabled)
        if state_animations:  # Only play if there are animations
            self.scene.play(*state_animations)

        self.scene.wait(AnimationTimingConfig.WAIT_TIME)

    def _finalize_race_and_start_next(self):
        """Reset block counters for next race.

        Resets all block creation counters and previous lead tracking to prepare
        for the next blockchain race.

        Notes
        -----
        **Counters Reset**:
        - ``self.honest_blocks_created`` → 0
        - ``self.selfish_blocks_created`` → 0
        - ``self.previous_selfish_lead`` → 0

        **Called By**:
        - :meth:`_trigger_resolution` (after race resolution animation)

        **Does NOT Reset**:
        - ``self.genesis`` (updated by :meth:`_transition_to_next_race`)
        - Chain lists (cleared by :meth:`_transition_to_next_race`)
        - Camera tracking (reset by :meth:`_transition_to_next_race`)

        See Also
        --------
        :meth:`_trigger_resolution` : Orchestrates resolution sequence
        :meth:`_transition_to_next_race` : Handles genesis and chain updates
        """
        # Reset counters
        self.honest_blocks_created = 0
        self.selfish_blocks_created = 0
        self.previous_selfish_lead = 0

    def _transition_to_next_race(self, winning_block: Block):
        """Update genesis and clear chains for next race.

        Sets the winning block as the new genesis, clears both chain lists, and
        resets camera tracking to prepare for the next blockchain race.

        Parameters
        ----------
        winning_block : Block
            The block that won the race (becomes next genesis)

        Notes
        -----
        **State Updates**:
        - ``self.genesis`` → ``winning_block``
        - ``self.selfish_chain.blocks`` → empty list
        - ``self.honest_chain.blocks`` → empty list
        - ``self._previous_max_chain_len`` → 4 (reset to threshold)

        **Called By**:
        - :meth:`_trigger_resolution` (after marking block as next genesis)

        **Important**:
        - Winning block must already be marked as next genesis via
          :meth:`Block.set_as_next_genesis` before calling this method
        - Chain lists are cleared, but block objects remain in scene
          (they become part of the historical blockchain visualization)

        See Also
        --------
        :meth:`_trigger_resolution` : Orchestrates resolution sequence
        :meth:`Block.set_as_next_genesis` : Marks block as next genesis
        :meth:`_check_and_shift_camera_if_needed` : Uses camera tracking threshold
        """
        self.genesis = winning_block

        # Clear the blockchain lists for next race
        self.selfish_chain.blocks.clear()
        self.honest_chain.blocks.clear()

        # Reset camera tracking for new race
        self._previous_max_chain_len = 4  # Reset to threshold

    ####################
    # Private
    # Tie Handling
    ####################

    def _reveal_selfish_chain_for_tie(self):
        """Reveal selfish chain by vertically shifting both chains to tie positions.

        Animates both chains to symmetric Y-positions relative to genesis, making
        the previously hidden selfish chain visible. Simultaneously transitions
        state text to "0prime" (tie state) if narration is enabled.

        Notes
        -----
        **Early Exit**:
        - Returns immediately if either chain is empty
        - No animation occurs if tie conditions aren't met

        **Position Calculation**:
        - Uses ``LayoutConfig.get_tie_positions(genesis_y)`` to get target Y-positions
        - Returns tuple: ``(honest_target_y, selfish_target_y)``
        - Calculates shift amounts: ``target_y - current_y`` for each chain

        **Animation Sequence**:

        1. **Collect Mobjects**: Get all mobjects from both chains via
           :meth:`ChainBranch.get_all_mobjects`

        2. **Collect FollowLine Animations**: Update connecting lines via
           :meth:`_collect_follow_line_animations`

        3. **Prepare Shift Animations**:
           - Honest chain: ``mob.animate.shift(UP * honest_shift)``
           - Selfish chain: ``mob.animate.shift(UP * selfish_shift)``
           - FollowLine updates for both chains

        4. **Add State Transition** (if narration enabled):
           - Transform state text to "0prime" using :meth:`NarrationManager.get_state`

        5. **Play All Animations**: Simultaneous vertical shift and state transition
           - Duration: ``AnimationTimingConfig.VERTICAL_SHIFT_TIME``

        6. **Wait**: Display tie state for ``AnimationTimingConfig.WAIT_TIME``

        **Typical Usage**:
        Called by :meth:`_check_if_tied` when chains reach equal length (state 0')

        Examples
        --------

        .. code-block:: python

            # Chains are tied (both length 3)
            # Honest chain at Y=2.0, Selfish chain at Y=-2.0
            # Genesis at Y=0.0

            # After _reveal_selfish_chain_for_tie():
            # Honest chain shifts to Y=1.0 (symmetric above genesis)
            # Selfish chain shifts to Y=-1.0 (symmetric below genesis)
            # State text shows "0'"

        See Also
        --------
        :meth:`_check_if_tied` : Calls this method during tie detection
        :meth:`_collect_follow_line_animations` : Updates connecting lines
        :meth:`ChainBranch.get_all_mobjects` : Collects chain mobjects
        :meth:`LayoutConfig.get_tie_positions` : Calculates target Y-positions
        """
        if not self.selfish_chain.blocks or not self.honest_chain.blocks:
            return

        # Calculate target y-positions using config - now returns both positions as a tuple
        genesis_y = self.genesis_position[1]
        honest_target_y, selfish_target_y = LayoutConfig.get_tie_positions(genesis_y)

        # Calculate shifts based on actual current block positions
        honest_current_y = self.honest_chain.blocks[0].get_center()[1]
        selfish_current_y = self.selfish_chain.blocks[0].get_center()[1]

        honest_shift = honest_target_y - honest_current_y
        selfish_shift = selfish_target_y - selfish_current_y

        # Collect all mobjects from both chains
        honest_mobjects = self.honest_chain.get_all_mobjects()
        selfish_mobjects = self.selfish_chain.get_all_mobjects()

        # Collect FollowLine animations
        follow_line_animations = self._collect_follow_line_animations(
            [self.honest_chain, self.selfish_chain]
        )

        # Prepare animations list
        shift_animations = [
            *[mob.animate.shift(UP * honest_shift) for mob in honest_mobjects],
            *[mob.animate.shift(UP * selfish_shift) for mob in selfish_mobjects],
            *follow_line_animations
        ]

        # Add state transition animation if narration is enabled
        # Always transform the primer - no need to check if it exists
        if self.enable_narration:
            final_state_text = self.narration.get_state("0prime")
            shift_animations.append(
                animations.transform_text(self.narration.current_state_text, final_state_text)
            )

        # Animate vertical shift for both chains simultaneously with state transition
        self.scene.play(
            *shift_animations,
            run_time=AnimationTimingConfig.VERTICAL_SHIFT_TIME
        )

        # Wait to show the tie state
        self.scene.wait(AnimationTimingConfig.WAIT_TIME)

    ####################
    # Private
    # Zoom/Camera Helpers
    ####################

    def _collect_blocks_for_zoom_out(self, max_races: int) -> list[Block]:
        """Collect blocks by traversing backward from current block, then forward BFS.

        Ensures the current race is always included and prevents partial races
        from being displayed by using a two-phase traversal: backward to find
        genesis blocks, then forward BFS to collect all descendants.

        Parameters
        ----------
        max_races : int
            Maximum number of complete races to display

        Returns
        -------
        list[Block]
            List of all blocks to include in zoom-out animation

        Notes
        -----
        **Algorithm Overview**:

        **Phase 1: Backward Traversal**
        - Start from most recent block via :meth:`_find_most_recent_block`
        - Traverse backward through parent links
        - Collect up to ``max_races`` genesis blocks (blocks marked as genesis or next_genesis)
        - Use the Nth genesis back as starting point

        **Phase 2: Forward BFS**
        - Start from the Nth genesis block (or ``self.original_genesis`` if insufficient)
        - Use breadth-first search to collect all descendant blocks
        - Naturally discovers all forks through ``block.children``
        - Uses visited set to prevent duplicate processing

        **Why This Approach**:
        - Guarantees current race is included (starts from most recent block)
        - Prevents partial races (only includes complete races from genesis)
        - Handles forks correctly (BFS discovers all branches)

        Examples
        --------

        .. code-block:: python

            # Collect blocks from last 3 complete races
            blocks = self._collect_blocks_for_zoom_out(max_races=3)

            # If only 2 races exist, returns all blocks from original_genesis
            # If 5 races exist, returns blocks from 3rd-most-recent genesis onward

        See Also
        --------
        :meth:`_find_most_recent_block` : Finds starting point for backward traversal
        :meth:`zoom_out_to_show_races` : Uses this to collect blocks for camera zoom
        :meth:`Block.is_genesis` : Checks if block is a genesis block
        :meth:`Block.is_next_genesis` : Checks if block is marked as next genesis
        """
        # Step 1: Find most recent block
        most_recent = self._find_most_recent_block()

        # Step 2: Traverse backward to find N genesis blocks
        genesis_blocks = []
        current = most_recent

        while current is not None and len(genesis_blocks) < max_races:
            if current.is_genesis() or current.is_next_genesis():
                genesis_blocks.append(current)
            current = current.parent_block

        # Step 3: Use the Nth genesis back as starting point (or original_genesis if not enough)
        starting_genesis = genesis_blocks[-1] if genesis_blocks else self.original_genesis

        # Step 4: Forward BFS from starting genesis
        all_blocks = []
        blocks_to_visit = [starting_genesis]
        visited = set()

        while blocks_to_visit:
            block = blocks_to_visit.pop(0)
            if block in visited:
                continue
            visited.add(block)
            all_blocks.append(block)
            blocks_to_visit.extend(block.children)  # Discovers all forks naturally

        return all_blocks

    def _find_most_recent_block(self) -> Block:
        """Find the most recent block in the current race.

        Returns the block marked as next_genesis if race is resolved,
        otherwise returns the furthest block from either chain based on
        chain length.

        Returns
        -------
        Block
            The most recent block in the blockchain

        Notes
        -----
        **Resolution Priority**:

        1. **Resolved Race**: If any block is marked as ``next_genesis``, return it
           - Check selfish chain last block first
           - Then check honest chain last block

        2. **Unresolved Race**: Return furthest block based on chain length
           - If both chains have blocks: return from longer chain
           - If tied: return selfish chain's last block (tiebreaker)
           - If only one chain has blocks: return that chain's last block
           - If no chains have blocks: return ``self.genesis``

        **Typical Usage**:
        Called by :meth:`_collect_blocks_for_zoom_out` as starting point for
        backward traversal to find genesis blocks.

        Examples
        --------

        .. code-block:: python

            # Race resolved: selfish chain won
            # selfish_chain.blocks[-1].is_next_genesis() == True
            block = self._find_most_recent_block()
            # Returns: selfish_chain.blocks[-1]

        .. code-block:: python

            # Race unresolved: honest=3 blocks, selfish=5 blocks
            block = self._find_most_recent_block()
            # Returns: selfish_chain.blocks[-1] (longer chain)

        .. code-block:: python

            # Race unresolved: honest=4 blocks, selfish=4 blocks (tied)
            block = self._find_most_recent_block()
            # Returns: selfish_chain.blocks[-1] (tiebreaker)

        See Also
        --------
        :meth:`_collect_blocks_for_zoom_out` : Uses this to start backward traversal
        :meth:`Block.is_next_genesis` : Checks if block is marked as next genesis
        """
        # Check if race is resolved (one block marked as next_genesis)
        if self.selfish_chain.blocks and self.selfish_chain.blocks[-1].is_next_genesis():
            return self.selfish_chain.blocks[-1]
        elif self.honest_chain.blocks and self.honest_chain.blocks[-1].is_next_genesis():
            return self.honest_chain.blocks[-1]

        # Race not resolved - return the furthest block from either chain
        selfish_last = self.selfish_chain.blocks[-1] if self.selfish_chain.blocks else None
        honest_last = self.honest_chain.blocks[-1] if self.honest_chain.blocks else None

        # Return whichever chain is longer, or selfish if tied
        if selfish_last and honest_last:
            return selfish_last if len(self.selfish_chain.blocks) >= len(self.honest_chain.blocks) else honest_last
        return selfish_last or honest_last or self.genesis

    @staticmethod
    def _collect_follow_line_animations(chains: list[ChainBranch]) -> list:
        """Collect FollowLine update animations from all blocks in chains.

        Iterates through all blocks in the provided chains and collects
        :class:`FollowLine` update animations. Used to ensure connecting
        lines follow their parent blocks during transform animations.

        Parameters
        ----------
        chains : list[ChainBranch]
            List of chain objects to collect animations from

        Returns
        -------
        list
            List of :class:`~.UpdateFromFunc` animations for FollowLines

        Notes
        -----
        **Collection Logic**:
        - Iterates through each chain in ``chains``
        - For each block in chain, checks if it has a line
        - Only collects animations from :class:`FollowLine` instances
        - Calls ``block.line.create_update_animation()`` for each FollowLine

        **Why Static**:
        - No instance state required
        - Pure utility function for animation collection
        - Can be called without class instance

        **Typical Usage**:
        Called during animations that move blocks (e.g., vertical shifts,
        race resolution) to ensure connecting lines update correctly.

        Examples
        --------

        .. code-block:: python

            # Collect animations for both chains during tie reveal
            follow_line_anims = self._collect_follow_line_animations(
                [self.honest_chain, self.selfish_chain]
            )

            # Use in play() call with other animations
            self.scene.play(
                *block_shift_animations,
                *follow_line_anims
            )

        See Also
        --------
        :meth:`_reveal_selfish_chain_for_tie` : Uses this during tie reveal
        :meth:`_animate_race_resolution` : Uses this during resolution
        :class:`FollowLine` : Line class that creates update animations
        :meth:`Block.has_line` : Checks if block has a connecting line
        """
        anims = []
        for chain in chains:
            for block in chain.blocks:
                if block.has_line() and isinstance(block.line, FollowLine):
                    anims.append(block.line.create_update_animation())
        return anims

    ####################
    # Private
    # State Management (Narration)
    ####################

    def _capture_state_before_block(self) -> str | None:
        """Capture current state name before block creation.

        Retrieves the current state name from the narration manager before any
        block is added. Used to detect state transitions for narration animations.

        Returns
        -------
        str | None
            Current state name (e.g., "0", "1", "0prime") if narration is enabled,
            None otherwise

        Notes
        -----
        - Returns None immediately if ``self.enable_narration`` is False
        - Accesses ``self.narration.current_state_name`` attribute
        - Called at the start of every block creation method
        - Used by :meth:`_animate_block_and_line` to show state transitions

        Examples
        --------

        .. code-block:: python

            # With narration enabled
            previous_state = self._capture_state_before_block()
            # Returns: "1" (current state)

            # With narration disabled
            previous_state = self._capture_state_before_block()
            # Returns: None

        See Also
        --------
        :meth:`_calculate_current_state` : Calculates new state after block creation
        :meth:`_animate_block_and_line` : Uses captured state for transition animation
        """
        if not self.enable_narration:
            return None

        captured_state = self.narration.current_state_name
        return captured_state

    def _calculate_current_state(self, in_tiebreak: bool = False) -> str:
        """Calculate current state name based on selfish lead.

        Determines the state machine state based on the current selfish lead value.
        Supports infinite states (any positive integer) and handles special cases
        for initial state, tie state, and tiebreak resolution.

        Parameters
        ----------
        in_tiebreak : bool, optional
            Whether currently in tiebreaking mode. If True and selfish is ahead,
            returns "0" instead of the lead value. Default: False

        Returns
        -------
        str
            State name: "0" (initial/honest ahead), "0prime" (tied), or positive
            integer as string (selfish lead)

        Notes
        -----
        **State Calculation Logic**:

        **Case 1: Selfish Lead = 0**
        - If both chains have blocks: Returns ``"0prime"`` (tie state)
        - If no blocks exist: Returns ``"0"`` (initial state)

        **Case 2: Selfish Lead > 0**
        - If ``in_tiebreak=True``: Returns ``"0"`` (race unresolved during tiebreak)
        - Otherwise: Returns ``str(selfish_lead)`` (e.g., "1", "2", "3", ...)

        **Case 3: Selfish Lead < 0** (Honest Ahead)
        - Always returns ``"0"`` (honest has overtaken)

        **Tiebreak Special Case**:
        During tiebreak resolution, even if selfish gains a lead, the state remains
        "0" until the race is fully resolved. This prevents premature state transitions.

        Examples
        --------

        .. code-block:: python

            # Initial state (no blocks)
            state = self._calculate_current_state()
            # Returns: "0"

            # Tie state (both chains have blocks, equal length)
            state = self._calculate_current_state()
            # Returns: "0prime"

            # Selfish ahead by 2
            state = self._calculate_current_state()
            # Returns: "2"

            # During tiebreak, selfish ahead by 1
            state = self._calculate_current_state(in_tiebreak=True)
            # Returns: "0" (not "1")

        See Also
        --------
        :meth:`_get_current_chain_lengths` : Gets chain lengths and lead
        :meth:`_capture_state_before_block` : Captures state before changes
        :meth:`_animate_block_and_line` : Uses calculated state for narration
        """
        _, _, selfish_lead = self._get_current_chain_lengths()

        if selfish_lead == 0:
            # Check if we're in a tie situation (both chains have blocks)
            honest_len, selfish_len, _ = self._get_current_chain_lengths()
            if honest_len > 0 and selfish_len > 0:
                return "0prime"  # Tied state
            return "0"  # Initial state
        elif selfish_lead > 0:
            # SPECIAL CASE: During tiebreaking, even if selfish is ahead, return "0"
            # because the race hasn't been resolved yet
            if in_tiebreak:
                return "0"
                # Return the lead as a string - supports infinite states
            result = str(selfish_lead)
            return result
        else:
            # Honest is ahead, back to state 0
            return "0"

    def _had_selfish_lead_of_exactly_two(self) -> bool:
        """Check if previous selfish lead was exactly 2.

        Determines whether the selfish lead was 2 before the most recent block
        addition. Used to detect when selfish should release their chain (when
        lead drops from 2 to 1).

        Returns
        -------
        bool
            True if ``self.previous_selfish_lead == 2``, False otherwise

        Notes
        -----
        - Checks ``self.previous_selfish_lead`` attribute
        - Updated by :meth:`_store_previous_lead` before each block creation
        - Used by :meth:`_check_if_honest_caught_up` for resolution detection

        **Selfish Mining Strategy Context**:
        When selfish lead drops from 2 to 1, the selfish pool releases their
        private chain to prevent honest miners from catching up completely.

        Examples
        --------

        .. code-block:: python

            # Previous lead was 2, now it's 1
            # (honest just mined a block)
            had_lead_of_two = self._had_selfish_lead_of_exactly_two()
            # Returns: True (triggers resolution)

            # Previous lead was 1, now it's 0
            had_lead_of_two = self._had_selfish_lead_of_exactly_two()
            # Returns: False (no resolution)

        See Also
        --------
        :meth:`_store_previous_lead` : Stores lead before block creation
        :meth:`_check_if_honest_caught_up` : Uses this for resolution detection
        """
        return self.previous_selfish_lead == 2


##########Examples##########

class SelfishMiningAutomaticExample(HUD2DScene):
    def construct(self):
        # Fully automated probabilistic simulation (no narration)
        sm = SelfishMiningSquares(self, alpha=0.40, gamma=0.15)
        for _ in range(20):
            sm.generate_next_block_probabilistic()  # Each block created using probability


class SelfishMiningManualExample(HUD2DScene):
    def construct(self):
        # Manual block-by-block control with narration enabled
        sm = SelfishMiningSquares(self, 0.30, 0.1, enable_narration=True)

        # Add blocks with optional captions
#        sm.advance_selfish_chain("A Block")
        sm.advance_selfish_chain("Selfish miners create a secret chain")
        sm.advance_selfish_chain("this is a short example video")
#        sm.update_caption("Narration without Block")  # Update caption independently
        sm.advance_selfish_chain("that explains Eyal-Sirer")
        sm.advance_honest_chain("Majority is not enough")
        sm.advance_selfish_chain("showing states and transitions")
        sm.advance_honest_chain("while mining a secret chain")
#        sm.advance_honest_chain("Another Block")  # ← This triggers race resolution (selfish wins)
        sm.advance_honest_chain("it shows the strategy")  # ← This triggers race resolution (selfish wins)

        # New race starts from winning block as genesis
        sm.advance_honest_chain("presented in the paper")  # ← First block of new race

        # Automatic tiebreak resolution (uses probability)
        sm.advance_selfish_chain("and uses probability")
        sm.advance_honest_chain("for tie resolution")

        # Continue building - automatic resolution when needed
        sm.advance_selfish_chain("selfish miners always mine in secret")
        sm.advance_selfish_chain("creating an unknown competing chain")
        sm.advance_honest_chain("and displacing honest blocks")

        # Zoom out to show multiple races
        sm.update_caption("earning disproportionate rewards")
        sm.zoom_out_to_show_races()
        self.wait(1)


class SelfishMiningManualTiesExample(HUD2DScene):
    def construct(self):
        # Manual tiebreak control (alpha=0.33, gamma=0.5 gives equal probability to each outcome)
        sm = SelfishMiningSquares(self, 0.33, 0.5, enable_narration=True)
        sm.advance_selfish_chain()

        # Demonstrate all three valid tiebreak options
        sm.advance_honest_chain(tiebreak="honest_on_honest")

        sm.advance_selfish_chain()
        sm.advance_honest_chain(caption="Honest mines on selfish chain",tiebreak="honest_on_selfish")

        sm.advance_selfish_chain()
        sm.advance_honest_chain(tiebreak="selfish_on_selfish")

        # Invalid tiebreak - silently falls back to probabilistic
        sm.advance_selfish_chain()
        # Comment here is to intentionally ignore the warning this generates, remove to see warning in IDE
        sm.advance_honest_chain("Passes invalid tiebreak, result probablistic", "bad tiebreak")  # type: ignore[arg-type]

        # No tiebreak parameter - uses probabilistic
        sm.advance_selfish_chain()
        sm.advance_honest_chain()

        sm.zoom_out_to_show_races()
        self.wait(3)


class SelfishMiningTrackingExample(HUD2DScene):
    def construct(self):
        # Manual block-by-block control with narration enabled
        sm = SelfishMiningSquares(self, 0.30, 0.1, enable_narration=True)

        # First race: Build long selfish chain (5 blocks)
        # Camera scrolls right by 1 block spacing when 5th block is added
        sm.advance_selfish_chain()  # Block 1
        sm.advance_selfish_chain()  # Block 2
        sm.advance_selfish_chain()  # Block 3
        sm.advance_selfish_chain()  # Block 4
        sm.advance_selfish_chain()  # Block 5 - triggers camera scroll

        # Honest chain catches up (4 blocks)
        # No additional camera scroll (max chain length still 5)
        sm.advance_honest_chain()  # Block 1
        sm.advance_honest_chain()  # Block 2
        sm.advance_honest_chain()  # Block 3
        sm.advance_honest_chain()  # Block 4 - race resolves, selfish wins

        # Second race: Build very long selfish chain (10 blocks)
        # Camera scrolls incrementally as chain grows beyond previous max
        sm.advance_selfish_chain()  # Block 1 (from new genesis)
        sm.advance_selfish_chain()  # Block 2
        sm.advance_selfish_chain()  # Block 3
        sm.advance_selfish_chain()  # Block 4
        sm.advance_selfish_chain()  # Block 5
        sm.advance_selfish_chain()  # Block 6 - camera scrolls (new max)
        sm.advance_selfish_chain()  # Block 7 - camera scrolls (new max)
        sm.advance_selfish_chain()  # Block 8 - camera scrolls (new max)
        sm.advance_selfish_chain()  # Block 9 - camera scrolls (new max)
        sm.advance_selfish_chain()  # Block 10 - camera scrolls (new max)

        # Honest chain catches up (9 blocks)
        # No additional camera scroll (max chain length still 10)
        sm.advance_honest_chain()  # Block 1
        sm.advance_honest_chain()  # Block 2
        sm.advance_honest_chain()  # Block 3
        sm.advance_honest_chain()  # Block 4
        sm.advance_honest_chain()  # Block 5
        sm.advance_honest_chain()  # Block 6
        sm.advance_honest_chain()  # Block 7
        sm.advance_honest_chain()  # Block 8
        sm.advance_honest_chain()  # Block 9 - race resolves, selfish wins

        # Zoom out to show both completed races
        # Camera adjusts to fit all blocks in view
        sm.zoom_out_to_show_races()
        self.wait(1)

##########Explaining Selfish Mining##########

# Broken Example, currently all races are automatically resolved according to Selfish Mining Strategy.
# Need to implement more granular controls first
class SelfishMiningExplanation(HUD2DScene):
    def construct(self):
        sm = SelfishMiningSquares(self, 0.33, 0.5, enable_narration=True)

        # === PART 1: Honest Mining Basics ===
        sm.update_caption("In Bitcoin, miners compete to find blocks")

        sm.advance_honest_chain("Honest miners build on the longest chain they see")

        sm.advance_honest_chain("When a new block is found, all miners switch to it")

        sm.advance_honest_chain("This creates a single, growing blockchain")

        sm.update_caption("But what if a miner doesn't play by the rules?")
        self.wait(2)

        # === PART 2: Introducing the Selfish Miner ===
        sm.update_caption("Selfish Mining: A strategic attack on Bitcoin's fairness")

        sm.advance_selfish_chain("A selfish miner finds a block but keeps it SECRET")

        sm.advance_selfish_chain("The honest network doesn't know about the hidden chain")

        sm.advance_honest_chain("Honest miners continue on the public chain")

        sm.update_caption("Now there are TWO competing chains")

        # === PART 3: Building a Lead ===
        sm.advance_selfish_chain("Selfish miner extends their secret chain")

        sm.update_caption("With a 2-block lead, the selfish miner has an advantage")

        sm.advance_honest_chain("When honest miners catch up...")

        sm.update_caption("...selfish miner reveals their longer chain and WINS!")
        self.wait(2)

        # === PART 4: The Tie Scenario ===
        sm.update_caption("New race begins from the winning chain")

        sm.advance_selfish_chain("Selfish miner finds another block")

        sm.advance_honest_chain("Honest miners catch up - now we have a TIE!")

        sm.update_caption("In a tie, network propagation speed matters")
        self.wait(2)

        # === PART 5: Network Connectivity (Gamma) ===
        sm.update_caption("Scenario 1: Honest miners see selfish block first")
        sm.advance_selfish_chain()
        sm.advance_honest_chain(
            tiebreak="honest_on_selfish",
            caption="Probability γ(1-α): Honest miners build on selfish chain"
        )
        self.wait(1)

        sm.update_caption("Scenario 2: Selfish miner wins the race")
        sm.advance_selfish_chain()
        sm.advance_honest_chain(
            tiebreak="selfish_on_selfish",
            caption="Probability α: Selfish miner finds next block first"
        )
        self.wait(1)

        sm.update_caption("Scenario 3: Honest miners build on honest chain")
        sm.advance_selfish_chain()
        sm.advance_honest_chain(
            tiebreak="honest_on_honest",
            caption="Probability (1-γ)(1-α): Network splits, honest chain wins"
        )
        self.wait(1)

        # === PART 6: The Attack's Impact ===
        sm.update_caption("Result: Selfish miner earns MORE than their fair share")

        sm.update_caption("With α=33% hash power, they can earn >33% of rewards")

        sm.update_caption("This breaks Bitcoin's fairness assumption")

        # === PART 7: Show Full History ===
        sm.zoom_out_to_show_races()
        sm.update_caption("Multiple races show the pattern of the attack")
        self.wait(3)

        sm.update_caption("Selfish mining: A threat to blockchain security")
        self.wait(2)


#TODO list of things to be implemented
#   Implement opacity(0.5) for the hidden seflish chain with an animation that changes to full opacity upon reveal .
#   Override automatic resolution so animations can be generated that deviate from selfish mining strategy(help explain why the strategy exists)
#   Add captioning to each part of race resolution (after breaking down into individual public calls, can try advance_animation that always plays the next step in the anim)
#   Add captioning to any public API
#   Limit zoom out by depth from current gen, but collect full race for that block.(if depth too deep, will zoom to the point of invisible blocks)
#   After zoom out to max depth, scroll camera(single animation where time is a func of distance, so scrolling speed remains the same)
#   Make AnimationTimingConfig.SHIFT_TO_NEW_GENESIS_TIME dynamic up to 4 blocks (so horizontal shift speed is the same)

#TODO resolved once migrated to use HUD2DScene (has new NarrationManager integrated in scene)
#   Narration works with Text OR MathTex OR Tex, add a way on creation to set one option, then use that on option only throughout NarrationManager/TextFactory
#   Camera movements can now be used in HUD2DScene, method chaining also works (wrappers restricted to camera panning and zooming, can still perform 3D movements but blanim is 2D)