from dataclasses import dataclass, field
from enum import Enum
from random import choice, randint
from typing import Dict, List
from itertools import chain
from abc import ABC, abstractmethod

from common import *
import string

BLOCK_H = 0.4
BLOCK_W = 0.4
GENESIS_POSITION = [-5,0,0]
BLOCK_SPACING_H = 1.3
BLOCK_SPACING_W = 2
DAG_WIDTH = 5
NOISE_H = 0.3
NOISE_W = 0.5

DEF_RATE_FUNC = smooth
DEF_RUN_TIME = 0.5

PROMPT_DELAY = 2

def safe_play(scene, anims):
    if anims:
        scene.play(anims)
####################
class ColoringState(Enum):
    BLUE = "blue"
    RED = "red"
    PENDING = "pending"

@dataclass
class GhostdagData:
    """Standardized GHOSTDAG data structure matching Kaspa's implementation"""
    blue_score: int = 0
    blue_work: int = 0  # Simplified for visualization
    selected_parent: str = ""
    mergeset_blues: List[str] = field(default_factory=list)
    mergeset_reds: List[str] = field(default_factory=list)
    blues_anticone_sizes: Dict[str, int] = field(default_factory=dict)

@dataclass
class ColoringOutput:
    """Result of GHOSTDAG coloring for a candidate block"""
    state: str  # "BLUE" or "RED"
    anticone_size: int = 0
    anticone_sizes: Dict[str, int] = field(default_factory=dict)

class ChainBlock:
    def __init__(self, hash_val, ghostdag_data):
        self.hash = hash_val
        self.data = ghostdag_data

class Parent:
    def __init__(self, name, **kwargs):
        self.name = name
        self.kwargs = kwargs

class Block(ABC):

    DEFAULT_COLOR = BLUE

#   def __init__(self, name, DAG, parents, pos, label=None, color=BLUE, h=BLOCK_H, w=BLOCK_W):
    def __init__(self, name=None, DAG=None, parents=None, pos=None, label=None, block_color=None, h=BLOCK_H, w=BLOCK_W):
#   def __init__(self, name=None, DAG=None, parents=None, pos=None, label=None, h=BLOCK_H, w=BLOCK_W):

        # Use provided name or fall back to string ID
        self.name = name if name is not None else str(id(self))

        # set default color of block
        if block_color is None:
            block_color = self.DEFAULT_COLOR

        self.width = w
        self.height = h
        self.DAG = DAG
        self.parents = [DAG.blocks[p.name] for p in parents]
        self.children = []
        self.hash = id(self)

        # Cache past blocks - calculated only once
        self.past_blocks = self._calculate_past_blocks()
        self.weight = len(self.past_blocks)
        self.outgoing_arrows = []

        self.rect = Rectangle(
            color=block_color,
            fill_opacity=1,
            height=h,
            width=w,
        )

        # Each block type implements its own parent selection
        self.selected_parent = self._select_parent()

        self.rect.move_to(pos)

        if label is None:
            if self.name == "Gen":
                self.label = Tex("Gen").set_z_index(1).scale(0.7)
                self.label.move_to(self.rect.get_center())  # Position it initially
                self.rect.add(self.label)  # Add as submobject
            else:
                # each block is initialized with a label of its weight
                self.label = Tex(str(self.weight)).set_z_index(1).scale(0.7)
                self.label.move_to(self.rect.get_center())  # Position it initially
                self.rect.add(self.label)  # Add as submobject
        else:
            # create a label
            self.label = Tex(label).set_z_index(1).scale(0.7)
            self.label.move_to(self.rect.get_center())  # Position it initially
            self.rect.add(self.label)  # Add as submobject


        for p in parents:
            DAG.blocks[p.name].children.append(self.name)

    @abstractmethod
    def _select_parent(self):
        """Each block type must implement its own parent selection logic"""
        pass

        # Common methods remain the same

    def _calculate_past_blocks(self):
        visited = set()
        self._collect_past_blocks(visited)
        return visited

    def _collect_past_blocks(self, visited):
        for parent in self.parents:
            if parent.name not in visited:
                visited.add(parent.name)
                parent._collect_past_blocks(visited)

    def get_past_blocks(self):
        return self.past_blocks

    def is_tip(self):
        return bool(self.children)

class GhostDAGBlock(Block):
    """Block that selects parent with highest weight (GHOST-DAG algorithm)"""
    DEFAULT_COLOR = PURE_BLUE

    def __init__(self, name=None, DAG=None, parents=None, pos=None, label=None, color=None, h=BLOCK_H, w=BLOCK_W):
        self.blue_count = 0
        super().__init__(name, DAG, parents, pos, label, color, h, w)

        # Handle genesis block case
        if not self.selected_parent:
            self.ghostdag_data = GhostdagData()
            return

            # Calculate GHOSTDAG data
        self.mergeset = self._calculate_mergeset_proper()
        k = getattr(DAG, 'k_param', 3)
        self.ghostdag_data = self._calculate_ghostdag_data(k)

        # Update blue count and label
        self.blue_count = self._calculate_blue_count()
        self._update_label()

    def _calculate_ghostdag_data(self, k) -> GhostdagData:
        """Calculate complete GHOSTDAG data for this block"""
        print(f"\n{'=' * 60}")
        print(f"GHOSTDAG COLORING: Block {self.name} (k={k})")
        print(f"Selected parent: {self.selected_parent.name}")
        print(f"Mergeset: {self.mergeset}")
        print(f"{'=' * 60}")

        # Initialize with selected parent as first blue
        ghostdag_data = GhostdagData(
            selected_parent=self.selected_parent.name,
            mergeset_blues=[self.selected_parent.name],
            blues_anticone_sizes={self.selected_parent.name: 0}
        )

        # Process mergeset candidates
        ordered_mergeset = self._topological_sort_mergeset(self.mergeset)

        for candidate_name in ordered_mergeset:
            coloring = self._check_blue_candidate_fixed(candidate_name, ghostdag_data, k)
            print(f"  Checking candidate {candidate_name}: {coloring.state}")

            if coloring.state == "BLUE":
                ghostdag_data.mergeset_blues.append(candidate_name)
                ghostdag_data.blues_anticone_sizes[candidate_name] = coloring.anticone_size

                # Update anticone sizes for affected blues
                for blue_name, size in coloring.anticone_sizes.items():
                    ghostdag_data.blues_anticone_sizes[blue_name] = size + 1
            else:
                ghostdag_data.mergeset_reds.append(candidate_name)

        print(f"\nCOLORING SUMMARY for {self.name}:")
        print(f"  Blue blocks: {ghostdag_data.mergeset_blues[1:]}")  # Exclude selected parent
        print(f"  Red blocks: {ghostdag_data.mergeset_reds}")
        print(f"  Final anticone sizes: {ghostdag_data.blues_anticone_sizes}")
        print(f"{'=' * 60}\n")

        return ghostdag_data

    def _check_blue_candidate_fixed(self, candidate_name: str, ghostdag_data: GhostdagData, k: int) -> ColoringOutput:
        """Fixed k-cluster validation that properly traverses the selected parent chain"""
        # Early exit if already at k+1 blues
        if len(ghostdag_data.mergeset_blues) == k + 1:
            return ColoringOutput(state="RED")

        anticone_size = 0
        counted_blocks = set()
        affected_anticone_sizes = {}
        candidate_block = self.DAG.blocks[candidate_name]

        # Start chain traversal from the new block (similar to Kaspa's ChainBlock approach)
        current_chain_data = ghostdag_data
        current_chain_hash = None  # None represents the NEW_BLOCK

        while True:
            # Check if candidate is in future of current chain block
            if current_chain_hash and current_chain_hash in self.DAG.blocks:
                chain_block_obj = self.DAG.blocks[current_chain_hash]
                if self._is_ancestor(chain_block_obj, candidate_block):
                    # Candidate is in future, so all remaining blues are in past - safe to color BLUE
                    return ColoringOutput(
                        state="BLUE",
                        anticone_size=anticone_size,
                        anticone_sizes=affected_anticone_sizes
                    )

                    # Check all blues in current chain block's data
            for peer_blue_name in current_chain_data.mergeset_blues:
                if peer_blue_name in self.DAG.blocks and peer_blue_name not in counted_blocks:
                    peer_blue = self.DAG.blocks[peer_blue_name]

                    # Skip if peer is in past of candidate (not in anticone)
                    if self._is_ancestor(peer_blue, candidate_block):
                        continue

                        # Skip if candidate is in past of peer (not in anticone)
                    if self._is_ancestor(candidate_block, peer_blue):
                        continue

                        # They're in anticone - count this peer
                    anticone_size += 1
                    counted_blocks.add(peer_blue_name)

                    # Check k-cluster violation for candidate
                    if anticone_size > k:
                        return ColoringOutput(state="RED")

                        # Check if peer already has k blues in anticone (would violate k-cluster)
                    peer_current_anticone_size = self._get_blue_anticone_size(peer_blue_name, current_chain_data)
                    if peer_current_anticone_size == k:
                        return ColoringOutput(state="RED")

                    affected_anticone_sizes[peer_blue_name] = peer_current_anticone_size

                    # Move to next block in selected parent chain
            if not current_chain_data.selected_parent or current_chain_data.selected_parent == "Gen":
                break

            if current_chain_data.selected_parent not in self.DAG.blocks:
                break

                # Get the next chain block's GHOSTDAG data
            next_chain_block = self.DAG.blocks[current_chain_data.selected_parent]
            if hasattr(next_chain_block, 'ghostdag_data'):
                current_chain_data = next_chain_block.ghostdag_data
                current_chain_hash = current_chain_data.selected_parent
            else:
                break

        return ColoringOutput(
            state="BLUE",
            anticone_size=anticone_size,
            anticone_sizes=affected_anticone_sizes
        )

    def _get_blue_anticone_size(self, block_name: str, context_ghostdag_data: GhostdagData) -> int:
        """Get the blue anticone size of a block from the given context"""
        # First check in current context
        if block_name in context_ghostdag_data.blues_anticone_sizes:
            return context_ghostdag_data.blues_anticone_sizes[block_name]

            # Traverse up the selected parent chain to find the anticone size
        current_parent = context_ghostdag_data.selected_parent
        while current_parent and current_parent != "Gen" and current_parent in self.DAG.blocks:
            parent_block = self.DAG.blocks[current_parent]
            if hasattr(parent_block, 'ghostdag_data'):
                if block_name in parent_block.ghostdag_data.blues_anticone_sizes:
                    return parent_block.ghostdag_data.blues_anticone_sizes[block_name]
                current_parent = parent_block.ghostdag_data.selected_parent
            else:
                break

                # If not found, the block is not in the blue set of this context
        raise ValueError(f"Block {block_name} is not in blue set of the given context")

    def _calculate_blue_count(self) -> int:
        """Calculate blue count from GHOSTDAG data"""
        if not self.selected_parent:
            return 0

        selected_parent_blue_count = getattr(self.selected_parent, 'blue_count', 0)
        mergeset_blue_count = len(self.ghostdag_data.mergeset_blues) - 1  # Exclude selected parent

        return selected_parent_blue_count + 1 + mergeset_blue_count

    def _update_label(self):
        """Update block label with blue count"""
        if self.name != "Gen":
            self.rect.remove(self.label)
            self.label = Tex(str(self.blue_count)).set_z_index(1).scale(0.7)
            self.label.move_to(self.rect.get_center())
            self.rect.add(self.label)

            # Keep essential helper methods

    def _calculate_mergeset_proper(self):
        """Calculate mergeset using Kaspa's algorithm"""
        if not self.parents or not self.selected_parent:
            return set()

        mergeset = set()
        queue = []

        # Initialize with non-selected parents
        for parent in self.parents:
            if parent != self.selected_parent:
                queue.append(parent.name)
                mergeset.add(parent.name)

                # BFS to collect all blocks not in past of selected parent
        while queue:
            current_name = queue.pop(0)
            current_block = self.DAG.blocks[current_name]

            for parent in current_block.parents:
                parent_name = parent.name
                if (parent_name not in mergeset and
                        not self._is_ancestor(parent, self.selected_parent)):
                    mergeset.add(parent_name)
                    queue.append(parent_name)

        return mergeset

    def _topological_sort_mergeset(self, mergeset):
        """Sort mergeset blocks by blue count with debug output"""

        def get_sort_key(block_name):
            block = self.DAG.blocks[block_name]
            blue_count = getattr(block, 'blue_count', 0)
            block_hash = getattr(block, 'hash', block_name)
            sort_key = (blue_count, block_hash)
            print(f"    Sort key for {block_name}: {sort_key}")
            return sort_key

        print(f"  Sorting mergeset blocks:")
        sorted_blocks = sorted(mergeset, key=get_sort_key)
        print(f"  Final order: {sorted_blocks}")
        return sorted_blocks

    def _are_in_anticone(self, block1, block2):
        """Check if two blocks are in anticone"""
        return (not self._is_ancestor(block1, block2) and
                not self._is_ancestor(block2, block1))

    @staticmethod
    def _is_ancestor(ancestor_block, descendant_block):
        """Check if ancestor_block is in the past of descendant_block"""
        return ancestor_block.name in descendant_block.past_blocks

    def _select_parent(self):
        """Select parent with highest blue count"""
        if not self.parents:
            return None

        best_parent = None
        max_blue_count = -1

        for parent in self.parents:
            blue_count = getattr(parent, 'blue_count', 0)
            if blue_count > max_blue_count:
                max_blue_count = blue_count
                best_parent = parent

        return best_parent

        # Properties for backward compatibility

    @property
    def mergeset_blues(self):
        return self.ghostdag_data.mergeset_blues[1:]  # Exclude selected parent

    @property
    def mergeset_reds(self):
        return self.ghostdag_data.mergeset_reds

    @property
    def blues_anticone_sizes(self):
        return self.ghostdag_data.blues_anticone_sizes

