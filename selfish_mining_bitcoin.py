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

    def __repr__(self) -> str:
        """String representation for debugging"""
        parent_label = self.parent_block.label.text if self.parent_block else "None"
        children_labels = [child.label.text for child in self.children]
        return f"Block(label={self.label.text}, parent={parent_label}, children={children_labels}, next_genesis={self.next_genesis})"

class FollowLine(Line):
    def __init__(self, start_mobject, end_mobject):
        # Initialize with proper start/end points
        super().__init__(
            start=start_mobject.get_left(),
            end=end_mobject.get_right(),
            buff=0.1,
            color=WHITE,
            stroke_width=2,
        )

        self.start_mobject = start_mobject
        self.end_mobject = end_mobject
        self._fixed_stroke_width = 2

    def _update_position_and_size(self, mobject):
        # Same update logic as before
        new_start = self.start_mobject.get_left()
        new_end = self.end_mobject.get_right()
        self.set_stroke(width=self._fixed_stroke_width)
        self.set_points_by_ends(new_start, new_end, buff=self.buff)

    def create_update_animation(self, run_time=None):
        """Create an UpdateFromFunc animation for this line"""
#        from manim.animation.updaters.update import UpdateFromFunc
        return UpdateFromFunc(
            self,
            update_function=self._update_position_and_size,
            run_time=run_time,
            suspend_mobject_updating=False  # Allow other updaters to work
        )

class Blockchain:
    def __init__(self, chain_type: str, color: str, y_offset: float = 0):
        self.chain_type = chain_type
        self.color = color
        self.y_offset = y_offset
        self.blocks = []
        self.lines = []

    def add_block(self, label: str, position: tuple, parent_block: 'Block' = None, is_genesis: bool = False):
        # Strict validation: either genesis or must have parent
        if is_genesis and parent_block is not None:
            raise ValueError("Genesis block cannot have a parent")

        if not is_genesis and parent_block is None:
            raise ValueError("Non-genesis block must have a parent - no default fallback allowed")

        block = Block(label, position, self.color, parent_block=parent_block)
        self.blocks.append(block)
        return block

    def create_line_to_target(self, source_block, target_block):
        """Create line connecting source block to target block - automatically chooses line type"""
        # Automatically detect if target is a genesis block
        if target_block.is_genesis() or target_block.is_next_genesis():
            line = FollowLine(start_mobject=source_block, end_mobject=target_block)
        else:
            line = Line(
                start=source_block.get_left(),
                end=target_block.get_right(),
                buff=0.1, color=WHITE, stroke_width=2
            )

        self.lines.append(line)
        return line

    def get_all_mobjects(self):
        all_mobjects = []
        for block in self.blocks:
            all_mobjects.extend(block.get_mobjects())
        for line in self.lines:
            all_mobjects.append(line)
        return all_mobjects

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

class RaceState:
    def __init__(self):
        self.final_honest_blocks = 0
        self.final_selfish_blocks = 0
        self.winner = None  # "honest" or "selfish"
        self.is_resolved = False

    def record_block(self, miner_type: str):
        """Record a block being created in the current race"""
        if miner_type == "honest":
            self.final_honest_blocks += 1
        elif miner_type == "selfish":
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
            self.current_race.record_block(miner_type)

    def resolve_current_race(self, winner: str):
        """Resolve the current race"""
        if self.current_race:
            self.current_race.resolve_race(winner)
            self.current_race = None

    def get_all_race_history(self) -> list[dict]:
        """Get complete history of all races"""
        return [race.get_race_summary() for race in self.race_history]

class AnimationTimingConfig:
    """Centralized animation timing configuration"""

    # Scene timing
    WAIT_TIME = 1.0

    # Animation durations
    FADE_IN_TIME = 1.0
    FADE_OUT_TIME = 1.0
    BLOCK_CREATION_TIME = 1.0
    CHAIN_RESOLUTION_TIME = 2.0
    SHIFT_TO_NEW_GENESIS_TIME = 3.0 #TODO make this dynamic up to 4 blocks(Shorter blockrace needs less time, blockrace max +4 to be moved)
    INITIAL_SCENE_WAIT_TIME = 3.0
    VERTICAL_SHIFT_TIME = 2.0
    CHAIN_REVEAL_ANIMATION_TIME = 2.0
    FOLLOW_LINE_UPDATE_TIME = 2.0

    @classmethod
    def set_speed_multiplier(cls, multiplier: float):
        """Scale all timings by a multiplier for faster/slower animations"""
        cls.WAIT_TIME *= multiplier
        cls.FADE_IN_TIME *= multiplier
        cls.FADE_OUT_TIME *= multiplier
        cls.BLOCK_CREATION_TIME *= multiplier
        cls.CHAIN_RESOLUTION_TIME *= multiplier
        cls.SHIFT_TO_NEW_GENESIS_TIME *= multiplier
        cls.INITIAL_SCENE_WAIT_TIME *= multiplier
        cls.VERTICAL_SHIFT_TIME *= multiplier
        cls.CHAIN_REVEAL_ANIMATION_TIME *= multiplier
        cls.FOLLOW_LINE_UPDATE_TIME *= multiplier

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
        return Create(mobject, run_time=AnimationTimingConfig.FADE_IN_TIME)

    @staticmethod
    def fade_out_and_remove(mobject):
        mobject.is_visible = False
        return FadeOut(mobject, run_time=AnimationTimingConfig.FADE_OUT_TIME)

