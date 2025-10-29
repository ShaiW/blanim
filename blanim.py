from __future__ import annotations

import string
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from itertools import chain
from random import choice, randint
from typing import List, Dict, Optional

from manim.typing import Point3DLike

from blanim import *

#TODO changed to using BaseVisualBlock, have not updated anything beyond BaseVisualBlock, BitcoinVisualBlock, or KaspaVisualBlock
"""
PLANNED BLANIM PROJECT FILE STRUCTURE
may contain errors or evolve as project takes shape
==============================  

Planned architecture for blockchain animation project supporting  
multiple consensus mechanisms (Bitcoin, Kaspa, future blockchains).  

blanim/                                    # ← Project root directory                                         #Exists  
├── blanim/                                # ← Python package directory                                       #Exists  
│   ├── __init__.py                        # Re-exports manim + all submodules                                #COMPLETE  
│   ├── core/                                                                                                 #Exists  
│   │   ├── __init__.py                                                                                       #COMPLETE
│   │   ├── base_visual_block.py          (BaseVisualBlock class)                                             #COMPLETE  
│   │   ├── parent_line.py                (ParentLine class)                                                  #COMPLETE  
│   │   ├── dag_structures.py             (Base DAG/Chain classes)                                            #Exists  Need to determine what/if is part of base DAGs  
│   │   └── hud_2d_scene.py               (HUD2DScene, Scene/engine)                                          #COMPLETE  
│   │    
│   ├── blockDAGs/                                                                                            #Exists
│   │   ├── __init__.py                                                                                       #Exists and Empty
│   │   ├── bitcoin/                                                                                          #Exists
│   │   │   ├── __init__.py                                                                                   #Exists
│   │   │   ├── visual_block.py           (BitcoinVisualBlock)                                                #Exists
│   │   │   ├── logical_block.py          (BitcoinBlock with chain logic)                                     #Exists
│   │   │   ├── chains/                   (Different chain mode implementations)                              #COMPLETE
│   │   │   │   ├── __init__.py                                                                               #Exists
│   │   │   │   ├── base_chain.py        (BaseBitcoinChain - shared logic)                                    #Exists and Empty
│   │   │   │   ├── free_chain.py        (FreeChain - no validation mode)                                     #Exists and Empty
│   │   │   │   ├── standard_chain.py    (StandardChain - normal consensus)                                   #Exists and Empty
│   │   │   │   ├── selfish_mining.py    (SelfishMiningChain - attack demo)                                   #Exists and Empty
│   │   │   │   └── simulation.py        (SimulationChain - realistic sim)                                    #Exists and Empty
│   │   │   └── utils/                    (Bitcoin-specific utilities)                                        #Exists
│   │   │       ├── __init__.py                                                                               #Exists and Empty
│   │   │       ├── colors.py             (Bitcoin color scheme)                                              #Exists and Empty
│   │   │       └── layouts.py            (Linear chain layout algorithms - may be empty)                     #exists and Empty
│   │   │    
│   │   ├── kaspa/                                                                                            #Exists and Empty
│   │   │   ├── __init__.py                                                                                   #Exists and Empty
│   │   │   ├── visual_block.py           (KaspaVisualBlock)                                                  #Exists
│   │   │   ├── logical_block.py          (KaspaBlock with DAG logic)                                         #Exists and Empty
│   │   │   ├── dags/                     (Different DAG mode implementations)                                #Exists
│   │   │   │   ├── __init__.py                                                                               #Exists and Empty
│   │   │   │   ├── base_dag.py          (BaseKaspaDAG - shared logic)                                        #Exists and Empty
│   │   │   │   ├── free_dag.py          (FreeDAG - no validation mode)                                       #Exists and Empty
│   │   │   │   ├── standard_dag.py      (StandardDAG - normal GHOSTDAG consensus)                            #Exists and Empty
│   │   │   │   ├── ghostdag_demo.py     (GHOSTDAGDemo - visualize GHOSTDAG ordering)                         
│   │   │   │   └── simulation.py        (SimulationDAG - realistic DAG sim)                                  #Exists and Empty
│   │   │   ├── ghostdag/                 (GHOSTDAG-specific logic)                                           #Exists
│   │   │   │   ├── __init__.py                                                                               #Exists and Empty
│   │   │   │   ├── ordering.py          (GHOSTDAG ordering algorithm)                                        #Exists and Empty
│   │   │   │   ├── tree_conversion.py   (DAG to tree visualization)                                          #Exists and Empty
│   │   │   │   └── blue_set.py          (Blue set computation)                                               #Exists and Empty
│   │   │   └── utils/                    (Kaspa-specific utilities)                                          #Exists  
│   │   │       ├── __init__.py                                                                               #Exists and Empty  
│   │   │       ├── colors.py             (Kaspa color scheme)                                                #Exists and Empty  
│   │   │       └── layouts.py            (DAG layout algorithms)                                             #Exists and Empty
│   │   │    
│   │   └── ethereum/                     (Future blockchain example)    
│   │       ├── __init__.py    
│   │       ├── visual_block.py    
│   │       ├── logical_block.py    
│   │       └── utils/                    (Ethereum-specific utilities)    
│   │           ├── __init__.py    
│   │           ├── colors.py    
│   │           └── layouts.py    
│   │    
│   └── utils/                            (Core/default utilities - optional)                                 #Exists and Empty
│       ├── __init__.py                                                                                       #COMPLETE  
│       ├── colors.py                     (Default color schemes)                                             #Exist and Empty  
│       └── layouts.py                    (Default layout algorithms)                                         #Exist and Empty  
│    
├── examples/                              # ← Example/demo scenes                                            #Exists
│   ├── __init__.py                                                                                           #COMPLETE  
│   ├── hud_2d_scene_examples.py          (HUD2DScene examples)                                               #COMPLETE (renamed from common_examples.py)  
│   ├── bitcoin_examples.py               (Bitcoin animation examples)                                        #Exist and Empty  
│   └── kaspa_examples.py                 (Kaspa animation examples)                                          #Exist and Empty  
│    
├── pyproject.toml                         # ← Package configuration                                          #COMPLETE  
├── README.md                              # ← Project documentation                                          #Could Update Soon  
└── .gitignore                             # ← Git ignore file                                                #Exists  

ARCHITECTURE PRINCIPLES:  
------------------------  

1. Separation by Blockchain: Each blockchain gets its own package under  
   blockchains/ with visual, logical, structure, AND utils components.  

2. Shared Core: Common base classes in core/ to avoid duplication.  
   - BaseVisualBlock: Visual rendering (square, label, lines)  
   - ParentLine: Line connections between blocks  
   - Base DAG/Chain structures  

3. Visual vs Logical Separation:  
   - visual_block.py: Handles rendering, animations, Manim integration  
   - logical_block.py: Handles consensus logic, parent selection, DAG traversal  
   - Visual classes inherit from BaseVisualBlock (VMobject)  
   - Logical classes inherit from visual classes and add domain logic  

4. Utils Organization:  
   - Each blockchain has its own utils/ subdirectory  
   - Complete isolation - blockchain-specific colors, layouts, and helpers  
   - No cross-imports between blockchain utils packages  
   - Optional: Keep blanim/utils/ for shared defaults that blockchains can  
     reference if needed, but each blockchain defines its own  

5. Scene Organization:  
   - Animations grouped by blockchain type in scenes/  
   - Cross-blockchain comparisons in comparison_scenes.py  

IMPORT PATTERNS:  
----------------  

In your scene file:  
    from blanim.blockchains.bitcoin import BitcoinVisualBlock, BitcoinBlock
    from blanim.blockchains.kaspa import KaspaVisualBlock, KaspaBlock
    from blanim.core import BaseVisualBlock
    from blanim.blockchains.bitcoin.utils.colors import BITCOIN_ORANGE  
    from blanim.blockchains.kaspa.utils.colors import KASPA_BLUE, KASPA_RED  
    from blanim.blockchains.kaspa.utils.layouts import dag_layout, ghostdag_tree_layout  

No cross-imports between blockchain utils - complete isolation  

EXAMPLE BLOCKCHAIN-SPECIFIC UTILS:  
-----------------------------------  

blanim/blockchains/bitcoin/utils/colors.py:  
    from manim import ManimColor  

    BITCOIN_ORANGE = ManimColor("#F7931A")  
    SELECTED_PARENT_BLUE = ManimColor("#0000FF")  
    BLOCK_DEFAULT = BITCOIN_ORANGE  

blanim/blockchains/kaspa/utils/colors.py:  
    from manim import ManimColor  

    KASPA_BLUE = ManimColor("#70C7BA")  
    KASPA_RED = ManimColor("#FF6B6B")  
    SELECTED_PARENT_COLOR = KASPA_BLUE  
    NON_SELECTED_PARENT_COLOR = ManimColor("#FFFFFF")  

blanim/blockchains/bitcoin/utils/layouts.py:  
    def linear_chain_layout(blocks, spacing=2.0):  
        Layout blocks in a linear chain (Bitcoin-specific)  
        positions = []  
        for i, block in enumerate(blocks):  
            positions.append([i * spacing, 0, 0])  
        return positions  

blanim/blockchains/kaspa/utils/layouts.py:  
    def dag_layout(blocks, layer_spacing=2.0, block_spacing=1.5):  
        Layout blocks in DAG structure (Kaspa-specific)  
        (Kaspa-specific DAG layout algorithm implementation here)  
        pass  

    def GHOSTDAG_tree_layout(blocks, blue_set):  
        Layout blocks according to GHOSTDAG ordering  
        (GHOSTDAG-specific layout implementation here)  
        pass  

ADDING NEW BLOCKCHAINS:  
-----------------------  

To add a new blockchain (e.g., Ethereum):  

1. Create blanim/blockchains/ethereum/ directory  
2. Implement EthereumVisualBlock inheriting from BaseVisualBlock  
3. Implement EthereumBlock inheriting from EthereumVisualBlock  
4. Create ethereum/utils/ subdirectory with:  
   - colors.py: Ethereum-specific colors (ETH purple, etc.)  
   - layouts.py: Ethereum-specific layouts (uncle blocks, etc.)  
5. Add consensus-specific logic (e.g., uncle blocks, gas)  
6. Create ethereum_scenes.py for animations  

BENEFITS OF THIS ARCHITECTURE:  
-------------------------------  

1. Complete Isolation: No risk of one blockchain's utils affecting another  
2. Clear Ownership: Each blockchain owns its visual style completely  
3. Easy Discovery: Developers know exactly where to find blockchain-specific code  
4. No Import Conflicts: No need to worry about overriding shared utilities  
5. Parallel Development: Multiple developers can work on different blockchains  
   without touching shared code  

OPTIONAL CENTRAL UTILS:  
-----------------------  

The top-level blanim/utils/ is optional and should only contain truly shared  
utilities that multiple blockchains might reference (e.g., common mathematical  
functions, shared animation helpers). Each blockchain should define its own  
colors and layouts in its utils/ subdirectory for complete independence.  

KASPA GHOSTDAG EXAMPLE:  
----------------------  

For Kaspa's GHOSTDAG ordering (DAG to Tree conversion):  

blanim/blockchains/kaspa/ghostdag.py:  
    class GHOSTDAGTree:
        def __init__(self, dag):  
            self.dag = dag  
            self.blue_set = self._compute_blue_set()  
            self.ordering = self._compute_ordering()  

        def as_visual_tree(self):  
            Convert DAG to tree visualization  
            pass  

Usage in scene:  
    Show DAG structure  
    self.play(kaspa_dag.create_with_lines())  

    Transform to tree  
    ghostdag_tree = GHOSTDAGTree(kaspa_dag)  
    self.play(Transform(kaspa_dag, ghostdag_tree.as_visual_tree()))  
"""

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