class RandomBlock(Block):
    """Block that randomly selects a parent"""

    def _select_parent(self):
        if not self.parents:
            return None

        from random import choice
        return choice(self.parents)

class BlockDAG:
    """A Directed Acyclic Graph visualization system for blockchain-like structures."""

    blocks: Dict[str, Block]
    history: List[List[str]]  # History of tip states
    #block_color: ManimColor
    block_w: float
    block_h: float

    def __init__(
            self,
            history_size: int = 20,
            block_color: ManimColor = BLUE,
            block_w: float = BLOCK_W,
            block_h: float = BLOCK_H,
            block_type: type = RandomBlock
    ):
        """Initialize the BlockDAG with configuration parameters."""
        self.blocks = {}
        self.history = []
        self.history_size = history_size
        #self.block_color = block_color
        self.block_h = block_h
        self.block_w = block_w
        self.block_type = block_type  # Store the block type to use
        ## Construction Methods

    def add(self, name: str, pos: list, parents: list = None, **kwargs):
        # Set default values
        if parents is None:
            parents = []
        self._set_default_kwargs(kwargs)

        # Validate and prepare data
        self._validate_new_block(name)
        pos = self._normalize_position(pos)
        parents = self._normalize_parents(parents)

        # Create the block using the configured block type
        block = self.block_type(name, self, parents, pos, **kwargs)

        # Generate animations and update state
        animations = self._create_block_animations(block, parents)
        self._register_block(name, block)
        self._update_history()

        return animations

    def _set_default_kwargs(self, kwargs: dict):
        """Set default values for block creation."""
        kwargs.setdefault("label", None)
#        kwargs.setdefault("color", self.block_color)
        kwargs.setdefault("w", self.block_w)
        kwargs.setdefault("h", self.block_h)

    def _validate_new_block(self, name: str):
        """Ensure the block name doesn't already exist."""
        assert name not in self.blocks, f"Block '{name}' already exists"

    @staticmethod
    def _normalize_position(pos: list) -> list:
        """Ensure position has 3D coordinates."""
        return pos + [0]

    @staticmethod
    def _normalize_parents(parents: list) -> list:
        """Convert parent names to Parent objects."""
        return [Parent(p) if isinstance(p, str) else p for p in parents]

    def _create_block_animations(self, block: Block, parents: list) -> list:
        """Create all animations for adding a block."""
        animations = [FadeIn(block.rect)]

            # Add arrow animations for each parent
        for parent in parents:
            parent_block = self.blocks[parent.name]

            # Determine arrow styling based on whether this is the selected parent
            arrow_kwargs = parent.kwargs.copy()  # Start with parent's kwargs

            if parent_block == block.selected_parent:
                # Override with blue styling for selected parent
                arrow_kwargs.update({
                    "color": BLUE,
                    "stroke_width": 3,
                    "z_index": -1  # Bring selected parent arrow to front
                })

            arrow_anim = self.add_arrow(block, parent_block, **arrow_kwargs)
            animations.append(arrow_anim)

        return animations

    def _register_block(self, name: str, block: Block):
        """Add the block to the DAG."""
        self.blocks[name] = block

    def _update_history(self):
        """Update the history with current tips."""
        self.history.insert(0, self._get_tips())
        if len(self.history) > self.history_size:
            self.history.pop()

    def random_block(self) -> str:
        """Get a random block name from the DAG."""
        return choice(list(self.blocks.keys()))

        ## Arrow Creation Methods

    def add_arrow(self, from_block: Block, to_block: Block, **kwargs):
        """Create an arrow between two blocks with automatic positioning."""
        # Set arrow defaults
        self._set_arrow_defaults(kwargs)

        # Create arrow with positioning
        arrow = self._create_positioned_arrow(from_block, to_block, **kwargs)

        # Set up arrow tracking
        self._setup_arrow_tracking(arrow, from_block, to_block)

        # Create updater animation
        return self._create_arrow_updater(arrow, from_block, to_block)

    @staticmethod
    def _set_arrow_defaults(kwargs: dict):
        """Set default arrow styling."""
        defaults = {
            "buff": 0,
            "stroke_width": 2,
            "tip_shape": StealthTip,
            "max_tip_length_to_length_ratio": 0.04,
            "color": WHITE
        }
        for key, value in defaults.items():
            kwargs.setdefault(key, value)

    def _create_positioned_arrow(self, from_block: Block, to_block: Block, **kwargs) -> Arrow:
        """Create an arrow with optimal positioning between blocks."""
        arrow = Arrow(**kwargs)

        def get_start_end():
            return self._calculate_arrow_endpoints(from_block, to_block)

        arrow.put_start_and_end_on(**get_start_end())
        return arrow

    @staticmethod
    def _calculate_arrow_endpoints(from_block: Block, to_block: Block) -> dict:
        """Calculate optimal start and end points for arrow between blocks."""
        # Get block boundaries
        from_rect = from_block.rect
        to_rect = to_block.rect

        # Calculate positions
        from_left, from_right = from_rect.get_left()[0], from_rect.get_right()[0]
        to_left, to_right = to_rect.get_left()[0], to_rect.get_right()[0]
        from_top, from_bottom = from_rect.get_top()[1], from_rect.get_bottom()[1]
        to_top, to_bottom = to_rect.get_top()[1], to_rect.get_bottom()[1]

        # Default to horizontal connection
        start = from_rect.get_left()
        end = to_rect.get_right()

        # Adjust for horizontal overlap
        if to_right - from_left > 0:
            start = from_rect.get_right()
            end = to_rect.get_left()

            # Check if vertical connection is better
        horizontal_overlap = max(to_right - from_left, from_right - to_left)
        vertical_overlap = max(to_bottom - from_top, from_bottom - to_top)

        if horizontal_overlap < vertical_overlap:
            if to_bottom - from_top > from_bottom - to_top:
                start = from_rect.get_top()
                end = to_rect.get_bottom()
            else:
                start = from_rect.get_bottom()
                end = to_rect.get_top()

        return {"start": start, "end": end}

    @staticmethod
    def _setup_arrow_tracking(arrow: Arrow, from_block: Block, to_block: Block):
        """Set up arrow tracking information."""
        arrow.source_block = from_block
        arrow.target_block = to_block

        if hasattr(from_block, 'outgoing_arrows'):
            from_block.outgoing_arrows.append(arrow)

    def _create_arrow_updater(self, arrow: Arrow, from_block: Block, to_block: Block):
        """Create the arrow updater animation."""

        class GrowArrowUpdater(GrowArrow):
            def __init__(self, arrow, updater_func, **kwargs):
                super().__init__(arrow, **kwargs)
                self.arrow = arrow
                self.updater_func = updater_func

            def __del__(self):
                self.arrow.add_updater(self.updater_func)

        updater_func = lambda a: a.put_start_and_end_on(
            **self._calculate_arrow_endpoints(from_block, to_block)
        )

        return GrowArrowUpdater(arrow, updater_func)

        ## Combinatorics Methods

    def get_future(self, block_name: str) -> list[str]:
        """Get all blocks in the future of the given block."""
        future_blocks = []
        self._collect_future_blocks(block_name, future_blocks)
        return future_blocks

    def _collect_future_blocks(self, block_name: str, visited: list[str]):
        """Recursively collect all blocks in the future."""
        if block_name not in visited:
            visited.append(block_name)
            for child_name in self.blocks[block_name].children:
                self._collect_future_blocks(child_name, visited)

    def get_tips(self, missed_blocks: int = 0) -> list[str]:
        """Get the tips from history at a specific point in time."""
        return self.history[min(missed_blocks, len(self.history) - 1)]

    def _get_tips(self) -> list[str]:
        """Get current tip blocks (blocks with no children)."""
        tips = list(filter(lambda x: not self.blocks[x].is_tip(), self.blocks.keys()))
        return tips

        ## Transformation Methods

    def shift(self, name: str, offset: list, rate_func=DEF_RATE_FUNC, run_time=DEF_RUN_TIME):
        """Create a shift animation for a block."""
        rects = self._name_to_rect(name)
        return Transform(rects, rects.copy().shift(offset + [0]), rate_func=rate_func, run_time=run_time)

    def change_color(self, blocks: str | list[str], color: ManimColor) -> list:
        """Create color change animations for blocks."""
        if isinstance(blocks, str):
            blocks = [blocks]
        return [FadeToColor(rect, color=color) for rect in self._name_to_rect(blocks)]

        ## Gesture Methods

    def blink(self, block_names: str | list[str]):
        """Create a blink animation for blocks."""
        if isinstance(block_names, str):
            rect = self._name_to_rect(block_names)
            rect_color = rect.color
            return Succession(
                FadeToColor(rect, color=YELLOW, run_time=0.2),
                FadeToColor(rect, color=rect_color)
            )
        return [self.blink(b) for b in block_names]

        ## Utility Methods

    def _name_to_rect(self, name: str | list[str]):
        """Convert block name(s) to rectangle mobject(s)."""
        if isinstance(name, str):
            return self.blocks[name].rect
        else:
            return VGroup(*[self.blocks[b].rect for b in name])

