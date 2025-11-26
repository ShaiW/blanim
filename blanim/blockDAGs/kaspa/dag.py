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
from manim import Wait, RIGHT, config, AnimationGroup, Animation, UpdateFromFunc

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

        reposition_column.is_repositioning = True
        self.workflow_steps.append(reposition_column)

        return placeholder

    def next_step(self)-> None:
        """Execute the next queued function, skipping empty repositioning."""
        if not self.workflow_steps:
            return None

        func = self.workflow_steps.pop(0)

        # Check if this is a marked repositioning function
        if getattr(func, 'is_repositioning', False):
            if self.all_blocks:
                x_pos = self.all_blocks[-1].visual_block.square.get_center()[0]
                column_blocks = [
                    b for b in self.all_blocks
                    if abs(b.visual_block.square.get_center()[0] - x_pos) < 0.01
                ]

                if column_blocks:
                    current_ys = [b.visual_block.square.get_center()[1] for b in column_blocks]
                    current_center_y = (max(current_ys) + min(current_ys)) / 2
                    shift_y = self.config.genesis_y - current_center_y

                    # Skip if negligible shift
                    if abs(shift_y) < 0.01:
                        return self.next_step()

        func()
        return None

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
            # First block at this x - use gen_y y
            y_position = self.config.genesis_y
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
                # Use shift instead of move_to to preserve x-position
                animations.append(
                    block.visual_block.create_movement_animation(
                        block.visual_block.animate.shift(np.array([0, shift_y, 0]))
                    )
                )

        if animations:
            self.scene.play(*animations)

