# blanim\blanim\blockDAGs\kaspa\logical_block.py

from __future__ import annotations

__all__ = ["KaspaLogicalBlock"]

import secrets
from dataclasses import dataclass, field

from .visual_block import KaspaVisualBlock
from typing import Optional, List, Set, Any, Dict

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ... import _KaspaConfigInternal

@dataclass
class GhostDAGData:
    """GHOSTDAG consensus data for a block."""
    blue_score: int = 0  # Total blue work in past cone
    unordered_mergeset: List['KaspaLogicalBlock'] = field(default_factory=list)
    blue_anticone: Set['KaspaLogicalBlock'] = field(default_factory=set)

    # NEW: Store local POV - blue status of all blocks evaluated from this block's perspective
    local_blue_pov: Dict['KaspaLogicalBlock', bool] = field(default_factory=dict)

class KaspaLogicalBlock:
    """Kaspa logical block with GHOSTDAG consensus."""

    def __init__(
            self,
            name: str,
            timestamp: Optional[float] = None,
            parents: Optional[List[KaspaLogicalBlock]] = None,
            position: tuple[float, float] = (0, 0),
            config: _KaspaConfigInternal = None,
            custom_label: Optional[str] = None,
    ):
        if config is None:
            raise ValueError("config parameter is required")
        self.config = config

        # Identity
        self.name = name
        # Time Created
        self.timestamp = timestamp
        # Tie-breaker (instead of actually hashing, just use a random number like a cryptographic hash)
        self.hash = secrets.randbits(32)  # 32-bit random integer to keep prob(collision) = low

        # DAG structure (single source of truth)
        self.parents = parents if parents else []
        self.children: List[KaspaLogicalBlock] = []

        # GHOSTDAG data
        self.ghostdag = GhostDAGData()
        self.selected_parent: Optional['KaspaLogicalBlock'] = None

        # Parent selection and GHOSTDAG computation (before visualization)
        if self.parents:
            self.selected_parent = self._select_parent()
            self.parents.sort(key=lambda p: p != self.selected_parent) #move SP to the index 0 before sending to visual
            self._create_unordered_mergeset()
            self._compute_ghostdag(self.config.k)

        # Create visual after GHOSTDAG computation
        parent_visuals = [p.visual_block for p in self.parents]

        # Custom Label if passed
        label_text = custom_label if custom_label is not None else str(self.ghostdag.blue_score)

        self._visual = KaspaVisualBlock(
            label_text=label_text,#TODO update this  NOTE: when passing an empty string, positioning breaks (fixed moving blocks by overriding move_to with only visual.square)
            position=position,
            parents=parent_visuals,
            config=self.config
        )
        self._visual.logical_block = self  # Bidirectional link

        # Register as child in parents
        for parent in self.parents:
            parent.children.append(self)

    @staticmethod
    def _get_sort_key(block: 'KaspaLogicalBlock') -> tuple:
        """Standardized tie-breaking: (blue_score, -hash) for ascending order."""
        return block.ghostdag.blue_score, -block.hash

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

    def _create_unordered_mergeset(self):
        """Compute mergeset without sorting."""
        if not self.selected_parent:
            self.ghostdag.unordered_mergeset = []
            return

        self_past = set(self.get_past_cone())
        selected_past = set(self.selected_parent.get_past_cone())
        self.ghostdag.unordered_mergeset = list(self_past - selected_past)

    def get_sorted_mergeset_with_sp(self) -> List['KaspaLogicalBlock']:
        """Get sorted mergeset with selected parent at index 0."""
        if not self.selected_parent:
            return []

            # Start with selected parent
        sorted_mergeset = [self.selected_parent]

        # Add and sort the rest (excluding selected parent)
        remaining = [block for block in self.ghostdag.unordered_mergeset if block != self.selected_parent]
        remaining.sort(key=self._get_sort_key)
        sorted_mergeset.extend(remaining)

        return sorted_mergeset

    def get_sorted_mergeset_without_sp(self) -> List['KaspaLogicalBlock']:
        """Get sorted mergeset excluding selected parent."""
        evaluation_mergeset = [block for block in self.ghostdag.unordered_mergeset if block != self.selected_parent]
        evaluation_mergeset.sort(key=self._get_sort_key)
        return evaluation_mergeset

    def _compute_ghostdag(self, k: int):
        """Compute GHOSTDAG consensus with parameter k."""
        if not self.selected_parent:
            return

        total_view = set(self.get_past_cone())
        selected_parent_blue_score = self.selected_parent.ghostdag.blue_score

        # Start with selected parent's local POV as baseline
        local_blue_status = self.selected_parent.ghostdag.local_blue_pov.copy()

        # Add selected parent itself as blue
        local_blue_status[self.selected_parent] = True

        blue_candidates = self.get_sorted_mergeset_without_sp()

        # Initialize all candidates as not blue locally
        for candidate in blue_candidates:
            local_blue_status[candidate] = False

        blue_in_mergeset = 0

        # Process candidates using local blue status
        for candidate in blue_candidates:
            if self._can_be_blue_local(candidate, local_blue_status, k, total_view):
                local_blue_status[candidate] = True
                blue_in_mergeset += 1
            else:
                local_blue_status[candidate] = False

                # Store the complete local POV (removed is_blue assignment)
        self.ghostdag.local_blue_pov = local_blue_status.copy()
        self.ghostdag.blue_score = selected_parent_blue_score + 1 + blue_in_mergeset

    def _can_be_blue_local(self,
                           candidate: 'KaspaLogicalBlock',
                           local_blue_status: Dict['KaspaLogicalBlock', bool],
                           k: int,
                           total_view: Set['KaspaLogicalBlock']) -> bool:
        """Check if candidate can be blue using local perspective."""

        # Get blue blocks from local perspective
        blue_blocks = {block for block, is_blue in local_blue_status.items() if is_blue}

        # Check 1: <= k blue blocks in candidate's anticone
        candidate_anticone = self.get_anticone(candidate, total_view)
        blue_in_anticone = len(candidate_anticone & blue_blocks)
        if blue_in_anticone > k:
            return False

            # Check 2: Adding candidate doesn't cause existing blues to have > k blues in anticone
        for blue_block in blue_blocks:
            blue_anticone = self.get_anticone(blue_block, total_view)
            if candidate in blue_anticone:
                blue_in_anticone = len(blue_anticone & blue_blocks) + 1
                if blue_in_anticone > k:
                    return False

        return True

    # TODO figure out if this can be replaced or if dag.get_anticone can be replaced
    @staticmethod
    def get_anticone(block: 'KaspaLogicalBlock',
                      total_view: Set['KaspaLogicalBlock']
                      ) -> Set['KaspaLogicalBlock']:
        """Get anticone of a block within the given total view."""
        past = set(block.get_past_cone())
        future = set(block.get_future_cone())

        # Anticone = total_view - past - future - block itself
        return total_view - past - future - {block}

    def get_dag_pov(self, target_block: 'KaspaLogicalBlock') -> Dict['KaspaLogicalBlock', bool]:
        """Get the DAG blue status from target_block's perspective recursively."""
        if target_block == self:
            return self.ghostdag.local_blue_pov.copy()

        # Recursively find the target block in the past cone
        for parent in self.parents:
            pov = parent.get_dag_pov(target_block)
            if pov is not None:
                return pov

        return {}
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