class LayerDAG(BlockDAG):
    def __init__(self,
                 layer_spacing=1.5,
                 chain_spacing=1,
                 gen_pos=None,
                 width=4,
                 block_spacing=1,
                 block_type=RandomBlock,
                 *args,
                 **kwargs
                 ):
        if gen_pos is None:
            gen_pos = [-6.5, 0]
        super().__init__(block_type=block_type, *args, **kwargs)

        self.init_animation = super().add("Gen", gen_pos)[0]
        self.layers = [["Gen"]]
        self.layer_spacing = layer_spacing
        self.chain_spacing = chain_spacing
        self.gen_pos = gen_pos
        self.block_spacing = block_spacing
        self.width = width

    def add(self, name, parent_names, selected_parent=None, random_sp=False, *args, **kwargs):
        # Normalize parent_names to list
        if isinstance(parent_names, str):
            parent_names = [parent_names]

            # Override block type based on random_sp parameter
        original_block_type = self.block_type
        if random_sp:
            self.block_type = RandomBlock

            # Find appropriate layer
        top_parent_layer = self._find_top_parent_layer(parent_names)
        target_layer = self._find_available_layer(top_parent_layer)

        # Calculate position and update layer structure
        pos = self._calculate_layer_position(target_layer)
        self.layers[target_layer].append(name)

        # Process parents with styling
        parents = self._process_parents(parent_names, selected_parent, random_sp)

        # Delegate to parent class
        result = super().add(name, pos, parents=parents, **kwargs)

        # Restore original block type
        self.block_type = original_block_type

        return result

    def _process_parents(self, parent_names: list[str], selected_parent: str = None, random_sp: bool = False) -> list:
        """Process parent names and create Parent objects with appropriate styling."""
        if random_sp and parent_names:
            selected_parent = choice(parent_names)

        parents = []
        for parent_name in parent_names:
            # Remove the blue styling logic - let the smart selection handle it
            parents.append(Parent(parent_name, z_index=-2))

        return parents

    def _find_top_parent_layer(self, parent_names: list[str]) -> int:
        """Find the topmost layer containing any parent block."""
        top_parent_layer = 0
        for i in range(len(self.layers)):
            if any(block_name in self.layers[i] for block_name in parent_names):
                top_parent_layer = i
        return top_parent_layer

    def _find_available_layer(self, top_parent_layer: int) -> int:
        """Find the next available layer for block placement."""
        # Check existing layers for space
        for i in range(top_parent_layer + 1, len(self.layers)):
            if len(self.layers[i]) < self.width - ((i + 1) % 2):
                return i

                # All layers are full, need a new one
        return len(self.layers)

    def _calculate_layer_position(self, layer: int) -> list[float]:
        """Calculate the position for a block in the given layer."""
        layer_top = -self.chain_spacing

        if layer == len(self.layers):
            # New layer
            self.layers.append([])
        else:
            # Existing layer - get position from last block
            last_block_name = self.layers[layer][-1]
            layer_top = self.blocks[last_block_name].rect.get_center()[1]

        x_pos = layer * self.layer_spacing + self.gen_pos[0]
        y_pos = layer_top + self.chain_spacing
        return [x_pos, y_pos]

    def adjust_layer(self, layer_index: int):
        """Adjust vertical positioning of blocks in a specific layer."""
        if layer_index >= len(self.layers):
            return None

        layer_blocks = self.layers[layer_index]
        if not layer_blocks:
            return None

            # Calculate current bounds
        top_y = self.blocks[layer_blocks[-1]].rect.get_center()[1]
        bottom_y = self.blocks[layer_blocks[0]].rect.get_center()[1]

        # Calculate needed shift to center the layer
        center_shift = abs(top_y - bottom_y) / 2 - top_y

        if center_shift == 0:
            return None  # Already centered

        # Return shift animations for all blocks in layer
        return [self.shift(block_name, [0, center_shift]) for block_name in layer_blocks]

    def adjust_layers(self, chained=True):
        shifts = list(filter(None,[self.adjust_layer(layer) for layer in range(len(self.layers))]))
        return list(chain(*shifts)) if chained else shifts

class GHOSTDAG(LayerDAG):
    def __init__(self, gd_k = 0, *args, **kwargs):

        self.k_param = gd_k
        # Force GhostDAGBlock type for GHOSTDAG, overriding LayerDAG's default
        super().__init__(block_type=GhostDAGBlock, *args, **kwargs)


    def create_ghostdag_step_by_step_animation(self, vertical_offset=0.5, horizontal_offset=1.25):
        """
        Create step-by-step GHOSTDAG animation showing the algorithm progression
        from genesis to the heaviest tip, highlighting what's being checked at each step.
        """
        best_tip = self._find_best_tip()
        if not best_tip:
            return AnimationGroup(Wait(0.1))

        parent_chain = self._get_parent_chain(best_tip)
        new_positions = self._calculate_chain_tree_positions_ordered(parent_chain, vertical_offset, horizontal_offset)

        # Start with everything faded
        self._fade_all_blocks()

        animations = []

        # Process each block in the parent chain from genesis to tip
        for i, current_block_name in enumerate(reversed(parent_chain)):  # Genesis first
            current_block = self.blocks[current_block_name]

            # Skip genesis (no GHOSTDAG calculation needed)
            if current_block_name == "Gen":
                # Just highlight genesis
                highlight_anim = self._highlight_block(current_block_name)
                animations.append(highlight_anim)
                continue

                # Step 1: Highlight the current block being processed
            step_animations = []
            step_animations.append(self._highlight_block(current_block_name))

            # Step 2: Show selected parent selection
            if hasattr(current_block, 'selected_parent') and current_block.selected_parent:
                step_animations.append(self._highlight_selected_parent(current_block))

                # Step 3: Show mergeset calculation
            if hasattr(current_block, 'mergeset') and current_block.mergeset:
                step_animations.append(self._highlight_mergeset(current_block))

                # Step 4: Show blue/red coloring process
            if hasattr(current_block, 'mergeset_blues') or hasattr(current_block, 'mergeset_reds'):
                step_animations.append(self._show_coloring_process(current_block))

                # Add all step animations for this block
            animations.extend(step_animations)

            # Brief pause between blocks
            animations.append(Wait(0.5))

            # Final positioning animation
        movement_animations = []
        for block_name, new_pos in new_positions.items():
            if block_name in self.blocks:
                current_block = self.blocks[block_name]
                movement_animations.append(current_block.rect.animate.move_to(new_pos))

        if movement_animations:
            animations.append(AnimationGroup(*movement_animations, run_time=1.0))

        return Succession(*animations)

    def create_block_perspective_animation(self, vertical_offset=0.5, horizontal_offset=1.25, hold_duration=1.0):
        """
        Animate each block (layer 2+) showing its GHOSTDAG perspective as a tree,
        then return to original positions before moving to the next block.
        """
        # Store original positions at the beginning
        self._store_original_positions()

        # Get blocks from layer 2 and higher
        blocks_to_animate = []
        for layer_idx in range(2, len(self.layers)):
            blocks_to_animate.extend(self.layers[layer_idx])

        if not blocks_to_animate:
            return AnimationGroup(Wait(0.1))

        animations = []

        for block_name in blocks_to_animate:
            current_block = self.blocks[block_name]

            # Step 1: Show this block's perspective
            perspective_animations = self._show_block_perspective(
                block_name, vertical_offset, horizontal_offset
            )
            animations.extend(perspective_animations)

            # Step 2: Hold the view
            animations.append(Wait(hold_duration))

            # Step 3: Return to original positions
            reset_animations = self._reset_to_original_positions()
            animations.append(reset_animations)

            # Brief pause before next block
            animations.append(Wait(0.3))

        return Succession(*animations)

    def _show_block_perspective(self, focus_block_name, v_offset, h_offset):
        """Show the DAG from a specific block's GHOSTDAG perspective"""
        focus_block = self.blocks[focus_block_name]

        # Calculate tree positions from this block's perspective
        tree_positions = self._calculate_perspective_tree_positions(
            focus_block_name, v_offset, h_offset
        )

        # Apply coloring based on this block's GHOSTDAG data
        coloring_animations = self._apply_perspective_coloring(focus_block)

        # Move blocks to tree positions
        movement_animations = []
        for block_name, new_pos in tree_positions.items():
            if block_name in self.blocks:
                current_block = self.blocks[block_name]
                movement_animations.append(
                    current_block.rect.animate.move_to(new_pos)
                )

        return [
            AnimationGroup(*coloring_animations, run_time=0.5),
            AnimationGroup(*movement_animations, run_time=0.8)
        ]

    def _calculate_perspective_tree_positions(self, focus_block_name, v_offset, h_offset):
        """Calculate tree positions from a specific block's perspective"""
        focus_block = self.blocks[focus_block_name]
        new_positions = {}

        # Get the selected parent chain from focus block to genesis
        parent_chain = self._get_parent_chain(focus_block_name)

        # Position the parent chain horizontally at bottom
        chain_y = min(block.rect.get_center()[1] for block in self.blocks.values())

        for i, chain_block_name in enumerate(reversed(parent_chain)):
            chain_block = self.blocks[chain_block_name]
            # Spread parent chain horizontally
            chain_x = i * h_offset - (len(parent_chain) * h_offset / 2)
            new_positions[chain_block_name] = [chain_x, chain_y, 0]

            # Position mergeset blocks above each chain block
            if hasattr(chain_block, 'mergeset') and chain_block.mergeset:
                mergeset_blocks = list(chain_block.mergeset)
                for j, mergeset_block_name in enumerate(mergeset_blocks):
                    if mergeset_block_name in self.blocks:
                        mergeset_x = chain_x - h_offset * 0.5
                        mergeset_y = chain_y + v_offset + (j * 0.4)
                        new_positions[mergeset_block_name] = [mergeset_x, mergeset_y, 0]

                        # Position the focus block prominently
        focus_x = 0
        focus_y = chain_y + v_offset * 2
        new_positions[focus_block_name] = [focus_x, focus_y, 0]

        return new_positions

    def _apply_perspective_coloring(self, focus_block):
        """Apply coloring based on the focus block's GHOSTDAG perspective"""
        animations = []

        # Reset all blocks to default opacity and color first
        for block_name, block in self.blocks.items():
            animations.append(block.rect.animate.set_opacity(0.3).set_color(GRAY))

            # Highlight the focus block
        animations.append(
            focus_block.rect.animate.set_opacity(1.0).set_color(YELLOW)
        )

        # Color selected parent chain in blue
        parent_chain = self._get_parent_chain(focus_block.name)
        for chain_block_name in parent_chain:
            if chain_block_name != focus_block.name:
                chain_block = self.blocks[chain_block_name]
                animations.append(
                    chain_block.rect.animate.set_opacity(1.0).set_color(PURE_BLUE)
                )

                # Color mergeset blues and reds from focus block's perspective
        if hasattr(focus_block, 'mergeset_blues'):
            for blue_name in focus_block.mergeset_blues:
                if blue_name in self.blocks and blue_name not in parent_chain:
                    blue_block = self.blocks[blue_name]
                    animations.append(
                        blue_block.rect.animate.set_opacity(1.0).set_color(PURE_BLUE)
                    )

        if hasattr(focus_block, 'mergeset_reds'):
            for red_name in focus_block.mergeset_reds:
                if red_name in self.blocks:
                    red_block = self.blocks[red_name]
                    animations.append(
                        red_block.rect.animate.set_opacity(1.0).set_color(PURE_RED)
                    )

        return animations

    def _reset_to_original_positions(self):
        """Reset all blocks to their original positions and colors"""
        animations = []

        for block_name, block in self.blocks.items():
            # Get original position (you'll need to store this)
            original_pos = getattr(block, 'original_position', block.rect.get_center())

            # Reset position and appearance
            animations.append(block.rect.animate.move_to(original_pos))
            animations.append(block.rect.animate.set_opacity(1.0))

            # Reset to original color based on block type
            if isinstance(block, GhostDAGBlock):
                animations.append(block.rect.animate.set_color(PURE_BLUE))
            else:
                animations.append(block.rect.animate.set_color(BLUE))

        return AnimationGroup(*animations, run_time=0.8)

    def _store_original_positions(self):
        """Store original positions for reset functionality"""
        for block_name, block in self.blocks.items():
            if not hasattr(block, 'original_position'):
                block.original_position = block.rect.get_center().copy()

    def _fade_all_blocks(self):
        """Set all blocks to low opacity initially"""
        for block_name, block in self.blocks.items():
            block.rect.set_opacity(0.2)
            if hasattr(block, 'label') and block.label:
                block.label.set_opacity(0.2)
            if hasattr(block, 'outgoing_arrows'):
                for arrow in block.outgoing_arrows:
                    arrow.set_opacity(0.2)

    def _highlight_block(self, block_name):
        """Highlight a specific block and its relevant arrows"""
        block = self.blocks[block_name]
        animations = []

        # Highlight the block itself
        animations.append(block.rect.animate.set_opacity(1.0))
        if hasattr(block, 'label') and block.label:
            animations.append(block.label.animate.set_opacity(1.0))

            # Highlight incoming arrows (arrows pointing to this block)
        for other_block_name, other_block in self.blocks.items():
            if hasattr(other_block, 'outgoing_arrows'):
                for arrow in other_block.outgoing_arrows:
                    if hasattr(arrow, 'target_block') and arrow.target_block.name == block_name:
                        animations.append(arrow.animate.set_opacity(1.0))

        return AnimationGroup(*animations, run_time=0.3)

    def _highlight_selected_parent(self, current_block):
        """Highlight the selected parent and show the selection process with arrows"""
        animations = []

        # Highlight all parents first (showing selection process)
        for parent in current_block.parents:
            parent_block = self.blocks[parent.name]
            animations.append(parent_block.rect.animate.set_color(YELLOW).set_opacity(1.0))

            # Highlight arrows from current block to all parents
            if hasattr(current_block, 'outgoing_arrows'):
                for arrow in current_block.outgoing_arrows:
                    if hasattr(arrow, 'target_block') and arrow.target_block.name == parent.name:
                        animations.append(arrow.animate.set_opacity(1.0))

                        # Then highlight the selected parent in blue
        selected_animations = []
        if current_block.selected_parent:
            selected_parent_block = self.blocks[current_block.selected_parent.name]
            selected_animations.append(selected_parent_block.rect.animate.set_color(BLUE).set_opacity(1.0))

            # Highlight the arrow to selected parent with blue color
            if hasattr(current_block, 'outgoing_arrows'):
                for arrow in current_block.outgoing_arrows:
                    if (hasattr(arrow, 'target_block') and
                            arrow.target_block.name == current_block.selected_parent.name):
                        selected_animations.append(arrow.animate.set_color(BLUE).set_opacity(1.0))

        return Succession(
            AnimationGroup(*animations, run_time=0.5),  # Show all parents with arrows
            AnimationGroup(*selected_animations, run_time=0.5)  # Highlight selected with blue arrow
        )

    def _highlight_mergeset(self, current_block):
        """Highlight the mergeset blocks and their connecting arrows"""
        animations = []

        if hasattr(current_block, 'mergeset'):
            for mergeset_block_name in current_block.mergeset:
                if mergeset_block_name in self.blocks:
                    mergeset_block = self.blocks[mergeset_block_name]
                    animations.append(mergeset_block.rect.animate.set_color(ORANGE).set_opacity(1.0))

                    # Highlight arrows connecting mergeset blocks to the current block's parents
                    # and arrows within the mergeset
                    if hasattr(mergeset_block, 'outgoing_arrows'):
                        for arrow in mergeset_block.outgoing_arrows:
                            if hasattr(arrow, 'target_block'):
                                target_name = arrow.target_block.name
                                # Show arrows to parents or other mergeset blocks
                                if (target_name in [p.name for p in current_block.parents] or
                                        target_name in current_block.mergeset):
                                    animations.append(arrow.animate.set_opacity(1.0))

        return AnimationGroup(*animations, run_time=0.5) if animations else Wait(0.1)

    def _show_coloring_process(self, current_block):
        """Show the blue/red coloring process with relevant arrows"""
        animations = []

        # First show blue blocks with their arrows
        if hasattr(current_block, 'mergeset_blues'):
            for blue_block_name in current_block.mergeset_blues:
                if blue_block_name in self.blocks and blue_block_name != current_block.selected_parent.name:
                    blue_block = self.blocks[blue_block_name]
                    animations.append(blue_block.rect.animate.set_color(PURE_BLUE).set_opacity(1.0))

                    # Highlight arrows from blue blocks
                    if hasattr(blue_block, 'outgoing_arrows'):
                        for arrow in blue_block.outgoing_arrows:
                            if hasattr(arrow, 'target_block'):
                                target_name = arrow.target_block.name
                                # Show arrows to other blue blocks or selected parent
                                if (target_name in current_block.mergeset_blues or
                                        target_name == current_block.selected_parent.name):
                                    animations.append(arrow.animate.set_color(PURE_BLUE).set_opacity(1.0))

                                    # Then show red blocks with their arrows
        if hasattr(current_block, 'mergeset_reds'):
            for red_block_name in current_block.mergeset_reds:
                if red_block_name in self.blocks:
                    red_block = self.blocks[red_block_name]
                    animations.append(red_block.rect.animate.set_color(PURE_RED).set_opacity(1.0))

                    # Highlight arrows from red blocks with reduced opacity
                    if hasattr(red_block, 'outgoing_arrows'):
                        for arrow in red_block.outgoing_arrows:
                            animations.append(arrow.animate.set_color(PURE_RED).set_opacity(0.6))

        return AnimationGroup(*animations, run_time=0.7) if animations else Wait(0.1)

    def _show_k_cluster_check(self, current_block, candidate_block_name):
        """Show the k-cluster validation process with anticone arrows highlighted"""
        animations = []

        # Highlight the candidate being checked
        candidate_block = self.blocks[candidate_block_name]
        animations.append(candidate_block.rect.animate.set_color(YELLOW).set_opacity(1.0))

        # Show the chain blocks being checked against
        parent_chain = self._get_parent_chain(current_block.name)
        for chain_block_name in parent_chain:
            if chain_block_name in self.blocks:
                chain_block = self.blocks[chain_block_name]
                if hasattr(chain_block, 'mergeset_blues'):
                    # Highlight blue blocks in the chain that affect the anticone calculation
                    for blue_name in chain_block.mergeset_blues:
                        if blue_name in self.blocks and blue_name != candidate_block_name:
                            blue_block = self.blocks[blue_name]
                            # Check if this blue block is in the anticone of candidate
                            if not self._is_ancestor(blue_block, candidate_block):
                                animations.append(blue_block.rect.animate.set_color(BLUE).set_opacity(1.0))

                                # Highlight arrows showing the anticone relationship
                                # (no direct arrows between anticone blocks, but show their connections to common ancestors)
                                if hasattr(blue_block, 'outgoing_arrows'):
                                    for arrow in blue_block.outgoing_arrows:
                                        if hasattr(arrow, 'target_block'):
                                            target_name = arrow.target_block.name
                                            if target_name in parent_chain:
                                                animations.append(arrow.animate.set_opacity(1.0))

        return AnimationGroup(*animations, run_time=0.5) if animations else Wait(0.1)

    def _generate_semantic_name(self, block_type: type, parents: list, layer: int = None) -> str:
        """Generate semantically meaningful names."""
