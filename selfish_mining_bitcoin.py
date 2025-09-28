from common import *


class Block:
    def __init__(self, label: str, position: tuple, color: str, side_length: float = 0.8, parent_block: 'Block' = None):
        # Visual components (existing Manim objects)
        self.square = Square(side_length=side_length, color=color, fill_opacity=0)
        self.square.move_to(position)
        self.label = Text(label, font_size=24, color=WHITE)
        self.label.move_to(self.square.get_center())

        # Bidirectional tracking - parent and children relationships
        self.parent_block = None
        self.children = []  # Direct children list for O(1) access
        self.next_genesis = False

        # Set parent relationship during initialization only
        if parent_block:
            self._set_parent(parent_block)

    def _set_parent(self, parent_block: 'Block'):
        """Internal method to set parent block - only called during initialization"""
        self.parent_block = parent_block
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

    def add_child(self, child_block: 'Block'):
        """Add a child block (automatically sets bidirectional relationship)"""
        if child_block.parent_block is not None:
            raise ValueError("Child block already has a parent - blocks cannot change parents")
        child_block._set_parent(self)

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

class BlockFactory:
    def __init__(self):
        self.created_blocks = {}  # Cache for reuse

    def create_block(self, label: str, chain_type: str, position: tuple, parent_block: 'Block') -> Block:
        """Create block on-demand with specified parent"""
        if label in self.created_blocks:
            return self.created_blocks[label]

        color_type = RED if chain_type == "selfish" else GREEN
        block = Block(label, position, color_type, parent_block=parent_block)  # Use provided parent
        self.created_blocks[label] = block
        return block

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
        self._create_all_states()

    def _create_all_states(self):
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

        for key, text in state_texts.items():
            state = MathTex(rf"\text{{{text}}}", color=WHITE)
            state.to_edge(UP)
            self.states[key] = state

    def get_state(self, state_name: str):
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

class AnimationFactory:
    def __init__(self, fade_in_time: float, fade_out_time: float):
        self.fade_in_time = fade_in_time
        self.fade_out_time = fade_out_time

    def fade_in(self, mobject):
        mobject.is_visible = True
        return mobject.animate(run_time=self.fade_in_time).set_opacity(1.0)

    def fade_out(self, mobject):
        mobject.is_visible = False
        return mobject.animate(run_time=self.fade_out_time).set_opacity(0)

    def fade_in_and_create(self, mobject):
        mobject.is_visible = True
        return Create(mobject, run_time=self.fade_in_time)

    def fade_out_and_remove(self, mobject):
        mobject.is_visible = False
        return FadeOut(mobject, run_time=self.fade_out_time)

