from manim import *
import numpy as np
from manim.typing import Point2DLike, Point3D, Point3DLike
from manim.animation.composition import AnimationGroup

"""  
Block and Line Animation System with Proper Rendering Order  
============================================================  

This module implements a hierarchical block-and-line visualization system for Manim  
that addresses critical rendering and animation synchronization challenges.  

Design Overview  
---------------  

The system consists of three main components:  
1. BlockWithBg: A composite mobject containing a square, background, and label  
2. ConnectingLine: Lines that connect parent-child blocks  
3. TestZIndexRendering: Scene with helper methods for animation deduplication  

Key Design Decisions  
--------------------  

### 1. Z-Index Layering (Rendering Order)  

Z-index values control which mobjects render on top of others:  
- Lines: z_index = 0 (bottom layer, render behind blocks)  
- Background rectangles: z_index = 1  
- Squares: z_index = 2  
- Labels: z_index = 3 (top layer)  

This ensures lines never obscure block content, maintaining visual clarity.  

### 2. Line Ownership and Creation  

Each line is owned by exactly ONE block (the child) to prevent duplicate animations:  
- Lines are created when a child block is initialized with a parent  
- Only the child block's create_animations() includes the line's Create animation  
- Lines register themselves with BOTH connected blocks via connected_lines list  
- This dual registration enables movement updates from either endpoint  

### 3. Animation Ordering to Prevent Line Lag  

The critical issue: When blocks move, their UpdateFromFunc animations for lines  
must execute AFTER the block transform animations complete their interpolation  
for each frame. Otherwise, lines read stale block positions and appear to lag.  

Solution: deduplicate_line_animations() separates animations by type:  
- Block transforms (animate.move_to) → block_animations list  
- Line updates (UpdateFromFunc) → line_updates list  
- Returns: block_animations + line_updates  

This ordering ensures that within each frame's render cycle:  
1. Block transforms interpolate to new positions  
2. Line UpdateFromFunc animations read the updated positions  
3. Lines stay synchronized with blocks throughout the animation  

### 4. Deduplication Strategy  

Lines appear in multiple blocks' connected_lines lists, causing duplicate  
UpdateFromFunc animations when multiple blocks move simultaneously. The  
deduplicate_line_animations() helper:  
- Tracks seen line mobjects by id()  
- Keeps only the first UpdateFromFunc for each unique line  
- Prevents conflicting animations on the same mobject  

### 5. Line Direction  

Lines draw from child→parent (not parent→child):  
- start = child block's left edge  
- end = parent block's right edge  
This matches the visual hierarchy and Create animation direction.  

Manim Rendering Pipeline Context  
---------------------------------  

During Scene.play(), Manim's render loop (Scene.play_internal) processes animations  
in the order they appear in the compiled animations list. For each frame:  
1. Animation.update_mobjects(dt) triggers updater functions  
2. Animation.interpolate(alpha) updates animation state  
3. Scene.update_mobjects(dt) runs scene-level updaters  

The interpolate() phase is where UpdateFromFunc.interpolate_mobject() executes,  
calling the line's _update_position function. By placing block transforms before  
line updates in the flat animation list, we guarantee blocks reach their target  
positions before lines query those positions.  

Usage Pattern  
-------------  

For block creation (no deduplication needed):  
    self.play(  
        block1.create_animations(),  
        block2.create_animations(),  
        run_time=2  
    )  

For block movement (requires deduplication):  
    animations = self.deduplicate_line_animations(  
        block1.animate_move_to(new_pos1),  
        block2.animate_move_to(new_pos2),  
    )  
    self.play(*animations, run_time=2)  

References  
----------  
- Manim render loop: manim/scene/scene.py:1335-1368  
- UpdateFromFunc implementation: manim/animation/updaters/update.py:18-38  
- Animation interpolation: manim/animation/animation.py:362-389  
"""

