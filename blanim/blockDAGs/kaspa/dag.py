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

TODO / Future Improvements:
---------------------------

5. **Block naming convention**: Verify this is Kaspa-specific.
   See `_generate_block_name()` and `get_block()` docstrings for update locations.
"""

from __future__ import annotations

import math
from typing import Optional, List, TYPE_CHECKING, Set, Callable

import numpy as np
from manim import Wait, RIGHT, config, AnimationGroup, Animation, UpdateFromFunc, Indicate, RED, ORANGE, YELLOW, logger

from .logical_block import KaspaLogicalBlock
from .config import KaspaConfig, DEFAULT_KASPA_CONFIG, _KaspaConfigInternal

if TYPE_CHECKING:
    from ...core.hud_2d_scene import HUD2DScene

class KaspaDAG:
    def __init__(self, scene: HUD2DScene):
        self.scene = scene
        self.config_manager = KaspaConfigManager(_KaspaConfigInternal(**DEFAULT_KASPA_CONFIG.__dict__))

        # Initialize components
        self.block_manager = BlockManager(self)
#        self.generator = DAGGenerator(self)
        self.movement = Movement(self)
        self.retrieval = BlockRetrieval(self)
        self.relationship_highlighter = RelationshipHighlighter(self)
        self.ghostdag_highlighter = GhostDAGHighlighter(self)


        self.blocks: dict[str, KaspaLogicalBlock] = {}
        self.all_blocks: List[KaspaLogicalBlock] = []
        self.genesis: Optional[KaspaLogicalBlock] = None

        # NEW: State tracking for step-by-step workflow
        self.workflow_steps: List[Callable] = []

        # CRITICAL: Enable z-index rendering
        self.scene.renderer.camera.use_z_index = True

    ########################################
    # Config
    ########################################

    @property
    def config(self) -> _KaspaConfigInternal:
        """Access config through manager."""
        return self.config_manager.config

    def set_k(self, k: int) -> 'KaspaDAG':
        """Set k with genesis lock protection."""
        self.config_manager.set_k(k, len(self.all_blocks) > 0)
        return self

    def apply_config(self, user_config: KaspaConfig) -> 'KaspaDAG':
        """Apply typed configuration with chaining."""
        self.config_manager.apply_config(user_config, len(self.all_blocks) > 0)
        return self

    ########################################
    # Block Retrieval #Complete
    ########################################

    def get_current_tips(self) -> List[KaspaLogicalBlock]:
        """Get current DAG tips (blocks without children)."""
        return self.retrieval.get_current_tips()

    def _generate_block_name(self, parents: List[KaspaLogicalBlock]) -> str:
        """Generate automatic block name based on round from genesis."""
        return self.retrieval.generate_block_name(parents)

    def get_block(self, name: str) -> Optional[KaspaLogicalBlock]:
        """Retrieve a block by name with fuzzy matching support."""
        return self.retrieval.get_block(name)

    ########################################
    # Movement #Complete
    ########################################

    def move(self, blocks, positions):
        """Move blocks to new positions with synchronized line updates."""
        return self.movement.move(blocks, positions)

    def shift_camera_to_follow_blocks(self):
        """Shift camera to keep rightmost blocks in view."""
        self.movement.shift_camera_to_follow_blocks()

    ########################################
    # Get Past/Future/Anticone Blocks #Complete
    ########################################

    def get_past_cone(self, block: KaspaLogicalBlock | str) -> List[KaspaLogicalBlock]:
        """Get all ancestors of a block."""
        return self.retrieval.get_past_cone(block)

    def get_future_cone(self, block: KaspaLogicalBlock | str) -> List[KaspaLogicalBlock]:
        """Get all descendants of a block."""
        return self.retrieval.get_future_cone(block)

    def get_anticone(self, block: KaspaLogicalBlock | str) -> List[KaspaLogicalBlock]:
        """Get all anticone of a block."""
        return self.retrieval.get_anticone(block)

    ########################################
    # Block Handling #Complete
    ########################################

    def queue_block(self, timestamp:float , parents: Optional[List[BlockPlaceholder | KaspaLogicalBlock]] = None, name: Optional[str] = None) -> BlockPlaceholder:
        """Queue a block that will be created later."""
        return self.block_manager.queue_block(timestamp, parents, name)

    def next_step(self)-> None:
        """Play next pending block creation/shift animation"""
        self.block_manager.next_step()

    def catch_up(self)-> None:
        """Play all pending block creation/shift animations"""
        self.block_manager.catch_up()

    def add_block(self, parents: Optional[List[BlockPlaceholder | KaspaLogicalBlock]] = None, name: Optional[str] = None) -> KaspaLogicalBlock:
        """Add a block to the DAG and animate"""
        return self.block_manager.add_block(parents, name)

    def add_blocks(self, blocks_data: List[tuple[Optional[List[BlockPlaceholder | KaspaLogicalBlock]], Optional[str]]]) -> List[KaspaLogicalBlock]:
        """Add multiple blocks and complete all animations automatically."""
        return self.block_manager.add_blocks(blocks_data)

    ########################################
    # Highlighting Relationships
    ########################################

    def highlight_past(self, focused_block: KaspaLogicalBlock | str) -> None:
        """Highlight a block's past cone with child-to-parent line animations."""
        self.relationship_highlighter.highlight_past(focused_block)

    def highlight_future(self, focused_block: KaspaLogicalBlock | str) -> None:
        """Highlight a block's future cone with child-to-parent line animations."""
        self.relationship_highlighter.highlight_future(focused_block)

    def highlight_anticone(self, focused_block: KaspaLogicalBlock | str) -> None:
        """Highlight a block's anticone with child-to-parent line animations."""
        self.relationship_highlighter.highlight_anticone(focused_block)

    def reset_highlighting(self) -> None:
        """Reset all blocks to neutral state using visual block methods."""
        self.relationship_highlighter.reset_highlighting()

    ########################################
    # Highlighting GHOSTDAG
    ########################################

    def animate_ghostdag_process(self, context_block: KaspaLogicalBlock | str, narrate: bool = True, step_delay: float = 1.0) -> None:
        """Animate the complete GhostDAG process for a context block."""
        self.ghostdag_highlighter.animate_ghostdag_process(context_block, narrate=narrate, step_delay=step_delay)

    ####################
    # Helper functions for finding k thresholds
    ####################
    # Verified
    def k_from_x(self, x_val: float, delta: float = 0.01) -> int:
        """Calculate k from x using Kaspa's cumulative probability algorithm."""
        k_hat = 0
        sigma = 0.0
        fraction = 1.0
        exp = math.exp(-x_val)

        while True:
            sigma += exp * fraction
            if 1.0 - sigma < delta:
                return k_hat
            k_hat += 1
            fraction *= x_val / k_hat

    # Verified
    def find_k_thresholds_iterative(self, max_delay: float = 5.0, delta: float = 0.01,
                                    max_seconds_per_block: int = 100):
        from collections import defaultdict

        k_ranges = defaultdict(list)

        print(f"Verifying k thresholds for BPS < 1 (max_delay={max_delay}s, delta={delta})")
        print("=" * 60)

        for seconds_per_block in range(1, max_seconds_per_block + 1):
            bps = 1.0 / seconds_per_block
            x = 2 * max_delay * bps
            k = self.k_from_x(x)

            # Debug output for verification
            if seconds_per_block <= 30 or seconds_per_block % 10 == 0:  # Show first 30 and every 10th
                print(f"{seconds_per_block:3d}s/block: BPS={bps:.9f}, x={x:.9f}, k={k}")

            k_ranges[k].append(bps)

            # Convert to min/max ranges
        thresholds = {}
        for k in sorted(k_ranges.keys()):
            bps_list = k_ranges[k]
            thresholds[k] = {
                'min_bps': min(bps_list),
                'max_bps': max(bps_list),
                'min_seconds': int(1.0 / max(bps_list)),
                'max_seconds': int(1.0 / min(bps_list))
            }

        print("\nFinal thresholds:")
        for k in sorted(thresholds.keys()):
            r = thresholds[k]
            print(f"k={k:2d}: {r['min_seconds']:3d}-{r['max_seconds']:3d}s/block "
                  f"(BPS: {r['min_bps']:.9f}-{r['max_bps']:.9f})")

        return thresholds

    # Tested
    def sample_mining_interval(self, bps):
        # Time between blocks follows Exp(bps) distribution
        interval = np.random.exponential(1.0 / bps)
        return max(interval * 1000, 1)  # Convert to milliseconds, minimum 1ms

    def generate_blocks_continuous(self, duration_seconds, bps):
        blocks = []
        current_time = 0

        while current_time < duration_seconds * 1000:
            interval = self.sample_mining_interval(bps)
            current_time += interval
            if current_time < duration_seconds * 1000:
                blocks.append(current_time)

        return blocks

    #_________________________________________________
    #TODO modify this to use current dag tips for each iteration instead of starting from scratch each time
    def add_simulated_blocks(self, duration: float, bps: float, delay: float) -> List[dict]:
        """
        Simulate and return blocks continuing from current DAG tips.
        Uses existing tips as starting state, not empty genesis.
        """
        # Get current tips from existing DAG
        current_tips = {block.name for block in self.get_current_tips()}

        # Generate timestamps
        timestamps = self.generate_blocks_continuous(duration, bps)

        # Use modified create_blocks_from_timestamps that starts with current tips
        return self.create_blocks_from_timestamps_debug(
            timestamps, delay
        )

    @staticmethod
    def create_blocks_from_timestamps_debug(timestamps: List[float], actual_delay: float) -> List[dict]:
        """
        Debug version that prints detailed information about parent selection.
        Selects ALL childless blocks as parents.
        """
        timestamps.sort()
        blocks = []

        print(f"\n=== DEBUG: Starting block generation ===")
        print(f"Actual delay: {actual_delay}ms")
        print(f"Number of timestamps: {len(timestamps)}")

        for i, timestamp in enumerate(timestamps):
            print(f"\n--- Block {i} at {timestamp:.0f}ms ---")

            # Find blocks that are old enough (not parallel)
            visible_blocks = [
                block for block in blocks
                if block['timestamp'] <= timestamp - actual_delay
            ]
            print(
                f"Visible blocks (timestamp <= {timestamp - actual_delay:.0f}ms): {[b['hash'] for b in visible_blocks]}")

            # Find tips among visible blocks (blocks with no children)
            tips = set()
            for candidate in visible_blocks:
                # Check if any visible block has this candidate as parent
                has_child = any(candidate['hash'] in other['parents'] for other in visible_blocks)
                if not has_child:
                    tips.add(candidate['hash'])

            print(f"Tips among visible blocks (no children): {tips}")

            # Select ALL tips as parents
            if tips:
                parents = list(tips)  # Select ALL childless blocks
                print(f"Selected ALL tips as parents: {parents}")
            elif visible_blocks:
                # Fallback to most recent visible block
                parents = [visible_blocks[-1]['hash']]
                print(f"No tips found, using most recent visible: {parents}")
            else:
                parents = []
                print("No visible blocks, creating genesis")

                # Create new block
            new_block = {
                'hash': f"block_{i}",
                'timestamp': timestamp,
                'parents': parents
            }
            blocks.append(new_block)
            print(f"Created {new_block['hash']} with parents {parents}")

        print(f"\n=== SUMMARY ===")
        avg_parents = sum(len(b['parents']) for b in blocks) / len(blocks) if blocks else 0
        print(f"Total blocks: {len(blocks)}")
        print(f"Average parents per block: {avg_parents:.2f}")

        return blocks
    #_________________________________________________

    @staticmethod
    def get_tips_at_time(tip_history: List[tuple], target_time: float) -> set:
        """Find tips at a specific time using binary search."""
        import bisect
        idx = bisect.bisect_right(tip_history, (target_time, set())) - 1
        return tip_history[idx][1] if idx >= 0 else set()

    def create_blocks_from_timestamps(self, timestamps: List[float], actual_delay: float) -> List[dict]:
        timestamps.sort()
        blocks = []
        tips = set()
        tip_history = []  # Store (timestamp, tips) pairs
        all_blocks = []

        # Initialize with empty tips at time 0
        tip_history.append((0, set()))

        for i, timestamp in enumerate(timestamps):
            # Find visible blocks
            visible_blocks = [
                block for block in all_blocks
                if block['timestamp'] <= timestamp - actual_delay
            ]

            # Get historical tips
            historical_tips = self.get_tips_at_time(tip_history, timestamp - actual_delay)
            visible_parents = [
                block for block in visible_blocks
                if block['hash'] in historical_tips
            ]

            # Create block
            if not visible_parents and visible_blocks:
                visible_parents = [visible_blocks[-1]]

            parents = [p['hash'] for p in visible_parents] if visible_parents else []

            new_block = {
                'hash': f"block_{i}",
                'timestamp': timestamp,
                'parents': parents
            }

            blocks.append(new_block)
            all_blocks.append(new_block)

            # Update tips FIRST
            for parent_hash in parents:
                tips.discard(parent_hash)
            tips.add(new_block['hash'])

            # THEN store in history
            tip_history.append((timestamp, tips.copy()))

        return blocks

    # Tested
    def test_block_generation(self, duration_in_seconds: float, bps_float: float, actual_delay_in_ms: float):
        """Test function to visualize block generation and relationships."""

        print("=" * 60)
        print("Testing Block Generation with Network Delay Simulation")
        print("=" * 60)

        # Test parameters
        duration_seconds = duration_in_seconds
        bps = bps_float  # block per second
        actual_delay = actual_delay_in_ms  # network delay in milliseconds

        print(f"\nParameters:")
        print(f"  Duration: {duration_seconds}s")
        print(f"  Block rate: {bps} BPS (1 block per {1 / bps}s)")
        print(f"  Network delay: {actual_delay}ms")
        print()

        # Generate timestamps
        timestamps = self.generate_blocks_continuous(duration_seconds, bps)
        print(f"Generated {len(timestamps)} block timestamps:")
        for i, ts in enumerate(timestamps):
            print(f"  Block {i}: {ts:.0f}ms")
        print()

        # Convert to blocks with relationships
        blocks = self.create_blocks_from_timestamps(timestamps, actual_delay)

        # Display block relationships
        print("Block Relationships:")
        print("-" * 40)
        for block in blocks:
            print(f"Block {block['hash']}:")
            print(f"  Timestamp: {block['timestamp']:.0f}ms")
            if block['parents']:
                print(f"  Parents: {', '.join(block['parents'])}")
            else:
                print(f"  Parents: None (genesis)")
            print()

            # Summary statistics
        print(f"Summary:")
        print(f"  Total blocks: {len(blocks)}")
        avg_parents = sum(len(b['parents']) for b in blocks) / len(blocks) if blocks else 0
        print(f"  Average parents per block: {avg_parents:.2f}")

        return blocks

    def create_blocks_from_simulator_list(
            self,
            simulator_blocks: List[dict]
    ) -> List[KaspaLogicalBlock]:
        """
        Convert simulator block dictionaries to actual KaspaLogicalBlock objects.
        The simulator list is already ordered by creation time.
        """
        # Get tips once at the start (ensures genesis exists)
        initial_tips = self.get_current_tips()

        # Map to track hash -> actual block
        block_map = {}
        created_blocks = []

        for block_dict in simulator_blocks:
            block_hash = block_dict['hash']
            block_timestamp = block_dict['timestamp']
            parent_hashes = block_dict.get('parents', [])

            # Resolve parent hashes to actual blocks
            parents = []
            if parent_hashes:
                # Normal case: has parents from simulator
                for parent_hash in parent_hashes:
                    if parent_hash in block_map:
                        parents.append(block_map[parent_hash])
                    else:
                        raise ValueError(f"Parent block {parent_hash} not found for block {block_hash}")
            else:
                # Empty parents case: use initial tips
                parents = initial_tips

                # Create the block using existing infrastructure
            placeholder = self.queue_block(parents=parents, name=block_hash, timestamp=block_timestamp)
            self.catch_up()  # Execute the creation

            actual_block = placeholder.actual_block
            block_map[block_hash] = actual_block
            created_blocks.append(actual_block)

        return created_blocks
    ####################
    # Generate DAG from parameters  #TODO this does not correctly color blocks when creating since DAG uses a predetermined k set in config #TODO replaced by sim?
    ####################

    def calculate_lambda_from_network(self, bps: float, delay: float) -> float:
        """Calculate λ from network conditions.

        Args:
            bps: Blocks per second (network block rate)
            delay: Network delay in seconds

        Returns:
            λ parameter for Poisson distribution
        """
        # In Kaspa, the effective block rate during network delay is λ * delay
        # This represents the expected number of blocks created within one network delay window
        return bps * delay

    def calculate_k_from_network(self, bps: float, max_delay: float, delta: float = 0.01) -> int:
        """Calculate k using Kaspa's formula."""
        x = 2 * max_delay * bps
        return self.k_from_x(x, delta)

    def generate_kaspa_dag(
            self,
            num_rounds: int,
            bps: float,
            max_delay: float,
            actual_delay: float,
            delta: float = 0.01
    ):
        """Generate DAG using Kaspa's network-based approach."""
        # Get current tips (auto-creates genesis if needed)
        current_tips = self.get_current_tips()
        previous_tips = []

        # Calculate network parameters
        k = self.calculate_k_from_network(bps, max_delay, delta)
        lambda_blocks = self.calculate_lambda_from_network(bps, actual_delay)

        print(f"Network: BPS={bps}, Max delay={max_delay}s, Actual delay={actual_delay}s")
        print(f"Calculated: k={k}, λ={lambda_blocks:.2f}")

        for round_num in range(num_rounds):
            # Sample number of blocks for this round
            num_blocks = np.random.poisson(lambda_blocks)
            num_blocks = max(1, num_blocks)  # Ensure at least one block

            # Create blocks for this round
            new_placeholders = []

            for _ in range(num_blocks):
                # ALWAYS use current tips for parent selection
                num_parents = min(len(current_tips), np.random.randint(1, 3))
                parents = list(np.random.choice(current_tips, size=num_parents, replace=False))

                placeholder = self.queue_block(parents=parents, timestamp=0)
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

    ####################
    # Generate DAG from k #TODO replaced by sim?
    ####################

    def calculate_params_from_k(self, target_k: int, fixed_delay: float = None,
                                fixed_bps: float = None, max_delay: float = 5.0) -> dict:
        """Calculate network parameters that would result in the target k."""
        thresholds = self.find_k_thresholds_iterative(max_delay=max_delay)

        if target_k not in thresholds:
            raise ValueError(f"k={target_k} not found in thresholds")

        k_range = thresholds[target_k]
        # Use the passed max_delay parameter
        x = 2 * max_delay * k_range['min_bps']

        if fixed_delay is not None:
            # Calculate BPS needed: x = 2Dλ -> λ = x/(2D)
            bps = x / (2 * fixed_delay)
            return {
                'k': target_k,
                'delay': fixed_delay,
                'bps': bps,
                'x': x
            }
        elif fixed_bps is not None:
            # Calculate delay needed: x = 2Dλ -> D = x/(2λ)
            delay = x / (2 * fixed_bps)
            return {
                'k': target_k,
                'delay': delay,
                'bps': fixed_bps,
                'x': x
            }
        else:
            # Default configuration
            default_delay = 5.0  # NETWORK_DELAY_BOUND
            return {
                'k': target_k,
                'delay': default_delay,
                'bps': k_range['min_bps'],
                'x': x
            }

    def generate_dag_from_k_continuous(
            self,
            duration_seconds: int,
            target_k: int,
            actual_delay_multiplier: float = 1.0,
    ):
        """Generate DAG using continuous time simulation like Kaspa."""
        # Get parameters
        params = self.calculate_params_from_k(target_k)
        bps = params['bps']

        # Generate block timestamps
        block_times = self.generate_blocks_continuous(duration_seconds, bps)

        print(f"Generated {len(block_times)} blocks over {duration_seconds}s")
        print(f"Expected blocks: {duration_seconds * bps:.1f}")

        # Create blocks at each timestamp
        current_tips = self.get_current_tips()

        for block_time in block_times:
            # Use current tips as parents
            parents = current_tips.copy()

            placeholder = self.queue_block(parents=parents, timestamp=0)
            self.catch_up()

            # Update tips
            block = placeholder.actual_block
            for parent in block.parents:
                if parent in current_tips:
                    current_tips.remove(parent)
            current_tips.append(block)

    def generate_dag_from_k(
            self,
            num_rounds: int,
            target_k: int,
            actual_delay_multiplier: float = 1.0,
    ):
        """Generate DAG using parameters derived from target k."""
        # Get current tips (auto-creates genesis if needed)
        current_tips = self.get_current_tips()
        previous_tips = []

        # Get base parameters for target k
        params = self.calculate_params_from_k(target_k)
        max_delay = params['delay']
        bps = params['bps']

        # Actual delay can be different from max delay
        actual_delay = max_delay * actual_delay_multiplier

        # Calculate λ for actual conditions
        lambda_blocks = bps * actual_delay

        print(f"Target k={target_k}: BPS={bps:.2f}, Max delay={max_delay}s, Actual delay={actual_delay}s")
        print(f"λ={lambda_blocks:.2f}")

        # Generate blocks with proper tip tracking
        for round_num in range(num_rounds):
            # Sample number of blocks for this round
            num_blocks = max(1, np.random.poisson(lambda_blocks))

            # Create blocks for this round
            new_placeholders = []

            for _ in range(num_blocks):
                # EVERY new block references ALL blocks from previous round
                parents = current_tips.copy()  # Use all current tips as parents

                placeholder = self.queue_block(parents=parents, timestamp=0)
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

    ####################
    # Old Generate DAG #TODO this can be removed/replaced
    ####################

    def generate_dag(
            self,
            num_rounds: int,
            lambda_parallel: float = 1.0,
            chain_prob: float = 0.7,
            old_tip_prob: float = 0.1,
    ):
        """Generate a DAG with Poisson-distributed parallel blocks."""

        # Start from current tips (auto-creates genesis if needed)
        current_tips = self.get_current_tips()
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
                placeholder = self.queue_block(parents=parents, timestamp=0)
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


