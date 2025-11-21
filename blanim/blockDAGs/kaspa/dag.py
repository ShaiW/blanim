# blanim\blanim\blockDAGs\kaspa\dag.py
"""
KaspaDAG: BlockDAG Visualization System
===========================================

Architecture Overview:
---------------------
This class manages Kaspa blockDAG visualization using a DAG (Directed Acyclic Graph)
structure where blocks can have multiple parents, forming a true DAG rather than a chain.
The system uses a shared configuration pattern where all blocks reference DEFAULT_KASPA_CONFIG
for consistent visual styling across the entire DAG.

Key Design Principles:
- **Separation of concerns**: KaspaLogicalBlock handles DAG structure/relationships,
  KaspaVisualBlock handles Manim rendering, and KaspaDAG orchestrates both layers
- **Proxy pattern**: Logical blocks expose a public `visual_block` property for clean
  access to visual layer, avoiding protected member access (`._visual`)
- **State tracking workflow**: Blocks can be created without animation, then animated
  step-by-step or all at once, giving users full control over timing
- **Unified config**: All visual properties (colors, opacities, stroke widths) and layout
  parameters (genesis position, spacing) are read from KaspaConfig
- **Animation delegation**: DAG methods call visual block animation methods rather than
  directly manipulating Manim objects, ensuring consistent animation behavior

Block Lifecycle & Workflow:
---------------------------
The system supports three workflow patterns:

1. **Automatic (backward compatible)**:
   - `add_block(parents=[...])` creates and animates a block immediately
   - `add_blocks([(parents, name), ...])` batch-creates and animates multiple blocks

2. **Step-by-step (fine-grained control)**:
   - `create_block(parents=[...])` creates logical block without animation
   - `next_step()` animates the next pending step (block creation or repositioning)
   - Allows inserting custom animations/narration between steps at scene level

3. **Batch with catch-up**:
   - Create multiple blocks with `create_block()`
   - `catch_up()` completes all pending animations at once

Block Positioning:
-----------------
- Blocks are positioned right (x+) of their rightmost parent
- Blocks at the same x-position stack vertically (y+) above existing neighbors
- After block creation, entire columns are vertically centered around genesis y-position
- Positioning automatically handles DAG structures with multiple parents per block

DAG Structure:
-------------
- **Logical layer** (KaspaLogicalBlock): Stores DAG structure as single source of truth
  - `parents`: List of parent blocks (multiple parents supported)
  - `children`: List of child blocks
  - `get_past_cone()`: Returns all ancestors via DFS
  - `get_future_cone()`: Returns all descendants via DFS

- **Visual layer** (KaspaVisualBlock): Handles Manim rendering
  - `parent_lines`: List of ParentLine objects connecting to parent blocks
  - Does NOT store parent/child references (queries logical layer when needed)
  - `create_movement_animation()`: Updates block and all connected lines

- **DAG layer** (KaspaDAG): Orchestrates both layers
  - `blocks`: Dict for O(1) name-based lookup
  - `all_blocks`: List for efficient iteration
  - `get_anticone(block)`: Returns blocks neither ancestors nor descendants

Fuzzy Block Retrieval:
---------------------
Methods like `get_past_cone()`, `get_future_cone()`, and `get_anticone()` support
fuzzy name matching:
- Accept either `KaspaLogicalBlock` instance or string name
- Use regex to extract block numbers and find closest match if exact match fails
- Return empty list if no match found (never raise exceptions)

DAG Generation:
--------------
`generate_dag()` creates realistic DAG structures with:
- Poisson-distributed parallel blocks (controlled by `lambda_parallel`)
- Chain extension probability (controlled by `chain_prob`)
- Occasional "delayed" blocks that reference old tips from previous round
  (simulating network propagation delay, controlled by `old_tip_prob`)

Movement:
--------
`move(blocks, positions)` moves multiple blocks simultaneously while automatically
updating all connected parent and child lines to maintain DAG visual connectivity.

State Tracking:
--------------
- `pending_blocks`: Blocks created but not yet animated
- `workflow_steps`: Queue of animation functions to execute
- `pending_repositioning`: Set of x-positions needing column recentering
- `next_step()` auto-detects when to queue repositioning after all block creations

Highlighting System (TODO):
--------------------------
The highlighting methods currently use protected `._visual` access and need refactoring:
1. Fading unrelated blocks and their parent lines to fade_opacity
2. Highlighting context blocks (past/future cone) with colored strokes
3. Adding a pulsing white stroke to the focused block via updater
4. Flashing parent lines that connect blocks within the highlighted context

Reset is achieved by reading original values from config, ensuring blocks always
return to their defined neutral state without needing to store temporary state.

TODO / Future Improvements:
---------------------------
1. **Refactor highlighting to use visual block methods**: Currently, highlighting methods
   manually construct fade/highlight animations and use `._visual` protected access.
   Should use:
   - `BaseVisualBlock.create_fade_animation()` for fading blocks
   - `BaseVisualBlock.create_reset_animation()` for resetting to neutral state
   - `BaseVisualBlock.create_pulsing_highlight()` instead of manual updaters
   - Access via public `visual_block` property instead of `._visual`

2. **Add line fade methods to visual block**: Parent line fading logic should move to
   visual block layer with a `create_line_fade_animation()` method.

3. **Complete proxy pattern migration**: Replace all remaining `._visual` access with
   `visual_block` property throughout highlighting methods.

4. **Persistent visual state**: Ensure DAG methods only set visual state without blocking
   scene execution, so timing can be handled at scene level and narration/captions/
   camera movements can happen while visual state persists.

5. **Block naming convention**: Current naming (Gen, B1, B2, ...) is inherited from
   blockchain implementation. May need updating for Kaspa-specific conventions.
   See `_generate_block_name()` and `get_block()` docstrings for update locations.
"""