# passing scene to class to bypass limitations of a single play call (last animation on a mobject will override previous)
class SelfishMiningSquares:
    def __init__(self, scene):
        self.scene = scene

        self.honest_y_offset = 0
        self.selfish_y_offset = -1.2
        self.genesis_position = (-4, self.honest_y_offset, 0) # (-4, 0, 0) Selected to center chain visually on screen AND keep focus on individual races/states (x block spacing is 2)

        self.selfish_miner_block_opacity = 0.5 #TODO ensure this is used for pre-reveal blocks

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
        self.race_history_manager.start_new_race()

        self.scene.wait(3)

        # Add genesis block to scene
        self.scene.play(*[AnimationFactory.fade_in_and_create(mob) for mob in self.genesis.get_mobjects()])
        self.scene.wait(1)

    ####################
    # Advance Race / Block Creation
    # Public API
    ####################

    def advance_selfish_chain(self):
        """Create next selfish block with animated fade-in and record in race history"""
        # Store previous lead before making changes
        current_race = self.race_history_manager.current_race
        if current_race:
            honest_blocks = current_race.final_honest_blocks
            selfish_blocks = current_race.final_selfish_blocks
            self.previous_selfish_lead = selfish_blocks - honest_blocks

        self.selfish_blocks_created += 1
        label = f"s{self.selfish_blocks_created}"

        # Determine parent block
        if self.selfish_blocks_created == 1:
            parent = self.genesis
        else:
            parent = self.selfish_chain.blocks[-1]

            # Calculate position
        parent_pos = parent.get_center()
        x_position = parent_pos[0] + LayoutConfig.BLOCK_HORIZONTAL_SPACING

        # Use chain offset if parent is genesis, otherwise use parent's y-position
        if parent == self.genesis:
            y_position = LayoutConfig.SELFISH_Y_OFFSET
        else:
            y_position = parent_pos[1]

        position = (x_position, y_position, 0)
        block = self.selfish_chain.add_block(label, position, parent_block=parent)

        # Create connecting line
        line = self.selfish_chain.create_line_to_target(block, parent)

        # Prepare animations
        animations = [self.animation_factory.fade_in_and_create(mob) for mob in block.get_mobjects()]
        if line:
            animations.append(self.animation_factory.fade_in_and_create(line))

        self.scene.play(*animations)
        self.scene.wait(AnimationTimingConfig.WAIT_TIME)

        # Record in race history
        self.race_history_manager.record_block_creation("selfish")

        # Check for automatic resolution after state change
        self._check_and_resolve_race()

        return block, line

    def advance_honest_chain(self):
        """Create next honest block with animated fade-in and record in race history"""
        # Store previous lead before making changes
        current_race = self.race_history_manager.current_race
        if current_race:
            honest_blocks = current_race.final_honest_blocks
            selfish_blocks = current_race.final_selfish_blocks
            self.previous_selfish_lead = selfish_blocks - honest_blocks

        self.honest_blocks_created += 1
        label = f"h{self.honest_blocks_created}"

        # Determine parent block
        if self.honest_blocks_created == 1:
            parent = self.genesis
        else:
            parent = self.honest_chain.blocks[-1]

            # Calculate position
        parent_pos = parent.get_center()
        x_position = parent_pos[0] + LayoutConfig.BLOCK_HORIZONTAL_SPACING

        # Use chain offset if parent is genesis, otherwise use parent's y-position
        if parent == self.genesis:
            y_position = LayoutConfig.HONEST_Y_OFFSET
        else:
            y_position = parent_pos[1]

        position = (x_position, y_position, 0)
        block = self.honest_chain.add_block(label, position, parent_block=parent)

        # Create connecting line
        line = self.honest_chain.create_line_to_target(block, parent)

        # Prepare animations
        animations = [self.animation_factory.fade_in_and_create(mob) for mob in block.get_mobjects()]
        if line:
            animations.append(self.animation_factory.fade_in_and_create(line))

        self.scene.play(*animations)
        self.scene.wait(AnimationTimingConfig.WAIT_TIME)

        # Record in race history
        self.race_history_manager.record_block_creation("honest")

        # Check for automatic resolution after state change
        self._check_and_resolve_race()

        return block, line

    ####################
    # Race Resolution Detection
    # Private
    ####################

    def _check_and_resolve_race(self) -> None:
        """Evaluate race conditions and trigger resolution if needed."""
        if not self.race_history_manager.current_race:
            return

        current_race = self.race_history_manager.current_race
        honest_blocks = current_race.final_honest_blocks
        selfish_blocks = current_race.final_selfish_blocks
        selfish_lead = selfish_blocks - honest_blocks

        # Define resolution strategies in priority order
        strategies = [
            self._check_honest_wins,
            self._check_tie_situation,
            self._check_selfish_strategy_trigger,
        ]

        for strategy in strategies:
            if strategy(selfish_lead, honest_blocks):
                return  # Strategy handled the resolution

        # If no strategy triggered, race continues

    def _check_honest_wins(self, selfish_lead: int, honest_blocks: int) -> bool:
        if selfish_lead == -1:
            self._trigger_resolution("honest")
            return True
        return False

    def _check_tie_situation(self, selfish_lead: int, honest_blocks: int) -> bool:
        if selfish_lead == 0 and honest_blocks > 0:
            self._reveal_selfish_chain_for_tie()
            winner = self._resolve_tiebreak()
            winning_block = self._add_tiebreak_winning_block(winner)
            self.scene.wait(AnimationTimingConfig.WAIT_TIME)
            self._trigger_resolution(winner)
            return True
        return False

    def _check_selfish_strategy_trigger(self, selfish_lead: int, honest_blocks: int) -> bool:
        if selfish_lead == 1 and self._was_previous_lead_2():
            self._trigger_resolution("selfish")
            return True
        return False

    ####################
    # Race Resolution Execution
    # Private
    ####################

    def _trigger_resolution(self, winner: str):
        """Trigger resolution and update genesis reference"""

        # Get winning block before resolution animations
        if winner == "honest":
            winning_block = self.honest_chain.blocks[-1] if self.honest_chain.blocks else None
        else:
            winning_block = self.selfish_chain.blocks[-1] if self.selfish_chain.blocks else None

        # Run resolution animation
        self._animate_race_resolution(winner)

        # Update genesis reference to winning block
        if winning_block:
            winning_block.set_as_next_genesis()
            self._transition_to_next_race(winning_block)

            # Reset for next race
        self._finalize_race_and_start_next(winner)

    def _animate_race_resolution(self, winner: str):
        """Unified 4-step animation with proper updater management: move up, move left, fade out, fade in new label"""
        print(f"_animate_race_resolution called with winner: {winner}")
        print(f"selfish_chain.blocks: {len(self.selfish_chain.blocks)}")
        print(f"honest_chain.blocks: {len(self.honest_chain.blocks)}")

        # Determine winning chain and block
        if winner == "honest":
            winning_chain = self.honest_chain
            losing_chain = self.selfish_chain
        else:
            winning_chain = self.selfish_chain
            losing_chain = self.honest_chain

        winning_block = winning_chain.blocks[-1] if winning_chain.blocks else None
        if not winning_block:
            return

            # Step 1: Calculate vertical shift based on winning block's ACTUAL current position
        genesis_y = self.genesis_position[1]
        winning_block_current_y = winning_block.get_center()[1]  # Get actual y-position
        vertical_shift = genesis_y - winning_block_current_y  # Calculate shift from current position

        # Collect all mobjects for movement (blocks and lines)
        all_mobjects = []
        for block in winning_chain.blocks:
            all_mobjects.extend(block.get_mobjects())
        for block in losing_chain.blocks:
            all_mobjects.extend(block.get_mobjects())
        all_mobjects.extend(winning_chain.lines)
        all_mobjects.extend(losing_chain.lines)

        # Collect UpdateFromFunc animations for FollowLines during vertical movement
        follow_line_animations = []
        for line in winning_chain.lines + losing_chain.lines:
            if isinstance(line, FollowLine):
                follow_line_animations.append(
                    line.create_update_animation(run_time=AnimationTimingConfig.FOLLOW_LINE_UPDATE_TIME))

                # Step 1: Move both chains up by the calculated amount
        self.scene.play(AnimationGroup(
            *[mob.animate.shift(UP * vertical_shift) for mob in all_mobjects],
            *follow_line_animations,
            run_time=AnimationTimingConfig.VERTICAL_SHIFT_TIME
        ))

        # Step 2: Calculate horizontal shift to move winning block to genesis x position
        winning_block_x = winning_block.get_center()[0]
        genesis_x = self.genesis_position[0]
        horizontal_shift = genesis_x - winning_block_x

        # Collect UpdateFromFunc animations for FollowLines during horizontal movement
        follow_line_animations = []
        for line in winning_chain.lines + losing_chain.lines:
            if isinstance(line, FollowLine):
                follow_line_animations.append(
                    line.create_update_animation(run_time=AnimationTimingConfig.FOLLOW_LINE_UPDATE_TIME))

                # Step 2: Move all mobjects left by the required amount
        # Note: Genesis block moves horizontally but never vertically
        self.scene.play(AnimationGroup(
            *[mob.animate.shift(LEFT * abs(horizontal_shift)) for mob in all_mobjects],
            *[mob.animate.shift(LEFT * abs(horizontal_shift)) for mob in self.genesis.get_mobjects()],
            *follow_line_animations,
            run_time=AnimationTimingConfig.SHIFT_TO_NEW_GENESIS_TIME
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

        # Add wait after genesis label is created
        self.scene.wait(AnimationTimingConfig.WAIT_TIME)

    def _finalize_race_and_start_next(self, winner: str):
        """Resolve the current race and start a new one"""
        self.race_history_manager.resolve_current_race(winner)

        # Reset counters for next race
        self.honest_blocks_created = 0
        self.selfish_blocks_created = 0
        self.previous_selfish_lead = 0

        # Start new race for next sequence
        self.race_history_manager.start_new_race()

    ####################
    # Tie Handling
    # Private
    ####################

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

        # Collect UpdateFromFunc animations for FollowLines
        follow_line_animations = []
        for line in self.honest_chain.lines + self.selfish_chain.lines:
            if isinstance(line, FollowLine):
                follow_line_animations.append(line.create_update_animation(run_time=AnimationTimingConfig.FOLLOW_LINE_UPDATE_TIME))

        # Animate both chains moving to their new positions
        # TODO for tie change timing to half normal vertical shift
        self.scene.play(AnimationGroup(
            *[mob.animate.shift(UP * honest_shift) for mob in honest_mobjects],
            *[mob.animate.shift(UP * selfish_shift) for mob in selfish_mobjects],
            *follow_line_animations,
            run_time=AnimationTimingConfig.VERTICAL_SHIFT_TIME
        ))

        # Wait to show the tie state
        self.scene.wait(AnimationTimingConfig.WAIT_TIME)

    def _resolve_tiebreak(self):
        """Simple 50/50 random tiebreak"""
        import random
        return "honest" if random.random() < 0.5 else "selfish"

    def _add_tiebreak_winning_block(self, winner: str):
        """Add the decisive block that breaks the tie"""
        if winner == "honest":
            block, line = self.advance_honest_chain()
        else:
            block, line = self.advance_selfish_chain()

        return block

    ####################
    # State Management
    # Private
    ####################

    def _was_previous_lead_2(self):
        """Check if previous selfish lead was 2"""
        return self.previous_selfish_lead == 2

    def _transition_to_next_race(self, winning_block: 'Block'):
        """Update genesis to point to the winning block and prepare for next race"""
        # Update our genesis reference to point to winning block
        self.genesis = winning_block

        # Clear the blockchain lists for next race
        self.selfish_chain.blocks.clear()
        self.selfish_chain.lines.clear()
        self.honest_chain.blocks.clear()
        self.honest_chain.lines.clear()

class SelfishMiningExample(Scene):
    def construct(self):
        # Initialize the mining system
        sm = SelfishMiningSquares(self)

        # TODO previous version limited to +4 from Gen, can change but any time selfish is +4 from gen and +1 added,
        #       need to shift chains left 1 position after filling the screen
        # TODO need to set up mining simulation based on a (either as initialize or with its own func)
        sm.advance_selfish_chain()
        sm.advance_selfish_chain()
        sm.advance_selfish_chain()
        sm.advance_honest_chain()
        sm.advance_selfish_chain()
        sm.advance_honest_chain()
        sm.advance_honest_chain()
        # first block race over
        sm.advance_honest_chain()
        # next race over
        sm.advance_honest_chain()
        # next race over
        sm.advance_selfish_chain()
        sm.advance_honest_chain()
        # tiebreak over

