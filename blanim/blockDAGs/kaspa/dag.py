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
        self.pending_blocks: List[KaspaLogicalBlock] = []
        self.pending_repositioning: Set[float] = set()
        self.workflow_steps: List[Callable] = []
    ########################################
    # Block Handling
    ########################################

    def create_block(
            self,
            parents: Optional[List[KaspaLogicalBlock]] = None,
            name: Optional[str] = None
    ) -> KaspaLogicalBlock:
        """Create a logical block without animation, saving steps for later."""
        if name is None:
            name = self._generate_block_name(parents)

        position = self._calculate_dag_position(parents)

        block = KaspaLogicalBlock(
            name=name,
            parents=parents if parents else [],
            position=position,
            kaspa_config=self.config,
        )

        # Register block
        self.blocks[name] = block
        self.all_blocks.append(block)

        if parents is None:
            self.genesis = block

            # Track as pending
        self.pending_blocks.append(block)

        # Queue animation step
        self.workflow_steps.append(lambda b=block: self._animate_block_creation(b))

        # Track x-position for repositioning (but don't queue yet)
        x_pos = block.visual_block.square.get_center()[0]
        self.pending_repositioning.add(x_pos)

        return block

    def queue_repositioning(self):
        """Queue repositioning animation for all pending x-positions."""
        if self.pending_repositioning:
            positions_to_reposition = self.pending_repositioning.copy()
            self.workflow_steps.append(
                lambda: self._animate_dag_repositioning(positions_to_reposition)
            )

    def next_step(self):
        """Execute the next pending animation step.

        Automatically queues repositioning if all pending block creations
        have been animated.
        """
        if self.workflow_steps:
            step = self.workflow_steps.pop(0)
            step()

            # Auto-detect if we should queue repositioning
            # Check if we just animated the last pending block creation
            if not self.workflow_steps and self.pending_repositioning:
                self.queue_repositioning()
        elif self.pending_repositioning:
            # No more workflow steps, but repositioning is pending
            self.queue_repositioning()
            if self.workflow_steps:
                self.next_step()  # Execute the repositioning we just queued

    def catch_up(self):
        """Complete all pending animation steps."""
        while self.workflow_steps:
            self.next_step()

            # Clear state
        self.pending_blocks.clear()
        self.pending_repositioning.clear()

    def add_block(
            self,
            parents: Optional[List[KaspaLogicalBlock]] = None,
            name: Optional[str] = None
    ) -> KaspaLogicalBlock:
        """Add a new block with full automatic workflow (create + animate + reposition)."""
        block = self.create_block(parents=parents, name=name)
        self.queue_repositioning()  # Queue repositioning once
        self.catch_up()
        return block

    def add_blocks(
            self,
            blocks_data: List[tuple[Optional[List[KaspaLogicalBlock]], Optional[str]]]
    ) -> List[KaspaLogicalBlock]:
        """Add multiple blocks and complete all animations automatically.

        This is a convenience method that creates multiple blocks, animates them,
        and repositions them in sequence without allowing scene-level animations
        in between steps.

        Args:
            blocks_data: List of (parents, name) tuples for each block to create

        Returns:
            List of created blocks

        Example:
            blocks = dag.add_blocks([
                ([genesis], "B1"),
                ([genesis], "B2"),
                ([b1, b2], "B3"),
            ])
        """
        created_blocks = []

        # Create all blocks (queues their animations)
        for parents, name in blocks_data:
            block = self.create_block(parents=parents, name=name)
            created_blocks.append(block)

            # Queue repositioning
        self.queue_repositioning()

        # Execute all pending steps automatically
        self.catch_up()

        return created_blocks

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
            old_tip_prob: float = 0.1,  # Probability of referencing old tips
    ):
        """Generate a DAG with Poisson-distributed parallel blocks.

        Parameters
        ----------
        num_rounds
            Number of block creation rounds
        lambda_parallel
            Poisson parameter for number of parallel blocks (when not chaining)
        chain_prob
            Probability of creating a single block (chain extension)
        old_tip_prob
            Probability that a block references old tips from previous round
        """
        if not self.genesis:
            raise ValueError("Genesis block must exist before generating DAG")

        current_tips = [self.genesis]
        previous_tips = []  # Tips from the previous round

        for round_num in range(num_rounds):
            # Decide: chain extension or parallel blocks?
            if np.random.random() < chain_prob:
                num_blocks = 1
            else:
                num_blocks = max(1, np.random.poisson(lambda_parallel) + 1)

            new_blocks = []

            for _ in range(num_blocks):
                # Decide if this block should reference old tips
                if previous_tips and np.random.random() < old_tip_prob:
                    # Select parents from previous round (network delay simulation)
                    num_parents = min(len(previous_tips), np.random.randint(1, 3))
                    parents = list(np.random.choice(previous_tips, size=num_parents, replace=False))
                else:
                    # Normal case: select from current tips
                    num_parents = min(len(current_tips), np.random.randint(1, 3))
                    parents = list(np.random.choice(current_tips, size=num_parents, replace=False))

                    # Create the block
                new_block = self.create_block(parents=parents)
                new_blocks.append(new_block)

                # Update tip tracking for next round
            previous_tips = current_tips.copy()  # Save current tips as "old tips"

            # Remove parents that now have children from current tips
            for block in new_blocks:
                for parent in block.parents:
                    if parent in current_tips:
                        current_tips.remove(parent)

                        # Add newly created blocks to current tips
            current_tips.extend(new_blocks)

            # Animate everything
        self.catch_up()