#TODO check if this generates a DAG from existing tips or only from GEN
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
    # Moving Blocks with Synchronized Line Updates  #COMPLETE do NOT modify
    ########################################

    def move(self, blocks, positions):
        """Move blocks to new positions with synchronized line updates.

        This method orchestrates the movement of multiple blocks while ensuring
        that all connected lines update correctly and render in the proper order.
        It implements the core animation deduplication pattern from the reference
        architecture to prevent rendering issues.

        **Architecture Overview**

        The method solves a critical rendering challenge: when multiple blocks move
        simultaneously, their connected lines must update positions without creating
        duplicate animations or rendering artifacts. This is achieved through:

        1. **Animation Collection**: Each block creates an AnimationGroup containing
           its movement animation plus UpdateFromFunc animations for all connected lines
        2. **Deduplication**: The `deduplicate_line_animations()` helper removes
           duplicate line updates (since a line connecting two moving blocks would
           otherwise get two update animations)
        3. **Ordering**: Animations are ordered to ensure block transforms execute
           before line updates in each frame

        **Why This Matters**

        Without deduplication and proper ordering:
        - Lines would render on top of blocks during movement (z-index conflicts)
        - Lines connecting two moving blocks would update twice per frame (performance)
        - Animation timing would be inconsistent across the DAG

        **Z-Index Rendering System**

        This method works in conjunction with the z-index layering system:
        - Lines: z_index 0-10 (regular at 0, selected parent at 5)
        - Blocks: z_index 11-20 (background 11, square 12, label 13)
        - Narrate/Caption: z_index 1000 (always on top)

        By ensuring block animations execute first, then line updates, we maintain
        the visual hierarchy where lines always render behind blocks, even during
        complex multi-block movements.

        Parameters
        ----------
        blocks : list[KaspaLogicalBlock]
            List of blocks to move. Can be any number of blocks, including blocks
            with parent-child relationships.
        positions : list[tuple[float, float]]
            List of (x, y) target positions, one per block. Z-coordinate is always
            set to 0 by the block's animate_move_to() method.

        Examples
        --------
        ::

            # Move single block
            dag.move([block1], [(2, 3)])

            # Move multiple blocks simultaneously
            dag.move([genesis, b1, b2], [(0, 2), (2, 2), (4, 2)])

            # Move parent and child together (lines stay synchronized)
            dag.move([parent, child], [(1, 1), (3, 1)])

        See Also
        --------
        deduplicate_line_animations : Core deduplication logic
        KaspaVisualBlock.animate_move_to : Creates movement animations with line updates
        ParentLine.create_update_animation : Creates UpdateFromFunc for line positioning

        Notes
        -----
        This method uses the DAG as the single API for all block movements, ensuring
        consistent animation handling across the entire visualization. Users should
        never manually create movement animations outside of this method.
        """
        animation_groups = []
        for block, pos in zip(blocks, positions):
            # Pass x, y coordinates to the new method
            animation_groups.append(block.visual_block.animate_move_to(pos[0], pos[1]))

            # Deduplicate and order animations
        animations = self.deduplicate_line_animations(*animation_groups)
        self.scene.play(*animations)

    @staticmethod
    def deduplicate_line_animations(*animation_groups: AnimationGroup) -> list[Animation]:
        """Collect animations, deduplicate UpdateFromFunc, and order them correctly.

        This is the core deduplication algorithm that ensures proper rendering order
        and prevents duplicate line updates when multiple connected blocks move
        simultaneously. It implements the same pattern as the reference Manim
        architecture's TestZIndexRendering.deduplicate_line_animations().

        **The Problem This Solves**

        When two connected blocks move simultaneously, each block's animate_move_to()
        creates an UpdateFromFunc animation for their shared connecting line. Without
        deduplication, this line would:

        1. Get two UpdateFromFunc animations in the same frame
        2. Update its position twice, causing visual glitches
        3. Potentially render on top of blocks due to animation ordering issues

        **The Solution**

        This method implements a three-step process:

        1. **Separation**: Separate block animations (Transform, etc.) from line
           updates (UpdateFromFunc)
        2. **Deduplication**: Track seen mobjects by ID to ensure each line only
           gets one UpdateFromFunc animation, even if multiple blocks reference it
        3. **Ordering**: Return block animations first, then line updates, ensuring
           blocks move before lines update in each frame

        **Why Animation Ordering Matters**

        Manim's render loop processes animations in the order they're provided to
        Scene.play(). By returning [block_animations] + [line_updates], we guarantee:

        - Frame N: Block positions interpolate to new locations
        - Frame N: Line UpdateFromFunc reads those updated positions
        - Frame N: Lines render at correct positions without lag

        If line updates executed first, they would read stale block positions,
        causing lines to lag one frame behind blocks during movement.

        **Z-Index Integration**

        This ordering works in conjunction with the z-index system:
        - Lines have z_index 0-10 (render first/behind)
        - Blocks have z_index 11-20 (render second/on top)

        Even though block animations execute first in the animation list, the
        z-index system ensures lines render behind blocks in the final frame.
        The animation ordering ensures correct position updates; the z-index
        ensures correct rendering order.

        Parameters
        ----------
        *animation_groups : AnimationGroup
            Variable number of AnimationGroup objects, typically one per moving block.
            Each group contains the block's movement animation plus UpdateFromFunc
            animations for all connected lines.

        Returns
        -------
        list[Animation]
            Flat list of animations in the correct order:
            [block_animation_1, block_animation_2, ..., line_update_1, line_update_2, ...]

            Block animations are all Transform/movement animations.
            Line updates are all deduplicated UpdateFromFunc animations.

        Examples
        --------
        ::

            # Internal usage in move() method
            animation_groups = [
                block1.visual_block.animate_move_to(2, 3),  # Contains block move + line updates
                block2.visual_block.animate_move_to(4, 3),  # Contains block move + line updates
            ]
            animations = self.deduplicate_line_animations(*animation_groups)
            # Result: [block1_move, block2_move, line1_update, line2_update]
            # (with duplicates removed if block1 and block2 share a line)

        See Also
        --------
        move : Public API that uses this deduplication
        KaspaVisualBlock.create_movement_animation : Creates AnimationGroups with line updates
        ParentLine.create_update_animation : Creates the UpdateFromFunc animations

        Notes
        -----
        This implementation matches the reference architecture from the pure Manim
        sample code (TestZIndexRendering.deduplicate_line_animations), ensuring
        blanim behaves identically to the proven reference implementation.

        The deduplication uses Python's id() function to track mobjects, which is
        safe because mobject instances are unique and persistent throughout the
        animation lifecycle.
        """
        block_animations = []
        line_updates = []
        seen_mobjects = {}

        for group in animation_groups:
            for anim in group.animations:
                if isinstance(anim, UpdateFromFunc):
                    mob_id = id(anim.mobject)
                    if mob_id not in seen_mobjects:
                        seen_mobjects[mob_id] = anim
                        line_updates.append(anim)
                else:
                    block_animations.append(anim)

        # Return block animations first, then line updates
        return block_animations + line_updates

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
    # Highlighting Blocks #TODO COMPLETE
    ########################################

    def highlight_past(self, focused_block: KaspaLogicalBlock) -> List:
        """Highlight a block's past cone with child-to-parent line animations."""
        context_blocks = self.get_past_cone(focused_block)
        self.flash_lines = self._highlight_with_context(
            focused_block, context_blocks, relationship_type="past"
        )
        return self.flash_lines

    def highlight_future(self, focused_block: KaspaLogicalBlock) -> List:
        """Highlight a block's future cone with child-to-parent line animations."""
        context_blocks = self.get_future_cone(focused_block)
        self.flash_lines = self._highlight_with_context(
            focused_block, context_blocks, relationship_type="future"
        )
        return self.flash_lines

    def highlight_anticone(self, focused_block: KaspaLogicalBlock) -> List:
        """Highlight a block's anticone with child-to-parent line animations."""
        context_blocks = self.get_anticone(focused_block)
        self.flash_lines = self._highlight_with_context(
            focused_block, context_blocks, relationship_type="anticone"
        )
        return self.flash_lines

    def _get_lines_to_highlight(
            self,
            focused_block: KaspaLogicalBlock,
            context_blocks: List[KaspaLogicalBlock],
            relationship_type: str  # "past", "future", or "anticone"
    ) -> Set[int]:
        """Determine which lines should remain highlighted based on relationship type.

        Returns a set of line IDs (using Python's id()) that should NOT be faded.
        """
        lines_to_keep = set()
        context_set = set(context_blocks)

        if relationship_type == "past":
            # RULE: Highlight lines where BOTH child and parent are in past cone
            for block in context_blocks:
                for parent_line, parent in zip(block.visual_block.parent_lines, block.parents):
                    if parent in context_set or parent == focused_block:
                        lines_to_keep.add(id(parent_line))

        elif relationship_type == "future":
            # RULE: Highlight lines where BOTH child and parent are in future cone
            for block in context_blocks:
                for parent_line, parent in zip(block.visual_block.parent_lines, block.parents):
                    if parent in context_set or parent == focused_block:
                        lines_to_keep.add(id(parent_line))

        elif relationship_type == "anticone":
            # RULE 1: Highlight ALL lines from context blocks
            for block in context_blocks:
                for parent_line in block.visual_block.parent_lines:
                    lines_to_keep.add(id(parent_line))

            # RULE 2: Highlight lines FROM non-anticone TO anticone
            for anticone_block in context_blocks:
                for child in anticone_block.children:
                    if child not in context_set and child != focused_block:
                        for parent_line, parent in zip(child.visual_block.parent_lines, child.parents):
                            if parent == anticone_block:
                                lines_to_keep.add(id(parent_line))

        return lines_to_keep

    def _highlight_with_context(
            self,
            focused_block: KaspaLogicalBlock,
            context_blocks: Optional[List[KaspaLogicalBlock]] = None,
            relationship_type: str = "anticone"
    ) -> List:
        """Highlight a block and its context with directional line animations."""
        self.currently_highlighted_block = focused_block

        if context_blocks is None:
            context_blocks = []

        context_set = set(context_blocks)

        # Get set of line IDs that should remain highlighted
        lines_to_keep = self._get_lines_to_highlight(
            focused_block, context_blocks, relationship_type
        )

        # Fade non-context blocks and selectively fade their lines
        fade_animations = []
        for block in self.all_blocks:
            if block not in context_set and block != focused_block:
                # Fade the block itself
                fade_animations.extend(block.visual_block.create_fade_animation())

                # Selectively fade lines NOT in lines_to_keep
                for parent_line in block.visual_block.parent_lines:
                    if id(parent_line) not in lines_to_keep:
                        fade_animations.append(
                            parent_line.animate.set_stroke(opacity=self.config.fade_opacity)
                        )

        # Fade focused block's parent lines if parents not in context
        if focused_block.visual_block.parent_lines:
            for parent_line, parent in zip(focused_block.visual_block.parent_lines, focused_block.parents):
                if parent not in context_set:
                    fade_animations.append(
                        parent_line.animate.set_stroke(opacity=self.config.fade_opacity)
                    )

        # Also fade lines within context blocks that should not be highlighted
        for block in context_blocks:
            for parent_line in block.visual_block.parent_lines:
                if id(parent_line) not in lines_to_keep:
                    fade_animations.append(
                        parent_line.animate.set_stroke(opacity=self.config.fade_opacity)
                    )

        if fade_animations:
            self.scene.play(*fade_animations)

        # Add pulsing highlight to focused block
        pulse_updater = focused_block.visual_block.create_pulsing_highlight()
        focused_block.visual_block.square.add_updater(pulse_updater)

        # Highlight context blocks
        context_animations = []
        for block in context_blocks:
            context_animations.append(block.visual_block.create_highlight_animation())

        if context_animations:
            self.scene.play(*context_animations)
        else:
            self.scene.play(Wait(0.01))

        # Flash lines that are in lines_to_keep
        flash_lines = []
        if self.config.flash_connections:
            # Flash lines within context blocks (only those in lines_to_keep)
            for block in context_blocks:
                for parent_line in block.visual_block.parent_lines:
                    if id(parent_line) in lines_to_keep:
                        # Create flash animation for this specific line
                        flash_copy = parent_line.copy()
                        flash_copy.set_stroke(
                            color=self.config.highlight_color,
                            width=self.config.line_stroke_width
                        )
                        from manim import ShowPassingFlash, cycle_animation
                        cycle_animation(
                            ShowPassingFlash(
                                flash_copy,
                                time_width=0.5,
                                run_time=self.config.highlight_line_cycle_time
                            )
                        )
                        self.scene.add(flash_copy)
                        flash_lines.append(flash_copy)

            # Flash focused block's lines if parents in context
            if focused_block.visual_block.parent_lines:
                for parent in focused_block.parents:
                    if parent in context_set:
                        block_flash_lines = focused_block.visual_block.create_directional_line_flash()
                        for flash_line in block_flash_lines:
                            self.scene.add(flash_line)
                            flash_lines.append(flash_line)
                        break

            # Flash lines FROM non-context blocks TO context blocks (for anticone)
            if relationship_type in "anticone":
                for block in self.all_blocks:
                    if block not in context_set and block != focused_block:
                        for parent_line, parent in zip(block.visual_block.parent_lines, block.parents):
                            if id(parent_line) in lines_to_keep:
                                # Create flash animation
                                flash_copy = parent_line.copy()
                                flash_copy.set_stroke(
                                    color=self.config.highlight_color,
                                    width=self.config.line_stroke_width
                                )
                                from manim import ShowPassingFlash, cycle_animation
                                cycle_animation(
                                    ShowPassingFlash(
                                        flash_copy,
                                        time_width=0.5,
                                        run_time=self.config.highlight_line_cycle_time
                                    )
                                )
                                self.scene.add(flash_copy)
                                flash_lines.append(flash_copy)

        return flash_lines

    def reset_highlighting(self) -> None:
        """Reset all blocks to neutral state using visual block methods."""
        # Remove pulse updater from focused block
        if self.currently_highlighted_block:
            if self.currently_highlighted_block.visual_block.square.updaters:
                self.currently_highlighted_block.visual_block.square.remove_updater(
                    self.currently_highlighted_block.visual_block.square.updaters[-1]
                )

                # Remove flash line copies
        for flash_line in self.flash_lines:
            self.scene.remove(flash_line)
        self.flash_lines = []

        # Reset all blocks using visual block methods
        reset_animations = []
        for block in self.all_blocks:
            reset_animations.extend(block.visual_block.create_reset_animation())
            reset_animations.extend(block.visual_block.create_line_reset_animations())

        self.currently_highlighted_block = None

        if reset_animations:
            self.scene.play(*reset_animations)