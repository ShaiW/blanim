# blanim\blanim\blockDAGs\kaspa\logical_block.py

from __future__ import annotations

__all__ = ["KaspaLogicalBlock"]

from .config import DEFAULT_KASPA_CONFIG, KaspaBlockConfig
from .visual_block import KaspaVisualBlock
from typing import Optional, List, Set

class KaspaLogicalBlock:
    """Kaspa logical block with GHOSTDAG consensus."""

    def __init__(
            self,
            name: str,
            parents: Optional[List[KaspaLogicalBlock]] = None,
            position: tuple[float, float] = (0, 0),
            kaspa_config: KaspaBlockConfig = DEFAULT_KASPA_CONFIG
    ):
        # Identity
        self.name = name
        self.hash = id(self)

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
        parent_visuals = [p._visual for p in self.parents]  # FIX: Define this variable
        self._visual = KaspaVisualBlock(
            label_text=str(self.weight),
            position=position,
            parents=parent_visuals,
            kaspa_config=kaspa_config  # Type-specific parameter
        )
        self._visual.logical_block = self  # Bidirectional link

        # Register as child in parents
        for parent in self.parents:
            parent.children.append(self)

    def _compute_blue_score(self):
        """Compute blue score via GHOSTDAG."""
        # TODO: Implement proper GHOSTDAG
        visited = set()
        self._collect_past_blocks(visited)
        self.blue_count = len(visited)

    def _collect_past_blocks(self, visited: Set[str]) -> None:
        """Recursive ancestor collection."""
        for parent in self.parents:
            if parent.name not in visited:
                visited.add(parent.name)
                parent._collect_past_blocks(visited)

    def __getattr__(self, attr: str):
        """Proxy pattern: delegate to _visual."""
        if attr == '_visual':
            raise AttributeError(f"'{type(self).__name__}' object has no attribute '_visual'")
        return getattr(self._visual, attr)