class KaspaConfigManager:
    """Manages configuration for a KaspaDAG instance."""

    def __init__(self, user_config: _KaspaConfigInternal):
        self.config = user_config

    def apply_config(self, user_config: KaspaConfig, is_locked: bool = False) -> None:
        """Apply typed config with genesis lock protection."""
        critical_params = {'k'}

        for key, value in user_config.items():
            if key in critical_params and is_locked:
                logger.warning(
                    f"Cannot change {key} after blocks have been added. "
                    "DAG parameters must remain consistent throughout the DAG lifecycle."
                )
                continue

            if hasattr(self.config, key):
                setattr(self.config, key, value)
                if hasattr(self.config, '__post_init__'):
                    self.config.__post_init__()

    def set_k(self, k: int, is_locked: bool = False) -> None:
        """Set k with lock protection."""
        if is_locked:
            logger.warning(
                "Cannot change k after blocks have been added. "
                "DAG parameters must remain consistent throughout the DAG lifecycle."
            )
            return
        self.config.k = k
        if hasattr(self.config, '__post_init__'):
            self.config.__post_init__()

    #Complete
class BlockPlaceholder:
    """Placeholder for a block that will be created later."""

    def __init__(self, dag, timestamp, parents, name):
        self.dag = dag
        self.timestamp = timestamp
        self.parents = parents
        self.name = name
        self.actual_block = None  # Will be set automatically when created

    def __getattr__(self, attr):
        """Automatically delegate to actual_block once it's created."""
        if self.actual_block is None:
            raise ValueError(f"Block {self.name} hasn't been created yet - call next_step() first")
        return getattr(self.actual_block, attr)