@dataclass
class Parent:
    name: str
    is_selected_parent: bool

#todo remove dag dependency
#TODO fix this since changing to BaseVisualBlock(or remome logical block to bitcoin/kaspa subfolders)
class Block(BaseVisualBlock, ABC):
    """Multiple Inheritance Pattern"""
    DEFAULT_COLOR = BLUE

    def __init__(self, name=None, DAG=None, parents=None, pos=None,
                 label=None, block_color=None, h=BLOCK_H, w=BLOCK_W):

        # === BLOCKCHAIN IDENTITY ===
        # Use provided name or generate unique ID from memory address
        self.name = name if name is not None else str(id(self))

        # === DAG STRUCTURE SETUP ===
        # Store reference to the DAG this block belongs to
        self.DAG = DAG

        # Convert parent references (from 'parents' param) to actual Block objects
        # by looking them up in the DAG's block registry
        self.parents = [DAG.blocks[p.name] for p in parents]

        # Initialize empty children list (will be populated by child blocks)
        self.children = []

        # Unique hash for this block instance
        self.hash = id(self)

        # === BLOCKCHAIN WEIGHT CALCULATION ===
        # Calculate and cache all ancestor blocks (past blocks in the DAG)
        # This is done once at initialization for performance
        self.past_blocks = self._calculate_past_blocks()

        # Weight = number of ancestor blocks (used for consensus/selection)
        self.weight = len(self.past_blocks)

        # === PARENT SELECTION ===
        # Each block type (subclass) implements its own parent selection logic
        # This determines which parent is the "main" parent for this block
        self.selected_parent = self._select_parent()

        # === VISUAL PROPERTIES DETERMINATION ===
        # Set default color if not provided
        if block_color is None:
            block_color = self.DEFAULT_COLOR

            # Determine label text based on block type and weight
        # Genesis blocks show "Gen", others show their weight
        if label is None:
            label = "Gen" if self.name == "Gen" else str(self.weight)

            # === VISUAL INITIALIZATION ===
        # Initialize visual components (rect, label) via VisualBlock base class
        # This separates visual concerns from blockchain logic
        super().__init__(pos, label, block_color, h, w)

        # === PARENT LINE CREATION ===
        # Create visual lines connecting this block to all parent blocks
        # Selected parent gets special color (PURE_BLUE), others are WHITE
        for parent in self.parents:
            # Check if this parent is the selected parent
            # First check ensures selected_parent exists (not None)
            # Second check compares names to identify the selected parent
            is_selected = (self.selected_parent and
                           self.selected_parent.name == parent.name)

            # Choose line color based on selection status
            line_color = PURE_BLUE if is_selected else WHITE

            # Create line using VisualBlock's method (stores in self.parent_lines)
            self.add_parent_line(parent.rect, line_color)

            # === DAG BIDIRECTIONAL LINKING ===
        # Register this block as a child in each parent's children list
        # This maintains bidirectional parent-child relationships in the DAG
        for p in parents:
            DAG.blocks[p.name].children.append(self.name)

    @abstractmethod
    def _select_parent(self):
        """Each block type implements its own parent selection logic"""
        pass

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
        return not bool(self.children)

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
        if not self.selected_parent:
            return 0

            # Get selected parent's blue score (total blues in its past)
        selected_parent_blue_score = getattr(self.selected_parent, 'blue_count', 0)

        # Add the count of mergeset blues (which includes selected parent)
        mergeset_blues_count = len(self.ghostdag_data.mergeset_blues)

        return selected_parent_blue_score + mergeset_blues_count

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
    block_w: float
    block_h: float

    def __init__(
            self,
            history_size: int = 20,
            block_w: float = BLOCK_W,
            block_h: float = BLOCK_H,
            block_type: type = RandomBlock
    ):
        """Initialize the BlockDAG with configuration parameters."""
        self.blocks = {}
        self.history = []
        self.history_size = history_size
        self.block_h = block_h
        self.block_w = block_w
        self.block_type = block_type  # Store the block type to use

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

        # UPDATE: Set the is_selected_parent flags based on block's actual selection
        if hasattr(block, 'selected_parent') and block.selected_parent:
            for parent in parents:
                if parent.name == block.selected_parent.name:
                    parent.is_selected_parent = True

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

        # Let the block create its own parent arrows
        arrow_animations = block.create_and_manage_parent_arrows(self)
        animations.extend(arrow_animations)

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
            # The is_selected_parent flag will be updated after block creation
            parents.append(Parent(parent_name, is_selected_parent=False))
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

        # Start with everything faded #TODO this can go back to adding block by block, just need to pass scene to dag
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
            # Assuming Block has a method to highlight its outgoing arrows
            # This would need to be implemented in the Block class
            animations.append(parent_block.highlight_outgoing_arrows(opacity=1.0))

            # Then highlight the selected parent in blue
        selected_animations = []
        if current_block.selected_parent:
            selected_parent_block = self.blocks[current_block.selected_parent.name]
            selected_animations.append(selected_parent_block.rect.animate.set_color(BLUE).set_opacity(1.0))
            # Assuming Block has a method to highlight its outgoing arrows with a specific color
            # This would need to be implemented in the Block class
            selected_animations.append(selected_parent_block.highlight_outgoing_arrows(color=BLUE, opacity=1.0))

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
                    # Assuming Block has a method to highlight its outgoing arrows
                    # This would need to be implemented in the Block class
                    animations.append(mergeset_block.highlight_outgoing_arrows(opacity=1.0))

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
                    # Assuming Block has a method to highlight its outgoing arrows with a specific color
                    # This would need to be implemented in the Block class
                    animations.append(blue_block.highlight_outgoing_arrows(color=PURE_BLUE, opacity=1.0))

                    # Then show red blocks with their arrows
        if hasattr(current_block, 'mergeset_reds'):
            for red_block_name in current_block.mergeset_reds:
                if red_block_name in self.blocks:
                    red_block = self.blocks[red_block_name]
                    animations.append(red_block.rect.animate.set_color(PURE_RED).set_opacity(1.0))
                    # Assuming Block has a method to highlight its outgoing arrows with a specific color and reduced opacity
                    # This would need to be implemented in the Block class
                    animations.append(red_block.highlight_outgoing_arrows(color=PURE_RED, opacity=0.6))

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
                                # Assuming Block has a method to highlight its outgoing arrows
                                # This would need to be implemented in the Block class
                                animations.append(blue_block.highlight_outgoing_arrows(opacity=1.0))

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
        start_time_total = time.time()
        print(f"--- Starting create_tree_animation_fast ---")

        best_tip = self._find_best_tip()
        if not best_tip:
            print(
                f"--- Finished create_tree_animation_fast (no best tip) in {time.time() - start_time_total:.4f} seconds ---")
            return AnimationGroup(Wait(0.1))

        parent_chain = self._get_parent_chain(best_tip)

        start_time_positions = time.time()
        new_positions = self._calculate_chain_tree_positions_ordered(parent_chain, vertical_offset, horizontal_offset)
        print(f"Time for _calculate_chain_tree_positions_ordered: {time.time() - start_time_positions:.4f} seconds")

        self._fade_all_blocks()

        animations = []

        # Initialize highlighted_blocks BEFORE the loop that uses it
        best_tip_block = self.blocks[best_tip]
        past_blocks = best_tip_block.get_past_blocks()
        highlighted_blocks = past_blocks.copy()
        highlighted_blocks.add(best_tip)

        # Collect all red and blue blocks from the parent chain
        red_blocks = set()
        blue_blocks = set()

        start_time_collect_colors = time.time()
        for chain_block_name in parent_chain:
            chain_block = self.blocks[chain_block_name]
            if hasattr(chain_block, 'mergeset_reds'):
                red_blocks.update(chain_block.mergeset_reds)
            if hasattr(chain_block, 'mergeset_blues'):
                blue_blocks.update(chain_block.mergeset_blues)
        print(f"Time for collecting red/blue blocks: {time.time() - start_time_collect_colors:.4f} seconds")

        start_time_set_properties = time.time()
        for block_name, block in self.blocks.items():
            if block_name not in highlighted_blocks:
                block.rect.set_opacity(0.2)
                if hasattr(block, 'label') and block.label:
                    block.label.set_opacity(0.2)
                    # Use block's method to fade outgoing arrows
                block.fade_outgoing_arrows(opacity=0.2)
            else:
                # Apply specific coloring based on GHOSTDAG data
                if block_name in red_blocks:
                    block.rect.set_color(PURE_RED, family=False)
                if block_name in blue_blocks:
                    block.rect.set_color(PURE_BLUE, family=False)

                    # Use block's method to set opacity for its outgoing arrows
                block.fade_outgoing_arrows(opacity=1.0)  # Set full opacity for highlighted blocks

            for red_block_name in red_blocks:
                if red_block_name in self.blocks and red_block_name in highlighted_blocks:
                    red_block = self.blocks[red_block_name]
                    # Use block's method to fade outgoing arrows
                    red_block.fade_outgoing_arrows(opacity=0.2)
                    # NEW: Handle arrows TO red blocks
            for block_name, block in self.blocks.items():
                if hasattr(block, 'outgoing_arrows'):
                    for arrow in block.outgoing_arrows:
                        if (hasattr(arrow, 'target_block') and
                                arrow.target_block.name in red_blocks and
                                arrow.target_block.name in highlighted_blocks):
                            arrow.set_opacity(0.2)  # This line still directly manipulates the arrow.
        print(f"Time for setting block/arrow properties: {time.time() - start_time_set_properties:.4f} seconds")

        start_time_movement_animations = time.time()
        movement_animations = []
        for block_name, new_pos in new_positions.items():
            if block_name in self.blocks:
                current_block = self.blocks[block_name]
                movement_animations.append(current_block.rect.animate.move_to(new_pos))

        if movement_animations:
            animations.append(AnimationGroup(*movement_animations, run_time=1.0))
        print(f"Time for creating movement animations: {time.time() - start_time_movement_animations:.4f} seconds")

        print(f"--- Finished create_tree_animation_fast in {time.time() - start_time_total:.4f} seconds ---")
        return AnimationGroup(*animations)

    def _calculate_chain_tree_positions_ordered(self, parent_chain, v_offset, h_offset):
        start_time_calc_positions = time.time()
        new_positions = {}

        chain_y = min(block.rect.get_center()[1] for block in self.blocks.values())

        for i, block_name in enumerate(reversed(parent_chain)):
            current_block = self.blocks[block_name]
            current_x = current_block.rect.get_center()[0]
            new_positions[block_name] = [current_x, chain_y, 0]

            if hasattr(current_block, 'mergeset') and current_block.mergeset:
                start_time_sort_mergeset = time.time()
                mergeset_blocks = list(current_block.mergeset)
                ordered_mergeset = self._sort_mergeset_by_distance_to_chain(mergeset_blocks, current_block)
                print(
                    f"  Time for _sort_mergeset_by_distance_to_chain for block {block_name}: {time.time() - start_time_sort_mergeset:.4f} seconds")

                for j, mergeset_block_name in enumerate(ordered_mergeset):
                    if mergeset_block_name in self.blocks:
                        mergeset_x = current_x - h_offset
                        mergeset_y = chain_y + v_offset + (j * 0.5)
                        new_positions[mergeset_block_name] = [mergeset_x, mergeset_y, 0]

        print(
            f"Time for _calculate_chain_tree_positions_ordered (internal): {time.time() - start_time_calc_positions:.4f} seconds")
        return new_positions

    def _sort_mergeset_by_distance_to_chain(self, mergeset_blocks, chain_block):
        start_time_sort = time.time()
        """Sort mergeset blocks by their distance from the parent chain (blue_count ascending)"""

        def get_distance_key(block_name):
            block = self.blocks[block_name]
            blue_count = getattr(block, 'blue_count', 0)
            block_hash = getattr(block, 'hash', block_name)
            return (blue_count, block_hash)

        sorted_blocks = sorted(mergeset_blocks, key=get_distance_key)
        print(
            f"    Sorting mergeset blocks ({len(mergeset_blocks)} items) took: {time.time() - start_time_sort:.4f} seconds")
        return sorted_blocks

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

    def add(self, parent_names, selected_parent=None, random_sp=False, name=None, *args, **kwargs):

        if isinstance(parent_names, str):
            parent_names = [parent_names]

        name = self._generate_semantic_name(block_type=self.block_type, parents=parent_names, layer=selected_parent)

        return super().add(name, parent_names, selected_parent=selected_parent, random_sp=False, *args, **kwargs)

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

        for block_name, block in self.blocks.items():
            if block_name not in highlighted_blocks:
                block.rect.set_opacity(0.2)
                if hasattr(block, 'label') and block.label:
                    block.label.set_opacity(0.2)
                    # Assuming Block has a method to fade its outgoing arrows
                # This would need to be implemented in the Block class
                block.fade_outgoing_arrows(opacity=0.2)
            else:
                block.rect.set_opacity(1.0)
                if hasattr(block, 'label') and block.label:
                    block.label.set_opacity(1.0)
                    # Assuming Block has a method to restore opacity of its outgoing arrows
                # This would need to be implemented in the Block class
                block.fade_outgoing_arrows(opacity=1.0)

        return AnimationGroup(Wait(0.1))

    def fade_except_parent_arrows(self, scene):
        """
        Set opacity to fade everything except the selected parent arrows (blue arrows)
        """
        for block_name, block in self.blocks.items():
            # Fade block rectangles to low opacity
            block.rect.set_opacity(0.2)
            if hasattr(block, 'label') and block.label:
                block.label.set_opacity(0.2)

                # Handle arrows - fade all arrows first, then restore selected parent arrows
            # Assuming Block has a method to fade its outgoing arrows
            # This would need to be implemented in the Block class
            block.fade_outgoing_arrows(opacity=0.2)

            # Keep selected parent arrows at full opacity
            if hasattr(block, 'selected_parent') and block.selected_parent:
                # Assuming Block has a method to highlight specific outgoing arrows
                # This would need to be implemented in the Block class
                block.highlight_outgoing_arrows_to_parent(block.selected_parent, opacity=1.0)

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
        for block_name, block in self.blocks.items():
            block.rect.set_opacity(1.0)
            if hasattr(block, 'label') and block.label:
                block.label.set_opacity(1.0)
                # Assuming 'pointer' refers to the incoming arrow, and 'outgoing_arrows' are also tracked
            if hasattr(block, 'pointer') and block.pointer:
                block.pointer.set_opacity(1.0)
                # Assuming Block has a method to reset opacity of its outgoing arrows
            # This would need to be implemented in the Block class
            block.fade_outgoing_arrows(opacity=1.0)

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

