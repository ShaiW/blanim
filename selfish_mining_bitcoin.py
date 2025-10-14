from manim.typing import Point3DLike
from common import *
import random

##########WARNINGS##########
# README: !!!Lines are stored in block objects BUT do not reference the block, lines use the square(visual block) for end points.
# README: !!!Do NOT cache any Mobject that gets removed with ReplacementTransform (e.g. state/transition/caption text), create new Mobjects instead.

##########NOTES##########
"""
THIS CURRENTLY WORKS AND CREATES AN ANIMATION VERY FAST.  Can replace selfish_mining_bitcoin.py

NEXT STEPS FOR Refactoring  

Concise MovingCamera Summary (Updated with TODO List)
Problem

Current zoom_out_to_show_races() has snap-back issues due to .animate syntax conflicting with UpdateFromFunc line animations.
Solution: MovingCamera Approach

Core Changes:

    Scene inheritance: Change from Scene to MovingCameraScene
    Replace block movement with camera zoom: Instead of moving/scaling blocks, animate self.camera.frame to zoom out
    Fixed UI elements: Use add_fixed_in_frame_mobjects() for narration/state text

Implementation:

# In zoom_out_to_show_races():  
# Calculate bounding box of all_blocks  
# Fade in previously hidden blocks/lines  
# Animate camera frame to fit bounding box  
self.scene.play(  
    self.scene.camera.frame.animate.move_to(center).set(width=width, height=height),  
    *fade_in_anims,  
    run_time=animation_time  
)

Benefits:

    Eliminates animation conflicts
    Simpler logic (no position calculations)
    Built-in fixed UI support

Trade-offs:

    Requires scene class refactoring
    Faded-out mobjects remain in scene (minimal performance impact)

TODO List for Refactoring

Required Changes:

    Scene Class Inheritance
        Change all scene classes from Scene to MovingCameraScene
        Update SelfishMiningSquares.__init__() to accept MovingCameraScene instance
        Verify all scene method calls still work with new base class
    Zoom-Out Method Refactor
        Replace zoom_out_to_show_races() block movement logic with camera frame animation
        Remove position/scale calculations for blocks (Steps 2-7)
        Keep block collection logic (_collect_blocks_for_zoom_out(), _find_most_recent_block())
        Replace block .animate calls with camera frame .animate
        Keep line fade-in logic using AnimationManager
    Fixed UI Elements
        Add self.scene.add_fixed_in_frame_mobjects() calls for:
            self.current_state_text
            self.current_caption_text
            Any narration text created by NarrationTextFactory
        Ensure fixed mobjects maintain position/size during camera zoom
    Race Resolution Animations
        Review _animate_race_resolution() for camera compatibility
        Decide: Keep block movement animations OR switch to camera panning
        If keeping block movement: Ensure compatibility with MovingCameraScene
        Test fade-out animations still work correctly
    Performance Considerations
        Profile render times with faded-out mobjects remaining in scene
        If performance degrades: Implement remove() for faded mobjects
        Consider using remove_fixed_in_frame_mobjects() for cleanup
    Testing Checklist
        All scene examples render without errors
        Narration/state text stays fixed during zoom
        Blocks fade in (not move) during zoom-out
        Camera frame animates to fit all blocks
        Race resolution animations still work correctly
        No snap-back behavior

Separate Fix (Independent of MovingCamera)

Genesis Line Fade-Out Issue:
In _animate_race_resolution(), add:

# Fade out winning block's line  
if winning_block.has_line():  
    fade_out_animations.append(animations.fade_out_and_remove_line(winning_block.line))

Recommendation: The MovingCamera approach is cleaner and aligns with Manim Community's official patterns. The refactoring effort is primarily changing the base class and replacing block movement with camera movement, which is less complex than debugging the current animation conflicts.  

END STEPS FOR Refactoring

Optional Optimization (If Needed)

If you want to reduce the slight slowdown, consider using VGroup only for the shift animations:

# In _animate_race_resolution(), replace lines 656-660 with:  
winning_group = VGroup(*winning_chain.get_all_mobjects())  
losing_group = VGroup(*losing_chain.get_all_mobjects())  

self.scene.play(  
    winning_group.animate.shift(UP * vertical_shift),  
    losing_group.animate.shift(UP * vertical_shift),  
    *follow_line_animations,  
    run_time=AnimationTimingConfig.VERTICAL_SHIFT_TIME  
)

This reduces 60+ animations to 2, but your current code is already performant enough for most use cases. 
"""
##########End Notes##########

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

        # Track if part of scene for animation factory
        self.square.is_in_scene = False
        self.label.is_in_scene = False

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