#Complete
class BlockManager:
    """Handles block creation, queuing, and workflow management."""

    def __init__(self, dag):
        self.dag = dag

    def queue_block(self, timestamp, parents=None, name=None) -> BlockPlaceholder:
        """Queue block creation, return placeholder that auto-resolves."""

        placeholder = BlockPlaceholder(self, timestamp, parents, name)

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
            block_name = name if name else self.dag.retrieval.generate_block_name(resolved_parents)
            position = self._calculate_dag_position(resolved_parents)

            block = KaspaLogicalBlock(
                name=block_name,
                timestamp=timestamp,
                parents=resolved_parents if resolved_parents else [],
                position=position,
                config=self.dag.config,
            )

            self.dag.blocks[block_name] = block
            self.dag.all_blocks.append(block)

            if not resolved_parents:
                self.genesis = block

            # AUTOMATICALLY link placeholder to actual block
            placeholder.actual_block = block

            # Animate it
            self._animate_block_creation(block)

            return block

        self.dag.workflow_steps.append(create_and_animate_block)

        # Queue repositioning
        def reposition_column():
            if self.dag.all_blocks:
                x_pos = self.dag.all_blocks[-1].visual_block.square.get_center()[0]
                self._animate_dag_repositioning({x_pos})

        reposition_column.is_repositioning = True
        self.dag.workflow_steps.append(reposition_column)

        return placeholder

    def add_block(self, parents=None, name=None) -> KaspaLogicalBlock:
        """Create and animate a block immediately."""
        placeholder = self.queue_block(parents=parents, name=name, timestamp=0)
        self.next_step()  # Execute block creation TODO does this break IF there is a pending queue of blocks when this is called
        self.next_step()  # Execute repositioning
        return placeholder.actual_block  # Return actual block, not placeholder

    def add_blocks(self, blocks_data: List[tuple[Optional[List[BlockPlaceholder | KaspaLogicalBlock]], Optional[str]]]) -> List[KaspaLogicalBlock]:
        """Add multiple blocks and complete all animations automatically."""
        placeholders = []

        # Queue all blocks
        for parents, name in blocks_data:
            placeholder = self.queue_block(parents, name)
            placeholders.append(placeholder)

            # Execute all queued steps
        self.catch_up()

        # Return actual blocks
        return [p.actual_block for p in placeholders]

    def next_step(self) -> None:
        """Execute the next queued function, skipping empty repositioning."""
        if not self.dag.workflow_steps:
            return None

        func = self.dag.workflow_steps.pop(0)

        # Check if this is a marked repositioning function
        if getattr(func, 'is_repositioning', False):
            if self.dag.all_blocks:
                x_pos = self.dag.all_blocks[-1].visual_block.get_center()[0]
                column_blocks = [
                    b for b in self.dag.all_blocks
                    if abs(b.visual_block.get_center()[0] - x_pos) < 0.01
                ]

                if column_blocks:
                    current_ys = [b.visual_block.get_center()[1] for b in column_blocks]
                    current_center_y = (max(current_ys) + min(current_ys)) / 2
                    shift_y = self.dag.config.genesis_y - current_center_y

                    # Skip if negligible shift
                    if abs(shift_y) < 0.01:
                        return self.next_step()

        func()
        return None

    def catch_up(self):
        """Execute all queued functions in sequence."""
        while self.dag.workflow_steps:
            self.next_step()

    def _calculate_dag_position(self, parents: Optional[List[KaspaLogicalBlock]]) -> tuple[float, float]:
        """Calculate position based on rightmost parent and topmost neighbor."""
        if not parents:
            return self.dag.config.genesis_x, self.dag.config.genesis_y

        # Use rightmost parent for x-position
        rightmost_parent = max(parents, key=lambda p: p.visual_block.square.get_center()[0])
        parent_pos = rightmost_parent.visual_block.square.get_center()
        x_position = parent_pos[0] + self.dag.config.horizontal_spacing

        # Find blocks at same x-position
        same_x_blocks = [
            b for b in self.dag.all_blocks
            if abs(b.visual_block.square.get_center()[0] - x_position) < 0.01
        ]

        if not same_x_blocks:
            # First block at this x - use gen_y y
            y_position = self.dag.config.genesis_y
        else:
            # Stack above topmost neighbor
            topmost_y = max(b.visual_block.get_center()[1] for b in same_x_blocks)
            y_position = topmost_y + self.dag.config.vertical_spacing

        return x_position, y_position

    def _animate_dag_repositioning(self, x_positions: Set[float]):
        """Center columns of blocks around genesis y-position."""
        if not x_positions:
            return

        animations = []
        genesis_y = self.dag.config.genesis_y

        for x_pos in x_positions:
            # Find all blocks at this x-position
            column_blocks = [
                b for b in self.dag.all_blocks
                if abs(b.visual_block.get_center()[0] - x_pos) < 0.01
            ]

            if not column_blocks:
                continue

            # Calculate current center and target shift
            current_ys = [b.visual_block.get_center()[1] for b in column_blocks]
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
            self.dag.scene.play(*animations)

    def _animate_block_creation(self, block: KaspaLogicalBlock):
        """Animate the creation of a block and its lines."""
        self.dag.shift_camera_to_follow_blocks()
        self.dag.scene.play(block.visual_block.create_with_lines())

