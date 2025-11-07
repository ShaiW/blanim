# blanim\blanim\blockDAGs\bitcoin\logical_block.py

from __future__ import annotations

__all__ = ["BitcoinLogicalBlock"]

from typing import Optional, List, Set

from .config import DEFAULT_BITCOIN_CONFIG, BitcoinBlockConfig
from .visual_block import BitcoinVisualBlock

class BitcoinLogicalBlock:
    """Bitcoin logical block with proxy pattern delegation."""

    def __init__(
            self,
            name: str,
            parent: Optional[BitcoinLogicalBlock] = None,
            position: tuple[float, float] = (0, 0),
            bitcoin_config: BitcoinBlockConfig = DEFAULT_BITCOIN_CONFIG
    ):
        # Identity
        self.name = name
        self.hash = id(self)

        # DAG structure (single source of truth)
        self.parent = parent
        self.children: List[BitcoinLogicalBlock] = []

        # Weight calculation
        self.weight = self._calculate_weight()

        # Selected parent (always parent)
        self.selected_parent = self.parent if self.parent else None

        # Create visual (composition)
        parent_visual = self.parent._visual if self.parent else None
        self._visual = BitcoinVisualBlock(
            label_text=str(self.weight),
            position=position,
            parent=parent_visual,
            bitcoin_config=bitcoin_config  # Type-specific parameter
        )
        self._visual.logical_block = self  # Bidirectional link

        # Register as child in parents
        if parent:
            parent.children.append(self)

    def _calculate_weight(self) -> int:
        """Bitcoin weight = chain length."""
        visited = set()
        self._collect_past_blocks(visited)
        return len(visited)

    def _collect_past_blocks(self, visited: Set[str]) -> None:
        """Recursive ancestor collection."""
        if self.parent and self.parent.name not in visited:
            visited.add(self.parent.name)
            self.parent._collect_past_blocks(visited)

    def __getattr__(self, attr: str):
        """Proxy pattern: delegate to _visual."""
        # Avoid infinite recursion for _visual itself
        if attr == '_visual':
            raise AttributeError(f"'{type(self).__name__}' object has no attribute '_visual'")
            # Delegate everything else to visual block
        return getattr(self._visual, attr)