from __future__ import annotations

from typing import Optional, List, TYPE_CHECKING, Set, Callable

import numpy as np
from manim import ShowPassingFlash, cycle_animation, Wait, RIGHT, config

from .logical_block import KaspaLogicalBlock
from .config import KaspaConfig, DEFAULT_KASPA_CONFIG

if TYPE_CHECKING:
    from ...core.hud_2d_scene import HUD2DScene

class BlockPlaceholder:
    """Placeholder for a block that will be created later."""

    def __init__(self, dag, parents, name):
        self.dag = dag
        self.parents = parents
        self.name = name
        self.actual_block = None  # Will be set automatically when created

    def __getattr__(self, attr):
        """Automatically delegate to actual_block once it's created."""
        if self.actual_block is None:
            raise ValueError(f"Block {self.name} hasn't been created yet - call next_step() first")
        return getattr(self.actual_block, attr)

#TODO block naming for DAG
#TODO lines should also retain their own original properties instead of always referring back to config
class KaspaDAG:
    def __init__(self, scene: HUD2DScene, dag_config: KaspaConfig = DEFAULT_KASPA_CONFIG):
        self.scene = scene
        self.config = dag_config
        self.blocks: dict[str, KaspaLogicalBlock] = {}
        self.all_blocks: List[KaspaLogicalBlock] = []
        self.genesis: Optional[KaspaLogicalBlock] = None
        self.currently_highlighted_block: Optional[KaspaLogicalBlock] = None
        self.flash_lines: List = []

        # NEW: State tracking for step-by-step workflow
        self.workflow_steps: List[Callable] = []

        # CRITICAL: Enable z-index rendering
        self.scene.renderer.camera.use_z_index = True

    ########################################
    # Block Handling
    ########################################

    def queue_block(
            self,
            parents: Optional[List[BlockPlaceholder | KaspaLogicalBlock]] = None,
            name: Optional[str] = None
    ) -> BlockPlaceholder:
        """Queue block creation, return placeholder that auto-resolves."""

        placeholder = BlockPlaceholder(self, parents, name)

        def create_and_animate_block():
            # Resolve parent placeholders to actual blocks
            resolved_parents = []
            if parents:
                for p in parents:
                    if isinstance(p, BlockPlaceholder):
                        if p.actual_block is None:
                            raise ValueError(f"Parent block hasn't been created yet")
                        resolved_parents.append(p.actual_block)
                    else:
                        resolved_parents.append(p)

            # Create the actual block
            block_name = name if name else self._generate_block_name(resolved_parents)
            position = self._calculate_dag_position(resolved_parents)

            block = KaspaLogicalBlock(
                name=block_name,
                parents=resolved_parents if resolved_parents else [],
                position=position,
                kaspa_config=self.config,
            )

            self.blocks[block_name] = block
            self.all_blocks.append(block)

            if not resolved_parents:
                self.genesis = block

            # AUTOMATICALLY link placeholder to actual block
            placeholder.actual_block = block

            # Animate it
            self._animate_block_creation(block)

            return block

        self.workflow_steps.append(create_and_animate_block)

        # Queue repositioning
        def reposition_column():
            if self.all_blocks:
                x_pos = self.all_blocks[-1].visual_block.square.get_center()[0]
                self._animate_dag_repositioning({x_pos})

        self.workflow_steps.append(reposition_column)

        return placeholder

    def next_step(self):
        """Execute the next queued function."""
        if self.workflow_steps:
            func = self.workflow_steps.pop(0)
            func()

    def catch_up(self):
        """Execute all queued functions in sequence."""
        while self.workflow_steps:
            self.next_step()

    def add_block(
            self,
            parents: Optional[List[BlockPlaceholder | KaspaLogicalBlock]] = None,
            name: Optional[str] = None
    ) -> KaspaLogicalBlock:
        """Create and animate a block immediately."""
        placeholder = self.queue_block(parents=parents, name=name)
        self.next_step()  # Execute block creation
        self.next_step()  # Execute repositioning
        return placeholder.actual_block  # Return actual block, not placeholder

    def add_blocks(
            self,
            blocks_data: List[tuple[Optional[List[BlockPlaceholder | KaspaLogicalBlock]], Optional[str]]]
    ) -> List[KaspaLogicalBlock]:
        """Add multiple blocks and complete all animations automatically."""
        placeholders = []

        # Queue all blocks
        for parents, name in blocks_data:
            placeholder = self.queue_block(parents=parents, name=name)
            placeholders.append(placeholder)

            # Execute all queued steps
        self.catch_up()

        # Return actual blocks
        return [p.actual_block for p in placeholders]

    def shift_camera_to_follow_blocks(self):
        """Shift camera to keep rightmost blocks in view."""
        if not self.all_blocks:
            return

            # Use visual_block property instead of _visual
        rightmost_x = max(block.visual_block.square.get_center()[0] for block in self.all_blocks)

        margin = self.config.horizontal_spacing * 2
        current_center = self.scene.camera.frame.get_center()
        frame_width = config["frame_width"]
        right_edge = current_center[0] + (frame_width / 2)

        if rightmost_x > right_edge - margin:
            shift_amount = rightmost_x - (right_edge - margin)
            self.scene.play(
                self.scene.camera.frame.animate.shift(RIGHT * shift_amount),
                run_time=self.config.camera_follow_time
            )

    def _calculate_dag_position(self, parents: Optional[List[KaspaLogicalBlock]]) -> tuple[float, float]:
        """Calculate position based on rightmost parent and topmost neighbor."""
        if not parents:
            return self.config.genesis_x, self.config.genesis_y

            # Use rightmost parent for x-position
        rightmost_parent = max(parents, key=lambda p: p.visual_block.square.get_center()[0])
        parent_pos = rightmost_parent.visual_block.square.get_center()
        x_position = parent_pos[0] + self.config.horizontal_spacing

        # Find blocks at same x-position
        same_x_blocks = [
            b for b in self.all_blocks
            if abs(b.visual_block.square.get_center()[0] - x_position) < 0.01
        ]

        if not same_x_blocks:
            # First block at this x - use rightmost parent's y
            y_position = parent_pos[1]
        else:
            # Stack above topmost neighbor
            topmost_y = max(b.visual_block.square.get_center()[1] for b in same_x_blocks)
            y_position = topmost_y + self.config.vertical_spacing

        return x_position, y_position

    def _animate_block_creation(self, block: KaspaLogicalBlock):
        """Animate the creation of a block and its lines."""
        self.shift_camera_to_follow_blocks()
        self.scene.play(block.visual_block.create_with_lines())

    def _animate_dag_repositioning(self, x_positions: Set[float]):
        """Center columns of blocks around genesis y-position."""
        if not x_positions:
            return

        animations = []
        genesis_y = self.config.genesis_y

        for x_pos in x_positions:
            # Find all blocks at this x-position
            column_blocks = [
                b for b in self.all_blocks
                if abs(b.visual_block.square.get_center()[0] - x_pos) < 0.01
            ]

            if not column_blocks:
                continue

                # Calculate current center and target shift
            current_ys = [b.visual_block.square.get_center()[1] for b in column_blocks]
            current_center_y = (max(current_ys) + min(current_ys)) / 2
            shift_y = genesis_y - current_center_y

            # Create shift animations for all blocks in column
            for block in column_blocks:
                current_pos = block.visual_block.square.get_center()
                target = np.array([current_pos[0], current_pos[1] + shift_y, 0])
                animations.append(
                    block.visual_block.create_movement_animation(
                        block.visual_block.animate.move_to(target)
                    )
                )

        if animations:
            self.scene.play(*animations)

    def generate_dag(
            self,
            num_rounds: int,
            lambda_parallel: float = 1.0,
            chain_prob: float = 0.7,
            old_tip_prob: float = 0.1,
    ):
        """Generate a DAG with Poisson-distributed parallel blocks."""
        if not self.genesis:
            raise ValueError("Genesis block must exist before generating DAG")

        current_tips = [self.genesis]
        previous_tips = []

        for round_num in range(num_rounds):
            if np.random.random() < chain_prob:
                num_blocks = 1
            else:
                num_blocks = max(1, np.random.poisson(lambda_parallel) + 1)

            new_placeholders = []

            for _ in range(num_blocks):
                if previous_tips and np.random.random() < old_tip_prob:
                    num_parents = min(len(previous_tips), np.random.randint(1, 3))
                    parents = list(np.random.choice(previous_tips, size=num_parents, replace=False))
                else:
                    num_parents = min(len(current_tips), np.random.randint(1, 3))
                    parents = list(np.random.choice(current_tips, size=num_parents, replace=False))

                    # Use queue_block instead of create_block
                placeholder = self.queue_block(parents=parents)
                new_placeholders.append(placeholder)

                # Execute all queued steps for this round
            self.catch_up()

            # Convert placeholders to actual blocks
            new_blocks = [p.actual_block for p in new_placeholders]

            # Update tip tracking
            previous_tips = current_tips.copy()

            for block in new_blocks:
                for parent in block.parents:
                    if parent in current_tips:
                        current_tips.remove(parent)

            current_tips.extend(new_blocks)
        #TODO determine a block naming based on DAG somehow
    def _generate_block_name(self, parents: List[KaspaLogicalBlock]) -> str:
        """Generate automatic block name based on round from genesis.

        Uses selected parent (parents[0]) to determine round/depth from genesis.
        Round 0: Genesis ("Gen")
        Round 1: "B1", "B1a", "B1b", ... (parallel blocks)
        Round 2: "B2", "B2a", "B2b", ...
        """
        if not parents:
            return "Gen"

            # Calculate round by following selected parent chain back to genesis
        selected_parent = parents[0]
        round_number = 1
        current = selected_parent

        while current.parents:  # Traverse back to genesis
            current = current.parents[0]  # Follow selected parent chain
            round_number += 1

            # Count parallel blocks at this round (blocks already in all_blocks)
        blocks_at_round = [
            b for b in self.all_blocks
            if b != self.genesis and self._get_round(b) == round_number
        ]

        # Generate name
        if len(blocks_at_round) == 0:
            return f"B{round_number}"
        else:
            # Subtract 1 to get correct suffix: 1 existing block → 'a', 2 → 'b', etc.
            suffix = chr(ord('a') + len(blocks_at_round) - 1)
            return f"B{round_number}{suffix}"

    def _get_round(self, block: KaspaLogicalBlock) -> int:
        """Helper to get round number for a block."""
        if not block.parents:
            return 0
        round_num = 1
        current = block.parents[0]
        while current.parents:
            current = current.parents[0]
            round_num += 1
        return round_num