class DAGGenerator:
    """Handles all DAG generation methods and network parameter calculations."""

    def __init__(self, dag):
        self.dag = dag

    def k_from_x(self, x_val: float, delta: float = 0.01) -> int:
        """Move k calculation methods here"""

    def find_k_thresholds_iterative(
            self,
            max_delay: float = 5.0,
            delta: float = 0.01,
            max_seconds_per_block: int = 100
    ):
        """Move threshold finding logic here"""

    def generate_kaspa_dag(
            self,
            num_rounds: int,
            bps: float,
            max_delay: float,
            actual_delay: float,
            delta: float = 0.01
    ):
        """Move network-based generation here"""

    def generate_dag_from_k(
            self,
            num_rounds: int,
            target_k: int,
            actual_delay_multiplier: float = 1.0
    ):
        """Move k-based generation here"""

#Complete
class Movement:
    """Handles block/camera movement and animation deduplication."""

    def __init__(self, dag):
        self.dag = dag

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
        self.dag.scene.play(*animations)

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

    def shift_camera_to_follow_blocks(self):
        """Shift camera to keep rightmost blocks in view."""
        if not self.dag.all_blocks:
            return

            # Use visual_block property instead of _visual
        rightmost_x = max(block.visual_block.get_center()[0] for block in self.dag.all_blocks)

        margin = self.dag.config.horizontal_spacing * 2
        current_center = self.dag.scene.camera.frame.get_center()
        frame_width = config["frame_width"]
        right_edge = current_center[0] + (frame_width / 2)

        if rightmost_x > right_edge - margin:
            shift_amount = rightmost_x - (right_edge - margin)
            self.dag.scene.play(
                self.dag.scene.camera.frame.animate.shift(RIGHT * shift_amount),
                run_time=self.dag.config.camera_follow_time
            )

