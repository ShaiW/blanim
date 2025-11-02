# blanim/blanim/blockDAGs/kaspa/layout_config.py

from __future__ import annotations

from dataclasses import dataclass

__all__ = ["DEFAULT_KASPA_LAYOUT_CONFIG", "KaspaLayoutConfig"]


@dataclass
class KaspaLayoutConfig:
    """Configuration for Kaspa DAG layer-based layout.

    Controls spatial positioning for Kaspa's multi-parent DAG structure.
    Blocks are organized into vertical layers based on their topological depth,
    with automatic positioning within each layer.
    """
    # Genesis block position
    genesis_x: float = -6.5
    genesis_y: float = 0.0

    # Horizontal spacing between layers (columns)
    layer_spacing: float = 1.5

    # Vertical spacing between blocks within the same layer
    chain_spacing: float = 1.0


# Default configuration instance
DEFAULT_KASPA_LAYOUT_CONFIG = KaspaLayoutConfig()