# TODO worked before adding
    def get_fade_out_animations(self, include_line=True):
        """Get fade out animations for all block components."""
        fade_animations = [
            animations.fade_out_and_remove_block_body(self.square),
            animations.fade_out_and_remove_block_label(self.label)
        ]
        if include_line and self.has_line():
            fade_animations.append(animations.fade_out_and_remove_line(self.line))
        return fade_animations

# TODO worked before adding
    def update_label(self, new_text: str) -> Text:
        """Update the block's label text and return the new label mobject."""
        new_label = Text(
            new_text,
            font_size=LayoutConfig.LABEL_FONT_SIZE,
            color=LayoutConfig.LABEL_COLOR
        )
        new_label.move_to(self.square.get_center())
        new_label.is_in_scene = False
        self.label = new_label
        self._label_text = new_text
        return new_label

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

        # Track if part of scene for animation factory
        self.is_in_scene = False

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
        self.lines = []

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
        if line:
            self.lines.append(line)

        return block, line

    def get_all_mobjects(self) -> list:
        """Get all mobjects including blocks and lines"""
        mobjects = []
        for block in self.blocks:
            mobjects.extend(block.get_mobjects())  # This already includes block.line
        # Don't add self.lines separately - they're already included above
        return mobjects

class NarrationTextFactory:
    def __init__(self):
        self.state_text_position = DOWN
        self.caption_text_position = UP

    def get_state(self, state_name: str) -> Mobject:
        """Get or create state text dynamically based on state name"""
        # Always create a new instance instead of caching
        text_map = {
            "0prime": "State 0'"
        }
        text = text_map.get(state_name, f"State {state_name}")

        state = MathTex(
            rf"\text{{{text}}}",
            color=LayoutConfig.STATE_TEXT_COLOR
        )
        state.to_edge(self.state_text_position)

        return state

    def get_transition(self, from_state: str, to_state: str) -> Mobject:
        """Get or create transition text (e.g., '1→0'', '2→0')"""
        # Always create a new instance instead of caching
        state_text_map = {
            "0prime": "0'"
        }
        from_text = state_text_map.get(from_state, from_state)
        to_text = state_text_map.get(to_state, to_state)

        transition = MathTex(
            rf"\text{{{from_text}}} \rightarrow \text{{{to_text}}}",
            color=LayoutConfig.STATE_TEXT_COLOR
        )
        transition.to_edge(self.state_text_position)

        return transition

    def get_caption(self, caption_text: str) -> Mobject:
        """Get or create caption text"""
        # Always create a new instance
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

