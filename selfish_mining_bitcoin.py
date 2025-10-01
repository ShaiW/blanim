from common import *
from enum import Enum


class Block:
    def __init__(self, label: str, position: tuple, color: str, side_length: float = 0.8, parent_block: 'Block' = None):
        # Visual components (existing Manim objects)
        self.square = Square(side_length=side_length, color=color, fill_opacity=0)
        self.square.move_to(position)
        self.label = Text(label, font_size=24, color=WHITE)
        self.label.move_to(self.square.get_center())

        self.children = []
        self.next_genesis = False

        self.parent_block = parent_block
        if parent_block:
            parent_block.children.append(self)


    def get_mobjects(self):
        """Return list of Manim mobjects for rendering"""
        return [self.square, self.label]

    def move_to(self, position):
        """Move block to new position"""
        self.square.move_to(position)
        self.label.move_to(self.square.get_center())

    def get_center(self):
        """Get center position of block"""
        return self.square.get_center()

    def get_left(self):
        """Get left edge of block"""
        return self.square.get_left()

    def get_right(self):
        """Get right edge of block"""
        return self.square.get_right()

    def get_children(self) -> list['Block']:
        """Get children directly from stored list - O(1) access"""
        return self.children.copy()  # Return copy to prevent external modification

    def set_as_next_genesis(self):
        """Mark this block as the next genesis block"""
        self.next_genesis = True

    def is_next_genesis(self) -> bool:
        """Check if this block is marked as next genesis"""
        return self.next_genesis

    def get_chain_depth(self) -> int:
        """Get depth from genesis (automatic ordering)"""
        depth = 0
        current = self
        while current.parent_block:
            depth += 1
            current = current.parent_block
        return depth

    def get_chain_path(self) -> list['Block']:
        """Get ordered path from genesis to this block"""
        path = []
        current = self
        while current:
            path.insert(0, current)
            current = current.parent_block
        return path

    def get_genesis_block(self) -> 'Block':
        """Get the genesis block for this chain"""
        current = self
        while current.parent_block:
            current = current.parent_block
        return current

    def is_genesis(self) -> bool:
        """Check if this block is a genesis block (has no parent)"""
        return self.parent_block is None

    def get_all_descendants(self) -> list['Block']:
        """Get all descendant blocks recursively - now O(n) instead of O(n²)"""
        descendants = []
        for child in self.children:
            descendants.append(child)
            descendants.extend(child.get_all_descendants())
        return descendants

    def get_family(self) -> list['Block']:
        """Get this block and all its descendants"""
        family = [self]
        family.extend(self.get_all_descendants())
        return family

    def serialize(self) -> dict:
        """Serialize block state for reconstruction"""
        return {
            "label": self.label.text if hasattr(self.label, 'text') else str(self.label),
            "position": self.get_center(),
            "color": self.square.color,
            "opacity": self.square.fill_opacity,
            "next_genesis": self.next_genesis,
            "parent_label": self.parent_block.label.text if self.parent_block else None,
            "children_labels": [child.label.text for child in self.children],
            "chain_depth": self.get_chain_depth()
        }

    def __repr__(self) -> str:
        """String representation for debugging"""
        parent_label = self.parent_block.label.text if self.parent_block else "None"
        children_labels = [child.label.text for child in self.children]
        return f"Block(label={self.label.text}, parent={parent_label}, children={children_labels}, next_genesis={self.next_genesis})"

class Blockchain:
    def __init__(self, chain_type: str, color: str, y_offset: float = 0):
        self.chain_type = chain_type
        self.color = color
        self.y_offset = y_offset
        self.blocks = []
        self.lines = []

    def add_block(self, label: str, x_position: float, parent_block: 'Block' = None, is_genesis: bool = False):
        position = (x_position, self.y_offset, 0)

        # Strict validation: either genesis or must have parent
        if is_genesis and parent_block is not None:
            raise ValueError("Genesis block cannot have a parent")

        if not is_genesis and parent_block is None:
            raise ValueError("Non-genesis block must have a parent - no default fallback allowed")

        block = Block(label, position, self.color, parent_block=parent_block)
        self.blocks.append(block)
        return block

    def create_line_to_previous(self, current_block_index: int):
        """Create line connecting current block to previous block"""
        if current_block_index > 0:
            current_block = self.blocks[current_block_index]
            previous_block = self.blocks[current_block_index - 1]
            line = Line(
                start=current_block.get_left(),
                end=previous_block.get_right(),
                buff=0.1, color=WHITE, stroke_width=2
            )
            self.lines.append(line)
            return line
        return None

    def create_line_to_genesis(self, genesis_block, block_index: int = 0):
        """Create line connecting first block to genesis"""
        if self.blocks:
            block = self.blocks[block_index]
            line = Line(
                start=block.get_left(),
                end=genesis_block.get_right(),
                buff=0.1, color=WHITE, stroke_width=2
            )
            if len(self.lines) <= block_index:
                self.lines.append(line)
            else:
                self.lines[block_index] = line
            return line
        return None

    def get_all_mobjects(self):
        mobjects = []
        for block in self.blocks:
            mobjects.extend(block.get_mobjects())
        mobjects.extend(self.lines)
        return mobjects

