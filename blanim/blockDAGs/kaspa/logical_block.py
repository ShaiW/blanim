# blanim\blanim\blockDAGs\kaspa\logical_block.py

from __future__ import annotations

__all__ = ["KaspaLogicalBlock"]

import secrets
from dataclasses import dataclass, field

from .config import DEFAULT_KASPA_CONFIG, KaspaConfig
from .visual_block import KaspaVisualBlock
from typing import Optional, List, Set, Any

@dataclass
class GhostDAGData:
    """GHOSTDAG consensus data for a block."""
    is_blue: bool = False
    blue_score: int = 0  # Total blue work in past cone
    mergeset: List['KaspaLogicalBlock'] = field(default_factory=list)
    blue_anticone: Set['KaspaLogicalBlock'] = field(default_factory=set)

class KaspaLogicalBlock:
    """Kaspa logical block with GHOSTDAG consensus.

    1. Always place Selected Parent in the [0] position.
    """

    def __init__(
            self,
            name: str,
            parents: Optional[List[KaspaLogicalBlock]] = None,
            position: tuple[float, float] = (0, 0),
            kaspa_config: KaspaConfig = DEFAULT_KASPA_CONFIG
    ):
        # Identity
        self.name = name
        # Tie-breaker (instead of actually hashing, just use a random number like a cryptographic hash)
        self.hash = secrets.randbits(32)  # 32-bit random integer

        # DAG structure (single source of truth)
        self.parents = parents if parents else []
        self.children: List[KaspaLogicalBlock] = []

        # GHOSTDAG data
        self.ghostdag = GhostDAGData()
        self.selected_parent: Optional['KaspaLogicalBlock'] = None

        # Parent selection and GHOSTDAG computation (before visualization)
        if self.parents:
            self.selected_parent = self._select_parent()
            self._compute_mergeset()
            self._compute_ghostdag(kaspa_config.k)

        # Create visual after GHOSTDAG computation
        parent_visuals = [p.visual_block for p in self.parents]
        self._visual = KaspaVisualBlock(
            label_text=str(" "),#TODO update this  NOTE: when passing an empty string, movement breaks when using move_to, use SHIFT
            position=position,
            parents=parent_visuals,
            kaspa_config=kaspa_config
        )
        self._visual.logical_block = self  # Bidirectional link

        # Register as child in parents
        for parent in self.parents:
            parent.children.append(self)

    def _get_sort_key(self, block: 'KaspaLogicalBlock') -> tuple:
        """Standardized tie-breaking: (blue_score, -hash) for ascending order."""
        return (block.ghostdag.blue_score, -block.hash)

    def _select_parent(self) -> Optional['KaspaLogicalBlock']:
        """Select parent with highest blue score, deterministic hash tie-breaker."""
        if not self.parents:
            return None

        # Sort by (blue_score, -hash) - highest first, so reverse=True
        sorted_parents = sorted(
            self.parents,
            key=self._get_sort_key,
            reverse=True
        )
        return sorted_parents[0]

    def _compute_mergeset(self):
        """Compute mergeset with topological ordering by blue work + hash tiebreaker."""
        if not self.selected_parent:
            self.ghostdag.mergeset = []
            return

        self_past = set(self.get_past_cone())
        selected_past = set(self.selected_parent.get_past_cone())
        mergeset = list(self_past - selected_past)

        # Topological sort: ascending blue work, hash as tiebreaker
        mergeset.sort(key=self._get_sort_key)
        self.ghostdag.mergeset = mergeset

    def _compute_ghostdag(self, k: int):
        """Compute GHOSTDAG consensus with parameter k."""
        if not self.selected_parent:
            return

        # The "total view" for GHOSTDAG is just the past cone of this block
        total_view = set(self.get_past_cone())

        # Start with selected parent as blue
        blue_blocks = {self.selected_parent}
        self.selected_parent.ghostdag.is_blue = True

        # Process mergeset in topological order
        for candidate in self.ghostdag.mergeset:
            if self._can_be_blue(candidate, blue_blocks, k, total_view):
                candidate.ghostdag.is_blue = True
                blue_blocks.add(candidate)
            else:
                candidate.ghostdag.is_blue = False

        self.ghostdag.blue_score = len(blue_blocks)

    def _can_be_blue(self, candidate: 'KaspaLogicalBlock',
                     blue_blocks: Set['KaspaLogicalBlock'], k: int,
                     total_view: Set['KaspaLogicalBlock']) -> bool:
        """Check if candidate can be blue according to GHOSTDAG rules."""
        # Check 1: <= k blue blocks in candidate's anticone
        candidate_anticone = self._get_anticone(candidate, total_view)
        blue_in_anticone = len(candidate_anticone & blue_blocks)
        if blue_in_anticone > k:
            return False

        # Check 2: Adding candidate doesn't cause existing blues to have > k blues in anticone
        for blue_block in blue_blocks:
            blue_anticone = self._get_anticone(blue_block, total_view)
            if candidate in blue_anticone:
                blue_in_anticone = len(blue_anticone & blue_blocks) + 1
                if blue_in_anticone > k:
                    return False

        return True

    def _get_anticone(self, block: 'KaspaLogicalBlock',
                      total_view: Set['KaspaLogicalBlock']) -> Set['KaspaLogicalBlock']:
        """Get anticone of a block within the given total view."""
        past = set(block.get_past_cone())
        future = set(block.get_future_cone())

        # Anticone = total_view - past - future - block itself
        return total_view - past - future - {block}

    ########################################
    # Collecting Past/Future
    ########################################

    def get_past_cone(self) -> List[KaspaLogicalBlock]:
        """Get all ancestors via depth-first search."""
        past = set()
        to_visit = [self]

        while to_visit:
            current = to_visit.pop()
            for parent in current.parents:
                if parent not in past:
                    past.add(parent)
                    to_visit.append(parent)

        return list(past)

    def get_future_cone(self) -> List[KaspaLogicalBlock]:
        """Get all descendants via depth-first search."""
        future = set()
        to_visit = [self]

        while to_visit:
            current = to_visit.pop()
            for child in current.children:
                if child not in future:
                    future.add(child)
                    to_visit.append(child)

        return list(future)

    ########################################
    # Accessing Visual Block
    ########################################

    @property
    def visual_block(self) -> KaspaVisualBlock:
        """Public accessor for the visual block."""
        return self._visual

    def __getattr__(self, attr: str) -> Any:
        """Proxy pattern: delegate to _visual."""
        if attr == '_visual':
            raise AttributeError(f"'{type(self).__name__}' object has no attribute '_visual'")
        return getattr(self._visual, attr)