#TODO may need to adjust fuzzy retrieval if naming convention changes
    def get_block(self, name: str) -> Optional[KaspaLogicalBlock]:
        """Retrieve a block by name with fuzzy matching support."""
        # Try exact match first
        if name in self.blocks:
            return self.blocks[name]

        if not self.all_blocks:
            return None

            # Extract round number and find closest
        import re
        match = re.search(r'B?(\d+)', name)
        if not match:
            return self.all_blocks[-1]

        target_round = int(match.group(1))
        max_round = max(self._get_round(b) for b in self.all_blocks)
        actual_round = min(target_round, max_round)

        # Find first block at this round
        for block in self.all_blocks:
            if self._get_round(block) == actual_round:
                return block

        return self.all_blocks[-1]

    ########################################
    # Moving Blocks #TODO COMPLETE  Lines are rendering on top of blocks when moved during updaters and update from func
    ########################################

    def move(self, blocks, positions):
        """Move blocks to new positions with synchronized line updates."""
        animations = []

        for block, pos in zip(blocks, positions):
            # Use create_movement_animation with move_to_position
            animations.append(
                block.visual_block.create_movement_animation(
                    block.visual_block.animate.move_to_position(pos)
                )
            )

        self.scene.play(*animations)

    ########################################
    # Get Past/Future/Anticone Blocks #TODO COMPLETE
    ########################################

    def get_past_cone(self, block: KaspaLogicalBlock | str) -> List[KaspaLogicalBlock]:
        """Get all ancestors via depth-first search.

        Args:
            block: Either a KaspaLogicalBlock instance or a block name string.
                   If a string is provided, fuzzy matching will be used.

        Returns:
            List of ancestor blocks.
        """
        if isinstance(block, str):
            block = self.get_block(block)
            if block is None:
                return []

        return block.get_past_cone()

    def get_future_cone(self, block: KaspaLogicalBlock | str) -> List[KaspaLogicalBlock]:
        """Get all descendants via depth-first search.

        Args:
            block: Either a KaspaLogicalBlock instance or a block name string.
                   If a string is provided, fuzzy matching will be used.

        Returns:
            List of descendant blocks.
        """
        if isinstance(block, str):
            block = self.get_block(block)
            if block is None:
                return []

        return block.get_future_cone()

    def get_anticone(self, block: KaspaLogicalBlock | str) -> List[KaspaLogicalBlock]:
        """Get blocks that are neither ancestors nor descendants.

        Args:
            block: Either a KaspaLogicalBlock instance or a block name string.
                   If a string is provided, fuzzy matching will be used.

        Returns:
            List of blocks in the anticone.
        """
        if isinstance(block, str):
            block = self.get_block(block)
            if block is None:
                return []

        past = set(block.get_past_cone())
        future = set(block.get_future_cone())

        return [
            b for b in self.all_blocks
            if b != block and b not in past and b not in future
        ]

    ########################################
    # Highlighting Blocks #TODO fix this for changes made AND for DAG
    ########################################

    def highlight_past(self, focused_block: KaspaLogicalBlock) -> List:
        """Highlight a block's past cone (ancestors).

        All styling comes from focused_block._visual.config.
        """
        context_blocks = self.get_past_cone(focused_block)
        self.flash_lines = self._highlight_with_context(focused_block, context_blocks)
        return self.flash_lines

    def highlight_future(self, focused_block: KaspaLogicalBlock) -> List:
        """Highlight a block's future cone (descendants).

        All styling comes from focused_block._visual.config.
        """
        context_blocks = self.get_future_cone(focused_block)
        self.flash_lines = self._highlight_with_context(focused_block, context_blocks)
        return self.flash_lines

    def highlight_anticone(self, focused_block: KaspaLogicalBlock) -> List:
        """Highlight a block's anticone (neither ancestors nor descendants).

        All styling comes from focused_block._visual.config.
        """
        context_blocks = self.get_anticone(focused_block)
        self.flash_lines = self._highlight_with_context(focused_block, context_blocks)
        return self.flash_lines

    def _create_pulse_updater(self):
        """Create pulsing stroke width updater using config values."""
        original_width = self.config.stroke_width
        highlighted_width = self.config.context_block_stroke_width
        context_color = self.config.context_block_color
        cycle_time = self.config.context_block_cycle_time  # Use renamed property

        def pulse_stroke(mob, dt):
            t = getattr(mob, 'time', 0) + dt
            mob.time = t
            width = original_width + (highlighted_width - original_width) * (
                    np.sin(t * 2 * np.pi / cycle_time) + 1
            ) / 2
            mob.set_stroke(context_color, width=width)

        return pulse_stroke

    def _highlight_with_context(
            self,
            focused_block: KaspaLogicalBlock,
            context_blocks: Optional[List[KaspaLogicalBlock]] = None
    ) -> List:
        """Highlight a block and its context with optional connection flashing.

        Returns:
            List of flash line copies that were added to the scene (for cleanup)
        """
        # Store the currently highlighted block
        self.currently_highlighted_block = focused_block
        # Read ALL styling from config
        fade_opacity = self.config.fade_opacity
        highlight_color = self.config.highlight_color
        flash_connections = self.config.flash_connections
        line_cycle_time = self.config.highlight_line_cycle_time

        if context_blocks is None:
            context_blocks = []

        # Fade non-context blocks (always fade unrelated blocks)
        fade_animations = []
        for block in self.all_blocks:
            if block not in context_blocks and block != focused_block:
                fade_animations.extend([
                    block._visual.square.animate.set_fill(opacity=fade_opacity),
                    block._visual.square.animate.set_stroke(opacity=fade_opacity),
                    block._visual.label.animate.set_fill(opacity=fade_opacity)
                ])
                for line in block._visual.parent_lines:
                    fade_animations.append(line.animate.set_stroke(opacity=fade_opacity))

        # Fade focused block's parent line if parent is not in context
        if focused_block._visual.parent_lines:
            parent_block = focused_block.parent
            if parent_block and parent_block not in context_blocks:
                fade_animations.append(
                    focused_block._visual.parent_lines[0].animate.set_stroke(opacity=fade_opacity)
                )

        if fade_animations:
            self.scene.play(*fade_animations)

        # Add pulsing white stroke to focused block (using updater)
        pulse_updater = self._create_pulse_updater()
        focused_block._visual.square.add_updater(pulse_updater)

        # Highlight context blocks with yellow stroke and increased width(highlight_stroke_width)
        context_animations = []
        for block in context_blocks:
            context_animations.extend([
                block._visual.square.animate.set_stroke(
                    highlight_color,
                    width=self.config.highlight_stroke_width
                )
            ])

        if context_animations:
            self.scene.play(*context_animations)
        else:
            # Play a minimal wait to commit the fade state
            self.scene.play(Wait(0.01))

        # Flash connections using cycle_animation (non-blocking)
        flash_lines = []
        if flash_connections:
            for block in context_blocks:
                if block._visual.parent_lines:
                    # Create a copy of the line with highlight color
                    flash_line = block._visual.parent_lines[0].copy().set_color(highlight_color)
                    self.scene.add(flash_line)
                    flash_lines.append(flash_line)

                    # Apply cycle_animation to make it flash
                    cycle_animation(
                        ShowPassingFlash(flash_line, time_width=0.5, run_time=line_cycle_time)#run_time sets cycle time
                    )

            # Flash focused block's parent line only if parent is in context
            if focused_block._visual.parent_lines and focused_block.parent in context_blocks:
                flash_line = focused_block._visual.parent_lines[0].copy().set_color(highlight_color)
                self.scene.add(flash_line)
                flash_lines.append(flash_line)
                cycle_animation(
                    ShowPassingFlash(flash_line, time_width=0.5, run_time=line_cycle_time)
                )

        # Return the flash line copies (not originals) for cleanup
        return flash_lines

    def reset_highlighting(self):
        """Reset all blocks to neutral state from config."""
        # Remove pulse updater from currently highlighted block
        if self.currently_highlighted_block and self.currently_highlighted_block._visual.square.updaters:
            self.currently_highlighted_block._visual.square.remove_updater(
                self.currently_highlighted_block._visual.square.updaters[-1]
            )

        # Remove flash line copies from scene
        for flash_line in self.flash_lines:
            self.scene.remove(flash_line)
        self.flash_lines = []

        # Reset ALL blocks to original styling from config
        reset_animations = []
        for block in self.all_blocks:
            reset_animations.extend([
                block._visual.square.animate.set_fill(opacity=self.config.fill_opacity),
                block._visual.square.animate.set_stroke(
                    self.config.stroke_color,
                    width=self.config.stroke_width,
                    opacity=self.config.stroke_opacity
                ),
                block._visual.label.animate.set_fill(opacity=self.config.label_opacity)
            ])
            for line in block._visual.parent_lines:
                reset_animations.append(
                    line.animate.set_stroke(
                        self.config.selected_parent_line_color,#TODO this is why lines need to retain their own properties
                        width=self.config.line_stroke_width,
                        opacity=self.config.line_stroke_opacity
                    )
                )

        # Clear the tracked state
        self.currently_highlighted_block = None

        if reset_animations:
            self.scene.play(*reset_animations)