class StateTextManager:
    def __init__(self):
        self.states = {}

    def get_state(self, state_name: str):
        if state_name not in self.states:
            state_texts = {
                "selfish_mining": "Selfish Mining in Bitcoin",
                "state0": "State 0",
                "state0prime": "State 0'",
                "state1": "State 1",
                "state2": "State 2",
                "state3": "State 3",
                "state4": "State 4",
                "honest_wins": "Honest miner finds a block",
                "selfish_wins": "Selfish miner finds a block",
                "reveal": "Selfish miner reveals blocks"
            }
            text = state_texts.get(state_name, state_name)
            state = MathTex(rf"\text{{{text}}}", color=WHITE)
            state.to_edge(UP)
            self.states[state_name] = state
        return self.states[state_name]

class ChainStateManager:
    def __init__(self):
        """Initialize the chain state manager for tracking mining sequences"""
        self.sequences = []  # List of all completed mining sequences
        self.current_sequence = None  # Currently active mining sequence
        self.sequence_counter = 0  # Auto-incrementing sequence ID

    def start_new_sequence(self, genesis_block: 'Block') -> 'MiningSequence':
        """
        Start tracking a new mining sequence

        Args:
            genesis_block: The genesis block for this sequence

        Returns:
            MiningSequence: The newly created sequence object
        """
        self.sequence_counter += 1
        sequence = MiningSequence(self.sequence_counter, genesis_block)
        self.sequences.append(sequence)
        self.current_sequence = sequence
        return sequence

    def end_current_sequence(self, winning_block: 'Block'):
        """
        End the current sequence and mark the winner

        Args:
            winning_block: The block that won and becomes next genesis
        """
        if self.current_sequence:
            self.current_sequence.set_winner(winning_block)
            winning_block.set_as_next_genesis()
            self.current_sequence = None  # Clear current sequence

    def get_all_blocks(self) -> list['Block']:
        """
        Get all blocks from all sequences using the new bidirectional tracking

        Returns:
            list[Block]: All blocks in chronological order
        """
        all_blocks = []
        for sequence in self.sequences:
            all_blocks.extend(sequence.get_all_blocks())
        return all_blocks

    def get_genesis_evolution(self) -> list['Block']:
        """
        Get the evolution of genesis blocks across sequences

        Returns:
            list[Block]: Genesis blocks in chronological order
        """
        return [sequence.genesis_block for sequence in self.sequences]

    def reconstruct_full_chain(self) -> dict:
        """
        Reconstruct complete chain state for debugging/analysis

        Returns:
            dict: Complete chain statistics and structure
        """
        return {
            "total_sequences": len(self.sequences),
            "total_blocks": len(self.get_all_blocks()),
            "genesis_evolution": [block.label.text for block in self.get_genesis_evolution()],
            "completed_sequences": [seq.get_summary() for seq in self.sequences if seq.is_complete()]
        }

    def get_all_forks(self) -> dict:
        """
        Get all fork structures with preserved colors and relationships

        Returns:
            dict: Fork data organized by sequence with full reconstruction info
        """
        forks = {}
        for sequence in self.sequences:
            forks[sequence.sequence_id] = {
                "genesis": sequence.genesis_block.serialize(),
                "blocks": [block.serialize() for block in sequence.get_all_blocks()],
                "fork_structure": sequence.get_fork_structure(),
                "winner": sequence.winner_block.serialize() if sequence.winner_block else None
            }
        return forks