#TODO determine a block naming based on DAG somehow
    def _generate_block_name(self, parents: Optional[List[KaspaLogicalBlock]]) -> str:
        """Generate block name based on DAG structure."""
        if not parents:
            return "Gen"

            # Use selected parent (first) for naming
        selected_parent = parents[0]
        height = selected_parent.weight + 1
        block_number = height - 1

        # Count existing blocks at this height
        blocks_at_height = [b for b in self.all_blocks if b.weight == height]

        if not blocks_at_height:
            return f"B{block_number}"
        else:
            suffix = chr(ord('a') + len(blocks_at_height))
            return f"B{block_number}{suffix}"

#TODO may need to adjust fuzzy retrieval if naming convention changes
    def get_block(self, name: str) -> Optional[KaspaLogicalBlock]:
        """Retrieve a block by name with fuzzy matching support.

        This method attempts to find a block using the provided name string.
        If an exact match is not found, it falls back to fuzzy matching by
        extracting numeric identifiers from the input and searching for
        similar block names.

        Parameters
        ----------
        name : str
            The block name to search for. Can be an exact name (e.g., "Gen", "B5")
            or a partial/fuzzy name (e.g., "5", "block5").

        Returns
        -------
        KaspaLogicalBlock | None
            The matching block if found, otherwise None.

        Examples
        --------
        Exact match::

            block = dag.get_block("B5")  # Returns block named "B5"

        Fuzzy match::

            block = dag.get_block("5")      # Finds "B5" via fuzzy matching
            block = dag.get_block("block5") # Also finds "B5"

        No match::

            block = dag.get_block("nonexistent")  # Returns None

        Notes
        -----
        **Naming Convention (Update Here if Changed):**

        The current naming convention follows this pattern:
        - Genesis block: "Gen"
        - Regular blocks: "B{number}" (e.g., "B1", "B2", "B3")
        - Parallel blocks: "B{number}{letter}" (e.g., "B2a", "B2b")

        The fuzzy matching logic uses regex to extract numeric identifiers
        from block names. If you change the naming convention, you must update:
        1. The `_generate_block_name()` method (defines naming pattern)
        2. The fuzzy matching regex in this method (extracts identifiers)
        3. This docstring to reflect the new convention

        **Fuzzy Matching Algorithm:**

        1. Try exact dictionary lookup in `self.blocks[name]`
        2. If not found, extract numbers from input using regex
        3. Search all block names for matches containing those numbers
        4. Return the first match found, or None if no matches exist

        This method is used internally by `get_past_cone()`, `get_future_cone()`,
        and `get_anticone()` to provide user-friendly block name resolution.

        See Also
        --------
        _generate_block_name : Defines the block naming convention
        get_past_cone : Uses fuzzy retrieval for ancestor queries
        get_future_cone : Uses fuzzy retrieval for descendant queries
        """
        # Try exact match first
        if name in self.blocks:
            return self.blocks[name]

        if not self.all_blocks:
            return None

            # Extract height and find closest
        import re
        match = re.search(r'B?(\d+)', name)
        if not match:
            return self.all_blocks[-1]

        target_height = int(match.group(1))
        max_height = max(b.weight for b in self.all_blocks)
        actual_height = min(target_height, max_height)

        # Find first block at this height
        for block in self.all_blocks:
            if block.weight == actual_height:
                return block

        return self.all_blocks[-1]

    ########################################
    # Moving Blocks #TODO COMPLETE
    ########################################

    def move(
            self,
            blocks: List[KaspaLogicalBlock],
            positions: List[tuple[float, float]]
    ):
        """Move multiple blocks using their visual block's movement animation.

        Args:
            blocks: List of blocks to move
            positions: Corresponding (x, y) positions
        """
        if len(blocks) != len(positions):
            raise ValueError("Number of blocks must match number of positions")

        animations = []
        for block, pos in zip(blocks, positions):
            target = np.array([pos[0], pos[1], 0])
            animations.append(
                block.visual_block.create_movement_animation(
                    block.visual_block.animate.move_to(target)
                )
            )

        if animations:
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