# TODO change from pre-creating to only dynamic creation
# passing scene to class to bypass limitations of a single play call (last animation on a mobject will override previous)
class SelfishMiningSquares:
    def __init__(self, scene):
        self.scene = scene
        self.genesis_position = (-4, 0, 0)
        self.wait_time = 1.0
        self.fade_in_time = 1.0
        self.fade_out_time = 1.0
        self.selfish_miner_block_opacity = 0.5
        self.current_state = "init"
        self.selfish_blocks_created = 0
        self.honest_blocks_created = 0

        # Initialize managers
        self.state_manager = StateTextManager()
        self.animation_factory = AnimationFactory(self.fade_in_time, self.fade_out_time)

        # Create blockchains
        self.selfish_chain = Blockchain("selfish", PURE_RED, -1.2)
        self.honest_chain = Blockchain("honest", "#0000FF", 0)

        # Create genesis block
        self.genesis = Block("Gen", self.genesis_position, "#0000FF")

        # Pre-create blocks and lines
        self._setup_blocks()
        self._setup_lines()

        self.race_history_manager = RaceHistoryManager()

        # Start the first race
        self.race_history_manager.start_new_race()

    def advance_selfish_chain(self):
        """Create next selfish block and record in race history"""
        self.selfish_blocks_created += 1
        label = f"s{self.selfish_blocks_created}"

        # Determine parent block
        if self.selfish_blocks_created == 1:
            parent = self.genesis
        else:
            parent = self.selfish_chain.blocks[-1]

            # Create block using existing chain method
        position = (-2 + (self.selfish_blocks_created - 1) * 2, -1.2, 0)
        block = self.selfish_chain.add_block(label, position[0], parent_block=parent)

        # Add to scene dynamically
        self.scene.add(*block.get_mobjects())

        # Create connecting line
        if self.selfish_blocks_created == 1:
            line = self.selfish_chain.create_line_to_genesis(self.genesis, 0)
        else:
            line = self.selfish_chain.create_line_to_previous(self.selfish_blocks_created - 1)

        if line:
            self.scene.add(line)

            # Record in race history
        self.race_history_manager.record_block_creation("selfish")

        return block, line

    def advance_honest_chain(self):
        """Create next honest block and record in race history"""
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

        # Add to scene dynamically
        self.scene.add(*block.get_mobjects())

        # Create connecting line
        if self.honest_blocks_created == 1:
            line = self.honest_chain.create_line_to_genesis(self.genesis, 0)
        else:
            line = self.honest_chain.create_line_to_previous(self.honest_blocks_created - 1)

        if line:
            self.scene.add(line)

            # Record in race history
        self.race_history_manager.record_block_creation("honest")

        return block, line

    def resolve_race(self, winner: str):
        """Resolve the current race and start a new one"""
        self.race_history_manager.resolve_current_race(winner)

        # Reset counters for next race
        self.honest_blocks_created = 0
        self.selfish_blocks_created = 0

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

    def determine_race_winner_by_lead(self, selfish_lead: int):
        """Determine race winner based on selfish mining lead"""
        if selfish_lead >= 2:
            # Selfish miner has significant lead, they win by revealing
            return "selfish"
        elif selfish_lead == 1:
            # Close race, could go either way based on next block
            return None  # Race continues
        elif selfish_lead <= 0:
            # Honest miners are ahead or tied
            return "honest"

        return None

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

    def simulate_race_outcome(self, honest_blocks: int, selfish_blocks: int) -> str:
        """Simulate what the outcome would be for given block counts"""
        if selfish_blocks > honest_blocks:
            return "selfish"
        elif honest_blocks > selfish_blocks:
            return "honest"
        else:
            return "tie"  # Would need tiebreak resolution

    def _setup_blocks(self):
        # First selfish block parents to genesis
        self.selfish_chain.add_block("s1", -2, parent_block=self.genesis)

        # Subsequent selfish blocks parent to previous block
        for i in range(2, 5):
            parent = self.selfish_chain.blocks[-1]
            self.selfish_chain.add_block(f"s{i}", -2 + (i - 1) * 2, parent_block=parent)

        # Same pattern for honest chain
        self.honest_chain.add_block("h1", -2, parent_block=self.genesis)
        for i in range(2, 5):
            parent = self.honest_chain.blocks[-1]
            self.honest_chain.add_block(f"h{i}", -2 + (i - 1) * 2, parent_block=parent)

    def _setup_lines(self):
        # Create lines for selfish chain
        self.selfish_chain.create_line_to_genesis(self.genesis, 0)
        for i in range(1, 4):
            self.selfish_chain.create_line_to_previous(i)

            # Create lines for honest chain
        self.honest_chain.create_line_to_genesis(self.genesis, 0)
        for i in range(1, 4):
            self.honest_chain.create_line_to_previous(i)

    def intro_anim(self):
        self.current_state = "intro"

        intro_animation = Succession(
            AnimationGroup(
                self.animation_factory.fade_in_and_create(self.state_manager.get_state("selfish_mining")),
                *[self.animation_factory.fade_in(mob) for mob in self.genesis.get_mobjects()],
                *[self.animation_factory.fade_in(mob) for mob in self.selfish_chain.blocks[0].get_mobjects()],
                self.animation_factory.fade_in_and_create(self.selfish_chain.lines[0]),
                *[self.animation_factory.fade_in(mob) for mob in self.selfish_chain.blocks[1].get_mobjects()],
                self.animation_factory.fade_in_and_create(self.selfish_chain.lines[1]),
                *[self.animation_factory.fade_in(mob) for mob in self.selfish_chain.blocks[2].get_mobjects()],
                self.animation_factory.fade_in_and_create(self.selfish_chain.lines[2]),
                *[self.animation_factory.fade_in(mob) for mob in self.selfish_chain.blocks[3].get_mobjects()],
                self.animation_factory.fade_in_and_create(self.selfish_chain.lines[3]),
                *[self.animation_factory.fade_in(mob) for mob in self.honest_chain.blocks[0].get_mobjects()],
                self.animation_factory.fade_in_and_create(self.honest_chain.lines[0])
            ),
            Wait(self.wait_time),
            AnimationGroup(
                self.animation_factory.fade_out_and_remove(self.state_manager.get_state("selfish_mining")),
                *[self.animation_factory.fade_out(mob) for mob in self.selfish_chain.blocks[0].get_mobjects()],
                self.animation_factory.fade_out_and_remove(self.selfish_chain.lines[0]),
                *[self.animation_factory.fade_out(mob) for mob in self.selfish_chain.blocks[1].get_mobjects()],
                self.animation_factory.fade_out_and_remove(self.selfish_chain.lines[1]),
                *[self.animation_factory.fade_out(mob) for mob in self.selfish_chain.blocks[2].get_mobjects()],
                self.animation_factory.fade_out_and_remove(self.selfish_chain.lines[2]),
                *[self.animation_factory.fade_out(mob) for mob in self.selfish_chain.blocks[3].get_mobjects()],
                self.animation_factory.fade_out_and_remove(self.selfish_chain.lines[3]),
                *[self.animation_factory.fade_out(mob) for mob in self.honest_chain.blocks[0].get_mobjects()],
                self.animation_factory.fade_out_and_remove(self.honest_chain.lines[0])
            ),
            AnimationGroup(
                self.animation_factory.fade_in_and_create(self.state_manager.get_state("state0"))
            )
        )
        return intro_animation

    def state_zero(self):
        self.current_state = "zero"

        # All selfish miner transitions

    def zero_to_one(self):
        self.current_state = "one"
        return Succession(
            AnimationGroup(
                self.animation_factory.fade_out_and_remove(self.state_manager.get_state("state0"))
            ),
            Wait(self.wait_time),
            AnimationGroup(
                self.animation_factory.fade_in_and_create(self.state_manager.get_state("state1")),
                *[self.animation_factory.fade_in(mob) for mob in self.selfish_chain.blocks[0].get_mobjects()],
                self.animation_factory.fade_in_and_create(self.selfish_chain.lines[0])
            )
        )

    def one_to_two(self):
        self.current_state = "two"
        return Succession(
            AnimationGroup(
                self.animation_factory.fade_out_and_remove(self.state_manager.get_state("state1"))
            ),
            Wait(self.wait_time),
            AnimationGroup(
                self.animation_factory.fade_in_and_create(self.state_manager.get_state("state2")),
                *[self.animation_factory.fade_in(mob) for mob in self.selfish_chain.blocks[1].get_mobjects()],
                self.animation_factory.fade_in_and_create(self.selfish_chain.lines[1])
            )
        )

    def two_to_three(self):
        self.current_state = "three"
        return Succession(
            AnimationGroup(
                self.animation_factory.fade_out_and_remove(self.state_manager.get_state("state2"))
            ),
            Wait(self.wait_time),
            AnimationGroup(
                self.animation_factory.fade_in_and_create(self.state_manager.get_state("state3")),
                *[self.animation_factory.fade_in(mob) for mob in self.selfish_chain.blocks[2].get_mobjects()],
                self.animation_factory.fade_in_and_create(self.selfish_chain.lines[2])
            )
        )

    def three_to_four(self):
        self.current_state = "four"
        return Succession(
            AnimationGroup(
                self.animation_factory.fade_out_and_remove(self.state_manager.get_state("state3"))
            ),
            Wait(self.wait_time),
            AnimationGroup(
                self.animation_factory.fade_in_and_create(self.state_manager.get_state("state4")),
                *[self.animation_factory.fade_in(mob) for mob in self.selfish_chain.blocks[3].get_mobjects()],
                self.animation_factory.fade_in_and_create(self.selfish_chain.lines[3])
            )
        )

    def one_to_zero_prime(self):
        self.current_state = "zero_prime"
        return Succession(
            AnimationGroup(
                self.animation_factory.fade_out_and_remove(self.state_manager.get_state("state1"))
            ),
            Wait(self.wait_time),
            AnimationGroup(
                self.animation_factory.fade_in_and_create(self.state_manager.get_state("state0prime")),
                *[self.animation_factory.fade_in(mob) for mob in self.honest_chain.blocks[0].get_mobjects()],
                self.animation_factory.fade_in_and_create(self.honest_chain.lines[0])
            )
        )

    def zero_to_zero(self):
        """Complete implementation of the complex zero_to_zero transition"""
        self.current_state = "zero"

        self.scene.play(AnimationGroup(
            self.animation_factory.fade_out_and_remove(self.state_manager.get_state("state0"))
        ))

        self.scene.play(Wait(self.wait_time))

        self.scene.play(AnimationGroup(
            *[self.animation_factory.fade_in(mob) for mob in self.honest_chain.blocks[0].get_mobjects()],
            self.animation_factory.fade_in_and_create(self.honest_chain.lines[0])
        ))

        self.scene.play(Wait(self.wait_time))

        # Move genesis and honest block
        self.scene.play(AnimationGroup(
            *[mob.animate.move_to((-6, 0, 0)) for mob in self.genesis.get_mobjects()],
            *[mob.animate.move_to((-4, 0, 0)) for mob in self.honest_chain.blocks[0].get_mobjects()],
            self.honest_chain.lines[0].animate.shift(LEFT * 2)
        ))

        self.scene.play(Wait(self.wait_time))

        # CORRECTED: Fade out line, genesis AND honest block label, keep only honest block square
        self.scene.play(AnimationGroup(
            *[self.animation_factory.fade_out(mob) for mob in self.genesis.get_mobjects()],
            self.animation_factory.fade_out(self.honest_chain.blocks[0].label),  # Fade out label
            self.animation_factory.fade_out_and_remove(self.honest_chain.lines[0])
            # Note: only honest block square stays visible here
        ))

        self.scene.play(Wait(self.wait_time))

        # Reset genesis position while it's invisible
        for mob in self.genesis.get_mobjects():
            mob.move_to(self.genesis_position)

            # CORRECTED: Fade in genesis while fading out honest block square
        self.scene.play(AnimationGroup(
            *[self.animation_factory.fade_in(mob) for mob in self.genesis.get_mobjects()],
            self.animation_factory.fade_out(self.honest_chain.blocks[0].square)  # Only fade out square
        ))

        self.scene.bring_to_front(*self.genesis.get_mobjects())

        return

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

    def get_visible_blocks(self):
        """Return currently visible blocks for debugging"""
        visible_blocks = {
            "genesis": [mob for mob in self.genesis.get_mobjects() if hasattr(mob, 'is_visible') and mob.is_visible],
            "selfish": [],
            "honest": []
        }

        for i, block in enumerate(self.selfish_chain.blocks):
            if any(hasattr(mob, 'is_visible') and mob.is_visible for mob in block.get_mobjects()):
                visible_blocks["selfish"].append(f"s{i + 1}")

        for i, block in enumerate(self.honest_chain.blocks):
            if any(hasattr(mob, 'is_visible') and mob.is_visible for mob in block.get_mobjects()):
                visible_blocks["honest"].append(f"h{i + 1}")

        return visible_blocks