# TODO doublecheck this AND make positioning dynamic so you can fit target number of blocks to screen based on expected block race length
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
        mobject.is_in_scene = True
        return Create(mobject, run_time=AnimationTimingConfig.FADE_IN_TIME)

    @staticmethod
    def fade_out_and_remove_block_body(mobject) -> Animation:
        """Fade out and remove a block body (square) from scene.

        Sets `mobject.is_in_scene = False` before returning the animation.

        Parameters
        ----------
        mobject : Square
            The block's square mobject to animate

        Returns
        -------
        Animation
            FadeOut animation with configured fade-out time
        """
        mobject.is_in_scene = False
        return FadeOut(mobject, run_time=AnimationTimingConfig.FADE_OUT_TIME)

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
        mobject.is_in_scene = True
        return Create(mobject, run_time=AnimationTimingConfig.FADE_IN_TIME)

    @staticmethod
    def fade_out_and_remove_block_label(mobject) -> Animation:
        """Fade out and remove a block label (text) from scene.

        Sets `mobject.is_in_scene = False` before returning the animation.

        Parameters
        ----------
        mobject : Text
            The block's label mobject to animate

        Returns
        -------
        Animation
            FadeOut animation with configured fade-out time
        """
        mobject.is_in_scene = False
        return FadeOut(mobject, run_time=AnimationTimingConfig.FADE_OUT_TIME)

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
        mobject.is_in_scene = True
        return Create(mobject, run_time=AnimationTimingConfig.FADE_IN_TIME)

    @staticmethod
    def fade_out_and_remove_line(mobject) -> Animation:
        """Fade out and remove a connection line from scene.

        Sets `mobject.is_in_scene = False` before returning the animation.
        This enables automatic filtering in `_collect_follow_line_animations()`.

        Parameters
        ----------
        mobject : FollowLine
            The line mobject to animate

        Returns
        -------
        Animation
            FadeOut animation with configured fade-out time
        """
        mobject.is_in_scene = False
        return FadeOut(mobject, run_time=AnimationTimingConfig.FADE_OUT_TIME)

    @staticmethod
    def add_state_text(mobject) -> Animation:
        """Create and fade in state text (narration).

        Sets `mobject.is_in_scene = True` before returning the animation.

        Parameters
        ----------
        mobject : VMobject or OpenGLVMobject
            The state text mobject to animate

        Returns
        -------
        Animation
            Create animation with configured fade-in time
        """
        mobject.is_in_scene = True
        return Create(mobject, run_time=AnimationTimingConfig.FADE_IN_TIME)

    @staticmethod
    def transform_state_text(old_mobject, new_mobject) -> Animation:
        """Transform one state text to another.

        Does not modify `is_in_scene` flags as the transformation
        handles scene membership automatically.

        Parameters
        ----------
        old_mobject : Mobject
            The current state text to transform from
        new_mobject : Mobject
            The new state text to transform to

        Returns
        -------
        Animation
            ReplacementTransform animation with configured fade-in time
        """
        return ReplacementTransform(old_mobject, new_mobject, run_time=AnimationTimingConfig.FADE_IN_TIME)

    @staticmethod
    def remove_state_text(mobject) -> Animation:
        """Fade out and remove state text from scene.

        Sets `mobject.is_in_scene = False` before returning the animation.

        Parameters
        ----------
        mobject : Mobject
            The state text mobject to animate

        Returns
        -------
        Animation
            FadeOut animation with configured fade-out time
        """
        mobject.is_in_scene = False
        return FadeOut(mobject, run_time=AnimationTimingConfig.FADE_OUT_TIME)

animations = AnimationManager()

