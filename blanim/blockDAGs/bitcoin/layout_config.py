# blanim/blanim/blockDAGs/bitcoin/layout_config.py

from __future__ import annotations

from dataclasses import dataclass

__all__ = ["DEFAULT_BITCOIN_LAYOUT_CONFIG", "BitcoinLayoutConfig"]


@dataclass
class BitcoinLayoutConfig:
    """Configuration for Bitcoin linear chain layout.

    Controls spatial positioning for Bitcoin's single-parent chain structure.
    Blocks are positioned horizontally in a straight line.
    """
    # Genesis block position
    genesis_x: float = -6.5
    genesis_y: float = 0.0

    # Spacing between consecutive blocks in the chain
    horizontal_spacing: float = 2.0

    # Vertical spacing for parallel blocks at the same height (during forks)
    vertical_spacing: float = 1.0

# Default configuration instance
DEFAULT_BITCOIN_LAYOUT_CONFIG = BitcoinLayoutConfig()