#TODO revisit miner later
class Miner:
    def __init__(self, scene, x=0, y=0, attempts=20):
        self.scene = scene
        self.x = x
        self.y = y
        self.attempts = attempts
        self.nonce = randint(10000, 99000)

        # Create all mobjects
        self.rect = Rectangle(color=RED, fill_opacity=1, height=2, width=3)
        self.rect.move_to([x, y, 0])

        self.lpar = Tex(r"(", font_size=220).move_to([x - 1.8, y, 0])
        self.rpar = Tex(r")", font_size=220).move_to([x + 1.8, y, 0])
        self.eq = Tex(r"=", font_size=100).move_to([x + 2.7, y, 0])
        self.H = Tex(r"\textsf{H}", font_size=100).move_to([x - 2.6, y, 0])

        self.header = Rectangle(color=BLACK, fill_opacity=1, height=0.5, width=2.8)
        self.header.move_to([x, y + 0.6, 0])

        self.nonce_label = Text(f"Nonce: {self.nonce}", font_size=30)
        self.nonce_label.move_to([x, y + 0.6, 0])

        self.hash = self._nexthash()
        self.hash.move_to([x + 7, y, 0])

        # Add all at once
        scene.add(self.rect, self.H, self.lpar, self.rpar, self.eq,
                  self.header, self.nonce_label, self.hash)
        scene.wait(0.5)

    def _nexthash(self, win=False, color=RED):
        hash_text = ("0" * 10 if win else fake_sha(10)) + "..." + fake_sha()
        nhash = Text(hash_text, font_size=36, color=color, font="Monospace")
        nhash.move_to([self.x + 7, self.y, 0])
        return nhash

    def update(self):
        self.nonce += 1
        self.attempts -= 1

        # Create new mobjects
        new_nonce = Text(f"Nonce: {self.nonce}", font_size=30)
        new_nonce.move_to([self.x, self.y + 0.6, 0])

        # Unwrite old hash
        self.scene.play(Unwrite(self.hash), run_time=0.3)

        # Transform nonce label
        self.scene.play(Transform(self.nonce_label, new_nonce))

        # Create new hash (white initially)
        new_hash = self._nexthash(win=not bool(self.attempts), color=WHITE)

        # Write new hash
        self.scene.play(Write(new_hash), run_time=0.3)

        # Fade to final color
        self.scene.play(FadeToColor(new_hash, RED if self.attempts else BLUE))

        # Update hash reference
        self.hash = new_hash

    def mining(self):
        return self.attempts > 0