#        type_prefix = block_type.__name__.replace('Block', '')[0]  # 'G' for GhostDAG

# Never used since "Gen" is parent name created on init.
#        if not parents:
#            return f"{type_prefix}_Genesis"

            # Find the target layer (where this block will be placed)
        if layer is None:
            parent_names = [p.name if hasattr(p, 'name') else p for p in parents]
            top_parent_layer = self._find_top_parent_layer(parent_names)
            target_layer = self._find_available_layer(top_parent_layer)
        else:
            target_layer = layer

            # Count existing blocks in target layer
        block_count_in_layer = len(self.layers[target_layer]) if target_layer < len(self.layers) else 0

        return f"L{target_layer}_{block_count_in_layer + 1}"

    def create_tree_animation_fast(self, vertical_offset=0.5, horizontal_offset=1.25):
        # Calculate positions as before
        best_tip = self._find_best_tip()
        if not best_tip:
            return AnimationGroup(Wait(0.1))

        parent_chain = self._get_parent_chain(best_tip)
        new_positions = self._calculate_chain_tree_positions_ordered(parent_chain, vertical_offset, horizontal_offset)

        # Set fade properties directly (no animation)
        best_tip_block = self.blocks[best_tip]
        past_blocks = best_tip_block.get_past_blocks()
        highlighted_blocks = past_blocks.copy()
        highlighted_blocks.add(best_tip)

        # Collect all red and blue blocks from the parent chain
        red_blocks = set()
        blue_blocks = set()

        for chain_block_name in parent_chain:
            chain_block = self.blocks[chain_block_name]
            if hasattr(chain_block, 'mergeset_reds'):
                red_blocks.update(chain_block.mergeset_reds)
            if hasattr(chain_block, 'mergeset_blues'):
                blue_blocks.update(chain_block.mergeset_blues)

        for block_name, block in self.blocks.items():
            if block_name not in highlighted_blocks:
                block.rect.set_opacity(0.2)
                if hasattr(block, 'label') and block.label:
                    block.label.set_opacity(0.2)
                if hasattr(block, 'outgoing_arrows'):
                    for arrow in block.outgoing_arrows:
                        arrow.set_opacity(0.2)
            else:
                # Apply specific coloring based on GHOSTDAG data
                if block_name in red_blocks:
                    block.rect.set_color(PURE_RED, family=False)
                if block_name in blue_blocks:
                    block.rect.set_color(PURE_BLUE, family=False)

#                    # Set full opacity for highlighted blocks
#                block.rect.set_opacity(1.0)
#                if hasattr(block, 'label') and block.label:
#                    block.label.set_opacity(1.0)
#                if hasattr(block, 'outgoing_arrows'):
#                    for arrow in block.outgoing_arrows:
#                        if hasattr(arrow, 'target_block') and arrow.target_block.name in highlighted_blocks:
#                            arrow.set_opacity(1.0)

            for red_block_name in red_blocks:
                if red_block_name in self.blocks and red_block_name in highlighted_blocks:
                    red_block = self.blocks[red_block_name]
                    if hasattr(red_block, 'outgoing_arrows'):
                        for arrow in red_block.outgoing_arrows:
                            arrow.set_opacity(0.2)
            # NEW: Handle arrows TO red blocks
            for block_name, block in self.blocks.items():
                if hasattr(block, 'outgoing_arrows'):
                    for arrow in block.outgoing_arrows:
                        if (hasattr(arrow, 'target_block') and
                                arrow.target_block.name in red_blocks and
                                arrow.target_block.name in highlighted_blocks):
                            arrow.set_opacity(0.2)

        # Only animate the movement
        movement_animations = []
        for block_name, new_pos in new_positions.items():
            if block_name in self.blocks:
                current_block = self.blocks[block_name]
                movement_animations.append(current_block.rect.animate.move_to(new_pos))

        return AnimationGroup(*movement_animations, run_time=1.0)

    def _calculate_chain_tree_positions_ordered(self, parent_chain, v_offset, h_offset):
        """Calculate positions with parent chain at bottom and mergesets ordered by blue work"""
        new_positions = {}

        # Position parent chain blocks at the bottom
        chain_y = min(block.rect.get_center()[1] for block in self.blocks.values())

        for i, block_name in enumerate(reversed(parent_chain)):  # Genesis first
            current_block = self.blocks[block_name]
            current_x = current_block.rect.get_center()[0]  # Keep current x position
            new_positions[block_name] = [current_x, chain_y, 0]

            # Position mergeset blocks above, ordered by distance from parent chain
            if hasattr(current_block, 'mergeset') and current_block.mergeset:
                # Sort mergeset blocks by blue_count (ascending = closest to parent chain first)
                mergeset_blocks = list(current_block.mergeset)
                ordered_mergeset = self._sort_mergeset_by_distance_to_chain(mergeset_blocks, current_block)

                for j, mergeset_block_name in enumerate(ordered_mergeset):
                    if mergeset_block_name in self.blocks:
                        mergeset_x = current_x - h_offset
                        # Position closer blocks (lower blue_count) closer to chain
                        mergeset_y = chain_y + v_offset + (j * 0.5)
                        new_positions[mergeset_block_name] = [mergeset_x, mergeset_y, 0]

        return new_positions

    def _sort_mergeset_by_distance_to_chain(self, mergeset_blocks, chain_block):
        """Sort mergeset blocks by their distance from the parent chain (blue_count ascending)"""

        def get_distance_key(block_name):
            block = self.blocks[block_name]
            blue_count = getattr(block, 'blue_count', 0)
            block_hash = getattr(block, 'hash', block_name)
            # Lower blue_count = closer to parent chain = should be positioned first
            return (blue_count, block_hash)

        return sorted(mergeset_blocks, key=get_distance_key)

    def _find_best_tip(self):
        """Find tip block with most blue work (blue blocks in past)"""
        tips = [name for name, block in self.blocks.items() if not block.children]
        if not tips:
            return None

        best_tip = None
        max_blue_count = -1  # Changed from max_blue_work

        for tip_name in tips:
            tip_block = self.blocks[tip_name]
            # Use blue_count for comparison
            current_blue_count = tip_block.blue_count  # Changed from tip_block.weight
            if current_blue_count > max_blue_count:  # Changed from max_blue_work
                max_blue_count = current_blue_count  # Changed from max_blue_work
                best_tip = tip_name

        return best_tip

    def _get_parent_chain(self, tip_name):
        """Get the selected parent chain from tip to genesis"""
        chain = []
        current = self.blocks[tip_name]

        while current:
            chain.append(current.name)
            current = getattr(current, 'selected_parent', None)

        return chain

    def _calculate_chain_tree_positions(self, parent_chain, v_offset, h_offset):
        """Calculate positions with parent chain at bottom and mergesets above"""
        new_positions = {}

        # Position parent chain blocks at the bottom, maintaining current horizontal spacing