class MiningSequence:
    def __init__(self, sequence_id: int, genesis_block: 'Block'):
        """
        Initialize a mining sequence

        Args:
            sequence_id: Unique identifier for this sequence
            genesis_block: The genesis block for this sequence
        """
        self.sequence_id = sequence_id
        self.genesis_block = genesis_block
        self.blocks_added = []  # Blocks added during this sequence
        self.winner_block = None  # Block that won this sequence
        self.is_active = True  # Whether sequence is still ongoing

    def add_block(self, label: str, position: tuple, color: str, parent: 'Block', side_length: float = 0.8) -> 'Block':
        """
        Create and add a block to this sequence with automatic parent relationship

        Args:
            label: Block label
            position: Block position
            color: Block color (preserves honest/selfish distinction)
            parent: The parent block (establishes chain relationship automatically)
            side_length: Block size

        Returns:
            Block: The newly created block with parent relationship established

        Why changed: Uses Block constructor with parent_block parameter to automatically
        establish bidirectional relationships during creation
        """
        block = Block(label, position, color, side_length, parent_block=parent)
        self.blocks_added.append(block)
        return block

    def set_winner(self, winning_block: 'Block'):
        """
        Mark the winning block and complete the sequence

        Args:
            winning_block: The block that won this sequence
        """
        self.winner_block = winning_block
        self.is_active = False

    def get_all_blocks(self) -> list['Block']:
        """
        Get all blocks in this sequence using the new bidirectional tracking

        Returns:
            list[Block]: All blocks in this sequence ordered by depth

        Why improved: No longer needs complex parent relationship traversal since
        Block class now maintains efficient bidirectional relationships
        """
        all_blocks = [self.genesis_block]

        # Use the genesis block's get_all_descendants() method for efficient traversal
        descendants = self.genesis_block.get_all_descendants()

        # Filter to only include blocks that were added in this sequence
        sequence_descendants = [block for block in descendants if block in self.blocks_added]

        # Sort by chain depth for proper ordering
        sequence_descendants.sort(key=lambda b: b.get_chain_depth())

        all_blocks.extend(sequence_descendants)
        return all_blocks

    def get_fork_structure(self) -> dict:
        """
        Get the fork structure for this sequence using efficient child access

        Returns:
            dict: Fork structure with parent-child relationships and colors
        """
        structure = {}
        all_blocks = self.get_all_blocks()

        for block in all_blocks:
            structure[block.label.text] = {
                "parent": block.parent_block.label.text if block.parent_block else None,
                "children": [child.label.text for child in block.get_children()],
                "color": block.square.color,
                "depth": block.get_chain_depth(),
                "is_genesis": block.is_genesis(),
                "next_genesis": block.is_next_genesis()
            }

        return structure

    def is_complete(self) -> bool:
        """
        Check if this sequence is complete (has a winner)

        Returns:
            bool: True if sequence has ended with a winner
        """
        return not self.is_active and self.winner_block is not None

    def get_summary(self) -> dict:
        """
        Get summary information about this sequence

        Returns:
            dict: Summary of sequence state and statistics
        """
        all_blocks = self.get_all_blocks()
        return {
            "sequence_id": self.sequence_id,
            "genesis_label": self.genesis_block.label.text,
            "total_blocks": len(all_blocks),
            "max_depth": max(block.get_chain_depth() for block in all_blocks) if all_blocks else 0,
            "winner_label": self.winner_block.label.text if self.winner_block else None,
            "is_complete": self.is_complete(),
            "fork_count": len([block for block in all_blocks if len(block.get_children()) > 1])
        }

class RaceState:
    def __init__(self):
        self.final_honest_blocks = 0
        self.final_selfish_blocks = 0
        self.winner = None  # "honest" or "selfish"
        self.is_resolved = False

    def add_block(self, miner_type: str):
        """Record a block being created during this race"""
        if miner_type == "honest":
            self.final_honest_blocks += 1
        else:
            self.final_selfish_blocks += 1

    def resolve_race(self, winner: str):
        """Mark the race as resolved with winner"""
        self.winner = winner
        self.is_resolved = True

    def get_race_summary(self) -> dict:
        """Get complete summary of the race state"""
        return {
            "final_state": {
                "honest_blocks": self.final_honest_blocks,
                "selfish_blocks": self.final_selfish_blocks
            },
            "winner": self.winner,
            "is_resolved": self.is_resolved
        }