class SelfishMiningExample(Scene):
    def construct(self):
        # Create the SelfishMining instance
        sm = SelfishMiningSquares(self)

        self.wait(2)
        # Start with the intro animation
        self.play(sm.intro_anim())

        # The intro_anim already ends with state0 showing and genesis visible
        self.wait(1)

        # Transition from state 0 to state 1 (selfish miner finds a block)
        self.play(sm.zero_to_one())
        self.wait(1)

        # Transition from state 1 to state 2 (selfish miner finds another block)
        self.play(sm.one_to_two())
        self.wait(1)

        # Transition from state 2 to state 3 (selfish miner finds another block)
        self.play(sm.two_to_three())
        self.wait(1)

        # Transition from state 3 to state 4 (selfish miner finds another block)
        self.play(sm.three_to_four())
        self.wait(1)

        # Now show what happens when honest miner finds a block in state 1
        # First, let's go back to state 1 by fading out the higher state blocks
        self.play(Succession(
            AnimationGroup(
                sm.animation_factory.fade_out_and_remove(sm.state_manager.get_state("state4")),
                *[sm.animation_factory.fade_out(mob) for mob in sm.selfish_chain.blocks[1].get_mobjects()],
                sm.animation_factory.fade_out_and_remove(sm.selfish_chain.lines[1]),
                *[sm.animation_factory.fade_out(mob) for mob in sm.selfish_chain.blocks[2].get_mobjects()],
                sm.animation_factory.fade_out_and_remove(sm.selfish_chain.lines[2]),
                *[sm.animation_factory.fade_out(mob) for mob in sm.selfish_chain.blocks[3].get_mobjects()],
                sm.animation_factory.fade_out_and_remove(sm.selfish_chain.lines[3]),
            ),
            Wait(1),
            AnimationGroup(
                sm.animation_factory.fade_in_and_create(sm.state_manager.get_state("state1")),
            )
        ))
        self.wait(1)

        # Show transition from state 1 to state 0' (honest miner finds a block)
        self.play(sm.one_to_zero_prime())
        self.wait(1)

        # Finally, demonstrate the zero_to_zero transition
        # First fade out state 0' elements and show state 0
        self.play(Succession(
            AnimationGroup(
                sm.animation_factory.fade_out_and_remove(sm.state_manager.get_state("state0prime")),
                *[sm.animation_factory.fade_out(mob) for mob in sm.honest_chain.blocks[0].get_mobjects()],
                sm.animation_factory.fade_out_and_remove(sm.honest_chain.lines[0]),
                *[sm.animation_factory.fade_out(mob) for mob in sm.selfish_chain.blocks[0].get_mobjects()],
                sm.animation_factory.fade_out_and_remove(sm.selfish_chain.lines[0]),
            ),
            Wait(1),
            AnimationGroup(
                sm.animation_factory.fade_in_and_create(sm.state_manager.get_state("state0"))
            )
        ))
        self.wait(2)

        # Show the zero_to_zero transition (honest miner finds a block in state 0)
        sm.zero_to_zero()

        self.wait(2)