#        chain_y = min(block.rect.get_center()[1] for block in self.blocks.values()) - v_offset
        chain_y = min(block.rect.get_center()[1] for block in self.blocks.values())

        for i, block_name in enumerate(reversed(parent_chain)):  # Genesis first
            current_block = self.blocks[block_name]
            current_x = current_block.rect.get_center()[0]  # Keep current x position
            new_positions[block_name] = [current_x, chain_y, 0]

            # Position mergeset blocks above and slightly left
            if hasattr(current_block, 'mergeset') and current_block.mergeset:
                mergeset_blocks = list(current_block.mergeset)
                for j, mergeset_block_name in enumerate(mergeset_blocks):
                    if mergeset_block_name in self.blocks:
                        mergeset_x = current_x - h_offset
                        mergeset_y = chain_y + v_offset + (j * 0.5)  # Stack vertically if multiple
                        new_positions[mergeset_block_name] = [mergeset_x, mergeset_y, 0]

        return new_positions

    def add(self, parent_names, selected_parent=None, random_sp=False, name= None, *args, **kwargs):
        if isinstance(parent_names, str):
            parent_names = [parent_names]
        name = self._generate_semantic_name(block_type=self.block_type, parents=parent_names, layer=selected_parent)
        print(name)
            # Force random_sp=False and maintain GhostDAGBlock behavior
        return super().add(name, parent_names, selected_parent=None, random_sp=False, *args, **kwargs)

    def highlight_random_block_and_past(self, scene):
        """
        Pick a random block and instantly set opacity for everything else,
        keeping only the selected block and its past visible
        """
        from random import choice

        if not self.blocks:
            return

        random_block_name = choice(list(self.blocks.keys()))
        random_block = self.blocks[random_block_name]

        past_blocks = set()
        if hasattr(random_block, 'get_past_blocks'):
            past_blocks = random_block.get_past_blocks()
        else:
            past_blocks = self._get_past_blocks_recursive(random_block)

        highlighted_blocks = past_blocks.copy()
        highlighted_blocks.add(random_block_name)

        # No animations list needed, as we're setting properties directly
        for block_name, block in self.blocks.items():
            if block_name not in highlighted_blocks:
                block.rect.set_opacity(0.2)
                if hasattr(block, 'label') and block.label:
                    block.label.set_opacity(0.2)
                if hasattr(block, 'outgoing_arrows'):
                    for arrow in block.outgoing_arrows:
                        arrow.set_opacity(0.2)
            else:
                block.rect.set_opacity(1.0)
                if hasattr(block, 'label') and block.label:
                    block.label.set_opacity(1.0)
                if hasattr(block, 'outgoing_arrows'):
                    for arrow in block.outgoing_arrows:
                        if hasattr(arrow, 'target_block') and arrow.target_block.name in highlighted_blocks:
                            arrow.set_opacity(1.0)

                            # Return an empty AnimationGroup or None if no animations are desired
        return AnimationGroup(Wait(0.1))

    def fade_except_parent_arrows(self, scene):
        """
        Set opacity to fade everything except the selected parent arrows (blue arrows)
        """
        # No animations list needed, as we're setting properties directly
        for block_name, block in self.blocks.items():
            # Fade block rectangles to low opacity
            block.rect.set_opacity(0.2)

            # Fade block labels to low opacity
            if hasattr(block, 'label') and block.label:
                block.label.set_opacity(0.2)

                # Handle arrows - fade all arrows first, then restore selected parent arrows
            if hasattr(block, 'outgoing_arrows'):
                for arrow in block.outgoing_arrows:
                    arrow.set_opacity(0.2)

                    # Keep selected parent arrows at full opacity
                    if (hasattr(arrow, 'target_block') and
                            arrow.target_block == block.selected_parent):
                        arrow.set_opacity(1.0)

                        # Return an empty AnimationGroup or None if no animations are desired
        return AnimationGroup(Wait(0.1))

    def _get_past_blocks_recursive(self, block, visited=None):
        """Helper method to recursively get all blocks in the past"""
        if visited is None:
            visited = set()

        for parent in block.parents:
            if parent.name not in visited:
                visited.add(parent.name)
                self._get_past_blocks_recursive(parent, visited)

        return visited

    def reset_all_opacity(self, scene):
        """Reset all blocks and pointers to full opacity instantly."""
        # No animations list needed, as we're setting properties directly
        for block_name, block in self.blocks.items():
            block.rect.set_opacity(1.0)
            if hasattr(block, 'label') and block.label:
                block.label.set_opacity(1.0)
                # Assuming 'pointer' refers to the incoming arrow, and 'outgoing_arrows' are also tracked
            if hasattr(block, 'pointer') and block.pointer:
                block.pointer.set_opacity(1.0)
            if hasattr(block, 'outgoing_arrows'):
                for arrow in block.outgoing_arrows:
                    arrow.set_opacity(1.0)

                    # Return an empty AnimationGroup or None if no animations are desired
        return AnimationGroup(Wait(0.1))

    def get_tips(self, missed_blocks=0):
        """Get tip blocks for parent selection, similar to LayerDAG"""
        # This should return available tip blocks for parent selection
        # You'll need to implement this based on your block structure
        if hasattr(super(), 'get_tips'):
            return super().get_tips(missed_blocks)
        else:
            # Fallback implementation
            tips = [name for name, block in self.blocks.items() if block.is_tip()]
            return tips

class Miner():
    def __init__(self, scene, x=0 , y=0, attempts = 20):
        self.scene = scene
        self.x = x
        self.y = y
        self.attempts = attempts
        self.nonce = randint(10000,99000)
        self.parts = {}
        self.rect = Rectangle(
            color=RED,
            fill_opacity=1,
            height = 2,
            width = 3
        )
        self.rect.move_to([x,y,0])
        self.lpar = Tex(r"(",font_size = 220)
        self.lpar.move_to([x-1.8,y,0])
        self.rpar = Tex(r")",font_size = 220)
        self.rpar.move_to([x+1.8,y,0])
        self.eq = Tex(r"=",font_size = 100)
        self.eq.move_to([x+2.7,y,0])
        self.H = Tex(r"\textsf{H}", font_size = 100)
        self.H.move_to([x-2.6,y,0])
        self.header = Rectangle(
            color=BLACK,
            fill_opacity=1,
            height = 0.5,
            width = 2.8
        )
        self.header.move_to([x,y+0.6,0])
        self.nonce_label = Text("Nonce: " + str(self.nonce), font_size = 30)
        self.nonce_label.move_to([x,y+0.6,0])
        self.hash = self._nexthash()
        self.hash.move_to([x+7,y,0])
        scene.add(self.rect, self.H, self.lpar, self.rpar, self.eq, self.header, self.nonce_label, self.hash)
        scene.wait(0.5)

    def _nexthash(self, win=False, color=RED):
        nhash = Text(("0"*10 if win else fake_sha(10)) + "..." + fake_sha(), font_size = 50, color=color, font="Monospace")
        nhash.move_to([self.x+7,self.y,0])
        return nhash

    def update(self):
        self.nonce += 1
        self.attempts -= 1
        newnonce = Text("Nonce: " + str(self.nonce), font_size = 30)
        newnonce.move_to([self.x,self.y+0.6,0])
        self.scene.play(Unwrite(self.hash),run_time = 0.3)
        self.scene.play(Transform(self.nonce_label, newnonce))
        self.hash = self._nexthash(win = not bool(self.attempts),color=WHITE)
        self.scene.play(Write(self.hash),run_time = 0.3)
        self.scene.play(FadeToColor(self.hash, RED if self.attempts else BLUE))

    def mining(self):
        return self.attempts > 0

def fake_sha(n=6):
    return ''.join(choice(string.ascii_lowercase[:6]+string.digits[1:]) for _ in range(n))

class Node(Square):
    def __init__(self, peers:list = []):
        super().__init__()
        # Create a Node with a list of peers

        self.side_length = 0.8
        self.set_fill("#0000FF", opacity=1)

        if peers:
            self.peers_list = peers

    def set_blue(self):
        self.set_fill("0000FF", opacity=1, family=False)

    def set_red(self):
        self.set_fill("#FF0000", opacity=1, family=False)

# TODO incomplete, not yet started