#Complete
class BlockRetrieval:
    """Handles block lookup, naming, and cone calculations."""

    def __init__(self, dag):
        self.dag = dag

    @staticmethod
    def get_round(block: KaspaLogicalBlock) -> int:
        """Helper to get round number for a block."""
        if not block.parents:
            return 0
        round_num = 1
        current = block.parents[0]
        while current.parents:
            current = current.parents[0]
            round_num += 1
        return round_num

    def get_block(self, name: str) -> Optional[KaspaLogicalBlock]:
        """Retrieve a block by name with fuzzy matching support."""
        # Try exact match first
        if name in self.dag.blocks:
            return self.dag.blocks[name]

        # If empty, return None
        if not self.dag.all_blocks:
            return None

        # Extract round number and find closest
        import re
        match = re.search(r'B?(\d+)', name)
        if not match:
            return self.dag.all_blocks[-1]

        target_round = int(match.group(1))
        max_round = max(self.get_round(b) for b in self.dag.all_blocks)
        actual_round = min(target_round, max_round)

        # Find first block at this round
        for block in self.dag.all_blocks:
            if self.get_round(block) == actual_round:
                return block

        return self.dag.all_blocks[-1]

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
            b for b in self.dag.all_blocks
            if b != block and b not in past and b not in future
        ]

    def get_current_tips(self) -> List[KaspaLogicalBlock]:
        """Get current DAG tips (blocks without children)."""
        # If no blocks exist, create genesis and return it
        if not self.dag.all_blocks:
            genesis = self.dag.add_block()
            return [genesis]

        # Find all blocks that are parents of other blocks
        non_tips = set()
        for block in self.dag.all_blocks:
            non_tips.update(block.parents)

        # Tips are blocks that are not parents of any other block
        tips = [block for block in self.dag.all_blocks if block not in non_tips]

        # There will always be at least one tip (genesis or others)
        return tips if tips else [self.dag.genesis]

    def generate_block_name(self, parents: List[KaspaLogicalBlock]) -> str:
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
            b for b in self.dag.all_blocks
            if b != self.dag.genesis and self.get_round(b) == round_number
        ]

        # Generate name
        if len(blocks_at_round) == 0:
            return f"B{round_number}"
        else:
            # Subtract 1 to get correct suffix: 1 existing block → 'a', 2 → 'b', etc.
            suffix = chr(ord('a') + len(blocks_at_round) - 1)
            return f"B{round_number}{suffix}"