class RaceHistoryManager:
    def __init__(self):
        self.race_history = []
        self.current_race = None

    def start_new_race(self) -> RaceState:
        """Start tracking a new race - always starts from genesis"""
        race = RaceState()
        self.current_race = race
        self.race_history.append(race)
        return race

    def record_block_creation(self, miner_type: str):
        """Record a block being created in the current race"""
        if self.current_race and not self.current_race.is_resolved:
            self.current_race.add_block(miner_type)

    def resolve_current_race(self, winner: str):
        """Resolve the current race"""
        if self.current_race:
            self.current_race.resolve_race(winner)
            self.current_race = None

    def get_all_race_history(self) -> list[dict]:
        """Get complete history of all races"""
        return [race.get_race_summary() for race in self.race_history]

class AnimationConfig:
    """Centralized animation timing configuration"""

    # Scene timing
    WAIT_TIME = 1.0

    # Animation durations
    FADE_IN_TIME = 1.0
    FADE_OUT_TIME = 1.0
    BLOCK_CREATION_TIME = 1.0
    CHAIN_RESOLUTION_TIME = 2.0

    @classmethod
    def set_speed_multiplier(cls, multiplier: float):
        """Scale all timings by a multiplier for faster/slower animations"""
        cls.FADE_IN_TIME *= multiplier
        cls.FADE_OUT_TIME *= multiplier
        cls.BLOCK_CREATION_TIME *= multiplier
        cls.CHAIN_RESOLUTION_TIME *= multiplier

#TODO START HERE and implement positioning in SelfishMiningSquares
#TODO doublecheck this AND make positioning dynamic so you can fit target number of blocks to screen based on expected block race length
class LayoutConfig:
    # Position constants
    GENESIS_X_POSITION = -4
    FIRST_BLOCK_X_POSITION = -2
    BLOCK_HORIZONTAL_SPACING = 2.0
#    CHAIN_VERTICAL_SPACING = 1.2

    # Chain offsets
    HONEST_Y_OFFSET = 0
    SELFISH_Y_OFFSET = -1.2

    @staticmethod
    def calculate_block_position(chain_type: str, block_number: int, parent_block: 'Block' = None) -> tuple:
        """Calculate position for a new block based on chain type and parent position"""

        if parent_block:
            # Position relative to parent
            parent_pos = parent_block.get_center()
            x_position = parent_pos[0] + LayoutConfig.BLOCK_HORIZONTAL_SPACING
            y_position = parent_pos[1]  # Same y as parent for chain continuation
        else:
            # Default positioning for first block in chain
            x_position = LayoutConfig.FIRST_BLOCK_X_POSITION + (block_number - 1) * LayoutConfig.BLOCK_HORIZONTAL_SPACING
            y_position = LayoutConfig.SELFISH_Y_OFFSET if chain_type == "selfish" else LayoutConfig.HONEST_Y_OFFSET

        return x_position, y_position, 0

class SelfishMiningConfig:
    HONEST_AHEAD_THRESHOLD = -1
    SELFISH_AHEAD_THRESHOLD = 1
    TIE_THRESHOLD = 0
    SELFISH_ADVANTAGE_THRESHOLD = 2
    GENESIS_LABEL = "Gen"


class RaceOutcome(Enum):
    HONEST_WINS = "honest"
    SELFISH_WINS = "selfish"
    CONTINUE = "continue"

class AnimationFactory:
    def __init__(self):
        pass

    @staticmethod
    def fade_in_and_create(mobject):
        mobject.is_visible = True
        return Create(mobject, run_time=AnimationConfig.FADE_IN_TIME)

    @staticmethod
    def fade_out_and_remove(mobject):
        mobject.is_visible = False
        return FadeOut(mobject, run_time=AnimationConfig.FADE_OUT_TIME)