class PHANTOM:
    def __init__(self, blocks:int = 0):
        self.blocks_to_create = blocks
        self.all_blocks = [] #all blocks added to the chain
        self.narration_text_mobject = NarrationMathTex()

        # Create Genesis
        block = BlockMob(None, "Gen")
        self.all_blocks.append(block)

        self.create_blocks_and_pointers(self.blocks_to_create - 1)

    def create_blocks_and_pointers(self, number_of_blocks_to_create:int = 0):
        # Create chain of BlockMob
        i = 0

        while i < number_of_blocks_to_create:
            parent = self.all_blocks[-1]

            block = BlockMob(parent)
            self.all_blocks.append(block)

            pointer = Pointer(block, parent)
            block.pointers.append(pointer)

            i += 1

    # returns animations for adding all blocks and pointers
    def add_chain(self, scene):
        add_chain_one_by_one_with_fade_in = []

        for each in self.all_blocks:

            add_chain_one_by_one_with_fade_in.append(
                AnimationGroup(
                    scene.camera.frame.animate.move_to(each.get_center()),
                    FadeIn(each),
                )
            )

            for pointer in each.pointers:
                add_chain_one_by_one_with_fade_in.append(
                    AnimationGroup(
                        FadeIn(pointer)
                    )
            )

            add_chain_one_by_one_with_fade_in.extend(
                [Wait(0.5)],
            )

        add_chain_one_by_one_with_fade_in.append(
            AnimationGroup(
                scene.camera.auto_zoom(self.all_blocks, margin= 1.0),
            )
        )

        add_chain_one_by_one_with_fade_in.append(Wait(run_time=0))
        return Succession(*add_chain_one_by_one_with_fade_in)

    def add_blocks(self, scene, how_many_blocks_to_add:int = 1):
        add_blocks_one_by_one_with_fade_in = []

        # Create blocks to add
        self.create_blocks_and_pointers(how_many_blocks_to_add)

        for each in self.all_blocks[-how_many_blocks_to_add:]:

            add_blocks_one_by_one_with_fade_in.append(
                AnimationGroup(
                    scene.camera.frame.animate.move_to(each.get_center()),
                    FadeIn(each),
                )
            )

            for pointer in each.pointers:
                add_blocks_one_by_one_with_fade_in.append(
                    AnimationGroup(
                        FadeIn(pointer)
                    )
            )

            add_blocks_one_by_one_with_fade_in.extend(
                [Wait(0.5)],
            )

        add_blocks_one_by_one_with_fade_in.append(
            AnimationGroup(
                scene.camera.auto_zoom(self.all_blocks, margin= 1.0),
            )
        )

        add_blocks_one_by_one_with_fade_in.append(Wait(run_time=0))
        return Succession(*add_blocks_one_by_one_with_fade_in)

    def create_fork(self, scene, how_many_blocks_to_add:int = 1, from_depth:int = 1):
        add_blocks_one_by_one_with_fade_in = []

        # Create forked blocks to add
        fork = [self.all_blocks[-from_depth -1]]

        i = 0
        while i < how_many_blocks_to_add:
            parent = fork[-1]

            block = BlockMob(parent)
            fork.append(block)

            pointer = Pointer(block, parent)
            block.pointers.append(pointer)

            i += 1

        self.all_blocks = list(set(self.all_blocks + fork))

        fork[1].shift_fork() # TODO Replace with position handling based on rounds_from_genesis

        for each in fork[1:]:

            add_blocks_one_by_one_with_fade_in.append(
                AnimationGroup(
                    scene.camera.frame.animate.move_to(each.get_center()),
                    FadeIn(each),
                )
            )

            for pointer in each.pointers:
                add_blocks_one_by_one_with_fade_in.append(
                    AnimationGroup(
                        FadeIn(pointer)
                    )
            )

            add_blocks_one_by_one_with_fade_in.extend(
                [Wait(0.5)],
            )

        add_blocks_one_by_one_with_fade_in.append(
            AnimationGroup(
                scene.camera.auto_zoom(self.all_blocks, margin= 1.0),
            )
        )

        add_blocks_one_by_one_with_fade_in.append(Wait(run_time=0))
        return Succession(*add_blocks_one_by_one_with_fade_in)

    ####################
    # Get past/future/anticone and blink
    ####################

    # returns group of blink animations on past of block at selected round
    def blink_past_of_random_block(self):
        random_block: 'Mobject' = choice(self.all_blocks)
        blink_past_animations = []
        current_list_to_blink = random_block.get_past()
        blink_past_animations.append(random_block.highlight_self())

        for each in current_list_to_blink:
            blink_past_animations.append(each.blink())

        blink_past_animations.append(Wait(run_time=0.1)) # added to prevent random block not having past and breaking animation with no runtime
        return AnimationGroup(*blink_past_animations)

    # returns group of blink animations on future of block at selected round
    def blink_future_of_random_block(self):
        random_block: 'Mobject' = choice(self.all_blocks)
        blink_future_animations = []
        current_list_to_blink = random_block.get_future()
        blink_future_animations.append(random_block.highlight_self())

        for each in current_list_to_blink:
            blink_future_animations.append(each.blink())

        blink_future_animations.append(Wait(run_time=0.1)) # added to prevent random block not having future and breaking animation with no runtime
        return AnimationGroup(*blink_future_animations)

    # returns group of blink animations on anticone of block at selected round
    def blink_anticone_of_random_block(self):
        random_block: 'Mobject' = choice(self.all_blocks)
        blink_anticone_animations = []

        # need to get past and get future, need to get all blocks from all_blocks, and compare
#        list_of_blocks_not_in_past = list(set(self.all_blocks) - set(random_block.get_past()))
#        list_of_blocks_not_in_past_or_future = list(set(list_of_blocks_not_in_past) - set(random_block.get_future()))
#        anticone = list(set(list_of_blocks_not_in_past_or_future) - set(random_block))
        list_of_blocks_reachable = list(set(self.all_blocks) - set(random_block.get_reachable()))
        anticone = list(set(list_of_blocks_reachable) - set(random_block))

        blink_anticone_animations.append(random_block.highlight_self())

        for each in anticone:
            blink_anticone_animations.append(each.blink())

        blink_anticone_animations.append(Wait(run_time=0.1)) # added to prevent random block not having future and breaking animation with no runtime
        return AnimationGroup(*blink_anticone_animations)

    ####################
    # Testing animation
    ####################

    # Gradually moves when called in scene, moving slowly enough allows updaters to keep up
    def smooth_genesis(self):
        animations = []

        animations.append(
            self.all_blocks[0].animate.shift(UP*1)
        )

        return AnimationGroup(animations)

    # TODO test this
    ####################
    # Positioning BlockMobs in DAG
    ####################

    # return an animation that adjusts the consensus rounds based on how many rounds_from_genesis for list(blocks passed)

    def adjust_consensus_round(self, blocks_added:list):
        adjust_rounds_affected_animations = []

        for each in blocks_added:
            consensus_round = each.rounds_from_genesis

            all_blocks_at_this_round = list(set(self.get_all_blocks_at_this_round(consensus_round)))

            # Create animations and add to animations to adjust these blocks at this depth

            adjust_rounds_affected_animations.append(self.adjust_consensus_round_animations(all_blocks_at_this_round))

        return AnimationGroup(adjust_rounds_affected_animations)

    def adjust_consensus_round_animations(self, all_blocks_at_this_round:list):
        animations = []

        # find all y position
        list_of_y_positions:list = []

        for each in all_blocks_at_this_round:
            position_of_each_block = each.get_center()
            list_of_y_positions.append(position_of_each_block[1])

        # Adjust their position to space them from each other and move to position from center (y = 0)
        y_min = min(list_of_y_positions)
        y_max = max(list_of_y_positions)
        adjust_by = (abs(y_min) + abs(y_max)) / all_blocks_at_this_round

        if abs(y_min) > abs(y_max):
            adjust_up = True
        else:
            adjust_up = False

        # Create the animations that move blocks in this round by + or - adjust_by
        # TODO finish creating animations that adjust rounds for DAG


        return AnimationGroup(animations)

    def get_all_blocks_at_this_round(self, consensus_round:int):
        all_blocks_at_this_round = []

        for each in self.all_blocks:
            if each.rounds_from_genesis == consensus_round:
                all_blocks_at_this_round.append(each)

        all_blocks_at_this_round = list(set(all_blocks_at_this_round))
        return all_blocks_at_this_round

# TODO incomplete, building

class Bitcoin:
    def __init__(
            self,
            scene
    ):
        """
        :param scene: self

        Scene is used for handling camera animations.
        Bitcoin currently supports a chain and competing fork
        """
        self.scene = scene

        self.all_blocks = [] # all blocks added to the chain
#        self.narration_text_mobject = NarrationMathTex() # currently unused

        # Create Genesis
        genesis = BTCBlock(None, "Gen")
        self.all_blocks.append(genesis)

    def genesis(self):
        """
        Must create Genesis first.
        If not, there will be no blocks the point to.
        """
        genesis = self.all_blocks[0]
        return [Succession(
                Wait(1.0),
                FadeIn(genesis),
                Wait(0.5)
            )]

# TODO change to add to longest chain
    def add_block(self):
        """
        Creates a new block, a pointer, and returns an animation that adds a single block to the chain.
        """
        block = BTCBlock(self.all_blocks[-1])
        self.all_blocks.append(block)
        pointer = Pointer(block, block.parent)

        return [AnimationGroup(
                [self.scene.camera.frame.animate.move_to([block.get_x(), 0, 0]),
                FadeIn(block),
                FadeIn(pointer)],
                Wait(0.5)
            )]

# TODO only one needed, add_block_to_chain or add_block
    def add_blocks(self, number_of_blocks_to_add:int = 1):
        """
        :param number_of_blocks_to_add: desired number of blocks to add to the chain.

        Returns an animation that plays one by one adding the desired number of blocks to the chain.
        """
        add_blocks_animations = []

        i = 0
        while i < number_of_blocks_to_add:
            add_blocks_animations.extend(
                self.add_block()
            )
            i += 1

        return Succession(add_blocks_animations)

    def add_first_fork_block(self, fork_depth):
        """
        :param fork_depth: desired depth to begin fork from tip.

        Creates a new block, a pointer, and returns an animation that adds a single fork block to the chain.
        """
        block = BTCBlock(self.all_blocks[-fork_depth - 1])
        self.all_blocks.append(block)
        block.is_fork = True
        pointer = Pointer(block, block.parent)

        block.set_y(-2)

        return [AnimationGroup(
                [self.scene.camera.frame.animate.move_to([block.get_x(), 0, 0]),
                FadeIn(block),
                FadeIn(pointer)],
                Wait(0.5)
            )]

    def add_block_to_chain(self):
        """
        Creates a new block, a pointer, and returns an animation that adds a single block to the longest chain.
        """
        tips = self.get_longest_chain_tips()
        original_chain_tip = tips[0] # pick one, if multiple tips have same weight,

        block = BTCBlock(original_chain_tip)
        self.all_blocks.append(block)
        pointer = Pointer(block, block.parent)

        return [AnimationGroup(
                [self.scene.camera.frame.animate.move_to([block.get_x(), 0, 0]),
                FadeIn(block),
                FadeIn(pointer)],
                Wait(0.5)
            )]

    def add_block_to_fork(self):
        """"""
        # determine the most recent fork chain
        fork_chain_tip = self.find_most_recent_forked_block()

        block = BTCBlock(fork_chain_tip)
        self.all_blocks.append(block)
        pointer = Pointer(block, block.parent)

        return [AnimationGroup(
                [self.scene.camera.frame.animate.move_to([block.get_x(), 0, 0]),
                FadeIn(block),
                FadeIn(pointer)],
                Wait(0.5)
            )]

    def find_most_recent_forked_block(self):
        tips = self.get_tips()

        for each in reversed(tips):
            if each.is_from_fork():
                return each
            else:
                ...

        return None

    def move_camera_to(self, name_of_block:int):
        """
        :param name_of_block: int of block rounds from genesis

        BTC blocks are named by weight,
        except Genesis, named 'Gen',
        move_to will adjust cameras center position to the desired round from genesis.

        """
        block = None

        for each in self.all_blocks:
            if each.name == name_of_block:
                block = each
                break

        return AnimationGroup(
#            self.scene.camera.frame.animate.move_to(block)
            self.scene.camera.frame.animate.move_to([block.get_x(), 0, 0])

        )

    def get_tips(self):
        """
        Returns a list of all tips.
        """
        tips = []

        for each in self.all_blocks:
            if each.is_tip():
                tips.append(each)

        return tips

    def get_heaviest_two_tips(self):
        """
        Return a sorted list of the heaviest two tips.
        Heaviest tip [0]
        Lighter tip [1]
        Unless tip weight is the same
        """
        tips = self.get_tips()
        tip_1 = tips[0]
        tip_2 = tips[1]

        if tip_1.get_weight() > tip_2.get_weight():
            sorted_tips = [tip_1, tip_2]
        else:
            sorted_tips = [tip_2, tip_1]

        return sorted_tips

    def get_longest_chain_tips(self):
        """
        Returns a list of blocks with the most blocks in its past.
        If a single tip is the heaviest, list will only have one block,
        If multiple tips exist with the same weight, list will have multiple blocks.
        """
        tips = self.get_tips()

        weight_of_each_tip = [each.weight for each in tips]
        most_blocks_in_past = max(weight_of_each_tip)

        return [each for each in tips if each.weight == most_blocks_in_past]

    def get_past_of_tips(self):
        """
        Returns a list of blocks in the past of the tips provided,
        back to and excluding the most recent common ancestor.
        """
        tips_to_find_blocks = self.get_heaviest_two_tips()

        if len(tips_to_find_blocks) == 1:
            print("incorrect usage of get_past_of_tips")
            return

        lists_of_past_blocks = []

        for each in tips_to_find_blocks:
            lists_of_past_blocks.append(each.get_self_inclusive_past())

        set_of_tip_0 = set(lists_of_past_blocks[0])
        set_of_tip_1 = set(lists_of_past_blocks[1])

        set_of_blocks_unique_to_0 = set_of_tip_0 - set_of_tip_1
        set_of_blocks_unique_to_1 = set_of_tip_1 - set_of_tip_0

        list_of_blocks_unique_to_0 = list(set_of_blocks_unique_to_0)
        list_of_blocks_unique_to_1 = list(set_of_blocks_unique_to_1)

        lists_of_past_blocks = [list_of_blocks_unique_to_0, list_of_blocks_unique_to_1]

        return lists_of_past_blocks

    def are_heaviest_two_tips_equal_weight(self):
        tips = self.get_heaviest_two_tips()

        if tips[0].get_weight() == tips[1].get_weight():
            return True
        else:
            return False

    def animate_these_blocks_blue(self, list_of_blocks:list):
        animate_turn_blue = []

        for each in list_of_blocks:
            animate_turn_blue.extend([each.fade_blue()])

        return AnimationGroup(
            animate_turn_blue
        )

    def animate_these_blocks_red(self, list_of_blocks:list):
        animate_turn_red = []

        for each in list_of_blocks:
            animate_turn_red.extend([each.fade_red()])

        return AnimationGroup(
            animate_turn_red
        )


    def adjust_block_color_by_longest_chain(self):
        """
        Returns animations to change block color depending on if they are part of the longest chain.
        """
        lists_of_past_blocks_of_tips = self.get_past_of_tips()
        block_color_animations = []

        if self.are_heaviest_two_tips_equal_weight():
            block_color_animations.append(self.animate_these_blocks_red(lists_of_past_blocks_of_tips[0])) # TODO change back to blue, using red for testing
            block_color_animations.append(self.animate_these_blocks_red(lists_of_past_blocks_of_tips[1]))
            return AnimationGroup(
                block_color_animations
            )
        else:
            pass



