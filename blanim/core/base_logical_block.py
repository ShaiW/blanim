# blanim/blanim/core/base_logical_block.py

from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Optional, Set, List

__all__ = ["BaseLogicalBlock"]

#TODO ensure this is correct for ALL consensus types, ensure this is everything we can extract/define

class BaseLogicalBlock(ABC):
    """Base logical block for all consensus protocols.

    This class provides the core DAG structure and traversal logic that is
    universal across all blockchain consensus mechanisms. It owns and manages
    its visual representation while remaining decoupled from any specific DAG
    coordinator.

    The block is self-contained - it only knows about its direct relationships
    (parents/children) and can reach any other block recursively through these
    relationships. The DAG class serves purely as a registry/coordinator for
    name-based access.

    Architecture:
    - Logical layer (this class): Manages graph structure, consensus logic
    - Visual layer (created internally): Handles rendering and animations
    - Bidirectional linking: logical._visual and visual.logical_block
    - Selected parent convention: parents[0] is always the selected parent

    Parameters
    ----------
    name : str, optional
        Unique identifier for this block. If None, generates from memory address.
    parents : list[BaseLogicalBlock], optional
        List of parent blocks. First parent (index 0) is the selected parent.
        Empty list for genesis blocks.
    position : Point3DLike, optional
        3D coordinates for visual block placement.
    visual_class : type, optional
        The visual block class to instantiate (e.g., BitcoinVisualBlock).
    visual_config : object, optional
        Configuration object for the visual block (e.g., BitcoinBlockConfig).

    Attributes
    ----------
    name : str
        Unique identifier for this block throughout animation lifecycle.
    hash : int
        Unique hash based on memory address.
    parents : list[BaseLogicalBlock]
        Direct parent blocks in the DAG. parents[0] is the selected parent.
    children : list[BaseLogicalBlock]
        Direct child blocks (populated as children are created).
    weight : int
        Protocol-specific weight metric (computed via _calculate_weight()).
    selected_parent : BaseLogicalBlock or None
        The selected parent (always parents[0] if parents exist).
    _visual : BaseVisualBlock
        The visual representation owned by this logical block.

    Examples
    --------
    Subclass implementation for Bitcoin::

        class BitcoinLogicalBlock(BaseLogicalBlock):
            def _calculate_weight(self):
                # Bitcoin: weight = number of ancestors
                visited = set()
                self._collect_past_blocks(visited)
                return len(visited)

            def _create_visual(self, visual_class, position, config):
                parent_visual = self.parents[0]._visual if self.parents else None
                visual = BitcoinVisualBlock(
                    label_text=str(self.weight),
                    position=position,
                    parent=parent_visual,
                    block_config=config or DEFAULT_BITCOIN_CONFIG
                )
                visual.logical_block = self
                return visual

    Usage with DAG coordinator::

        dag = BitcoinDAG()
        genesis = BitcoinLogicalBlock(name="Gen", parents=[], position=[0,0,0])
        dag.add_block(genesis)

        block1 = BitcoinLogicalBlock(name="A", parents=[genesis], position=[2,0,0])
        dag.add_block(block1)

        # Access by name through DAG
        self.play(dag["Gen"].create_with_lines())
        self.play(dag["A"].create_with_lines())

    Notes
    -----
    This class uses composition over inheritance - it owns a visual block
    rather than inheriting from it. This maintains clean separation between
    logical (consensus) and visual (rendering) concerns.

    The `children` list exists in BOTH logical and visual layers for different
    purposes: logical children enable DAG traversal/algorithms, visual children
    enable animation propagation during movement.

    Past blocks are computed on-demand (not cached) to avoid O(n²) memory
    overhead in large DAGs. For animation purposes, this recalculation is
    infrequent and fast enough.
    """

    def __init__(
            self,
            name: Optional[str] = None,
            parents: Optional[List[BaseLogicalBlock]] = None,
            position: Optional[List[float]] = None,
            visual_class: Optional[type] = None,
            visual_config: Optional[object] = None
    ) -> None:
        # === BLOCK IDENTITY ===
        # Stable identifier throughout animation lifecycle
        self.name = name if name is not None else str(id(self))
        self.hash = id(self)

        # === DAG STRUCTURE (NO DAG REFERENCE) ===
        # Blocks are self-contained and only know direct relationships
        # They can reach any other block recursively through parents/children
        # parents[0] is ALWAYS the selected parent (by convention)
        self.parents = parents if parents else []
        self.children: List[BaseLogicalBlock] = []

        # === PROTOCOL-SPECIFIC WEIGHT ===
        # Each protocol implements its own weight calculation
        # Bitcoin: len(past_blocks), Kaspa: blue_count, etc.
        # NOTE: past_blocks are NOT cached to avoid O(n²) memory
        self.weight = self._calculate_weight()

        # === SELECTED PARENT (CONVENTION) ===
        # Selected parent is always parents[0] if parents exist
        # The DAG/protocol layer is responsible for ordering parents correctly
        self.selected_parent: Optional[BaseLogicalBlock] = self.parents[0] if self.parents else None

        # === VISUAL REPRESENTATION (COMPOSITION) ===
        # Create and own the visual block (composition over inheritance)
        # Visual block gets bidirectional reference back to this logical block
        self._visual = self._create_visual(visual_class, position, visual_config)

        # === BIDIRECTIONAL LINKING ===
        # Register this block as a child in each parent's children list
        # This maintains bidirectional relationships for DAG traversal
        for parent in self.parents:
            parent.children.append(self)

    # === ABSTRACT METHODS (PROTOCOL-SPECIFIC) ===

    @abstractmethod
    def _calculate_weight(self) -> int:
        """Calculate protocol-specific weight metric.

        This method must be implemented by each consensus protocol.
        Weight calculation varies by protocol:
        - Bitcoin: Number of ancestors (len(past_blocks))
        - Kaspa: Blue score (cumulative blue blocks)
        - Future protocols: Stake, difficulty, or other metrics

        Returns
        -------
        int
            The weight value for this block.

        Examples
        --------
        Bitcoin implementation::

            def _calculate_weight(self):
                visited = set()
                self._collect_past_blocks(visited)
                return len(visited)

        Kaspa implementation::

            def _calculate_weight(self):
                return self.blue_count

        Notes
        -----
        For protocols that need past blocks for weight calculation,
        compute them locally without caching to avoid O(n²) memory overhead.
        """
        pass

    @abstractmethod
    def _create_visual(
            self,
            visual_class: Optional[type],
            position: Optional[List[float]],
            config: Optional[object]
    ):
        """Create the visual block representation for this logical block.

        This method must be implemented by each consensus protocol to create
        the appropriate visual block type (BitcoinVisualBlock, KaspaVisualBlock, etc.)
        and establish the bidirectional link between logical and visual layers.

        Parameters
        ----------
        visual_class : type
            The visual block class to instantiate.
        position : list[float]
            3D coordinates [x, y, z] for block placement.
        config : object
            Protocol-specific configuration object.

        Returns
        -------
        BaseVisualBlock
            The created visual block with bidirectional link established.

        Examples
        --------
        Bitcoin implementation::

            def _create_visual(self, visual_class, position, config):
                parent_visual = self.parents[0]._visual if self.parents else None
                visual = BitcoinVisualBlock(
                    label_text=str(self.weight),
                    position=position,
                    parent=parent_visual,
                    block_config=config or DEFAULT_BITCOIN_CONFIG
                )
                visual.logical_block = self  # Bidirectional link
                return visual

        Kaspa implementation::

            def _create_visual(self, visual_class, position, config):
                parent_visuals = [p._visual for p in self.parents]
                visual = KaspaVisualBlock(
                    label_text=str(self.blue_count),
                    position=position,
                    parents=parent_visuals,
                    block_config=config or DEFAULT_KASPA_CONFIG
                )
                visual.logical_block = self  # Bidirectional link
                return visual

        Notes
        -----
        MUST establish bidirectional link: visual.logical_block = self
        This allows visual blocks to query logical structure for animations.
        """
        pass

    # === UNIVERSAL DAG TRAVERSAL (SHARED ACROSS ALL PROTOCOLS) ===

    def _collect_past_blocks(self, visited: Set[str]) -> None:
        """Recursive helper to collect all ancestor blocks.

        Parameters
        ----------
        visited : set[str]
            Set of already-visited block names (modified in-place).

        Notes
        -----
        This is a helper method for get_past_blocks() and _calculate_weight().
        It performs depth-first traversal through parent relationships.
        """
        for parent in self.parents:
            if parent.name not in visited:
                visited.add(parent.name)
                parent._collect_past_blocks(visited)

    def get_past_blocks(self) -> Set[str]:
        """Calculate all ancestor blocks on-demand (not cached).

        Returns
        -------
        set[str]
            Set of ancestor block names.

        Notes
        -----
        This method computes past blocks on-demand rather than caching them
        to avoid O(n²) memory overhead in large DAGs. For animation purposes,
        this is called infrequently enough that recalculation is acceptable.

        Examples
        --------
        ::

            # Get all ancestors of a block
            ancestors = block.get_past_blocks()
            print(f"Block {block.name} has {len(ancestors)} ancestors")
        """
        visited: Set[str] = set()
        self._collect_past_blocks(visited)
        return visited

    def is_tip(self) -> bool:
        """Check if this block is a tip (has no children).

        Returns
        -------
        bool
            True if block has no children, False otherwise.

        Examples
        --------
        ::

            if block.is_tip():
                print(f"Block {block.name} is a tip")
        """
        return not bool(self.children)

    # === VISUAL DELEGATION (CONVENIENCE METHODS) ===

    # These delegate to the visual layer for clean API

    def create_with_lines(self, **kwargs):
        """Create animation for block, label, and parent lines.

        Delegates to the visual block's create_with_lines() method.

        Parameters
        ----------
        **kwargs
            Keyword arguments passed to visual block's method.

        Returns
        -------
        AnimationGroup
            Animation for creating the block with all visual elements.

        Examples
        --------
        ::

            self.play(block.create_with_lines())
            self.play(block.create_with_lines(run_time=1.5))
        """
        return self._visual.create_with_lines(**kwargs)

    def create_movement_animation(self, animation):
        """Wrap movement animation with automatic line updates.

        Delegates to the visual block's create_movement_animation() method.

        Parameters
        ----------
        animation : Animation
            The movement animation to wrap.

        Returns
        -------
        AnimationGroup
            Animation with line updates for this block and its children.

        Examples
        --------
        ::

            self.play(block.create_movement_animation(
                block._visual.animate.shift(RIGHT * 2)
            ))
        """
        return self._visual.create_movement_animation(animation)

    def change_label(self, text: str, **kwargs):
        """Change the block's label text with animation.

        Delegates to the visual block's change_label() method.

        Parameters
        ----------
        text : str
            New label text.
        **kwargs
            Keyword arguments passed to visual block's method.

        Returns
        -------
        Transform
            Animation for changing the label.

        Examples
        --------
        ::

            self.play(block.change_label("42"))
        """
        return self._visual.change_label(text, **kwargs)