# passing scene to class to bypass limitations of a single play call (last animation on a mobject will override previous)
class SelfishMiningSquares:
    def __init__(self, scene):
        self.scene = scene

        self.honest_y_offset = 0
        self.selfish_y_offset = -1.2
        self.genesis_position = (-4, self.honest_y_offset, 0) # (-4, 0, 0) Selected to center chain visually on screen AND keep focus on individual races/states (x block spacing is 2)

        self.selfish_miner_block_opacity = 0.5 #TODO ensure this is used for pre-reveal blocks
        self.current_state = "init" #TODO remove/replace and use auto state tracking

        # TODO this might be able to replace state manager (or the other way around)
        self.selfish_blocks_created = 0
        self.honest_blocks_created = 0
        self.previous_selfish_lead = 0

        # Initialize managers
        self.state_manager = StateTextManager()
        self.animation_factory = AnimationFactory()
        # Race history for recreating full chain later, if desired
        self.race_history_manager = RaceHistoryManager()

        # Create blockchains
        self.selfish_chain = Blockchain("selfish", PURE_RED, self.selfish_y_offset)
        self.honest_chain = Blockchain("honest", "#0000FF", self.honest_y_offset)

        # Create genesis block
        self.genesis = Block("Gen", self.genesis_position, "#0000FF")

        # Start the first race
        # TODO need to automate (start first race within RaceManager init?)
        self.race_history_manager.start_new_race()

    def advance_selfish_chain(self):
        """Create next selfish block with animated fade-in and record in race history"""
        self.selfish_blocks_created += 1
        label = f"s{self.selfish_blocks_created}"

        # Determine parent block #TODO, parent not always genesis since switching to dynamic block creation.
        if self.selfish_blocks_created == 1:
            parent = self.genesis
        else:
            parent = self.selfish_chain.blocks[-1]

            # Create block using existing chain method
        position = (-2 + (self.selfish_blocks_created - 1) * 2, -1.2, 0)
        block = self.selfish_chain.add_block(label, position[0], parent_block=parent)

        # Create connecting line
        if self.selfish_blocks_created == 1:
            line = self.selfish_chain.create_line_to_genesis(self.genesis, 0)
        else:
            line = self.selfish_chain.create_line_to_previous(self.selfish_blocks_created - 1)

            # Animate the block and line creation with proper fade-in timing
        animations = [self.animation_factory.fade_in_and_create(mob) for mob in block.get_mobjects()]
        if line:
            animations.append(self.animation_factory.fade_in_and_create(line))

        self.scene.play(*animations)

        # Record in race history
        self.race_history_manager.record_block_creation("selfish")

        # Check for automatic resolution after state change
        self._check_and_resolve_race()

        return block, line

    def advance_honest_chain(self):
        """Create next honest block with animated fade-in and record in race history"""
        self.honest_blocks_created += 1
        label = f"h{self.honest_blocks_created}"

        # Determine parent block
        if self.honest_blocks_created == 1:
            parent = self.genesis
        else:
            parent = self.honest_chain.blocks[-1]

            # Create block using existing chain method
        position = (-2 + (self.honest_blocks_created - 1) * 2, 0, 0)
        block = self.honest_chain.add_block(label, position[0], parent_block=parent)

        # Create connecting line
        if self.honest_blocks_created == 1:
            line = self.honest_chain.create_line_to_genesis(self.genesis, 0)
        else:
            line = self.honest_chain.create_line_to_previous(self.honest_blocks_created - 1)

            # Animate the block and line creation with proper fade-in timing
        animations = [self.animation_factory.fade_in_and_create(mob) for mob in block.get_mobjects()]
        if line:
            animations.append(self.animation_factory.fade_in_and_create(line))

        self.scene.play(*animations)

        # Record in race history
        self.race_history_manager.record_block_creation("honest")

        # Check for automatic resolution after state change
        self._check_and_resolve_race()

        return block, line

    def _check_and_resolve_race(self) -> None:
        """Evaluate race conditions and trigger resolution if needed.

        Implements selfish mining strategy:
        - Honest ahead by 1: Honest wins immediately
        - Tie with blocks: Random 50/50 tiebreak, change later
        - Selfish catches up from -2 to -1: Selfish publishes and wins
        """
        if not self.race_history_manager.current_race:
            return

        current_race = self.race_history_manager.current_race
        honest_blocks = current_race.final_honest_blocks
        selfish_blocks = current_race.final_selfish_blocks
        selfish_lead = selfish_blocks - honest_blocks

        # Rule 1: Honest chain gets ahead by 1 -> honest wins
        if selfish_lead == -1:  # honest ahead by 1
            self._trigger_resolution("honest")

            # Rule 2: Selfish goes from 0 to +1 -> race continues (no action)
        elif selfish_lead == 1:
            pass  # Race continues

        # Rule 3: Honest catches up from -1 to 0 -> publish selfish, then tiebreak
        elif selfish_lead == 0 and honest_blocks > 0:
            # First reveal the selfish chain with positioning animation
            self._reveal_selfish_chain_for_tie()

            # Determine tiebreak winner
            winner = self._resolve_tiebreak()

            # Add the decisive block that breaks the tie
            winning_block = self._add_tiebreak_winning_block(winner)

            # Wait to show the new state
            self.scene.wait(1)

            # Use consistent resolution path
            self._trigger_resolution(winner)

            return  # Important: exit early to avoid duplicate resolution

        # Rule 4: Selfish +1 to +2 -> race continues (no action)
        elif selfish_lead == 2:
            pass  # Race continues

        # Rule 5: Selfish >+2 -> race continues (no action)
        elif selfish_lead > 2:
            pass  # Race continues

        # Rule 6: Honest catches up from -2 to -1 -> selfish publishes and wins
        elif selfish_lead == 1 and self._was_previous_lead_2():
            self._trigger_resolution("selfish")

        self.previous_selfish_lead = selfish_lead

    def _reveal_selfish_chain_for_tie(self):
        """Reveal selfish chain by moving both chains to equal y-positions from genesis"""
        if not self.selfish_chain.blocks or not self.honest_chain.blocks:
            return

            # Calculate target y-positions (equal distance from genesis)
        genesis_y = self.genesis_position[1]
        chain_spacing = 0.6  # Half the normal spacing for visual balance

        honest_target_y = genesis_y + chain_spacing
        selfish_target_y = genesis_y - chain_spacing

        # Calculate shifts needed
        honest_shift = honest_target_y - self.honest_chain.y_offset
        selfish_shift = selfish_target_y - self.selfish_chain.y_offset

        # Collect all mobjects for movement
        honest_mobjects = []
        for block in self.honest_chain.blocks:
            honest_mobjects.extend(block.get_mobjects())
        honest_mobjects.extend(self.honest_chain.lines)

        selfish_mobjects = []
        for block in self.selfish_chain.blocks:
            selfish_mobjects.extend(block.get_mobjects())
        selfish_mobjects.extend(self.selfish_chain.lines)

        # Animate both chains moving to their new positions
        self.scene.play(AnimationGroup(
            *[mob.animate.shift(UP * honest_shift) for mob in honest_mobjects],
            *[mob.animate.shift(UP * selfish_shift) for mob in selfish_mobjects]
        ))

        # Wait to show the tie state
        self.scene.wait(1)

    def _was_previous_lead_2(self):
        """Check if previous selfish lead was 2"""
        return self.previous_selfish_lead == 2

    def _update_genesis_reference(self, winning_block: 'Block'):
        """Update genesis to point to the winning block and prepare for next race"""
        # Update our genesis reference to point to winning block
        self.genesis = winning_block

        # Clear the blockchain lists for next race
        self.selfish_chain.blocks.clear()
        self.selfish_chain.lines.clear()
        self.honest_chain.blocks.clear()
        self.honest_chain.lines.clear()

    def _resolve_tiebreak(self):
        """Simple 50/50 random tiebreak"""
        import random
        return "honest" if random.random() < 0.5 else "selfish"

    def _trigger_resolution(self, winner: str):
        """Trigger resolution and update genesis reference"""
        # Get winning block before resolution animations
        if winner == "honest":
            winning_block = self.honest_chain.blocks[-1] if self.honest_chain.blocks else None
        else:
            winning_block = self.selfish_chain.blocks[-1] if self.selfish_chain.blocks else None

            # Run resolution animation
        self.resolve_race_winner(winner)

        # Update genesis reference to winning block
        if winning_block:
            self._update_genesis_reference(winning_block)

            # Reset for next race
        self.resolve_race(winner)

    def resolve_race(self, winner: str):
        """Resolve the current race and start a new one"""
        self.race_history_manager.resolve_current_race(winner)

        # Reset counters for next race
        self.honest_blocks_created = 0
        self.selfish_blocks_created = 0
        self.previous_selfish_lead = 0

        # Start new race for next sequence
        self.race_history_manager.start_new_race()

    def check_race_resolution(self):
        """Check if current race should be resolved and determine winner"""
        if not self.race_history_manager.current_race:
            return None

        current_race = self.race_history_manager.current_race
        honest_blocks = current_race.final_honest_blocks
        selfish_blocks = current_race.final_selfish_blocks

        # Determine if race should be resolved based on blockchain rules
        if honest_blocks > selfish_blocks:
            return "honest"
        elif selfish_blocks > honest_blocks:
            return "selfish"
        elif honest_blocks == selfish_blocks and honest_blocks > 0:
            # Tiebreak scenario - in Bitcoin, first received block typically wins
            # For simulation purposes, you can implement your preferred tiebreak logic
            return "honest"  # Default to honest miner in ties

        return None  # Race continues - no clear winner yet

    def get_current_race_state(self) -> dict:
        """Get current race state information"""
        if not self.race_history_manager.current_race:
            return {"active": False}

        current_race = self.race_history_manager.current_race
        return {
            "active": True,
            "honest_blocks": current_race.final_honest_blocks,
            "selfish_blocks": current_race.final_selfish_blocks,
            "selfish_lead": current_race.final_selfish_blocks - current_race.final_honest_blocks,
            "is_resolved": current_race.is_resolved,
            "winner": current_race.winner
        }

    def get_race_history(self) -> list[dict]:
        """Get complete race history for analysis and visualization"""
        return self.race_history_manager.get_all_race_history()

    def get_current_state(self):
        """Get the current state of the animation"""
        return self.current_state

    def reset_to_initial_state(self):
        """Reset all blocks and state to initial position"""
        self.current_state = "init"

        # Reset genesis
        for mob in self.genesis.get_mobjects():
            mob.move_to(self.genesis_position)
            mob.set_opacity(1.0)

            # Reset all chain blocks to initial positions and opacity
        for i, block in enumerate(self.selfish_chain.blocks):
            for mob in block.get_mobjects():
                mob.move_to((-2 + i * 2, -1.2, 0))
                mob.set_opacity(0)

        for i, block in enumerate(self.honest_chain.blocks):
            for mob in block.get_mobjects():
                mob.move_to((-2 + i * 2, 0, 0))
                mob.set_opacity(0)

                # Reset all lines
        for line in self.selfish_chain.lines + self.honest_chain.lines:
            line.set_opacity(0)

    def _add_tiebreak_winning_block(self, winner: str):
        """Add the decisive block that breaks the tie"""
        if winner == "honest":
            # Add new honest block
            self.honest_blocks_created += 1
            label = f"h{self.honest_blocks_created}"
            parent = self.honest_chain.blocks[-1]
            position = (-2 + (self.honest_blocks_created - 1) * 2, 0, 0)
            block = self.honest_chain.add_block(label, position[0], parent_block=parent)
            line = self.honest_chain.create_line_to_previous(self.honest_blocks_created - 1)
        else:
            # Add new selfish block
            self.selfish_blocks_created += 1
            label = f"s{self.selfish_blocks_created}"
            parent = self.selfish_chain.blocks[-1]
            position = (-2 + (self.selfish_blocks_created - 1) * 2, -1.2, 0)
            block = self.selfish_chain.add_block(label, position[0], parent_block=parent)
            line = self.selfish_chain.create_line_to_previous(self.selfish_blocks_created - 1)

            # Animate the new block
        animations = [self.animation_factory.fade_in_and_create(mob) for mob in block.get_mobjects()]
        if line:
            animations.append(self.animation_factory.fade_in_and_create(line))
        self.scene.play(*animations)

        return block
    ####################
    # handle chain resolution
    ####################
    def resolve_race_winner(self, winner: str):
        """Unified 4-step animation: move up, move left, fade out, fade in new label"""
        # Determine winning chain and block
        if winner == "honest":
            winning_chain = self.honest_chain
            losing_chain = self.selfish_chain
            winning_y_offset = self.honest_chain.y_offset
        else:
            winning_chain = self.selfish_chain
            losing_chain = self.honest_chain
            winning_y_offset = self.selfish_chain.y_offset

        winning_block = winning_chain.blocks[-1] if winning_chain.blocks else None
        if not winning_block:
            return

            # Step 1: Calculate vertical shift to move winning chain to genesis y position
        genesis_y = self.genesis_position[1]
        vertical_shift = genesis_y - winning_y_offset

        # Collect all mobjects for movement
        all_mobjects = []
        for block in winning_chain.blocks:
            all_mobjects.extend(block.get_mobjects())
        for block in losing_chain.blocks:
            all_mobjects.extend(block.get_mobjects())
        all_mobjects.extend(winning_chain.lines)
        all_mobjects.extend(losing_chain.lines)

        # Step 1: Move both chains up by the same amount
        self.scene.play(AnimationGroup(
            *[mob.animate.shift(UP * vertical_shift) for mob in all_mobjects]
        ))

        # Step 2: Calculate horizontal shift to move winning block to genesis x position
        winning_block_x = winning_block.get_center()[0]
        genesis_x = self.genesis_position[0]
        horizontal_shift = genesis_x - winning_block_x

        # Move all mobjects left by the required amount
        self.scene.play(AnimationGroup(
            *[mob.animate.shift(LEFT * abs(horizontal_shift)) for mob in all_mobjects],
            *[mob.animate.shift(LEFT * abs(horizontal_shift)) for mob in self.genesis.get_mobjects()]
        ))

        # Step 3: Fade out everything except winning block square
        fade_out_mobjects = []

        # All winning chain blocks except winner square
        for block in winning_chain.blocks[:-1]:
            fade_out_mobjects.extend(block.get_mobjects())
        fade_out_mobjects.append(winning_block.label)  # Fade out winner's label too

        # All losing chain blocks
        for block in losing_chain.blocks:
            fade_out_mobjects.extend(block.get_mobjects())

            # All lines and old genesis
        fade_out_mobjects.extend(winning_chain.lines)
        fade_out_mobjects.extend(losing_chain.lines)
        fade_out_mobjects.extend(self.genesis.get_mobjects())

        self.scene.play(AnimationGroup(
            *[self.animation_factory.fade_out_and_remove(mob) for mob in fade_out_mobjects]
        ))

        # Step 4: Create and fade in new "Gen" label for winning block
        new_label = Text("Gen", font_size=24, color=WHITE)
        new_label.move_to(winning_block.square.get_center())

        self.scene.play(self.animation_factory.fade_in_and_create(new_label))

        # Update the winning block's label reference
        winning_block.label = new_label

    def resolve_tie_situation(self):
        """Handle resolution when chains are tied - both coexist temporarily"""

        # Get the first blocks from both chains
        # This is the only situation where a tiebreaker occurs
        selfish_block = self.selfish_chain.blocks[0] if len(self.selfish_chain.blocks) > 0 else None
        honest_block = self.honest_chain.blocks[0] if len(self.honest_chain.blocks) > 0 else None

        if not selfish_block or not honest_block:
            return

        self.scene.wait(1)  # Show coexistence for a moment

        return "tie_state"


