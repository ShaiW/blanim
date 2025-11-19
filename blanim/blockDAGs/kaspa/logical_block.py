# blanim\blanim\blockDAGs\kaspa\logical_block.py

from __future__ import annotations

__all__ = ["KaspaLogicalBlock"]

import secrets

from .config import DEFAULT_KASPA_CONFIG, KaspaConfig
from .visual_block import KaspaVisualBlock
from typing import Optional, List, Set, Any

#TODO instead of passing config around, use config as a single instance for the DAG
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

        # Kaspa-specific: blue score
        self.blue_count = 0
        self._compute_blue_score()
        self.weight = self.blue_count

        # Selected parent (always parents[0])
        self.selected_parent = self.parents[0] if self.parents else None

        # Create visual (composition)
        parent_visuals = [p.visual_block for p in self.parents]
        self._visual = KaspaVisualBlock(
            label_text=str(self.weight),
            position=position,
            parents=parent_visuals,
            kaspa_config=kaspa_config
        )
        self._visual.logical_block = self  # Bidirectional link

        # Register as child in parents
        for parent in self.parents:
            parent.children.append(self)

    def _compute_blue_score(self):
        """Compute blue score via GHOSTDAG."""
        # TODO: Implement proper GHOSTDAG
        visited = set()
#        self._collect_past_blocks(visited)
        self.blue_count = len(visited)

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