# class Miner:
#     def __init__(self, scene, x=0 , y=0, attempts = 20):
#         self.scene = scene
#         self.x = x
#         self.y = y
#         self.attempts = attempts
#         self.nonce = randint(10000,99000)
#         self.parts = {}
#         self.rect = Rectangle(
#             color=RED,
#             fill_opacity=1,
#             height = 2,
#             width = 3
#         )
#         self.rect.move_to([x,y,0])
#         self.lpar = Tex(r"(",font_size = 220)
#         self.lpar.move_to([x-1.8,y,0])
#         self.rpar = Tex(r")",font_size = 220)
#         self.rpar.move_to([x+1.8,y,0])
#         self.eq = Tex(r"=",font_size = 100)
#         self.eq.move_to([x+2.7,y,0])
#         self.H = Tex(r"\textsf{H}", font_size = 100)
#         self.H.move_to([x-2.6,y,0])
#         self.header = Rectangle(
#             color=BLACK,
#             fill_opacity=1,
#             height = 0.5,
#             width = 2.8
#         )
#         self.header.move_to([x,y+0.6,0])
#         self.nonce_label = Text("Nonce: " + str(self.nonce), font_size = 30)
#         self.nonce_label.move_to([x,y+0.6,0])
#         self.hash = self._nexthash()
#         self.hash.move_to([x+7,y,0])
#         scene.add(self.rect, self.H, self.lpar, self.rpar, self.eq, self.header, self.nonce_label, self.hash)
#         scene.wait(0.5)
#
#     def _nexthash(self, win=False, color=RED):
#         nhash = Text(("0"*10 if win else fake_sha(10)) + "..." + fake_sha(), font_size = 50, color=color, font="Monospace")
#         nhash.move_to([self.x+7,self.y,0])
#         return nhash
#
#     def update(self):
#         self.nonce += 1
#         self.attempts -= 1
#         newnonce = Text("Nonce: " + str(self.nonce), font_size = 30)
#         newnonce.move_to([self.x,self.y+0.6,0])
#         self.scene.play(Unwrite(self.hash),run_time = 0.3)
#         self.scene.play(Transform(self.nonce_label, newnonce))
#         self.hash = self._nexthash(win = not bool(self.attempts),color=WHITE)
#         self.scene.play(Write(self.hash),run_time = 0.3)
#         self.scene.play(FadeToColor(self.hash, RED if self.attempts else BLUE))
#
#     def mining(self):
#         return self.attempts > 0