#Complete
class RelationshipHighlighter:
    def __init__(self, dag):
        self.dag = dag
        self.currently_highlighted_block: Optional[KaspaLogicalBlock] = None
        self.flash_lines: List = []


    def highlight_past(self, focused_block: KaspaLogicalBlock) -> None:
        """Highlight a block's past cone with child-to-parent line animations."""
        self.reset_highlighting()

        context_blocks = self.dag.get_past_cone(focused_block)
        self.flash_lines = self._highlight_with_context(
            focused_block, context_blocks, relationship_type="past"
        )

    def highlight_future(self, focused_block: KaspaLogicalBlock) -> None:
        """Highlight a block's future cone with child-to-parent line animations."""
        self.reset_highlighting()

        context_blocks = self.dag.get_future_cone(focused_block)
        self.flash_lines = self._highlight_with_context(
            focused_block, context_blocks, relationship_type="future"
        )

    def highlight_anticone(self, focused_block: KaspaLogicalBlock) -> None:
        """Highlight a block's anticone with child-to-parent line animations."""
        self.reset_highlighting()

        context_blocks = self.dag.get_anticone(focused_block)
        self.flash_lines = self._highlight_with_context(
            focused_block, context_blocks, relationship_type="anticone"
        )

    @staticmethod
    def _get_lines_to_highlight(focused_block: KaspaLogicalBlock, context_blocks: List[KaspaLogicalBlock], relationship_type: str) -> Set[int]:
        """Determine which lines should remain highlighted based on relationship type (past/future/anticone).

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

    def _highlight_with_context(self, focused_block: KaspaLogicalBlock, context_blocks: Optional[List[KaspaLogicalBlock]] = None, relationship_type: str = "anticone") -> List:
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
        for block in self.dag.all_blocks:
            if block not in context_set and block != focused_block:
                # Fade the block itself
                fade_animations.extend(block.visual_block.create_fade_animation())

                # Selectively fade lines NOT in lines_to_keep
                for parent_line in block.visual_block.parent_lines:
                    if id(parent_line) not in lines_to_keep:
                        fade_animations.append(
                            parent_line.animate.set_stroke(opacity=self.dag.config.fade_opacity)
                        )

        # Fade focused block's parent lines if parents not in context
        if focused_block.visual_block.parent_lines:
            for parent_line, parent in zip(focused_block.visual_block.parent_lines, focused_block.parents):
                if parent not in context_set:
                    fade_animations.append(
                        parent_line.animate.set_stroke(opacity=self.dag.config.fade_opacity)
                    )

        # Also fade lines within context blocks that should not be highlighted
        for block in context_blocks:
            for parent_line in block.visual_block.parent_lines:
                if id(parent_line) not in lines_to_keep:
                    fade_animations.append(
                        parent_line.animate.set_stroke(opacity=self.dag.config.fade_opacity)
                    )

        if fade_animations:
            self.dag.scene.play(*fade_animations)

        # Add pulsing highlight to focused block
        pulse_updater = focused_block.visual_block.create_pulsing_highlight()
        focused_block.visual_block.square.add_updater(pulse_updater)

        # Highlight context blocks
        context_animations = []
        for block in context_blocks:
            context_animations.append(block.visual_block.create_highlight_animation())

        if context_animations:
            self.dag.scene.play(*context_animations)
        else:
            self.dag.scene.play(Wait(0.01))

        # Flash lines that are in lines_to_keep
        flash_lines = []
        if self.dag.config.flash_connections:
            # Flash lines within context blocks (only those in lines_to_keep)
            for block in context_blocks:
                for parent_line in block.visual_block.parent_lines:
                    if id(parent_line) in lines_to_keep:
                        # Create flash animation for this specific line
                        flash_copy = parent_line.copy()
                        flash_copy.set_stroke(
                            color=self.dag.config.highlight_line_color,
                            width=self.dag.config.line_stroke_width
                        )
                        from manim import ShowPassingFlash, cycle_animation
                        cycle_animation(
                            ShowPassingFlash(
                                flash_copy,
                                time_width=0.5,
                                run_time=self.dag.config.highlight_line_cycle_time
                            )
                        )
                        self.dag.scene.add(flash_copy)
                        flash_lines.append(flash_copy)

            # Flash focused block's lines if parents in context
            if focused_block.visual_block.parent_lines:
                for parent in focused_block.parents:
                    if parent in context_set:
                        block_flash_lines = focused_block.visual_block.create_directional_line_flash()
                        for flash_line in block_flash_lines:
                            self.dag.scene.add(flash_line)
                            flash_lines.append(flash_line)
                        break

            # Flash lines FROM non-context blocks TO context blocks (for anticone)
            if relationship_type in "anticone":
                for block in self.dag.all_blocks:
                    if block not in context_set and block != focused_block:
                        for parent_line, parent in zip(block.visual_block.parent_lines, block.parents):
                            if id(parent_line) in lines_to_keep:
                                # Create flash animation
                                flash_copy = parent_line.copy()
                                flash_copy.set_stroke(
                                    color=self.dag.config.highlight_line_color,
                                    width=self.dag.config.line_stroke_width
                                )
                                from manim import ShowPassingFlash, cycle_animation
                                cycle_animation(
                                    ShowPassingFlash(
                                        flash_copy,
                                        time_width=0.5,
                                        run_time=self.dag.config.highlight_line_cycle_time
                                    )
                                )
                                self.dag.scene.add(flash_copy)
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
            self.dag.scene.remove(flash_line)
        self.flash_lines = []

        # Reset all blocks using visual block methods
        reset_animations = []
        for block in self.dag.all_blocks:
            reset_animations.extend(block.visual_block.create_reset_animation())
            reset_animations.extend(block.visual_block.create_line_reset_animations())

        self.currently_highlighted_block = None

        if reset_animations:
            self.dag.scene.play(*reset_animations)

class GhostDAGHighlighter:
    def __init__(self, dag):
        self.dag = dag

    def animate_ghostdag_process(
            self,
            context_block: KaspaLogicalBlock | str,
            narrate: bool = True,
            step_delay: float = 1.0
    ) -> None:
        """Animate the complete GhostDAG process for a context block."""
        if isinstance(context_block, str):
            context_block = self.dag.get_block(context_block)
            if context_block is None:
                return

        try:
            # Step 1: Fade to context inclusive past cone
            if narrate:
                self.dag.scene.narrate("Fade all except past cone of context block(inclusive)")
            self._ghostdag_fade_to_past(context_block)
            self.dag.scene.wait(step_delay)

            # Step 2: Show parents
            if narrate:
                self.dag.scene.narrate("Highlight all parent blocks")
            self._ghostdag_highlight_parents(context_block)
            self.dag.scene.wait(step_delay)

            # Step 3: Show selected parent
            if narrate:
                self.dag.scene.narrate("Selected parent chosen with highest blue score(with uniform tiebreaking)")
            self._ghostdag_show_selected_parent(context_block)
            self.dag.scene.wait(step_delay)

            # Step 4: Show mergeset
            if narrate:
                self.dag.scene.narrate("Creating mergeset from past cone differences")
            self._ghostdag_show_mergeset(context_block)
            self.dag.scene.wait(step_delay)

            # Step 5: Show ordering #TODO create copies of blocks as ordering them, and line them up in order
            if narrate:
                self.dag.scene.narrate("Ordering mergeset by blue score and hash")
            self._ghostdag_show_ordering(context_block)
            self.dag.scene.wait(step_delay)

            # Step 6: Blue candidate process
            if narrate:
                self.dag.scene.narrate("Evaluating blue candidates (k-parameter constraint)") #TODO highlight(BLUE) blue blocks in anticone of blue candidate OR show candidate.SP k-cluster
            self._ghostdag_show_blue_process(context_block)
            self.dag.scene.wait(step_delay)

        finally:
            # Always cleanup
            if narrate:
                self.dag.scene.clear_narrate()
                self.dag.scene.clear_caption()
            self.dag.reset_highlighting()


    def _ghostdag_fade_to_past(self, context_block: KaspaLogicalBlock):
        """Fade everything not in context block's past cone."""
        context_inclusive_past_blocks = set(context_block.get_past_cone())
        context_inclusive_past_blocks.add(context_block)

        fade_animations = []
        for block in self.dag.all_blocks:
            if block not in context_inclusive_past_blocks:
                fade_animations.extend(block.visual_block.create_fade_animation())
                # Also fade lines from these blocks
                for line in block.visual_block.parent_lines:
                    fade_animations.append(
                        line.animate.set_stroke(opacity=self.dag.config.fade_opacity)
                    )

        if fade_animations:
            self.dag.scene.play(*fade_animations)

    def _ghostdag_highlight_parents(self, context_block: KaspaLogicalBlock):
        """Highlight all parents of context block."""
        if not context_block.parents:
            return

        parent_animations = []

        # Highlight all parent blocks
        for parent in context_block.parents:
            parent_animations.append(
                parent.visual_block.square.animate.set_style(
                    stroke_color=self.dag.config.ghostdag_parent_stroke_highlight_color,
                    stroke_width=self.dag.config.ghostdag_parent_stroke_highlight_width
                )
            )

        # Highlight all parent lines (they always connect to parents)
        for line in context_block.visual_block.parent_lines:
            parent_animations.append(
                line.animate.set_stroke(
                    color=self.dag.config.ghostdag_parent_line_highlight_color
                )
            )

        self.dag.scene.play(*parent_animations)

        #Change lines back to normal
        return_lines_animations = context_block.visual_block.create_line_reset_animations()
        self.dag.scene.play(*return_lines_animations)

    def _ghostdag_show_selected_parent(self, context_block: KaspaLogicalBlock):
        """Highlight selected parent and fade its past cone."""
        if not context_block.selected_parent:
            return

        selected = context_block.selected_parent

        # Highlight selected parent with unique style
        self.dag.scene.play(
            selected.visual_block.square.animate.set_style(
                fill_color=self.dag.config.ghostdag_selected_parent_fill_color,
                fill_opacity=self.dag.config.ghostdag_selected_parent_opacity,
                stroke_width=self.dag.config.ghostdag_selected_parent_stroke_width,
                stroke_color=self.dag.config.ghostdag_selected_parent_stroke_color,
            )
        )

        # Fade selected parent's past cone
        selected_past = set(selected.get_past_cone())
        fade_animations = []
        for block in selected_past:
            fade_animations.extend(block.visual_block.create_fade_animation())
            for line in block.visual_block.parent_lines:
                fade_animations.append(
                    line.animate.set_stroke(opacity=self.dag.config.fade_opacity)
                )
        # Fade selected parents parent lines as well
        for line in context_block.selected_parent.parent_lines:
            fade_animations.append(
                line.animate.set_stroke(opacity=self.dag.config.fade_opacity)
            )
        self.dag.scene.play(*fade_animations)

    def _ghostdag_show_mergeset(self, context_block: KaspaLogicalBlock):
        """Visualize mergeset creation."""
        mergeset = context_block.get_sorted_mergeset_without_sp()

        # Early return if no blocks to animate
        if not mergeset:
            return

        # Highlight mergeset blocks
        mergeset_animations = []
        for block in mergeset:
            mergeset_animations.append(
                block.visual_block.square.animate.set_style(
                    fill_color=self.dag.config.ghostdag_mergeset_color,
                    stroke_width=self.dag.config.ghostdag_mergeset_stroke_width
                )
            )

        self.dag.scene.play(*mergeset_animations)

    def _ghostdag_show_ordering(self, context_block: KaspaLogicalBlock):
        """Show sorted ordering without temporary text objects."""
        sorted_mergeset = context_block.get_sorted_mergeset_without_sp()

        # Just highlight in sequence, no text overlays
        for i, block in enumerate(sorted_mergeset):
            self.dag.scene.play(
                Indicate(block.visual_block.square, scale=1.1),
                run_time=1
            )
            self.dag.scene.wait(0.1)

    #TODO clean this up AND check, it appears the first check misses sp as blue
    def _ghostdag_show_blue_process(self, context_block: KaspaLogicalBlock):
        """Animate blue evaluation with blue anticone visualization."""
        blue_candidates = context_block.get_sorted_mergeset_without_sp()
        total_view = set(context_block.get_past_cone())
        total_view.add(context_block)

        # Start with selected parent's local POV as baseline
        local_blue_status = context_block.selected_parent.ghostdag.local_blue_pov.copy()
        local_blue_status[context_block.selected_parent] = True

        # Initialize all candidates as not blue locally
        for candidate in blue_candidates:
            local_blue_status[candidate] = False

        for candidate in blue_candidates:
            # Show candidate being evaluated
            self.dag.scene.play(
                Indicate(candidate.visual_block.square, scale=1.2),
                run_time=1.0
            )

            # Get blue blocks from CURRENT local perspective
            blue_blocks = {block for block, is_blue in local_blue_status.items() if is_blue}

            # FIRST CHECK: Highlight blue blocks in candidate's anticone
            candidate_anticone = context_block.get_anticone(candidate, total_view)
            blue_in_anticone = candidate_anticone & blue_blocks

            # Highlight first check
            anticone_animations = []
            for block in blue_in_anticone:
                anticone_animations.append(
                    block.visual_block.square.animate.set_style(
                        fill_color=self.dag.config.ghostdag_blue_color,
                        stroke_width=8,
                        stroke_opacity=0.9,
                        fill_opacity=0.9,
                    )
                )

            if anticone_animations:
                self.dag.scene.play(*anticone_animations)
                self.dag.scene.wait(0.5)
                # Reset first check highlighting
                reset_animations = []
                for block in blue_in_anticone:
                    reset_animations.append(
                        block.visual_block.create_fade_animation()
                    )
                self.dag.scene.play(*reset_animations)

            # SECOND CHECK: For each blue block, check if candidate would exceed k in its anticone
            second_check_failed = False
            for blue_block in blue_blocks:
                blue_anticone = context_block.get_anticone(blue_block, total_view)
                if candidate in blue_anticone:
                    # Highlight the blue block being checked
                    self.dag.scene.play(
                        blue_block.visual_block.square.animate.set_style(
                            stroke_color=YELLOW,
                            stroke_width=10,
                            stroke_opacity=1.0
                        )
                    )

                    # Highlight blue blocks in this blue block's anticone
                    affected_blue_in_anticone = blue_anticone & blue_blocks
                    second_check_animations = []

                    # Highlight existing blue blocks in anticone
                    for block in affected_blue_in_anticone:
                        if block != blue_block:  # Don't highlight the blue block itself
                            second_check_animations.append(
                                block.visual_block.square.animate.set_style(
                                    fill_color=self.dag.config.ghostdag_blue_color,
                                    stroke_width=6,
                                    stroke_opacity=0.8,
                                    fill_opacity=0.8,
                                )
                            )

                    # Highlight candidate as it would be added
                    second_check_animations.append(
                        candidate.visual_block.square.animate.set_style(
                            stroke_color=ORANGE,
                            stroke_width=8,
                            stroke_opacity=1.0,
                        )
                    )

                    if second_check_animations:
                        self.dag.scene.play(*second_check_animations)
                        self.dag.scene.wait(0.3)

                        # Check if this would exceed k
                        blue_count = len(affected_blue_in_anticone) + 1  # +1 for candidate
                        if blue_count > context_block.kaspa_config.k:
                            second_check_failed = True
                            self.dag.scene.caption(
                                f"Second check FAILED: {blue_block.name} would have {blue_count} $>$ k blues in anticone")
                            # Flash red to indicate failure
                            self.dag.scene.play(
                                blue_block.visual_block.square.animate.set_fill(color=RED, opacity=0.5),
                                candidate.visual_block.square.animate.set_fill(color=RED, opacity=0.5)
                            )
                        else:
                            self.dag.scene.caption(
                                f"Second check PASSED: {blue_block.name} would have {blue_count} $<$= k blues in anticone")

                        self.dag.scene.wait(0.5)

                        # Reset second check highlighting
                        reset_animations = []
                        for block in affected_blue_in_anticone:
                            if block != blue_block:
                                reset_animations.append(
                                    block.visual_block.create_fade_animation()
                                )
                        reset_animations.append(
                            blue_block.visual_block.square.animate.set_style(
                                fill_color=self.dag.config.ghostdag_blue_color,
                                stroke_width=2,
                                stroke_opacity=1.0,
                                fill_opacity=self.dag.config.ghostdag_blue_opacity
                            )
                        )
                        reset_animations.append(
                            candidate.visual_block.square.animate.set_style(
                                stroke_width=2,
                                stroke_opacity=1.0,
                            )
                        )
                        self.dag.scene.play(*reset_animations)

                    if second_check_failed:
                        break  # No need to check further blue blocks

            # Final decision based on both checks
            can_be_blue = context_block._can_be_blue_local(
                candidate, local_blue_status, context_block.kaspa_config.k, total_view
            )

            if can_be_blue:
                local_blue_status[candidate] = True
                self.dag.scene.caption(f"Block {candidate.name}: BLUE (accepted)")
                self.dag.scene.play(
                    candidate.visual_block.square.animate.set_fill(
                        color=self.dag.config.ghostdag_blue_color,
                        opacity=self.dag.config.ghostdag_blue_opacity
                    )
                )
            else:
                local_blue_status[candidate] = False
                self.dag.scene.caption(f"Block {candidate.name}: RED (rejected)")
                self.dag.scene.play(
                    candidate.visual_block.square.animate.set_fill(
                        color=self.dag.config.ghostdag_red_color,
                        opacity=self.dag.config.ghostdag_red_opacity
                    )
                )

            self.dag.scene.wait(0.3)