class BlockWithBg(VGroup):
    """Simplified block with label and background rectangle."""

    def __init__(
            self,
            label_text: str,
            position: Point2DLike,
            parent: 'BlockWithBg | None' = None,
            **kwargs
    ):
        super().__init__(**kwargs)
        position_3d: Point3D = np.array([position[0], position[1], 0.0])

        # Create square
        self.square = Square(
            side_length=1,
            fill_color=BLUE,
            fill_opacity=0.7,
            stroke_color=WHITE,
            stroke_width=3
        )
        self.square.move_to(position_3d)

        # Create background rectangle
        self.background_rect = BackgroundRectangle(
            self.square,
            color=BLACK,
            fill_opacity=0.75,
            buff=0
        )
        self.background_rect.move_to(position_3d)

        # Create label
        self.label = Text(label_text, font_size=36, color=WHITE)
        self.label.move_to(position_3d)

        # Set z_index for layering (higher = rendered on top)
        self.background_rect.set_z_index(1)
        self.square.set_z_index(2)
        self.label.set_z_index(3)

        self.add(self.background_rect, self.square, self.label)

        # Track connected lines
        self.connected_lines: list[ConnectingLine] = []

        # Store parent and create parent line if parent exists
        self.parent = parent
        self.parent_line: ConnectingLine | None = None

        if parent is not None:
            self.parent_line = ConnectingLine(parent, self)

    def create_animations(self) -> AnimationGroup:
        animations = [
            Create(self.square),
            Create(self.background_rect),
            Write(self.label),
        ]

        if self.parent_line is not None:
            animations.append(Create(self.parent_line, lag_ratio=0))

        return AnimationGroup(*animations)

    def animate_move_to(self, position: Point3DLike) -> AnimationGroup:
        """Return AnimationGroup that moves this block and updates all connected lines."""
        animations = [self.animate.move_to(position)]

        # Add update animations for all connected lines
        for line in self.connected_lines:
            animations.append(line.create_update_animation())

        return AnimationGroup(*animations)


class ConnectingLine(Line):
    """Line that connects two blocks and follows them during movement."""

    def __init__(self, block1: BlockWithBg, block2: BlockWithBg):
        super().__init__(
            start=block2.square.get_left(),
            end=block1.square.get_right(),
            color=YELLOW,
            stroke_width=5
        )
        # Store direct references to squares for updates
        self.square1: Square = block1.square
        self.square2: Square = block2.square

        # Set z_index lower than blocks so lines render behind
        self.set_z_index(0)

        # Register this line with both blocks
        block1.connected_lines.append(self)
        block2.connected_lines.append(self)

    def _update_position(self, mobject):
        new_start = self.square2.get_left()
        new_end = self.square1.get_right()
        self.put_start_and_end_on(new_start, new_end)

    def create_update_animation(self):
        return UpdateFromFunc(
            self,
            update_function=self._update_position,
            suspend_mobject_updating=False
        )


class TestZIndexRendering(ThreeDScene):
    def construct(self):
        # Set camera for 2D orthographic view
        self.set_camera_orientation(phi=0, theta=-90 * DEGREES)

        # Create blocks with parent relationships
        block1 = BlockWithBg("A", (-3, 0))  # No parent
        block2 = BlockWithBg("B", (0, 0), parent=block1)  # Parent is A
        block3 = BlockWithBg("C", (3, 0), parent=block2)  # Parent is B

        # Test 1: Create blocks - parent lines are automatically created!
        self.play(
            block1.create_animations(),
            block2.create_animations(),
            block3.create_animations(),
            run_time=2
        )
        self.wait(1)

        # Test 2: Move blocks up - lines update automatically!
        animations = self.deduplicate_line_animations(
            block1.animate_move_to((-3, 2, 0)),
            block2.animate_move_to((0, 2, 0)),
            block3.animate_move_to((3, 2, 0)),
        )
        self.play(*animations, run_time=2)
        self.wait(1)

        # Test 3: Move back
        animations = self.deduplicate_line_animations(
            block1.animate_move_to((-3, 0, 0)),
            block2.animate_move_to((0, 0, 0)),
            block3.animate_move_to((3, 0, 0)),
        )
        self.play(*animations, run_time=2)
        self.wait(1)

        # Test 4: Create block D below B (parent is B)
        block4 = BlockWithBg("D", (0, -2), parent=block2)

        self.play(
            block4.create_animations(),
            run_time=2
        )
        self.wait(1)

        # Test 5: Final move - all blocks move
        animations = self.deduplicate_line_animations(
            block1.animate_move_to((-2, 1, 0)),
            block2.animate_move_to((1, 1, 0)),
            block3.animate_move_to((4, 1, 0)),
            block4.animate_move_to((-2, -2, 0)),
        )
        self.play(*animations, run_time=3)
        self.wait(2)

    def deduplicate_line_animations(self, *animation_groups: AnimationGroup) -> list[Animation]:
        """Collect animations, deduplicate UpdateFromFunc, and order them correctly."""
        block_animations = []
        line_updates = []
        seen_mobjects = {}

        for group in animation_groups:
            for anim in group.animations:
                if isinstance(anim, UpdateFromFunc):
                    mob_id = id(anim.mobject)
                    if mob_id not in seen_mobjects:
                        seen_mobjects[mob_id] = anim
                        line_updates.append(anim)  # Add to separate list
                else:
                    block_animations.append(anim)

                    # Return block animations first, then line updates
        return block_animations + line_updates