def fake_sha(n=6):
    return ''.join(choice(string.ascii_lowercase[:6]+string.digits[1:]) for _ in range(n))

class MinerDemo(Scene):
    def construct(self):
        m = Miner(self, x=-3.5, y=0, attempts = 5)
        while m.mining():
            m.update()

# TODO, removed for now to ignore(selfish_mining_bitcoin.py has replaced this for now)
# class Bitcoin:
#     def __init__(
#             self,
#             scene
#     ):
#         """
#         :param scene: self
#
#         Scene is passed so animations can be handled within Bitcoin
#         Bitcoin currently supports a chain and competing fork
#         """
#         self.scene = scene
#
#         self.all_blocks = [] # all blocks added to the chain
#
#         # Create Genesis
#         genesis = BTCBlock(None, "Gen")
#         self.all_blocks.append(genesis)
#
#     def add_block(self):
#         """
#         Creates a new block, a pointer, and returns an animation that adds a single block to the chain.
#         """
#         block = BTCBlock(self.all_blocks[-1])
#         self.all_blocks.append(block)
#         pointer = Pointer(block, block.parent)
#
#         return [AnimationGroup(
#                 [self.scene.camera.frame.animate.move_to([block.get_x(), 0, 0]),
#                 FadeIn(block),
#                 FadeIn(pointer)],
#                 Wait(0.5)
#             )]
#
#     def add_blocks(self, number_of_blocks_to_add:int = 1):
#         """
#         :param number_of_blocks_to_add: desired number of blocks to add to the chain.
#
#         Returns an animation that plays one by one adding the desired number of blocks to the chain.
#         """
#         add_blocks_animations = []
#
#         i = 0
#         while i < number_of_blocks_to_add:
#             add_blocks_animations.extend(
#                 self.add_block()
#             )
#             i += 1
#
#         return Succession(add_blocks_animations)
#
#     def add_first_fork_block(self, fork_depth):
#         """
#         :param fork_depth: desired depth to begin fork from tip.
#
#         Creates a new block, a pointer, and returns an animation that adds a single fork block to the chain.
#         """
#         block = BTCBlock(self.all_blocks[-fork_depth - 1])
#         self.all_blocks.append(block)
#         block.is_fork = True
#         pointer = Pointer(block, block.parent)
#
#         block.set_y(-2)
#
#         return [AnimationGroup(
#                 [self.scene.camera.frame.animate.move_to([block.get_x(), 0, 0]),
#                 FadeIn(block),
#                 FadeIn(pointer)],
#                 Wait(0.5)
#             )]
#
#     def add_block_to_chain(self):
#         """
#         Creates a new block, a pointer, and returns an animation that adds a single block to the longest chain.
#         """
#         tips = self.get_longest_chain_tips()
#         original_chain_tip = tips[0] # pick one, if multiple tips have same weight,
#
#         block = BTCBlock(original_chain_tip)
#         self.all_blocks.append(block)
#         pointer = Pointer(block, block.parent)
#
#         return [AnimationGroup(
#                 [self.scene.camera.frame.animate.move_to([block.get_x(), 0, 0]),
#                 FadeIn(block),
#                 FadeIn(pointer)],
#                 Wait(0.5)
#             )]
#
#     def add_block_to_fork(self):
#         """"""
#         # determine the most recent fork chain
#         fork_chain_tip = self.find_most_recent_forked_block()
#
#         block = BTCBlock(fork_chain_tip)
#         self.all_blocks.append(block)
#         pointer = Pointer(block, block.parent)
#
#         return [AnimationGroup(
#                 [self.scene.camera.frame.animate.move_to([block.get_x(), 0, 0]),
#                 FadeIn(block),
#                 FadeIn(pointer)],
#                 Wait(0.5)
#             )]
#
#     def find_most_recent_forked_block(self):
#         tips = self.get_tips()
#
#         for each in reversed(tips):
#             if each.is_from_fork():
#                 return each
#             else:
#                 ...
#
#         return None
#
#     def move_camera_to(self, name_of_block:int):
#         """
#         :param name_of_block: int of block rounds from genesis
#
#         BTC blocks are named by weight,
#         except Genesis, named 'Gen',
#         move_to will adjust cameras center position to the desired round from genesis.
#
#         """
#         block = None
#
#         for each in self.all_blocks:
#             if each.name == name_of_block:
#                 block = each
#                 break
#
#         return AnimationGroup(
# #            self.scene.camera.frame.animate.move_to(block)
#             self.scene.camera.frame.animate.move_to([block.get_x(), 0, 0])
#
#         )
#
#     def get_tips(self):
#         """
#         Returns a list of all tips.
#         """
#         tips = []
#
#         for each in self.all_blocks:
#             if each.is_tip():
#                 tips.append(each)
#
#         return tips
#
#     def get_heaviest_two_tips(self):
#         """
#         Return a sorted list of the heaviest two tips.
#         Heaviest tip [0]
#         Lighter tip [1]
#         Unless tip weight is the same
#         """
#         tips = self.get_tips()
#         tip_1 = tips[0]
#         tip_2 = tips[1]
#
#         if tip_1.get_weight() > tip_2.get_weight():
#             sorted_tips = [tip_1, tip_2]
#         else:
#             sorted_tips = [tip_2, tip_1]
#
#         return sorted_tips
#
#     def get_longest_chain_tips(self):
#         """
#         Returns a list of blocks with the most blocks in its past.
#         If a single tip is the heaviest, list will only have one block,
#         If multiple tips exist with the same weight, list will have multiple blocks.
#         """
#         tips = self.get_tips()
#
#         weight_of_each_tip = [each.weight for each in tips]
#         most_blocks_in_past = max(weight_of_each_tip)
#
#         return [each for each in tips if each.weight == most_blocks_in_past]
#
#     def get_past_of_tips(self):
#         """
#         Returns a list of blocks in the past of the tips provided,
#         back to and excluding the most recent common ancestor.
#         """
#         tips_to_find_blocks = self.get_heaviest_two_tips()
#
#         if len(tips_to_find_blocks) == 1:
#             print("incorrect usage of get_past_of_tips")
#             return
#
#         lists_of_past_blocks = []
#
#         for each in tips_to_find_blocks:
#             lists_of_past_blocks.append(each.get_self_inclusive_past())
#
#         set_of_tip_0 = set(lists_of_past_blocks[0])
#         set_of_tip_1 = set(lists_of_past_blocks[1])
#
#         set_of_blocks_unique_to_0 = set_of_tip_0 - set_of_tip_1
#         set_of_blocks_unique_to_1 = set_of_tip_1 - set_of_tip_0
#
#         list_of_blocks_unique_to_0 = list(set_of_blocks_unique_to_0)
#         list_of_blocks_unique_to_1 = list(set_of_blocks_unique_to_1)
#
#         lists_of_past_blocks = [list_of_blocks_unique_to_0, list_of_blocks_unique_to_1]
#
#         return lists_of_past_blocks
#
#     def are_heaviest_two_tips_equal_weight(self):
#         tips = self.get_heaviest_two_tips()
#
#         if tips[0].get_weight() == tips[1].get_weight():
#             return True
#         else:
#             return False
#
#     def animate_these_blocks_blue(self, list_of_blocks:list):
#         animate_turn_blue = []
#
#         for each in list_of_blocks:
#             animate_turn_blue.extend([each.fade_blue()])
#
#         return AnimationGroup(
#             animate_turn_blue
#         )
#
#     def animate_these_blocks_red(self, list_of_blocks:list):
#         animate_turn_red = []
#
#         for each in list_of_blocks:
#             animate_turn_red.extend([each.fade_red()])
#
#         return AnimationGroup(
#             animate_turn_red
#         )
#
#
#     def adjust_block_color_by_longest_chain(self):
#         """
#         Returns animations to change block color depending on if they are part of the longest chain.
#         """
#         lists_of_past_blocks_of_tips = self.get_past_of_tips()
#         block_color_animations = []
#
#         if self.are_heaviest_two_tips_equal_weight():
#             block_color_animations.append(self.animate_these_blocks_red(lists_of_past_blocks_of_tips[0]))
#             block_color_animations.append(self.animate_these_blocks_red(lists_of_past_blocks_of_tips[1]))
#             return AnimationGroup(
#                 block_color_animations
#             )
#         else:
#             pass
#
#
#
# #        for each in lists_of_past_blocks_of_tips:
# #            each.sort(key=lambda x: x.weight)
#
#         return None
#
#
#
#
#     ####################
#     # Get past/future/anticone and blink
#     ####################
#
#     def blink_these_blocks(self, blocks_to_blink:list):
#         """
#         Returns an animation that blinks all blocks in the list provided.
#         """
#         blink_these_animations = []
#         current_list_to_blink = blocks_to_blink
#
#         for each in current_list_to_blink:
#             blink_these_animations.append(each.blink())
#
#         return AnimationGroup(*blink_these_animations)
#
#     def blink_past_of_random_block(self):
#         """
#         Returns an animation,
#         picks a block at random and blinks the reachable past,
#         while highlighting the block.
#         """
#         random_block = choice(self.all_blocks)
#         blink_past_animations = []
#         current_list_to_blink = random_block.get_past()
#         blink_past_animations.append(random_block.highlight_self())
#
#         for each in current_list_to_blink:
#             blink_past_animations.append(each.blink())
#
#         return AnimationGroup(*blink_past_animations)
#
#     def blink_future_of_random_block(self):
#         """
#         Returns an animation,
#         picks a block at random and blinks the reachable future,
#         while highlighting the block.
#         """
#         random_block = choice(self.all_blocks)
#         blink_future_animations = []
#         current_list_to_blink = random_block.get_future()
#         blink_future_animations.append(random_block.highlight_self())
#
#         for each in current_list_to_blink:
#             blink_future_animations.append(each.blink())
#
#         return AnimationGroup(*blink_future_animations)
#
#     def blink_anticone_of_random_block(self):
#         """
#         Returns an animation,
#         picks a block at random and blinks the anticone(unreachable blocks),
#         while highlighting the block.
#         """
#         random_block = choice(self.all_blocks)
#         blink_anticone_animations = []
#
#         list_of_blocks_reachable = list(set(self.all_blocks) - set(random_block.get_reachable()))
#         anticone = list(set(list_of_blocks_reachable) - set(random_block))
#
#         blink_anticone_animations.append(random_block.highlight_self())
#
#         for each in anticone:
#             blink_anticone_animations.append(each.blink())
#
#         return AnimationGroup(*blink_anticone_animations)
#
#     ####################
#     # Testing animation
#     ####################
#
#     # Gradually moves when called in scene, moving slowly enough allows updaters to keep up
#     def smooth_genesis(self):
#         animations = []
#
#         animations.append(
#             self.all_blocks[0].animate.shift(UP*1)
#         )
#
#         return AnimationGroup(animations)
#
#     ####################
#     # Positioning Blocks in Bitcoin
#     ####################
#
#     def adjust_chain_position(self):
#         adjust_chain_animations = []
#
#         for each_list in self.find_forks():
#             heaviest_block = self.find_heaviest_block_looking_forward(each_list)
#             position_of_heaviest_block = heaviest_block.get_position()
#             delta_y_of_heaviest_block = abs(position_of_heaviest_block)
#
#             if position_of_heaviest_block[1] == 0:
#                 ...  # do nothing
#             elif position_of_heaviest_block[1] < 0:
#                 move_up_by = delta_y_of_heaviest_block
#                 for each in each_list:
#                     adjust_chain_animations.append(
#                         each.animate.shift(UP*move_up_by)
#                     )
#             else:
#                 move_down_by = delta_y_of_heaviest_block
#                 for each in each_list:
#                     adjust_chain_animations.append(
#                         each.animate.shift(UP*move_down_by)
#                     )
#
#         return AnimationGroup(adjust_chain_animations)
#
#     def find_heaviest_block_looking_forward(self, blocks:list):
#
#         heaviest_block = blocks[0]
#
#         for each_block in blocks:
#             if len(each_block.get_future()) > len(heaviest_block.get_future()):
#                 heaviest_block = each_block
#
#         return heaviest_block
#
#     def find_forks(self):
#
#         forks = [] # list[[block, block], [block, block], [block, block, block], ...]
#
#         for each in self.all_blocks:
#             if len(each.childen) > 1:
#                 forks.append(each.children)
#
#         return forks
#
#     # return an animation that adjusts the consensus rounds based on how many rounds_from_genesis for list(blocks passed)
#
#     def adjust_consensus_round(self, blocks_added:list):
#         adjust_rounds_affected_animations = []
#
#         for each in blocks_added:
#             consensus_round = each.rounds_from_genesis
#
#             all_blocks_at_this_round = list(set(self.get_all_blocks_at_this_round(consensus_round)))
#
#             # Create animations and add to animations to adjust these blocks at this depth
#
#             adjust_rounds_affected_animations.append(self.adjust_consensus_round_animations(all_blocks_at_this_round))
#
#         return AnimationGroup(adjust_rounds_affected_animations)
#
#     def adjust_consensus_round_animations(self, all_blocks_at_this_round:list):
#         animations = []
#
#         # find all y position
#         list_of_y_positions:list = []
#
#         for each in all_blocks_at_this_round:
#             position_of_each_block = each.get_center()
#             list_of_y_positions.append(position_of_each_block[1])
#
#         # Adjust their position to space them from each other and move to position from center (y = 0)
#         y_min = min(list_of_y_positions)
#         y_max = max(list_of_y_positions)
#         adjust_by = (abs(y_min) + abs(y_max)) / all_blocks_at_this_round
#
#         if abs(y_min) > abs(y_max):
#             adjust_up = True
#         else:
#             adjust_up = False
#
#         if adjust_up:
#             for each in all_blocks_at_this_round:
#                 animations.append(each.animate.shift(UP*adjust_by))
#         else:
#             for each in all_blocks_at_this_round:
#                 animations.append(each.animate.shift(DOWN*adjust_by))
#
#         return AnimationGroup(animations)
#
#     def get_all_blocks_at_this_round(self, consensus_round:int):
#         all_blocks_at_this_round = []
#
#         for each in self.all_blocks:
#             if each.rounds_from_genesis == consensus_round:
#                 all_blocks_at_this_round.append(each)
#
#         all_blocks_at_this_round = list(set(all_blocks_at_this_round))
#         return all_blocks_at_this_round