class SelfishMiningExample(Scene):
    def construct(self):
        # Initialize the mining system
        sm = SelfishMiningSquares(self)
        self.wait(1)

        # Add genesis block to scene
        self.play(*[sm.animation_factory.fade_in_and_create(mob) for mob in sm.genesis.get_mobjects()])
        self.wait(1)

        # TODO previous version limited to +4 from Gen, can change but any time selfish is +4 from gen and +1 added,
        #       need to shift chains left 1 position
        # TODO need to set up mining simulation based on a (either as initialize or with its own func)
        sm.advance_selfish_chain()
        self.wait(1)
        sm.advance_selfish_chain()
        self.wait(1)
        sm.advance_selfish_chain()
        self.wait(1)
        sm.advance_honest_chain()
        self.wait(1)
        sm.advance_selfish_chain()
        self.wait(1)
        sm.advance_honest_chain()
        self.wait(1)
        sm.advance_honest_chain()
        self.wait(1)

        # Handle race resolution
        # TODO nothing currently happens, need to set up for tie breaking based on a and y
#        sm.resolve_tie_situation()
#        self.wait(1)
#        sm.advance_honest_chain()  # Break the tie
#        self.wait(1)
        # TODO lines do not follow Gen since changing to dynamic handling(only required updating is when selfish wins)
        # TODO need to automatically resolve on either tiebreaking or reveal(from honest catching up -1)
        # TODO Gen needs to be the same color as the winning block(this is probably from moving gen back to gen pos, then replacing winning block with gen, this is not required, only label replace is required)
        sm.resolve_selfish_chain_wins()
        self.wait(1)