"""  
Z-Index Rendering Solution for 3D Scenes Modeled as 2D  
=======================================================  

PROBLEM:  
--------  
When using ThreeDScene (via HUD2DScene) for 2D visualizations, parent lines were   
rendering on top of blocks during move animations despite setting z-index values   
and using `use_z_index=True`. The issue occurred because:  

1. Manim's z-index sorting happens during mobject extraction for rendering  
2. During animations with updaters, the scene's mobject list order can override   
   z-index sorting  
3. `UpdateFromFunc` animations update during `interpolate_mobject()` phase, which   
   happens AFTER z-index sorting for that frame  

ATTEMPTED SOLUTIONS (THAT DIDN'T WORK):  
----------------------------------------  
1. Setting `use_z_index=True` alone - insufficient during updater animations  
2. Using `bring_to_front()` before/after animations - only affects initial order  
3. Adding blocks as foreground mobjects - caused timing issues with line animations  
4. Setting z-index within `UpdateFromFunc` - too late in rendering pipeline  
5. Adding per-frame `bring_to_front()` updaters - computationally expensive  

WORKING SOLUTION:  
-----------------  
Use ThreeDCamera's depth-based rendering by setting z-coordinates:  

1. **For blocks**: Set z=0.001 when converting 2D coordinates to 3D  
   - Example: `(x, y)` becomes `(x, y, 0.001)`  

2. **For lines**: Keep z=0 (default)  
   - Lines remain at z=0 during initialization  

3. **Enable z-index**: Set `self.scene.renderer.camera.use_z_index = True` in DAG init  

4. **Use updaters for line positioning**: Replace `UpdateFromFunc` with mobject updaters  
   - Add updaters before `scene.play()`  
   - Remove updaters after animation completes  
   - Updaters run during scene's update phase (before rendering)  

WHY THIS WORKS:  
---------------  
- ThreeDCamera uses depth-based sorting via `get_mobjects_to_display()` which sorts   
  by z-coordinate when `shade_in_3d=True`  
- A z-offset of 0.001 is negligible at typical camera distances (focal_distance=20.0)  
  so no visual misalignment occurs in 2D space  
- Blocks at z=0.001 always render in front of lines at z=0  
- Updaters update mobjects during the update phase (before rendering), allowing   
  z-index sorting to work correctly each frame  

IMPLEMENTATION:  
---------------  
In `move()` method:  
```python  
# Convert 2D to 3D with z-offset for blocks  [header-2](#header-2)
positions_3d = [(pos[0], pos[1], 0.001) if len(pos) == 2 else pos   
                for pos in positions]  

# Use regular .animate for blocks  [header-3](#header-3)
animations = []  
for block, pos in zip(blocks, positions_3d):  
    animations.append(block.visual_block.square.animate.move_to(pos))  
    animations.append(block.visual_block.label.animate.move_to(pos))  

# Add updaters for lines (temporary, only during animation)  [header-4](#header-4)
for block in blocks:  
    for line in block.visual_block.parent_lines:  
        line.add_updater(lambda mob, l=line: l._update_position_and_size(l))  

self.scene.play(*animations)  

# Clean up updaters  [header-5](#header-5)
for block in blocks:  
    for line in block.visual_block.parent_lines:  
        line.clear_updaters()
"""