class SelfishMiningSquares:
    def __init__(self, scene, alpha=0.3, gamma=0.5, enable_narration=False):
        # Scene to bypass manim and use play in SelfishMiningSquares
        self.scene = scene

        # Adversary % and Connectedness
        self.alpha = alpha
        self.gamma = gamma

        # Narration control
        self.enable_narration = enable_narration

        self.current_race_number = 0
        self.race_history = []  # List of dicts with race results

        self.genesis_position = (LayoutConfig.GENESIS_X, LayoutConfig.GENESIS_Y, 0)

        self.selfish_miner_block_opacity = LayoutConfig.SELFISH_BLOCK_OPACITY

        self.selfish_blocks_created = 0
        self.honest_blocks_created = 0
        self.previous_selfish_lead = 0

        # Initialize managers
        self.narration_factory = NarrationTextFactory()

        self.current_state_text = None
        self.current_caption_text = None
        self.current_state_name = "0"

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
            initial_state = self.narration_factory.get_state("0")
            genesis_animations.append(animations.add_state_text(initial_state))
            self.current_state_text = initial_state

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

    # TODO duplicate logic within here and _get_current_chain_lengths
    def _get_race_state(self) -> tuple[int, int, int, bool]:
        """Get current race state from chain lengths"""
        honest_len = len(self.honest_chain.blocks)
        selfish_len = len(self.selfish_chain.blocks)
        selfish_lead = selfish_len - honest_len
        is_tied = (selfish_lead == 0 and honest_len > 0)
        return honest_len, selfish_len, selfish_lead, is_tied

    def _decide_next_block_in_tie(self) -> str:
        """Decide which type of block to create during tie state

        Returns:
            str: One of "selfish_on_selfish", "honest_on_honest", "honest_on_selfish"
        """
        rand = random.random()
        h = 1 - self.alpha

        if rand < self.alpha:
            return "selfish_on_selfish"
        elif rand < self.alpha + h * (1 - self.gamma):
            return "honest_on_honest"
        else:
            return "honest_on_selfish"

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

    # TODO add optional manual tiebreaking, possible when creating an instance of SMS
    def advance_selfish_chain(self, caption: str = None) -> None:
        """Create next selfish block with animated fade-in"""

        self._store_previous_lead()

        previous_state = self._capture_state_before_block()

        self.selfish_blocks_created += 1

        label = f"S{self.selfish_blocks_created}"

        parent = self._get_parent_block("selfish")

        position = self._calculate_block_position(parent, "selfish")

        block, line = self.selfish_chain.add_block(label, position, parent_block=parent)

        self._animate_block_and_line(block, line, caption, previous_state)

        self._check_if_race_continues()

    def advance_honest_chain(self, caption: str = None) -> None:
        """Create next honest block with animated fade-in"""

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

    # TODO does this store the actual branches(here or in a related process) A. NO, but blocks contain info to recreate the race anyways
    def _record_race_result(self, winner: str):
        """Record race result in simple dict format"""
        honest_len, selfish_len, _ = self._get_current_chain_lengths()
        self.race_history.append({
            'race_number': self.current_race_number,
            'winner': winner,
            'honest_blocks': honest_len,
            'selfish_blocks': selfish_len
        })
        self.current_race_number += 1

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

    # TODO Document and clean this up
    def _animate_block_and_line(self, block: Block, line: Line | FollowLine, caption: str = None,
                                previous_state: str = None) -> None:
        """Animate block and line creation"""

        ########## Block Anims ##########
        anims = [
            animations.fade_in_and_create_block_body(block.square),
            animations.fade_in_and_create_block_label(block.label),
        ]

        ########## Line Anims ##########
        if line:
            anims.append(animations.fade_in_and_create_line(line))

        ########## Caption Anims ##########     #TODO remove old caption if no new caption provided
        if caption:
            caption_mobject = self.narration_factory.get_caption(caption)

            if self.current_caption_text:
                anims.append(animations.transform_state_text(
                    self.current_caption_text, caption_mobject))
            else:
                anims.append(animations.add_state_text(caption_mobject))

            self.current_caption_text = caption_mobject

        ########## State Anims ##########
        transition_text_ref = None
        current_state = None  # Store the calculated state to reuse later
        is_special_case_2_to_0 = False  # Track if this is the 2→0 special case (honest catches up from -2)
        is_special_case_0_to_0 = False  # Track if this is the 0→0 special case (honest wins, triggers race resolution)
        is_special_case_to_0prime = False  # Track if this is a transition to 0' (tie reveal situation)
        is_special_case_from_0prime = False  # Track if transitioning from 0prime during tiebreak resolution

        # Always calculate current state when narration is enabled
        if self.enable_narration:
            # Check if we're in tiebreaking mode by seeing if previous state was 0prime
            in_tiebreak = (previous_state == "0prime")
            current_state = self._calculate_current_state(in_tiebreak=in_tiebreak)

            # SPECIAL CASE: Check if this triggers the "honest catches up from -2 to -1" resolution
            # In this case, we want to show transition to "0" instead of "1"
            if previous_state == "2" and current_state == "1":
                current_state = "0"  # Override to show 2→0 transition
                is_special_case_2_to_0 = True  # Mark this as special case

            # SPECIAL CASE: Check if this is a 0→0 transition (honest wins, triggers race resolution)
            # In this case, we want State 0 to fade in with genesis label during race resolution
            if previous_state == "0" and current_state == "0":
                is_special_case_0_to_0 = True  # Mark this as special case

            # SPECIAL CASE: Check if this is a transition to 0' (tie reveal situation)
            # In this case, we want State 0' to fade in during the tie movement shift
            if current_state == "0prime":
                is_special_case_to_0prime = True  # Mark this as special case

            # SPECIAL CASE: Check if transitioning from 0prime during tiebreak resolution
            # In this case, we want the state transition to happen with genesis label fade-in
            if previous_state == "0prime" and current_state in ["0", "1"]:
                is_special_case_from_0prime = True  # Mark this as special case

        # Only show transition if we have a previous state
        if self.enable_narration and self.current_state_text and previous_state is not None and current_state is not None:
            transition_text_ref = self.narration_factory.get_transition(previous_state, current_state)
            anims.append(animations.transform_state_text(self.current_state_text, transition_text_ref))

        ########## PLAY Anims ##########     Draw Block, Line, Caption, and State Transition
        self.scene.play(*anims)

        # NOW update the reference using the SAME object
        if transition_text_ref is not None:
            self.current_state_text = transition_text_ref

        ########## WAIT Anims ##########
        self.scene.wait(AnimationTimingConfig.WAIT_TIME)

        ########## ANOTHER PLAY Anims ##########
        # Skip the second transformation for special cases - let race resolution/tie reveal handle it
        if self.enable_narration and previous_state is not None and current_state is not None and not is_special_case_2_to_0 and not is_special_case_0_to_0 and not is_special_case_to_0prime and not is_special_case_from_0prime:
            final_state_text = self.narration_factory.get_state(current_state)

            if self.current_state_text is not None:
                self.scene.play(
                    animations.transform_state_text(self.current_state_text, final_state_text)
                )
            else:
                # First block - just show the state without transition
                self.scene.play(animations.add_state_text(final_state_text))

            self.current_state_text = final_state_text
            self.current_state_name = current_state

        ########## WAIT Anims ##########
        self.scene.wait(AnimationTimingConfig.WAIT_TIME)

    @staticmethod
    def _collect_follow_line_animations(chains: list[ChainBranch]) -> list:
        """Collect FollowLine update animations from all blocks in chains"""
        anims = []
        for chain in chains:
            for block in chain.blocks:
                if block.has_line() and isinstance(block.line, FollowLine):
                    # Only collect lines that are in scene
                    if getattr(block.line, 'is_in_scene', False):
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
        self._finalize_race_and_start_next(winner)

    def _animate_race_resolution(self, winner: str):
        """Unified 4-step animation: move up, move left, fade out, fade in new label"""

        # Get winning and losing chains
        winning_chain, losing_chain = self._get_winning_and_losing_chains(winner)
        winning_block = winning_chain.blocks[-1] if winning_chain.blocks else None

        if not winning_block:
            return

        # Mark winning block as next genesis
        winning_block.set_as_next_genesis()

        # Step 1: Calculate vertical shift based on winning block's current position
        genesis_y = self.genesis_position[1]
        winning_block_current_y = winning_block.get_center()[1]
        vertical_shift = genesis_y - winning_block_current_y

        # Collect transform-safe mobjects (squares and labels only)
        # Lines handled separately via UpdateFromFunc to avoid animation conflicts
        all_mobjects = []
        for block in winning_chain.blocks:
            all_mobjects.extend(block.get_transform_safe_mobjects())
        for block in losing_chain.blocks:
            all_mobjects.extend(block.get_transform_safe_mobjects())

        # Collect FollowLine animations for vertical movement
        follow_line_animations = self._collect_follow_line_animations(
            [winning_chain, losing_chain]
        )

        # Step 1: Move both chains vertically to genesis Y position
        self.scene.play(AnimationGroup(
            *[mob.animate.shift(UP * vertical_shift) for mob in all_mobjects],
            *follow_line_animations,
            run_time=AnimationTimingConfig.VERTICAL_SHIFT_TIME
        ))

        # Step 2: Calculate horizontal shift to move winning block to genesis X position
        winning_block_x = winning_block.get_center()[0]
        genesis_x = self.genesis_position[0]
        horizontal_shift = genesis_x - winning_block_x

        # Collect FollowLine animations for horizontal movement
        follow_line_animations = self._collect_follow_line_animations(
            [winning_chain, losing_chain]
        )

        # Step 2: Move all mobjects horizontally to genesis X position
        genesis_mobjects = self.genesis.get_transform_safe_mobjects()

        self.scene.play(AnimationGroup(
            *[mob.animate.shift(LEFT * abs(horizontal_shift)) for mob in all_mobjects],
            *[mob.animate.shift(LEFT * abs(horizontal_shift)) for mob in genesis_mobjects],
            *follow_line_animations,
            run_time=AnimationTimingConfig.SHIFT_TO_NEW_GENESIS_TIME
        ))

        # Step 3: Fade out everything except winning block square
        fade_out_animations = []

        # All winning chain blocks except winner
        for block in winning_chain.blocks[:-1]:
            fade_out_animations.extend(block.get_fade_out_animations())

        # Fade out winning block's old label and line (keep square)
        fade_out_animations.append(animations.fade_out_and_remove_block_label(winning_block.label))
        fade_out_animations.append(animations.fade_out_and_remove_line(winning_block.line))

        # All losing chain blocks
        for block in losing_chain.blocks:
            fade_out_animations.extend(block.get_fade_out_animations())

        # Old genesis (no line to fade out)
        fade_out_animations.extend(self.genesis.get_fade_out_animations(include_line=False))

        self.scene.play(AnimationGroup(*fade_out_animations))

        # Step 4: Create and fade in new "Gen" label for winning block
        new_label = winning_block.update_label("Gen")

        state_animations = [animations.fade_in_and_create_block_label(new_label)]

        # Transform transition text back to state text if narration enabled
        if self.enable_narration and self.current_state_text:
            final_state = self.narration_factory.get_state("0")
            state_animations.append(animations.transform_state_text(self.current_state_text, final_state))
            self.current_state_text = final_state
            self.current_state_name = "0"

        self.scene.play(*state_animations)

        # Add wait after genesis label is created
        self.scene.wait(AnimationTimingConfig.WAIT_TIME)

    def _finalize_race_and_start_next(self, winner: str):
        """Record result and reset for next race"""
        self._record_race_result(winner)

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
        final_state_text = None  # Declare outside the if block
        if self.enable_narration and self.current_state_text:
            final_state_text = self.narration_factory.get_state("0prime")
            shift_animations.append(
                animations.transform_state_text(self.current_state_text, final_state_text)
            )

            # Animate vertical shift for both chains simultaneously with state transition
        self.scene.play(
            *shift_animations,
            run_time=AnimationTimingConfig.VERTICAL_SHIFT_TIME
        )

        # Update the state text reference after the animation completes
        if self.enable_narration and final_state_text is not None:
            self.current_state_text = final_state_text
            self.current_state_name = "0prime"

        # Wait to show the tie state
        self.scene.wait(AnimationTimingConfig.WAIT_TIME)

    ####################
    # ZoomOut on Chain
    # Public
    ####################

