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
### Next Steps  

#### 1. Cleanup & Refactoring  
- [ ] Remove outdated documentation references to `MovingCameraHUDScene`  
- [ ] Update docstrings to reflect `HUD2DScene` usage  
- [ ] Remove any remaining `ViewportCullingHUDScene` references  
- [ ] Clean up debug prints if any remain  

#### 2. Performance Testing  
- [ ] **Test leaving offscreen blocks in place** instead of removing them  
  - Since we're using `ThreeDScene`, blocks outside viewport may not impact performance significantly  
  - This would eliminate the need to recreate blocks during `zoom_out_to_show_races()`  
  - Measure render time with 200+ blocks all in scene vs current approach  
  - If performance is acceptable, remove block removal logic for simplicity  

#### 3. Implement `zoom_out_to_show_races()`  
- [ ] Replace `self.scene.camera.auto_zoom()` (doesn't exist in `ThreeDCamera`)  
- [ ] Manually calculate bounding box of all blocks  
- [ ] Use `self.scene.move_camera(frame_center=..., zoom=...)` to fit all blocks in view  
- [ ] Test with blocks left in place (see performance testing above)  

#### 4. Documentation  
- [ ] Document `HUD2DScene` pattern for future use  
- [ ] Add examples showing state text vs narration text patterns  
- [ ] Document why `add_fixed_in_frame_mobjects()` must be called before `Create` animation  
- [ ] Add notes about `Transform` vs `Create` for HUD text updates  

#### 5. Code Simplification  
- [ ] Consider extracting HUD text management into reusable helper  
- [ ] Evaluate if `NarrationManager` and state text can share more code  
- [ ] Review if `AnimationManager` narration/state methods can be consolidated
"""
##########End Notes##########

##########Proposed Structure##########

"""
DO NOT USE, FOR REF ONLY AT THIS POINT
Proposed Module Structure  
---------------------------------  

blanim/  
├── core/  
│   ├── hud/  
│   │   ├── __init__.py  
│   │   ├── narration_factory.py      # NarrationTextFactory  
│   │   ├── narration_manager.py      # NarrationManager  
│   │   ├── animation_manager.py      # AnimationManager  
│   │   └── protocols.py              # HUDSceneProtocol  
│   ├── scenes/  
│   │   ├── __init__.py  
│   │   └── hud_2d_scene.py          # HUD2DScene  
│   └── config/  
│       ├── __init__.py  
│       ├── layout.py                 # LayoutConfig (parameterized)  
│       └── timing.py                 # AnimationTimingConfig (parameterized)  
└── blockchain/  
    ├── __init__.py  
    └── selfish_mining.py             # SelfishMiningSquares (uses core)  

Module Dependencies  
-------------------  
Core modules (hud/, scenes/, config/) should be blockchain-agnostic and reusable  
across different Blanim animation projects. The blockchain/ directory contains  
domain-specific implementations that use the core modules.  

Key Design Principles:  
- HUD text management uses primer pattern for fixed-in-frame text  
- AnimationManager provides consistent is_in_scene tracking  
- All configuration (styling, timing) should be parameterizable  
- Scene types must support ThreeDScene.add_fixed_in_frame_mobjects()  
"""


##########END Proposed Structure##########

class Block:
    """A blockchain block visualization composed of Manim mobjects.

    Represents a single block in a blockchain, consisting of a square shape,
    text label, and optional connecting line to a parent block. Blocks can
    form a tree structure through parent-child relationships.

    Animation Conflicts Warning
    ---------------------------
    When animating blocks with FollowLines, be aware that the line uses
    UpdateFromFunc animations and will conflict with transform animations
    (.animate.shift(), .animate.scale(), etc.) if included in the same
    Scene.play() call. Use get_transform_safe_mobjects() for transform
    animations, or manually exclude lines. See FollowLine class documentation
    for complete list of conflicting animations.

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

    Attributes
    ----------
    square : Square
        The visual square representing the block
    label : Text
        The text label displayed on the block
    line : FollowLine or None
        Connection line to parent block, or None for genesis blocks
    children : list[Block]
        List of child blocks connected to this block
    next_genesis : bool
        Flag indicating if this block will become the next genesis block
    parent_block : Block or None
        Reference to the parent block, or None for genesis blocks
    """

    def __init__(self, label_text: str, position: Point3DLike, block_color: str, parent_block: 'Block' = None) -> None:

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
            Animation duration. If None, uses AnimationTimingConfig.FADE_IN_TIME

        Returns
        -------
        Animation
            Transform animation that morphs the current label to the new text
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

        Warning
        -------
        If using transform animations (.animate.shift(), .animate.scale(), etc.),
        use get_transform_safe_mobjects() instead to avoid animation conflicts
        with the FollowLine's UpdateFromFunc animation. Safe to use with
        FadeIn/FadeOut, Create/Uncreate, and style animations.

        Returns
        -------
        list[Mobject]
            List containing square, label, and optionally the connecting line
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
        UpdateFromFunc and would conflict with transform animations like
        .animate.shift(), .animate.scale(), .animate.rotate(), etc.

        Use this method when animating block positions or transformations.
        The line should be animated separately using line.create_update_animation().

        Example
        -------
        # Correct usage for transform animations
        all_mobjects = []
        for block in chain.blocks:
            all_mobjects.extend(block.get_transform_safe_mobjects())

        self.play(
            *[mob.animate.shift(RIGHT) for mob in all_mobjects],
            *[block.line.create_update_animation() for block in chain.blocks if block.has_line()]
        )

        Returns
        -------
        list[Mobject]
            List containing only square and label (excludes line)
        """
        return [self.square, self.label]

    def move_to(self, position):
        """Move block to a new position.

        Updates both the square and label positions. The line position
        is updated separately via its UpdateFromFunc animation.

        Parameters
        ----------
        position : Point3DLike
            The new position for the block's center
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

        Sets the next_genesis flag to True, indicating this block will
        become a genesis block in the next epoch or chain split.
        """
        self.next_genesis = True

    def is_next_genesis(self) -> bool:
        """Check if this block is marked as the next genesis block.

        Returns
        -------
        bool
            True if this block is marked as next genesis, False otherwise
        """
        return self.next_genesis

    def is_genesis(self) -> bool:
        """Check if this block is a genesis block.

        A genesis block is one with no parent (the first block in a chain).

        Returns
        -------
        bool
            True if this block has no parent, False otherwise
        """
        return self.parent_block is None

    def has_line(self) -> bool:
        """Check if this block has a connecting line to a parent.

        Returns
        -------
        bool
            True if a connecting line exists, False otherwise
        """
        return self.line is not None

    def __repr__(self) -> str:
        """String representation for debugging.

        Returns
        -------
        str
            A string showing the block's label, parent, children, and genesis status
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
    """

    def __init__(self, start_mobject, end_mobject):
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
        UpdateFromFunc animation created by create_update_animation()
        is played via Scene.play().
        """
        new_start = self.start_mobject.get_left()
        new_end = self.end_mobject.get_right()
        self.set_stroke(width=self._fixed_stroke_width)
        self.set_points_by_ends(new_start, new_end, buff=self.buff)

    def create_update_animation(self):
        """Create an UpdateFromFunc animation to play alongside other animations.

        The animation duration automatically matches other animations in the same
        play() call.

        Usage:
            # Line updates while block moves
            self.play(
                block.animate.shift(RIGHT),
                line.create_update_animation()
            )

        Returns
        -------
        UpdateFromFunc
            Animation that updates line position each frame
        """
        return UpdateFromFunc(
            self,
            update_function=self._update_position_and_size,
            suspend_mobject_updating=False
        )


class ChainBranch:
    def __init__(self, chain_type: str):
        self.chain_type = chain_type
        self.blocks = []

    def add_block(self, label: str, position: Point3DLike, parent_block: Block):
        """Add a block to this chain. Block creates its own line internally."""
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
        """Get all mobjects including blocks and lines"""
        mobjects = []
        for block in self.blocks:
            mobjects.extend(block.get_mobjects())

        return mobjects


class NarrationTextFactory:
    """Factory for creating HUD text mobjects with primer-based Transform support.

    Text Type Compatibility Notes
    -----------------------------
    The primer pattern works with Text, MathTex, and Tex individually, but mixing
    types (e.g., Text → MathTex) fails due to incompatible submobject structures.

    Tested combinations:
    - Text → Text: ✅ Works (tested)
    - MathTex → MathTex: ✅ Works (tested)
    - Tex → Tex: ✅ Works (tested)
    - Text → MathTex → Tex: ❌ Fails (tested)

    Untested combinations to explore:
    - MathTex ↔ Tex: Unknown (both inherit from SingleStringMathTex, may be compatible)
    - Text with different fonts: Unknown
    - MarkupText: Unknown

    To expand this factory for multiple text types:
    1. Test MathTex ↔ Tex compatibility (both use tex_environment parameter)
    2. If compatible, consider separate primer pools per compatible type group
    3. Document character counting differences (spaces, LaTeX commands, etc.)

    """
    """Factory for creating HUD text mobjects with primer-based Transform support.  

    Blanim Standalone Module Notes  
    -------------------------------  
    This module is designed to be extracted into Blanim's core library for reusable  
    HUD text management across blockchain/DAG animation projects.  

    Current Dependencies to Parameterize:  
    1. **LayoutConfig** - Hardcoded styling constants  
       - STATE_FONT_SIZE, STATE_TEXT_COLOR  
       - CAPTION_FONT_SIZE, CAPTION_TEXT_COLOR  
       - Solution: Pass as constructor parameters with sensible defaults  

    2. **Manim Position Constants** - DOWN, UP from manim.constants  
       - Solution: Accept position parameters (Vector3D or constants)  

    3. **Text Type** - Currently hardcoded to use Text class  
       - Solution: Add text_class parameter to support Text/MathTex/Tex  

    Proposed Standalone Constructor:  
    ```python  
    def __init__(  
        self,  
        state_position=DOWN,  
        caption_position=UP,  
        state_font_size=24,  
        caption_font_size=24,  
        state_color=WHITE,  
        caption_color=WHITE,  
        max_state_chars=20,  
        max_caption_chars=100,  
        text_class=Text  # Allow Text, MathTex, or Tex  
    ):  
    ```  

    Integration Checklist for Blanim:  
    - [ ] Remove LayoutConfig dependency  
    - [ ] Make all styling configurable via constructor  
    - [ ] Add text type selection (Text/MathTex/Tex)  
    - [ ] Document character counting for each text type  
    - [ ] Add validation for max_chars vs actual text length  
    - [ ] Create factory presets for common use cases (state, caption, label)  

    Text Type Compatibility (for future expansion):  
    - Text → Text: ✅ Works  
    - MathTex → MathTex: ✅ Works    
    - Tex → Tex: ✅ Works  
    - MathTex ↔ Tex: ❓ Untested (likely compatible, both inherit from SingleStringMathTex)  
    - Mixed types: ❌ Fails (incompatible submobject structures)  

    See: manim/mobject/text/tex_mobject.py:448-477 for Tex/MathTex relationship  
    """

    def __init__(self):
        self.state_text_position = DOWN
        self.caption_text_position = UP
        self.max_state_chars = 20
        self.max_caption_chars = 100

    @staticmethod
    def create_primer_text(max_chars: int, position) -> Text:
        """Create invisible primer text with maximum character capacity."""
        primer_string = "0" * max_chars
        primer = Text(primer_string, color=BLACK, font_size=1)
        primer.to_edge(position)
        return primer

    def get_state(self, state_name: str) -> Mobject:
        """Get or create state text dynamically based on state name"""
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
        """Get or create transition text (e.g., '1→0'', '2→0')"""
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
        """Get or create caption text"""
        caption = Text(
            caption_text,
            font_size=LayoutConfig.CAPTION_FONT_SIZE,
            color=LayoutConfig.CAPTION_TEXT_COLOR
        )
        caption.to_edge(self.caption_text_position)
        return caption


class AnimationTimingConfig:
    """Centralized animation timing configuration"""

    # Scene timing
    WAIT_TIME = 1.0

    # Animation durations
    FADE_IN_TIME = 1.0
    FADE_OUT_TIME = 1.0
    BLOCK_CREATION_TIME = 1.0
    CHAIN_RESOLUTION_TIME = 2.0
    SHIFT_TO_NEW_GENESIS_TIME = 3.0  # TODO make this dynamic up to 4 blocks(Shorter block race needs less time, block race max +4 to be moved)
    INITIAL_SCENE_WAIT_TIME = 3.0  # pause at the beginning before any animations are added
    VERTICAL_SHIFT_TIME = 2.0
    CHAIN_REVEAL_ANIMATION_TIME = 2.0
    FOLLOW_LINE_UPDATE_TIME = 2.0

    @classmethod
    def set_speed_multiplier(cls, multiplier: float):
        """Scale all timings by a multiplier for faster/slower animations"""
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
        """Calculate tie chain spacing as half the distance between honest and selfish chains"""
        return abs(LayoutConfig.SELFISH_Y_OFFSET - LayoutConfig.HONEST_Y_OFFSET) / 2

    @staticmethod
    def get_tie_positions(genesis_y: float) -> tuple[float, float]:
        """Calculate both honest and selfish tie positions

        Returns:
            tuple[float, float]: (honest_y, selfish_y) positions for tie state
        """
        spacing = LayoutConfig.get_tie_chain_spacing()
        return genesis_y + spacing, genesis_y - spacing


class AnimationManager:
    """Facade for Manim animations with scene membership tracking.

    This class wraps Manim's animation system to automatically track which
    mobjects are currently in the scene via the `is_in_scene` flag. All
    animations in the SelfishMiningSquares system MUST go through this
    manager to maintain consistent visibility tracking.

    The `is_in_scene` flag is set synchronously when animations are created,
    not when they are played. This enables automatic filtering of faded-out
    mobjects in methods like `_collect_follow_line_animations()`.

    Architecture
    ------------
    - **Facade Pattern**: Extends Manim's animation system without modifying it
    - **Synchronous Tracking**: `is_in_scene` flag set at animation creation time
    - **Automatic Filtering**: Faded-out lines excluded from animation collection
    - **Module-level Singleton**: Eliminates parameter passing throughout codebase

    Usage
    -----
    Use the module-level singleton `animations` instead of instantiating directly::

        # Correct usage
        animations.fade_in_and_create_block_body(block.square)

        # Don't do this
        manager = AnimationManager()  # Unnecessary

    Notes
    -----
    All methods are static and operate on mobjects passed as parameters.
    The manager does not maintain state; it only sets the `is_in_scene`
    attribute on mobjects and returns standard Manim animations.

    See Also
    --------
    Block.get_fade_out_animations : Uses AnimationManager for consolidated fade-outs
    SelfishMiningSquares._collect_follow_line_animations : Filters by is_in_scene flag
    """
    """Facade for Manim animations with scene membership tracking.  

    Blanim Standalone Module Notes  
    -------------------------------  
    This module provides consistent is_in_scene tracking for all mobjects.  
    It's a core Blanim component that should be included in the framework.  

    Current Dependencies to Parameterize:  
    1. **AnimationTimingConfig** - Hardcoded timing constants  
       - FADE_IN_TIME, FADE_OUT_TIME, etc.  
       - Solution: Accept timing config as class-level or method parameters  

    2. **Manim Animation Classes** - Create, FadeOut, Transform  
       - Solution: Already using Manim directly (acceptable dependency)  

    Integration Checklist for Blanim:  
    - [ ] Make timing configurable (constructor or class variable)  
    - [ ] Add animation presets for common blockchain patterns  
    - [ ] Document is_in_scene flag usage  
    - [ ] Add validation for mobject types  
    - [ ] Consider adding animation queueing/batching  

    Text Animation Methods:  
    - transform_text(): Uses Transform (preserves fixed-in-frame)  
    - remove_text(): Uses FadeOut (sets is_in_scene=False)  
    - DO NOT use add_text() with primer pattern (removed/deprecated)  

    Block/Line Animation Methods:  
    - fade_in_and_create_block_body/label/line()  
    - fade_out_and_remove_block_body/label/line()  
    - All set is_in_scene flag for filtering  
    """

    @staticmethod
    def fade_in_and_create_block_body(mobject) -> Animation:
        """Create and fade in a block body (square).

        Sets `mobject.is_in_scene = True` before returning the animation.

        Parameters
        ----------
        mobject : Square
            The block's square mobject to animate

        Returns
        -------
        Animation
            Create animation with configured fade-in time
        """
        return Create(mobject, run_time=AnimationTimingConfig.FADE_IN_TIME)

    @staticmethod
    def fade_in_and_create_block_label(mobject) -> Animation:
        """Create and fade in a block label (text).

        Sets `mobject.is_in_scene = True` before returning the animation.

        Parameters
        ----------
        mobject : Text
            The block's label mobject to animate

        Returns
        -------
        Animation
            Create animation with configured fade-in time
        """
        return Create(mobject, run_time=AnimationTimingConfig.FADE_IN_TIME)

    @staticmethod
    def fade_in_and_create_line(mobject) -> Animation:
        """Create and fade in a connection line.

        Sets `mobject.is_in_scene = True` before returning the animation.

        Parameters
        ----------
        mobject : FollowLine
            The line mobject to animate

        Returns
        -------
        Animation
            Create animation with configured fade-in time
        """
        return Create(mobject, run_time=AnimationTimingConfig.FADE_IN_TIME)

    @staticmethod
    def transform_text(old_mobject, new_mobject) -> Animation:
        """Transform one text to another.

        Sets `new_mobject.is_in_scene = True` before returning the animation.

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
        """
        return Transform(old_mobject, new_mobject, run_time=AnimationTimingConfig.FADE_IN_TIME)


animations = AnimationManager()


class NarrationManager:
    """Scene-aware narration factory with automatic HUD fixing and lifecycle tracking.

    This class wraps NarrationTextFactory and automatically:
    1. Marks all created narration text as fixed in the HUD2DScene
    2. Tracks currently displayed state/caption text
    3. Provides methods to update or remove tracked text

    Designed for blockchain/DAG visualization scripts as part of blanim extension.

    Text Type Expansion Notes
    -------------------------
    Current implementation uses Text class exclusively. To support multiple text types:

    1. **Test MathTex/Tex compatibility**: Since both inherit from SingleStringMathTex
       and only differ in tex_environment ("align*" vs "center"), they may be
       interchangeable. Test: primer = MathTex(...) → Transform to Tex(...)

    2. **Separate primer pools**: If mixing types is needed, maintain separate primers:
       - text_primer for Text objects
       - math_primer for MathTex/Tex objects (if compatible)
       - markup_primer for MarkupText (if needed)

    3. **Type detection**: Add logic to detect text type and route to correct primer:
       ```python
       def get_state(self, state: str, text_type: str = "text"):
           if text_type == "math":
               return self._get_math_state(state)
           return self._get_text_state(state)
       ```

    4. **Character capacity per type**: Different text types may count characters
       differently (LaTeX commands, markup tags, etc.). Document max_chars for each.

    """
    """Scene-aware narration factory with automatic HUD fixing and lifecycle tracking.  

    This class wraps NarrationTextFactory and automatically:  
    1. Marks all created narration text as fixed in the HUD2DScene  
    2. Tracks currently displayed state/caption text  
    3. Provides methods to update or remove tracked text  

    Designed for blockchain/DAG visualization scripts as part of Blanim extension.  

    Blanim Standalone Module Notes  
    -------------------------------  
    This module manages the primer pattern for HUD text in ThreeDScene-based animations.  
    It's designed to be extracted into Blanim's core library.  

    Current Dependencies to Abstract:  
    1. **HUD2DScene** - Specific scene type requirement  
       - Needs: scene.camera.fixed_in_frame_mobjects (Set[Mobject])  
       - Needs: scene.add_fixed_in_frame_mobjects(*mobjects) method  
       - Solution: Create HUDSceneProtocol interface  

    2. **NarrationTextFactory** - Tightly coupled factory  
       - Solution: Accept factory as dependency injection (already done)  

    3. **Scene Camera API** - Direct access to camera internals  
       - Currently: self.scene.camera.fixed_in_frame_mobjects.add(submob)  
       - Solution: Use scene.add_fixed_in_frame_mobjects() instead  

    Proposed HUDSceneProtocol:  
    ```python  
    from typing import Protocol, Set  
    from manim import Mobject, ThreeDCamera  

    class HUDSceneProtocol(Protocol):  
        camera: ThreeDCamera  # Must have fixed_in_frame_mobjects  

        def add_fixed_in_frame_mobjects(self, *mobjects: Mobject) -> None:  
            '''Register mobjects to stay fixed in camera frame'''  
            ...  
    ```  

    Integration Checklist for Blanim:  
    - [ ] Create HUDSceneProtocol for type hints  
    - [ ] Replace direct camera.fixed_in_frame_mobjects access with scene method  
    - [ ] Make primer creation configurable (max_chars, text type)  
    - [ ] Add primer visibility toggle (for debugging)  
    - [ ] Add methods to reset/clear primers  
    - [ ] Document primer lifecycle and Transform limitations  
    - [ ] Add error handling for character overflow  

    External Dependencies (must be provided by Blanim):  
    1. **AnimationManager** - For transform_text() method  
       - Used in: All calling code (_animate_block_and_line, etc.)  
       - Solution: Document as required Blanim component  

    2. **AnimationTimingConfig** - For animation timing  
       - Used by: AnimationManager  
       - Solution: Make configurable or use Blanim defaults  

    3. **HUD2DScene or ThreeDScene** - Scene type  
       - Required: ThreeDScene with fixed_in_frame_mobjects support  
       - Solution: Document as requirement, provide HUD2DScene in Blanim  

    Primer Pattern Implementation Details:  
    - Primers are created once in __init__() with max character capacity  
    - Primers start invisible (BLACK color, font_size=1)  
    - First Transform makes primer visible  
    - All subsequent Transforms reuse same primer mobject  
    - Character capacity is fixed at initialization  
    - Exceeding capacity causes characters to detach from HUD  

    Character Capacity Guidelines:  
    - State text: "State 0prime" = 12 chars → use max_state_chars=20  
    - Transitions: "0prime → 0prime" = ~15 chars → use max_state_chars=20  
    - Captions: Measure longest caption + 20% buffer  
    - Spaces count as characters in Text objects  
    - LaTeX commands may count differently in MathTex/Tex  

    Known Limitations:  
    - Cannot mix text types (Text → MathTex fails)  
    - Character count must be pre-determined  
    - Primer mobject must never be removed from scene  
    - Transform (not ReplacementTransform) must be used  

    See: manim/animation/transform.py:197-209 for Transform behavior  
    See: manim/camera/three_d_camera.py:416-430 for fixed_in_frame_mobjects  
    """
    """
    ---PERFORMANCE CONSIDERATIONS---
    Tested after clearing all text and MathTex files, cacheing disabled
    Text - Fast
    MathTex - Mixed Text and MathTex during testing, need to properly test.
    LaTex - Untested
    """

    def __init__(self, scene: HUD2DScene, narration_factory: NarrationTextFactory):
        """Initialize narration manager with scene and text factory.

        Parameters
        ----------
        scene : HUD2DScene
            The scene instance with HUD support
        narration_factory : NarrationTextFactory
            Factory for creating narration text mobjects
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
        """Create state text for Transform animation."""
        text = self.factory.get_state(state)
        text.move_to(self.current_state_text.get_center())
        # No registration needed - primer already registered
        self.current_state_name = state
        return text

    def get_transition(self, from_state: str, to_state: str):
        """Create transition text for Transform animation."""
        text = self.factory.get_transition(from_state, to_state)
        text.move_to(self.current_state_text.get_center())
        # No registration needed - primer already registered
        return text

    def get_narration(self, narration: str):
        """Create narration text for Transform animation."""
        text = self.factory.get_caption(narration)
        text.move_to(self.current_caption_text.get_center())
        # No registration needed - primer already registered
        return text

    def get_empty_narration(self):
        """Create invisible placeholder text to clear narration."""
        text = self.factory.get_caption(".....")
        text.set_color(BLACK)  # Invisible against black background
        text.move_to(self.current_caption_text.get_center())
        return text


# TiebreakDecision = Literal["honest_on_honest", "honest_on_selfish", "selfish_on_selfish"]
if TYPE_CHECKING:
    TiebreakDecision: TypeAlias = Literal["honest_on_honest", "honest_on_selfish", "selfish_on_selfish"]


class SelfishMiningSquares:
    # TODO - Low Priority - might be able to generate animations faster(5-10%) if using a 2d scene, will require
    #   refactoring AND getting HUD to work(might be able to get an old version to work, if persisting HUD
    #   variables(with transform) and priming(similar to how it is done here), this was functional, but after
    #   learning how to accomplish this with extending ThreeDScene, might be able to apply this to
    #   MovingCamera(extended for a HUD))
    def __init__(self, scene: HUD2DScene, alpha=0.3, gamma=0.5, enable_narration=False):
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
            animations.fade_in_and_create_block_body(self.genesis.square),
            animations.fade_in_and_create_block_label(self.genesis.label)
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
    # Probabilistic Block Generation
    # Public API
    ####################

    def generate_next_block_probabilistic(self):
        """Generate next block based on alpha and gamma probabilities"""
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
    # Probabilistic Decision Helpers
    # Private
    ####################

    def _get_race_state(self) -> tuple[int, int, int, bool]:
        """Get current race state from chain lengths"""
        honest_len, selfish_len, selfish_lead = self._get_current_chain_lengths()
        is_tied = (selfish_lead == 0 and honest_len > 0)
        return honest_len, selfish_len, selfish_lead, is_tied

    def _decide_next_block_in_tie(self) -> "TiebreakDecision":
        """Decide which chain gets the next block during a tie.

        Returns "honest_on_honest", "honest_on_selfish", or "selfish_on_selfish"
        based on manual override or probabilistic distribution using alpha (adversarial hash power)
        and gamma (network connectivity).

        Probability Distribution (from selfish mining paper state 0'):
        - P(selfish_on_selfish) = α
          (selfish pool mines next block with probability equal to their hash power)

        - P(honest_on_selfish) = γ(1-α)
          (honest miners build on selfish chain: honest % × connectivity advantage)

        - P(honest_on_honest) = (1-γ)(1-α)
          (honest miners build on honest chain: honest % × (1 - connectivity))

        Where:
        - α = selfish pool's hash power (adversarial percentage)
        - γ = network connectivity (proportion of honest miners who see selfish chain first)
        - (1-α) = honest miners' hash power

        Total probability: α + γ(1-α) + (1-γ)(1-α) = 1
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
        """Decide which type of block to create during normal (non-tie) state

        Returns:
            str: Either "selfish" or "honest"
        """
        return "selfish" if random.random() < self.alpha else "honest"

    ####################
    # Advance Race / Block Creation
    # Public API
    ####################

    def advance_selfish_chain(self, caption: str | None = None, tiebreak: "TiebreakDecision | None" = None) -> None:
        """Create next selfish block with animated fade-in

        Parameters
        ----------
        caption : str | None
            Optional caption text to display
        tiebreak : Literal["honest_on_honest", "honest_on_selfish", "selfish_on_selfish"] | None
            Manual tiebreak override. Invalid values are silently ignored.
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
        """Create next honest block with animated fade-in

        Parameters
        ----------
        caption : str | None
            Optional caption text to display
        tiebreak : Literal["honest_on_honest", "honest_on_selfish", "selfish_on_selfish"] | None
            Manual tiebreak override. Invalid values are silently ignored.
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

    def _advance_honest_on_selfish_chain(self, caption: str = None) -> None:
        """Create honest block on selfish chain (honest miner builds on selfish parent)"""

        self._store_previous_lead()

        previous_state = self._capture_state_before_block()

        self.honest_blocks_created += 1

        label = f"H{self.honest_blocks_created}"

        parent = self._get_parent_block("selfish")

        position = self._calculate_block_position(parent, "selfish")

        block, line = self.selfish_chain.add_block(label, position, parent_block=parent)

        self._animate_block_and_line(block, line, caption, previous_state)

        self._check_if_race_continues()

    def update_caption(self, caption_text: str) -> None:
        """Update caption text without advancing any chain.

        This method transforms the caption text and waits for the same duration
        as a normal block addition (including state transitions and waits).

        Parameters
        ----------
        caption_text : str
            The text to display in the caption/narration space. Pass empty string
            or None to clear the caption.
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
    # Block Race Tracking
    # Private
    ####################

    def _get_current_chain_lengths(self) -> tuple[int, int, int]:
        """Get current chain lengths directly from the chain objects"""
        honest_len = len(self.honest_chain.blocks)
        selfish_len = len(self.selfish_chain.blocks)
        selfish_lead = selfish_len - honest_len
        return honest_len, selfish_len, selfish_lead

    ####################
    # Helper Methods
    # Private
    ####################

    def _store_previous_lead(self) -> None:
        """Store the previous selfish lead before making changes"""
        _, _, self.previous_selfish_lead = self._get_current_chain_lengths()

    def _get_parent_block(self, chain_type: str) -> Block:
        """Get parent block for next block in chain"""
        chain = self.selfish_chain if chain_type == "selfish" else self.honest_chain

        if not chain.blocks:
            return self.genesis
        else:
            return chain.blocks[-1]

    def _calculate_block_position(self, parent: Block, chain_type: str) -> Point3DLike:
        """Calculate position for new block based on parent and chain type"""
        parent_pos = parent.get_center()
        x_position = float(parent_pos[0]) + LayoutConfig.BLOCK_HORIZONTAL_SPACING

        if parent == self.genesis:
            y_position = LayoutConfig.SELFISH_Y_OFFSET if chain_type == "selfish" else LayoutConfig.HONEST_Y_OFFSET
        else:
            y_position = float(parent_pos[1])

        return x_position, y_position, 0

    def _animate_block_and_line(self, block: Block, line: Line | FollowLine, caption: str = None,
                                previous_state: str = None) -> None:
        """Animate block and line creation with primer-based Transform for HUD text.

        This method now uses Transform instead of ReplacementTransform for state/caption text,
        leveraging the primer pattern to avoid re-registering fixed-in-frame mobjects.
        """

        ########## Block Anims ##########
        anims = [
            animations.fade_in_and_create_block_body(block.square),
            animations.fade_in_and_create_block_label(block.label),
        ]

        ########## Line Anims ##########
        if line:
            anims.append(animations.fade_in_and_create_line(line))

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
        """Shift camera right if either chain exceeds previous maximum length."""
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

    @staticmethod
    def _collect_follow_line_animations(chains: list[ChainBranch]) -> list:
        """Collect FollowLine update animations from all blocks in chains"""
        anims = []
        for chain in chains:
            for block in chain.blocks:
                if block.has_line() and isinstance(block.line, FollowLine):
                    anims.append(block.line.create_update_animation())
        return anims

    def _get_winning_and_losing_chains(self, winner: str) -> tuple[ChainBranch, ChainBranch]:
        """Get winning and losing chains based on winner"""
        if winner == "honest":
            return self.honest_chain, self.selfish_chain
        else:
            return self.selfish_chain, self.honest_chain

    def _get_winning_block(self, winner: str) -> Block | None:
        """Get the winning block based on winner"""
        if winner == "honest":
            return self.honest_chain.blocks[-1] if self.honest_chain.blocks else None
        else:
            return self.selfish_chain.blocks[-1] if self.selfish_chain.blocks else None

    ####################
    # Race Resolution Detection
    # Private
    ####################

    def _check_if_race_continues(self) -> None:
        """Evaluate race conditions and trigger resolution if needed."""

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
        if selfish_lead == -1:
            self._trigger_resolution("honest")
            return True
        return False

    def _check_if_tied(self, selfish_lead: int, honest_blocks: int) -> bool:
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
        if selfish_lead == 1 and self._had_selfish_lead_of_exactly_two():
            self._trigger_resolution("selfish")
            return True
        return False

    ####################
    # Race Resolution Execution
    # Private
    ####################

    def _trigger_resolution(self, winner: str):
        """Trigger resolution and update genesis reference"""

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
        """Animate the resolution of a blockchain race."""
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

        # Step 3: Update label to "Gen"
        state_animations = [winning_block.change_label_to("Gen")]

        if self.enable_narration and self.narration.current_state_text:
            final_state = self.narration.get_state("0")
            state_animations.append(animations.transform_text(self.narration.current_state_text, final_state))

        self.scene.play(*state_animations)
        self.scene.wait(AnimationTimingConfig.WAIT_TIME)

    def _finalize_race_and_start_next(self):
        """Record result and reset for next race"""
        # Reset counters
        self.honest_blocks_created = 0
        self.selfish_blocks_created = 0
        self.previous_selfish_lead = 0

    ####################
    # Tie Handling
    # Private
    ####################

    def _reveal_selfish_chain_for_tie(self):
        """Reveal selfish chain by moving both chains to equal y-positions from genesis"""
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
    # ZoomOut on Chain
    # Public
    ####################

    # TODO this uses hardcoded vars, this should be in config
    def zoom_out_to_show_races(self, max_races: int = 10, animation_time: float = 3.0, margin: float = 1.0):
        """Zoom camera to show multiple races by calculating bounding box manually"""
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

    def _collect_blocks_for_zoom_out(self, max_races: int) -> list[Block]:
        """Collect blocks by traversing backward from current block, then forward BFS.

        This ensures the current race is always included and prevents partial races
        from being displayed.

        Parameters
        ----------
        max_races : int
            Maximum number of complete races to display

        Returns
        -------
        list[Block]
            List of all blocks to include in zoom-out animation
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
        otherwise returns the furthest block from either chain.

        Returns
        -------
        Block
            The most recent block in the blockchain
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

    ####################
    # State Management
    # Private
    ####################

    def _capture_state_before_block(self) -> str | None:
        """Capture current state before adding a block (for narration)"""
        if not self.enable_narration:
            return None

        captured_state = self.narration.current_state_name
        return captured_state

    def _calculate_current_state(self, in_tiebreak: bool = False) -> str:
        """Calculate current state name based on selfish lead

        Args:
            in_tiebreak: Whether we're currently in tiebreaking mode

        Returns:
            State name as string: "0", "0prime", "1", "2", etc.
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
        """Check if previous selfish lead was 2"""
        return self.previous_selfish_lead == 2

    def _transition_to_next_race(self, winning_block: Block):
        """Update genesis to point to the winning block and prepare for next race"""
        self.genesis = winning_block

        # Clear the blockchain lists for next race
        self.selfish_chain.blocks.clear()
        self.honest_chain.blocks.clear()

        # Reset camera tracking for new race
        self._previous_max_chain_len = 4  # Reset to threshold


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
        sm.advance_selfish_chain("A Block")
        sm.advance_selfish_chain()
        sm.update_caption("Narration without Block")  # Update caption independently
        sm.advance_selfish_chain()
        sm.advance_honest_chain()
        sm.advance_selfish_chain()
        sm.advance_honest_chain()
        sm.advance_honest_chain("Another Block")  # ← This triggers race resolution (selfish wins)

        # New race starts from winning block as genesis
        sm.advance_honest_chain()  # ← First block of new race

        # Automatic tiebreak resolution (uses probability)
        sm.advance_selfish_chain()
        sm.advance_honest_chain()

        # Continue building - automatic resolution when needed
        sm.advance_selfish_chain()
        sm.advance_selfish_chain()
        sm.advance_honest_chain()

        # Zoom out to show multiple races
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
        sm.advance_honest_chain(tiebreak="honest_on_selfish")

        sm.advance_selfish_chain()
        sm.advance_honest_chain(tiebreak="selfish_on_selfish")

        # Invalid tiebreak - silently falls back to probabilistic
        sm.advance_selfish_chain()
        sm.advance_honest_chain(tiebreak="bad tiebreak")

        # No tiebreak parameter - uses probabilistic
        sm.advance_selfish_chain()
        sm.advance_honest_chain()

        sm.zoom_out_to_show_races()
        self.wait(3)


# TODO need to limit zoom out by depth from current gen block, but collect the full race that depth is part of
#   (if depth too far, will zoom out to the point where blocks are not visible)
# TODO low priority, after zoom out to max depth, scroll camera(single animation where animation time is function
#   of how far camera scrolls, so scrolling speed is always same)
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