#        for each in lists_of_past_blocks_of_tips:
#            each.sort(key=lambda x: x.weight)

        return None # TODO change this to animations




    ####################
    # Get past/future/anticone and blink
    ####################

    def blink_these_blocks(self, blocks_to_blink:list):
        """
        Returns an animation that blinks all blocks in the list provided.
        """
        blink_these_animations = []
        current_list_to_blink = blocks_to_blink

        for each in current_list_to_blink:
            blink_these_animations.append(each.blink())

        return AnimationGroup(*blink_these_animations)

    def blink_past_of_random_block(self):
        """
        Returns an animation,
        picks a block at random and blinks the reachable past,
        while highlighting the block.
        """
        random_block = choice(self.all_blocks)
        blink_past_animations = []
        current_list_to_blink = random_block.get_past()
        blink_past_animations.append(random_block.highlight_self())

        for each in current_list_to_blink:
            blink_past_animations.append(each.blink())

        return AnimationGroup(*blink_past_animations)

    def blink_future_of_random_block(self):
        """
        Returns an animation,
        picks a block at random and blinks the reachable future,
        while highlighting the block.
        """
        random_block = choice(self.all_blocks)
        blink_future_animations = []
        current_list_to_blink = random_block.get_future()
        blink_future_animations.append(random_block.highlight_self())

        for each in current_list_to_blink:
            blink_future_animations.append(each.blink())

        return AnimationGroup(*blink_future_animations)

    def blink_anticone_of_random_block(self):
        """
        Returns an animation,
        picks a block at random and blinks the anticone(unreachable blocks),
        while highlighting the block.
        """
        random_block = choice(self.all_blocks)
        blink_anticone_animations = []

        list_of_blocks_reachable = list(set(self.all_blocks) - set(random_block.get_reachable()))
        anticone = list(set(list_of_blocks_reachable) - set(random_block))

        blink_anticone_animations.append(random_block.highlight_self())

        for each in anticone:
            blink_anticone_animations.append(each.blink())

        return AnimationGroup(*blink_anticone_animations)

    ####################
    # Testing animation
    ####################

    # Gradually moves when called in scene, moving slowly enough allows updaters to keep up
    def smooth_genesis(self):
        animations = []

        animations.append(
            self.all_blocks[0].animate.shift(UP*1)
        )

        return AnimationGroup(animations)

    # TODO rewrite this to use new functions created above
    ####################
    # Positioning Blocks in Bitcoin
    ####################

    # TODO test this and find a way to leave tips alone
    def adjust_chain_position(self):
        adjust_chain_animations = []

        for each_list in self.find_forks():
            heaviest_block = self.find_heaviest_block_looking_forward(each_list)
            position_of_heaviest_block = heaviest_block.get_position()
            delta_y_of_heaviest_block = abs(position_of_heaviest_block)

            if position_of_heaviest_block[1] == 0:
                ...  # do nothing
            elif position_of_heaviest_block[1] < 0:
                move_up_by = delta_y_of_heaviest_block
                for each in each_list:
                    adjust_chain_animations.append(
                        each.animate.shift(UP*move_up_by)
                    )
            else:
                move_down_by = delta_y_of_heaviest_block
                for each in each_list:
                    adjust_chain_animations.append(
                        each.animate.shift(UP*move_down_by)
                    )

        return AnimationGroup(adjust_chain_animations)

    def find_heaviest_block_looking_forward(self, blocks:list):

        heaviest_block = blocks[0]

        for each_block in blocks:
            if len(each_block.get_future()) > len(heaviest_block.get_future()):
                heaviest_block = each_block

        return heaviest_block

    def find_forks(self):

        forks = [] # list[[block, block], [block, block], [block, block, block], ...]

        for each in self.all_blocks:
            if len(each.childen) > 1:
                forks.append(each.children)

        return forks

    # return an animation that adjusts the consensus rounds based on how many rounds_from_genesis for list(blocks passed)

    def adjust_consensus_round(self, blocks_added:list):
        adjust_rounds_affected_animations = []

        for each in blocks_added:
            consensus_round = each.rounds_from_genesis

            all_blocks_at_this_round = list(set(self.get_all_blocks_at_this_round(consensus_round)))

            # Create animations and add to animations to adjust these blocks at this depth

            adjust_rounds_affected_animations.append(self.adjust_consensus_round_animations(all_blocks_at_this_round))

        return AnimationGroup(adjust_rounds_affected_animations)

# TODO test
    def adjust_consensus_round_animations(self, all_blocks_at_this_round:list):
        animations = []

        # find all y position
        list_of_y_positions:list = []

        for each in all_blocks_at_this_round:
            position_of_each_block = each.get_center()
            list_of_y_positions.append(position_of_each_block[1])

        # Adjust their position to space them from each other and move to position from center (y = 0)
        y_min = min(list_of_y_positions)
        y_max = max(list_of_y_positions)
        adjust_by = (abs(y_min) + abs(y_max)) / all_blocks_at_this_round

        if abs(y_min) > abs(y_max):
            adjust_up = True
        else:
            adjust_up = False

        if adjust_up:
            for each in all_blocks_at_this_round:
                animations.append(each.animate.shift(UP*adjust_by))
        else:
            for each in all_blocks_at_this_round:
                animations.append(each.animate.shift(DOWN*adjust_by))

        return AnimationGroup(animations)

    def get_all_blocks_at_this_round(self, consensus_round:int):
        all_blocks_at_this_round = []

        for each in self.all_blocks:
            if each.rounds_from_genesis == consensus_round:
                all_blocks_at_this_round.append(each)

        all_blocks_at_this_round = list(set(all_blocks_at_this_round))
        return all_blocks_at_this_round


# Succession returns animations to be played one by one
# AnimationGroup plays all animations together

class BlockMob(Square):
    def __init__(self,
                 selected_parent:'BlockMob' = None,
                 name:str = ""
                 ):
        super().__init__(
            color="#0000FF",
            fill_opacity=1,
            side_length=0.8,
            background_stroke_color=WHITE,
            background_stroke_width=10,
            background_stroke_opacity=1.0
        )
        self.set_blue()

        # set instance variables
        self.name = name
        self.parent = selected_parent
        self.weight = 1
        self.rounds_from_genesis = 0

        self.mergeset = []
        self.children = []
        self.pointers = []

        if self.parent:
            self.mergeset.append(self.parent)
            self.weight = self.get_number_of_blue_blocks_in_past() + 1 # Change to mergeset weight +1 # Does not account for k yet
            self.rounds_from_genesis = selected_parent.rounds_from_genesis + 1
            self.shift_position_to_parent() # Initial positioning only for locating relative to parent

        if self.mergeset:
            for each in self.mergeset:
                each.add_self_to_children(self)

        # name instead displays weight of the block
        if self.name != "Gen":
            self.name = self.rounds_from_genesis

        # changed label to text mobject, will attempt to create a latex mobject at a later date
        if self.name:
            self.label = Text(str(self.weight), font_size=24, color=WHITE, weight=BOLD)
            self.label.move_to(self.get_center())
            self.add(self.label)


    # Setters and getters

    def get_number_of_blue_blocks_in_past(self):
        return len(self.get_past())

    def fade_in(self):
        return AnimationGroup(
            self.animate(runtime=0.5).set_opacity(1)
        )

    def add_self_to_children(self, mobject):
        self.children.append(mobject)

    def is_tip(self):
        return bool(self.children)

    def set_label(self, to_label:str = ""):
        if self.label:
            self.remove(self.label)
        self.label = Text(to_label, font_size=24, color=WHITE, weight=BOLD)
        self.label.move_to(self.get_center())
        self.add(self.label)

    # TODO test this
    def fade_to_next_label(self, to_label: str = ""):
        animations = []

        # Fade out existing label if it exists
        if self.label:
            animations.append(FadeOut(self.label))

            # Create new label
        new_label = Text(to_label, font_size=24, color=WHITE, weight=BOLD)
        new_label.move_to(self.get_center())

        # Fade in new label
        animations.append(FadeIn(new_label))

        # Update the label reference
        self.label = new_label

        # Return animation sequence
        return Succession(*animations) if len(animations) > 1 else animations[0]

    ####################
    # Color Setters
    ####################
    # TODO test if adding run_time to setters will make them change color slowly
    def set_blue(self):
        self.set_color("#0000FF", family=False)

    def set_red(self):
        self.set_color("#FF0000", family=False)

    def set_to_color(self, to_color):
        self.set_color(to_color, family=False)

    def fade_blue(self):
        return self.animate.fade_to(color=PURE_BLUE, alpha=1.0, family=False)

    def fade_red(self):
        return self.animate.fade_to(color=PURE_RED, alpha=1.0, family=False)

    # fade_to_color ONLY works with ManimColor, does not work with hex format str
    def fade_to_color(self, to_color:ManimColor = WHITE):
        return self.animate.fade_to(color=to_color, alpha=1.0, family=False)

    ####################
    # Pointers Handling
    ####################

    def attach_pointer(self, pointer):
        self.pointers.append(pointer)

    ####################
    # Position Handling (Updaters leave position at [0,0,0])
    ####################

    # immediately changes position relative to self.parent, no animation, for setting initial position
    def shift_position_to_parent(self):
        self.next_to(self.parent, RIGHT * 4)
        if self.children:
            self.children[0].shift_position_to_parent()

    def shift_fork(self):
        self.next_to(self.parent, RIGHT * 4 + DOWN * 4)
        if self.children:
            self.children[0].shift_position_to_parent()

    ####################
    # Blink Animations
    ####################

    def blink(self):
        return Succession(
            ApplyMethod(self.set_color, YELLOW, False, run_time=0.8),
            ApplyMethod(self.set_color, self.color, False, run_time=0.8),
        )
        # Using ApplyMethod directly bypasses limitations of Manim FadeToColor

    def highlight_self(self):
        return Succession(
            ApplyMethod(self.set_color, GREEN, False, run_time=0.8),
            ApplyMethod(self.set_color, self.color, False, run_time=0.8),
        )

    ####################
    # Determine past/future/anticone
    ####################

    def get_future(self):
        future_of_this_block = []
        future_of_this_block.extend(self.children)

        for each in self.children:
            future_of_this_block.extend(each.get_future())

        duplicates_removed = list(set(future_of_this_block))
        return duplicates_removed

    def get_past(self):
        past_of_this_block = []
        past_of_this_block.extend(self.mergeset)

        for each in self.mergeset:
            past_of_this_block.extend(each.get_past())

        duplicates_removed = list(set(past_of_this_block))
        return duplicates_removed

    def get_reachable(self):
        reachable = []

        reachable.extend(self.get_past())
        reachable.extend(self.get_future())

        return reachable