#TODO this uses hardcoded vars, this should be in config
    def zoom_out_to_show_races(self, max_races: int = 10, animation_time: float = 3.0, margin: float = 1.0):
        """Automatically scale and center the blockchain to fit on screen

        Args:
            max_races: Maximum number of complete races to display
            animation_time: Duration of the repositioning animation
            margin: Buffer space on each side (in Manim units)
        """
        # Step 1: Collect all blocks using backward traversal approach
        all_blocks = self._collect_blocks_for_zoom_out(max_races)

        if not all_blocks:
            return

            # Step 2: Calculate blockchain depth (max level)
        block_levels = {}
        queue = [(self.original_genesis, 0)]
        visited_levels = set()
        max_depth = 0

        while queue:
            depth_block, depth_level = queue.pop(0)
            if depth_block in visited_levels:
                continue
            visited_levels.add(depth_block)
            block_levels[depth_block] = depth_level
            max_depth = max(max_depth, depth_level)

            for child in depth_block.children:
                queue.append((child, depth_level + 1))

                # Step 3: Calculate required scale factor to fit on screen
        screen_width = 2 * config.frame_x_radius - 2 * margin
        unscaled_width = max_depth * LayoutConfig.BLOCK_HORIZONTAL_SPACING

        if unscaled_width > 0:
            calculated_scale = screen_width / unscaled_width
            scale_factor = min(calculated_scale, 1.0)
        else:
            scale_factor = 1.0

            # Step 4: Calculate where original_genesis should be positioned
        scaled_width = max_depth * LayoutConfig.BLOCK_HORIZONTAL_SPACING * scale_factor
        original_genesis_target_x = -scaled_width / 2

        # Step 5: Identify winning chain
        winning_chain_blocks = set()
        next_genesis_blocks = [b for b in all_blocks if b.is_next_genesis()]

        for ng_block in next_genesis_blocks:
            chain_block = ng_block
            while chain_block is not None:
                winning_chain_blocks.add(chain_block)
                chain_block = chain_block.parent_block
                if chain_block == self.original_genesis:
                    winning_chain_blocks.add(chain_block)
                    break

                    # Step 6: Calculate positions for all blocks
        block_positions = {}
        scaled_spacing = LayoutConfig.BLOCK_HORIZONTAL_SPACING * scale_factor
        scaled_selfish_offset = LayoutConfig.SELFISH_Y_OFFSET * scale_factor

        for pos_block in all_blocks:
            pos_level = block_levels.get(pos_block, 0)
            x_pos = original_genesis_target_x + (pos_level * scaled_spacing)

            if pos_block in winning_chain_blocks:
                y_pos = LayoutConfig.GENESIS_Y
            else:
                if pos_block.get_label_text().startswith("H"):
                    y_pos = LayoutConfig.GENESIS_Y - scaled_selfish_offset
                elif pos_block.get_label_text().startswith("S"):
                    y_pos = LayoutConfig.GENESIS_Y + scaled_selfish_offset
                else:
                    y_pos = LayoutConfig.GENESIS_Y

            block_positions[pos_block] = (x_pos, y_pos, 0)

        # Step 7: Create animations for blocks using AnimationManager
        anims = []

        for anim_block in all_blocks:
            new_pos = block_positions[anim_block]

            # Handle fade-in for previously faded blocks using AnimationManager
            if not getattr(anim_block.square, 'is_in_scene', True):
                anims.append(animations.fade_in_and_create_block_body(anim_block.square))
                anims.append(animations.fade_in_and_create_block_label(anim_block.label))

                # Use .animate for movement and scaling
            # These will be coordinated with UpdateFromFunc in the same play() call
            anims.append(anim_block.square.animate.scale(scale_factor).move_to(new_pos))
            anims.append(anim_block.label.animate.scale(scale_factor).move_to(new_pos))

        # Step 8 & 9: Handle all line animations using AnimationManager
        for anim_block in all_blocks:
            if anim_block.has_line():
                # If line was faded out, fade it back in using AnimationManager
                if not getattr(anim_block.line, 'is_in_scene', True):
                    anims.append(animations.fade_in_and_create_line(anim_block.line))

                    # Always add UpdateFromFunc for lines in scene
                if getattr(anim_block.line, 'is_in_scene', True):
                    anims.append(anim_block.line.create_update_animation())

                    # Step 10: Play all animations
        self.scene.play(*anims, run_time=animation_time)
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

        captured_state = self.current_state_name
        return captured_state

    def _calculate_current_state(self, in_tiebreak: bool = False) -> str:
        """Calculate current state name based on selfish lead

        Args:
            in_tiebreak: Whether we're currently in tiebreaking mode

        Returns:
            State name as string: "0", "0prime", "1", "2", etc.
        """
        _, _, selfish_lead = self._get_current_chain_lengths()

        print(f"DEBUG [_calculate_current_state]: selfish_lead = {selfish_lead}, in_tiebreak = {in_tiebreak}")

        if selfish_lead == 0:
            # Check if we're in a tie situation (both chains have blocks)
            honest_len, selfish_len, _ = self._get_current_chain_lengths()
            if honest_len > 0 and selfish_len > 0:
                print(f"DEBUG [_calculate_current_state]: Returning '0prime' (tie state)")
                return "0prime"  # Tied state
            print(f"DEBUG [_calculate_current_state]: Returning '0' (initial state)")
            return "0"  # Initial state
        elif selfish_lead > 0:
            # SPECIAL CASE: During tiebreaking, even if selfish is ahead, return "0"
            # because the race hasn't been resolved yet
            if in_tiebreak:
                print(f"DEBUG [_calculate_current_state]: Returning '0' (tiebreak in progress)")
                return "0"
                # Return the lead as a string - supports infinite states
            result = str(selfish_lead)
            print(f"DEBUG [_calculate_current_state]: Returning '{result}' (selfish lead)")
            return result
        else:
            # Honest is ahead, back to state 0
            print(f"DEBUG [_calculate_current_state]: Returning '0' (honest ahead)")
            return "0"

    # unused atm
    def _show_state(self, state_name: str):
        """Display state text at top of scene"""
        if not self.enable_narration:
            return  # Skip state text if narration is disabled

        new_state = self.narration_factory.get_state(state_name)

        if self.current_state_text:
            self.scene.play(
                animations.transform_state_text(self.current_state_text, new_state)
            )
        else:
            self.scene.play(
                animations.add_state_text(new_state)
            )
            self.current_state_text = new_state

    # unused atm
    def _hide_current_state(self):
        """Remove current state text"""
        if not self.enable_narration:
            return  # Skip state text if narration is disabled

        if self.current_state_text:
            self.scene.play(
                animations.remove_state_text(self.current_state_text)
            )
            self.current_state_text = None

    def _had_selfish_lead_of_exactly_two(self) -> bool:
        """Check if previous selfish lead was 2"""
        return self.previous_selfish_lead == 2

    def _transition_to_next_race(self, winning_block: Block):
        """Update genesis to point to the winning block and prepare for next race"""
        self.genesis = winning_block

        # Clear the blockchain lists for next race
        self.selfish_chain.blocks.clear()
        self.honest_chain.blocks.clear()

        # Also clear the lines cache
        self.selfish_chain.lines.clear()
        self.honest_chain.lines.clear()