class BTCBlock:
    square: Square
    name: str | int
    parent: BTCBlock | None
    weight: int
    rounds_from_genesis: int
    is_fork: bool
    children: list[BTCBlock]
    pointers: list
    label: Text
    def __init__(self, parent_ref:BTCBlock = None, name:str = ""):
        """name should never be more than 3 characters, anything more than 5 will cause unexpected behavior"""
        self.square = Square(
            color="#0000FF",
            fill_opacity=1,
            side_length=0.8,
            stroke_color=WHITE,
            stroke_width=10
        )

        self.name = name
        self.parent = None
        self.rounds_from_genesis = 0

        self.children = []
        self.pointers = []  # TODO instead of tracking pointers manually, see if possible to automatically return an update_from_func anim when block.square OR block.parent.square is moved

        if parent_ref is not None:
            self.parent = parent_ref
            self.rounds_from_genesis = self.parent.rounds_from_genesis + 1
            self._shift_position_to_parent()
            self.parent.add_self_to_children(self)

        if self.name:
            self.label = Text(str(self.name), font_size=24, color=WHITE, weight=BOLD)
        else:
            # Create invisible black label as placeholder
            self.label = Text(".....", font_size=24, color=BLACK, weight=BOLD)

        self.label.move_to(self.square.get_center())
        self.square.add(self.label)


    def add_self_to_children(self, mobject):
        self.children.append(mobject)

    def is_tip(self):
        return not bool(self.children)

    ####################
    # Color
    # Each returns and animation
    ####################

    def fade_blue(self):
        return self.square.animate.fade_to(color=PURE_BLUE, alpha=1.0, family=False)

    def fade_red(self):
        return self.square.animate.fade_to(color=PURE_RED, alpha=1.0, family=False)

    # this is supposed to work with hex string, test
    def fade_to_color(self, to_color:ManimColor = WHITE):
        return self.square.animate.fade_to(color=to_color, alpha=1.0, family=False)

    ####################
    # Label
    # Returns an animation that changes the text only
    ####################

    def fade_to_next_label(self, to_label: str = ""):
        """blocks always have a label, as a submobject of the square"""
        new_label = Text(to_label, font_size=24, color=WHITE, weight=BOLD)
        new_label.move_to(self.square.get_center())

        return Transform(self.label, new_label)

    ####################
    # Pointers
    ####################

    def attach_pointer(self, pointer):
        self.pointers.append(pointer)

    ####################
    # Position
    ####################

    def _shift_position_to_parent(self):
        self.square.next_to(self.parent.square, RIGHT * 4)

    ####################
    # Animations
    ####################

    def draw(self):
        return Create(self.square)

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
        if self.parent is None:
            return []

        past_of_this_block = [self.parent]

        past_of_this_block.extend(self.parent.get_past())

        ordered_past = self.order_list_by_weight(past_of_this_block, descending=True)

        return ordered_past

    @staticmethod
    def order_list_by_weight(list_to_order: list, descending=False):
        """Returns an ascending list by default, set descending=True if descending list is desired"""
        list_to_order.sort(key=lambda x: x.weight, reverse=descending)

        return list_to_order

    def get_reachable(self):
        """
        Returns an ordered list of the reachable blocks, sorted by ascending weight
        """
        reachable = []

        reachable.extend(self.get_past())
        reachable.extend(self.get_future())

        reachable.sort(key=lambda x: x.weight)

        return reachable
# verified BTCBlock and ParentLine does not chew through ram, builds anims very fast, will apply the same fix to DAGs


#TODO network simulation for visualizing block propagation
class Node(Square):
    def __init__(self, peers:list):
        super().__init__()
        # Create a Node with a list of peers

        self.side_length = 0.8
        self.set_fill("#0000FF", opacity=1)

        self.peers_list = peers


# TODO
#  ...
#  CURRENT      Clean up and restart blockDAG progress, solved problems preventing progress already
#                   should build for HUD2DScene, Narration and Camera w/chaining complete.