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

        # Test 6: Move block D back to its previous position
        animations = self.deduplicate_line_animations(
            block4.animate_move_to((0, -2, 0)),
        )
        self.play(*animations, run_time=2)
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

#TODO implement this later
"""  
Multi-Dimensional Configuration System for Blanim DAG Visualization  
====================================================================  

This module defines a hierarchical configuration system using nested dataclasses  
that allows users to configure all aspects of DAG visualization (lines, blocks,  
and DAG-level settings) from a single, copy-pasteable config object.  

Design Philosophy  
-----------------  

The config system follows these principles:  

1. **Single Source of Truth**: One DAGConfig instance per DAG, defined at scene level  
2. **Copy-Pasteable**: Users can copy entire config blocks across scenes  
3. **Selective Overrides**: Only specify parameters that differ from defaults  
4. **Hierarchical Organization**: Related settings grouped into logical sections  
5. **Type-Safe**: Dataclasses provide type hints and validation  
6. **Clean Unpacking**: Each component receives only its relevant config section  

Configuration Hierarchy  
-----------------------  

DAGConfig (top level)  
├── LineConfig (line styling and z-index)  
├── BlockConfig (block styling and z-index)  
└── DAG-level settings (animation defaults, etc.)  

Z-Index Ranges  
--------------  

The system uses expanded z-index ranges for future extensibility:  

Lines: 0-10  
    - Regular lines: z_index = 0 (bottom layer)  
    - Selected parent lines: z_index = 5 (middle of range)  
    - Reserved: 1-4, 6-10 for future line types  

Blocks: 11-20  
    - Background rectangles: z_index = 11  
    - Squares: z_index = 12  
    - Labels: z_index = 13  
    - Reserved: 14-20 for future block layers  

Usage Pattern  
-------------  

**At Scene Level (Outside Scene Class)**:  

.. code-block:: python  

    from blanim import DAGConfig, LineConfig, BlockConfig  
    from manim import YELLOW, RED, WHITE  

    # Define config outside scene - copy-pasteable across scenes  
    config = DAGConfig(  
        line_config=LineConfig(  
            color=YELLOW,  
            stroke_width=7,  
            z_index_regular=0,  
            z_index_selected=5  
        ),  
        block_config=BlockConfig(  
            square_fill_color=RED,  
            label_font_size=48,  
            z_index_background=11,  
            z_index_square=12,  
            z_index_label=13  
        ),  
        default_animation_run_time=2.5  
    )  

    class MyScene(HUD2DScene):  
        def construct(self):  
            # Pass config to DAG  
            dag = DAG(config=config)  

            # All blocks and lines created by DAG use this config  
            block1 = dag.create_block("A", position=(-3, 0))  
            block2 = dag.create_block("B", position=(0, 0), parent=block1)  

**Config Unpacking in Components**:  

.. code-block:: python  

    # In DAG class  
    class DAG:  
        def __init__(self, config: DAGConfig | None = None):  
            self.config = config if config is not None else DAGConfig()  

        def create_line(self, child_block, parent_block, is_selected=False):  
            # Pass down line config section  
            return ParentLine(  
                this_block=child_block.square,  
                parent_block=parent_block.square,  
                is_selected_parent_line=is_selected,  
                config=self.config.line_config  # Unpack line config  
            )  

    # In ParentLine class  
    class ParentLine(Line):  
        def __init__(  
            self,  
            this_block,  
            parent_block,  
            is_selected_parent_line=False,  
            config: LineConfig | None = None  
        ):  
            if config is None:  
                config = LineConfig()  

            super().__init__(  
                start=this_block.get_left(),  
                end=parent_block.get_right(),  
                buff=config.buff,  
                color=config.color,  
                stroke_width=config.stroke_width,  
                cap_style=config.cap_style  
            )  

            # Use config z-index values  
            z_index = config.z_index_selected if is_selected_parent_line else config.z_index_regular  
            self.set_z_index(z_index)  

Configuration Classes  
---------------------  

LineConfig  
~~~~~~~~~~  

Attributes:  
    color : ManimColor  
        Line color (default: WHITE)  
    stroke_width : float  
        Line stroke width (default: 5)  
    cap_style : CapStyleType  
        Line cap style (default: CapStyleType.ROUND)  
    buff : float  
        Buffer distance from block edges (default: 0.1)  
    z_index_regular : float  
        Z-index for regular lines (default: 0)  
    z_index_selected : float  
        Z-index for selected parent lines (default: 5)  

BlockConfig  
~~~~~~~~~~~  

Attributes:  
    square_fill_color : ManimColor  
        Block square fill color (default: BLUE)  
    square_fill_opacity : float  
        Block square fill opacity (default: 0.7)  
    square_stroke_color : ManimColor  
        Block square stroke color (default: WHITE)  
    square_stroke_width : float  
        Block square stroke width (default: 3)  
    square_side_length : float  
        Block square side length (default: 1)  
    bg_color : ManimColor  
        Background rectangle color (default: BLACK)  
    bg_fill_opacity : float  
        Background fill opacity (default: 0.75)  
    bg_buff : float  
        Background buffer around square (default: 0)  
    label_font_size : int  
        Label text font size (default: 36)  
    label_color : ManimColor  
        Label text color (default: WHITE)  
    z_index_background : float  
        Z-index for background rectangles (default: 11)  
    z_index_square : float  
        Z-index for squares (default: 12)  
    z_index_label : float  
        Z-index for labels (default: 13)  

DAGConfig  
~~~~~~~~~  

Attributes:  
    line_config : LineConfig  
        Configuration for all lines (default: LineConfig())  
    block_config : BlockConfig  
        Configuration for all blocks (default: BlockConfig())  
    default_animation_run_time : float  
        Default run time for animations (default: 2.0)  
    enable_deduplication : bool  
        Enable line animation deduplication (default: True)  

Benefits  
--------  

1. **Maintainability**: Single config object easier to manage than scattered parameters  
2. **Consistency**: All components use same styling automatically  
3. **Flexibility**: Easy to create variations by copying and modifying config  
4. **Type Safety**: Dataclass validation catches configuration errors early  
5. **Extensibility**: New config options can be added without breaking existing code  
6. **Documentation**: Config structure self-documents available options  

Integration with Manim  
-----------------------  

This pattern aligns with Manim's own configuration system (ManimConfig) which uses  
a similar hierarchical approach for managing library-wide settings. See:  
- manim/_config/utils.py:146-328 for ManimConfig implementation  
- manim/_config/__init__.py for config initialization  

See Also  
--------  
HUD2DScene : Scene class with z-index support  
ParentLine : Line class that uses LineConfig  
BlockWithBg : Reference implementation for block structure (from sample code)  
ManimConfig : Manim's configuration system (manim/_config/utils.py)  

Notes  
-----  

**Implementation Status**: This is a proposed architecture to be implemented after  
completing the blocks, lines, and DAG refactoring to match the sample code architecture.  

**Compatibility**: The config system is designed to work with the z-index-based  
rendering system in HUD2DScene (which extends ThreeDScene with use_z_index=True).  

**Future Extensions**: The expanded z-index ranges (0-10 for lines, 11-20 for blocks)  
provide room for additional layer types without breaking existing code.  
"""