class BTCBlock(Square):
    def __init__(self,
                 selected_parent:'BTCBlock' = None,
                 name:str = ""
                 ):
        super().__init__(
            color="#0000FF",
            fill_opacity=1,
            side_length=0.8,
            background_stroke_color=WHITE,
            background_stroke_width=10,
            background_stroke_opacity=1.0
        )
        self.set_blue()

        self.name = name
        self.parent = selected_parent
        self.mergeset = [] # Mergeset will only have one(parent) or none in BTC
        self.weight = 1
        self.rounds_from_genesis = 0
        self.is_fork = False

        self.children = []
        self.pointers = []

        if selected_parent is not None:
            self.mergeset.append(self.parent)
            self.weight = self.get_number_of_blocks_in_past() + 1
            self.rounds_from_genesis = selected_parent.rounds_from_genesis + 1
            self.shift_position_to_parent() # Only used to initially position blocks relative to parent along y axis
            self.parent.add_self_to_children(self)

        # name instead displays weight of the block
        if self.name != "Gen":
            self.name = self.weight

        # changed label to text mobject, will attempt to create a latex mobject at a later date
        if self.name:
            self.label = Text(str(self.name), font_size=24, color=WHITE, weight=BOLD)
            self.label.move_to(self.get_center())
            self.add(self.label)


    def add_self_to_children(self, mobject):
        self.children.append(mobject)

    def is_tip(self):
        return not bool(self.children)


    ####################
    # Color Setters
    ####################
    # TODO test if adding run_time to setters will make them change color slowly
    def set_blue(self):
        self.set_color("#0000FF", family=False)

    def set_red(self):
        self.set_color("#FF0000", family=False)

    def set_to_color(self, to_color):
        self.set_color(to_color, family=False)

    def fade_blue(self):
        return self.animate.fade_to(color=PURE_BLUE, alpha=1.0, family=False)

    def fade_red(self):
        return self.animate.fade_to(color=PURE_RED, alpha=1.0, family=False)

    # fade_to_color ONLY works with ManimColor, does not work with hex format str
    def fade_to_color(self, to_color:ManimColor = WHITE):
        return self.animate.fade_to(color=to_color, alpha=1.0, family=False)

    ####################
    # Label Handling
    ####################

    def set_label(self, to_label:str = ""):
        if self.label:
            self.remove(self.label)
        self.label = Text(to_label, font_size=24, color=WHITE, weight=BOLD)
        self.label.move_to(self.get_center())
        self.add(self.label)

    # TODO test this
    def fade_to_next_label(self, to_label: str = ""):
        animations = []

        # Fade out existing label if it exists
        if self.label:
            animations.append(FadeOut(self.label))

            # Create new label
        new_label = Text(to_label, font_size=24, color=WHITE, weight=BOLD)
        new_label.move_to(self.get_center())

        # Fade in new label
        animations.append(FadeIn(new_label))

        # Update the label reference
        self.label = new_label

        # Return animation sequence
        return Succession(*animations) if len(animations) > 1 else animations[0]

    ####################
    # Pointers Handling
    ####################

    def attach_pointer(self, pointer):
        self.pointers.append(pointer)

    ####################
    # Position Handling (Updaters leave position at [0,0,0])
    ####################

    # immediately changes position relative to self.parent, no animation, for setting initial position
    def shift_position_to_parent(self):
        self.next_to(self.parent, RIGHT * 4)
        if self.children:
            self.children[0].shift_position_to_parent()

    ####################
    # Animations
    ####################

    def fade_in(self):
        return AnimationGroup(
            self.animate(runtime=0.5).set_opacity(1)
        )

    ####################
    # Blink Animations
    ####################

    # Using ApplyMethod directly bypasses limitations of Manim FadeToColor

    def blink(self):
        return Succession(
            ApplyMethod(self.set_color, YELLOW, False, run_time=0.8),
            ApplyMethod(self.set_color, self.color, False, run_time=0.8),
        )

    def highlight_self(self):
        return Succession(
            ApplyMethod(self.set_color, GREEN, False, run_time=0.8),
            ApplyMethod(self.set_color, self.color, False, run_time=0.8),
        )

    ####################
    # Determine past/future/anticone
    ####################

    def get_future(self):
        """
        Returns an ordered list of the future blocks, sorted by weight
        """
        future_of_this_block = []
        future_of_this_block.extend(self.children)

        for each in self.children:
            future_of_this_block.extend(each.get_future())

        duplicates_removed = list(set(future_of_this_block))

        ordered_future = self.order_list_by_weight(duplicates_removed)

        return ordered_future

    def get_past(self):
        """
        Returns an ordered list of the past blocks, sorted by weight
        """
        past_of_this_block = []
        past_of_this_block.extend(self.mergeset)

        for each in self.mergeset:
            past_of_this_block.extend(each.get_past())

        duplicates_removed = list(set(past_of_this_block))

        ordered_past = self.order_list_by_weight(duplicates_removed)

        return ordered_past

    def get_self_inclusive_past(self):
        """
        Returns an ordered list of the past, self inclusive, blocks, sorted by weight
        """
        past_of_this_block = [self]
        past_of_this_block.extend(self.mergeset)

        for each in self.mergeset:
            past_of_this_block.extend(each.get_past())

        duplicates_removed = list(set(past_of_this_block))

        ordered_past = self.order_list_by_weight(duplicates_removed)

        return ordered_past


    def order_list_by_weight(self, list_to_order:list):
        list_to_order.sort(key=lambda x: x.weight)

        return list_to_order

    def get_reachable(self):
        """
        Returns an ordered list of the reachable blocks, sorted by weight
        """
        reachable = []

        reachable.extend(self.get_past())
        reachable.extend(self.get_future())

        return reachable

    def get_number_of_blocks_in_future(self):
        return len(self.get_future())

    def get_number_of_blocks_in_past(self):
        return len(self.get_past())

    def get_number_of_blocks_in_reachable(self):
        return len(self.get_reachable())

    def is_from_fork(self):
        if self.is_fork:
            return True

        list_of_past_blocks = self.get_past()

        for each in reversed(list_of_past_blocks):
            print(each.is_fork)
            if each.is_fork:
                return True
            else:
                pass

        return False

class Pointer(Line):
    def __init__(self, this_block, parent_block):
        # Initialize with proper start/end points
        super().__init__(
            start=this_block.get_left(),
            end=parent_block.get_right(),
            buff=0.1,
            color=BLUE,
            stroke_width=5,  # Set stroke width directly
            cap_style = CapStyleType.ROUND
        )

        self.this_block = this_block
        self.parent_block = parent_block

        # Store fixed stroke width (no tip needed for Line)
        self._fixed_stroke_width = 5

        # Add updater for continuous tracking
        self.add_updater(self._update_position_and_size)

    def _update_position_and_size(self, mobject):
        # Get the raw endpoints from the blocks
        new_start = self.this_block.get_left()
        new_end = self.parent_block.get_right()

        # Maintain fixed stroke width
        self.set_stroke(width=self._fixed_stroke_width)

        # Use set_points_by_ends which respects buff
        self.set_points_by_ends(new_start, new_end, buff=self.buff)

# TODO check if useful using MovingCameraFixedLayerScene, if not destroy this
class Narration(Text):
    def __init__(self):
        super().__init__(
            text="empty narration Text",
            color=WHITE
        )

    def fade_to_next_narration(self, to_text: str = ""):
        # Store current properties
        current_pos = self.get_center()
        current_color = self.color

        # Create new text object
        new_text_obj = Text(to_text, color=current_color)
        new_text_obj.move_to(current_pos)

        # Update this object to become the new text
        self.become(new_text_obj)

        return Succession(
            self.animate.set_opacity(0),
            self.animate.set_opacity(1)
        )

# TODO test each of these
class NarrationText(Text):
    def __init__(self):
        super().__init__(
            "created on init text",
            color=WHITE
        )

        self.fixedLayer= True
        self.to_edge(UP)

    def fade_to_next_narration(self, to_text: str = ""):
        # Store current properties
        current_pos = self.get_center()
        current_color = self.color

        # Create new text object
        new_text_obj = Text(to_text, color=current_color)
        new_text_obj.move_to(current_pos)

        # Update this object to become the new text
        self.become(new_text_obj)

        return Succession(
            self.animate(runtime = 1).set_opacity(0),
            self.animate(runtime = 1).set_opacity(1)
        )

class NarrationTex(Tex):
    def __init__(self):
        super().__init__(
            r"\text{created on init text and math: } \int_0^\infty e^{-x^2} dx",
            color=WHITE
        )

        self.fixedLayer= True
        self.to_edge(UP)

    def fade_to_next_narration(self, to_text: str = ""):
        # Store current properties
        current_pos = self.get_center()
        current_color = self.color

        # Create new text object
        new_text_obj = Tex(to_text, color=current_color)
        new_text_obj.move_to(current_pos)

        # Update this object to become the new text
        self.become(new_text_obj)

        return Succession(
            self.animate(runtime = 1).set_opacity(0),
            self.animate(runtime = 1).set_opacity(1)
        )

class NarrationMathTex(MathTex):
    def __init__(self):
        super().__init__(
            r"\text{created on init text and math: } \int_0^\infty e^{-x^2} dx",
            color=WHITE
        )

        self.fixedLayer= True
        self.to_edge(UP)

    def fade_to_next_narration(self, to_text: str = ""):
        # Store current properties
        current_pos = self.get_center()
        current_color = self.color

        # Create new text object
        new_text_obj = MathTex(to_text, color=current_color)
        new_text_obj.move_to(current_pos)

        # Update this object to become the new text
        self.become(new_text_obj)

        return Succession(
            self.animate(runtime = 1).set_opacity(0),
            self.animate(runtime = 1).set_opacity(1)
        )
# TODO
#  This is rough notes from discussion
#  priorities
#  ...
#  COMPLETE     labels misbehaving, # Currently labels function as intended
#  PAUSED       blockchain class - location updates based on parent,  # when getting to about 6 or more btc blocks, simple animations start taking too much time(mem leaks?)
#  COMPLETE     for BlockMobBitcoin(BlockDAG(blink(get_past, get future, get_anticone)) #method works for Kaspa),
#               parallel chains like kadena, ect,
#  COMPLETE     ghostdag, function that computes k cluster and blueset for each block, # pretty sure this is functional and correct
#               output a transcript that has each step eg. added to blue set, appended children,

# TODO please list priorities here