##########Examples##########

class SelfishMiningAutomaticExample(Scene):
    def construct(self):
        # Initialize the mining system
        sm = SelfishMiningSquares(self, alpha=0.40, gamma=0.15)
        for _ in range(20):  # Generate 30 blocks
            sm.generate_next_block_probabilistic()

class SelfishMiningManualExample(Scene):
    def construct(self):
        # Initialize the mining system
        sm = SelfishMiningSquares(self, 0.30, 0.1, enable_narration=True)

        # TODO previous version limited to +4 from Gen, can change but any time selfish is +4 from gen and +1 added,
        #       need to shift chains left 1 position after filling the screen
        sm.advance_selfish_chain()
        sm.advance_selfish_chain()
        sm.advance_selfish_chain()
        sm.advance_honest_chain()
        sm.advance_selfish_chain()
        sm.advance_honest_chain()
        sm.advance_honest_chain()
        # TODO after caption added, never removed
        # TODO add a way to caption without advancing chain
        # TODO add a way to manually tiebreak
        # first block race over
        sm.advance_honest_chain()
        # next race over
        sm.advance_honest_chain()
        # next race over
        sm.advance_selfish_chain()
        sm.advance_honest_chain()
        # tiebreak handled automatically
        sm.advance_selfish_chain()
        sm.advance_selfish_chain()
        sm.advance_honest_chain()
        # too close, reveal
        sm.zoom_out_to_show_races()
        self.wait(1)

class SelfishMiningManualTiesExample(Scene):
    def construct(self):
        # Ties handled automatically
        sm = SelfishMiningSquares(self, 0.33, 0.5, enable_narration=True)  # gives 1/3 chance to each outcome
        sm.advance_selfish_chain()
        sm.advance_honest_chain()

        sm.advance_selfish_chain()
        sm.advance_honest_chain()

        sm.advance_selfish_chain()
        sm.advance_honest_chain()

        sm.advance_selfish_chain()
        sm.advance_honest_chain()

        sm.advance_selfish_chain()
        sm.advance_honest_chain()

        sm.zoom_out_to_show_races()

        self.wait(3)