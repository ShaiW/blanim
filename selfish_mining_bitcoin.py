from manim.typing import Point3DLike
from common import *

# README: !!!Do NOT store lines in blocks!!! (slows animation creation down to a crawl) Creates circular references?

class Block:
    def __init__(self, label: str, position: Point3DLike, block_color: str, parent_block: 'Block' = None) -> None:
        # Visual components (existing Manim objects)
        self.square = Square(side_length=LayoutConfig.BLOCK_SIDE_LENGTH, color=block_color, fill_opacity=LayoutConfig.BLOCK_FILL_OPACITY)
        self.square.move_to(position)
        self.label = Text(label, font_size=LayoutConfig.LABEL_FONT_SIZE, color=LayoutConfig.LABEL_COLOR)
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

    def set_as_next_genesis(self):
        """Mark this block as the next genesis block"""
        self.next_genesis = True

    def is_next_genesis(self) -> bool:
        """Check if this block is marked as next genesis"""
        return self.next_genesis

    def is_genesis(self) -> bool:
        """Check if this block is a genesis block (has no parent)"""
        return self.parent_block is None

    def __repr__(self) -> str:
        """String representation for debugging"""
        parent_label = self.parent_block.label.text if self.parent_block else "None"
        children_labels = [child.label.text for child in self.children]
        return f"Block(label={self.label.text}, parent={parent_label}, children={children_labels}, next_genesis={self.next_genesis})"

class FollowLine(Line):
    def __init__(self, start_mobject, end_mobject):
        super().__init__(
            start=start_mobject.get_left(),
            end=end_mobject.get_right(),
            buff=LayoutConfig.LINE_BUFFER,
            color=LayoutConfig.LINE_COLOR,
            stroke_width=LayoutConfig.LINE_STROKE_WIDTH,
        )

        self.start_mobject = start_mobject
        self.end_mobject = end_mobject
        self._fixed_stroke_width = LayoutConfig.LINE_STROKE_WIDTH

    def _update_position_and_size(self, _mobject):

        new_start = self.start_mobject.get_left()
        new_end = self.end_mobject.get_right()
        self.set_stroke(width=self._fixed_stroke_width)
        self.set_points_by_ends(new_start, new_end, buff=self.buff)

    def create_update_animation(self, run_time=None):
        """Create an UpdateFromFunc animation for this line"""

        return UpdateFromFunc(
            self,
            update_function=self._update_position_and_size,
            run_time=run_time,
            suspend_mobject_updating=False  # Allow other updaters to work
        )

class ChainBranch:
    def __init__(self, chain_type: str):
        self.chain_type = chain_type
        self.blocks = []
        self.lines = []

    def add_block(self, label: str, position: Point3DLike, parent_block: Block):
        """Add a block to this chain. Parent block is required."""
        # Determine color based on chain type
        block_color = (
            LayoutConfig.SELFISH_CHAIN_COLOR
            if self.chain_type == "selfish"
            else LayoutConfig.HONEST_CHAIN_COLOR
        )

        block = Block(label, position, block_color, parent_block=parent_block)
        self.blocks.append(block)
        return block

    def create_line_to_target(self, source_block, target_block):
        """Create line connecting source block to target block"""
        line_params = {
            'buff': LayoutConfig.LINE_BUFFER,
            'color': LayoutConfig.LINE_COLOR,
            'stroke_width': LayoutConfig.LINE_STROKE_WIDTH
        }

        if target_block.is_genesis() or target_block.is_next_genesis():
            line = FollowLine(
                start_mobject=source_block,
                end_mobject=target_block)
        else:
            line = Line(
                start=source_block.get_left(),
                end=target_block.get_right(),
                **line_params
            )

        self.lines.append(line)  # Store in blockchain, not block
        return line

    def get_all_mobjects(self) -> list:
        """Get all mobjects including blocks and lines"""
        mobjects = []
        for block in self.blocks:
            mobjects.extend(block.get_mobjects())
        mobjects.extend(self.lines)
        return mobjects

# TODO implement an optional state text / narration, currently this is unused
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
            state = MathTex(rf"\text{{{text}}}", color=LayoutConfig.STATE_TEXT_COLOR)
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
    SHIFT_TO_NEW_GENESIS_TIME = 3.0 #TODO make this dynamic up to 4 blocks(Shorter block race needs less time, block race max +4 to be moved)
    INITIAL_SCENE_WAIT_TIME = 3.0 # pause at the beginning before any animations are added
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

#TODO doublecheck this AND make positioning dynamic so you can fit target number of blocks to screen based on expected block race length
class LayoutConfig:
    GENESIS_X = -4
    GENESIS_Y = 0
    BLOCK_HORIZONTAL_SPACING = 2
    HONEST_Y_OFFSET = 0
    SELFISH_Y_OFFSET = -1.2

    LINE_BUFFER = 0.1
    LINE_STROKE_WIDTH = 2

    BLOCK_SIDE_LENGTH = 0.8
    BLOCK_FILL_OPACITY = 0

    LABEL_FONT_SIZE = 24

    LABEL_COLOR = WHITE
    LINE_COLOR = WHITE
    SELFISH_CHAIN_COLOR = "#FF0000" # PURE_RED
    HONEST_CHAIN_COLOR = "#0000FF" # PURE_BLUE
    GENESIS_BLOCK_COLOR = "#0000FF" # PURE_BLUE
    STATE_TEXT_COLOR = WHITE

    SELFISH_BLOCK_OPACITY = 0.5

    @staticmethod
    def get_tie_chain_spacing() -> float:
        """Calculate tie chain spacing as half the distance between honest and selfish chains"""
        return abs(LayoutConfig.SELFISH_Y_OFFSET - LayoutConfig.HONEST_Y_OFFSET) / 2

    @staticmethod
    def get_tie_positions(genesis_y: float) -> tuple[float, float]:
        """Calculate both honest and selfish tie positions

        Returns:
            tuple[float, float]: (honest_y, selfish_y) positions for tie state
        """
        spacing = LayoutConfig.get_tie_chain_spacing()
        return genesis_y + spacing, genesis_y - spacing

class AnimationFactory:

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

        self.genesis_position = (LayoutConfig.GENESIS_X, LayoutConfig.GENESIS_Y, 0)

        self.selfish_miner_block_opacity = LayoutConfig.SELFISH_BLOCK_OPACITY #TODO ensure this is used for pre-reveal blocks

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
        self.selfish_chain = ChainBranch("selfish")
        self.honest_chain = ChainBranch("honest")

        # Create Genesis block
        self.genesis = Block("Gen", self.genesis_position, LayoutConfig.GENESIS_BLOCK_COLOR)

        # Start the first race
        self.race_history_manager.start_new_race()

        self.scene.wait(AnimationTimingConfig.INITIAL_SCENE_WAIT_TIME)

        # Add genesis block to scene
        self.scene.play(*[AnimationFactory.fade_in_and_create(mob) for mob in self.genesis.get_mobjects()])
        self.scene.wait(AnimationTimingConfig.WAIT_TIME)

    ####################
    # Advance Race / Block Creation
    # Public API
    ####################

    def advance_selfish_chain(self):
        """Create next selfish block with animated fade-in and record in race history"""
        self._store_previous_lead()

        self.selfish_blocks_created += 1
        label = f"s{self.selfish_blocks_created}"

        parent = self._get_parent_block("selfish")
        position = self._calculate_block_position(parent, "selfish")

        block = self.selfish_chain.add_block(label, position, parent_block=parent)
        line = self.selfish_chain.create_line_to_target(block, parent)

        self._animate_block_and_line(block, line)

        self.race_history_manager.record_block_creation("selfish")
        self._check_if_race_continues()

    def advance_honest_chain(self):
        """Create next honest block with animated fade-in and record in race history"""
        self._store_previous_lead()

        self.honest_blocks_created += 1
        label = f"h{self.honest_blocks_created}"

        parent = self._get_parent_block("honest")
        position = self._calculate_block_position(parent, "honest")

        block = self.honest_chain.add_block(label, position, parent_block=parent)
        line = self.honest_chain.create_line_to_target(block, parent)

        self._animate_block_and_line(block, line)

        self.race_history_manager.record_block_creation("honest")
        self._check_if_race_continues()

    ####################
    # Helper Methods
    # Private
    ####################

    def _store_previous_lead(self) -> None:
        """Store the previous selfish lead before making changes"""
        current_race = self.race_history_manager.current_race
        if current_race:
            honest_blocks = current_race.final_honest_blocks
            selfish_blocks = current_race.final_selfish_blocks
            self.previous_selfish_lead = selfish_blocks - honest_blocks

    def _get_parent_block(self, chain_type: str) -> Block:
        """Get parent block for next block in chain"""
        blocks_created = self.selfish_blocks_created if chain_type == "selfish" else self.honest_blocks_created
        chain = self.selfish_chain if chain_type == "selfish" else self.honest_chain

        if blocks_created == 1:
            return self.genesis
        else:
            return chain.blocks[-1]

    def _calculate_block_position(self, parent: Block, chain_type: str) -> Point3DLike:
        """Calculate position for new block based on parent and chain type"""
        parent_pos = parent.get_center()
        x_position = float(parent_pos[0]) + LayoutConfig.BLOCK_HORIZONTAL_SPACING

        if parent == self.genesis:
            y_position = LayoutConfig.SELFISH_Y_OFFSET if chain_type == "selfish" else LayoutConfig.HONEST_Y_OFFSET
        else:
            y_position = float(parent_pos[1])

        return x_position, y_position, 0

    def _animate_block_and_line(self, block: Block, line: Line | FollowLine) -> None:
        """Animate block and line creation"""
        animations = [self.animation_factory.fade_in_and_create(mob) for mob in block.get_mobjects()]
        if line:
            animations.append(self.animation_factory.fade_in_and_create(line))

        self.scene.play(*animations)
        self.scene.wait(AnimationTimingConfig.WAIT_TIME)

    @staticmethod
    def _collect_follow_line_animations(chains: list[ChainBranch], run_time: float) -> list:
        return [
            line.create_update_animation(run_time=run_time)
            for chain in chains
            for line in chain.lines
            if isinstance(line, FollowLine)
        ]

    def _get_winning_and_losing_chains(self, winner: str) -> tuple[ChainBranch, ChainBranch]:
        """Get winning and losing chains based on winner"""
        if winner == "honest":
            return self.honest_chain, self.selfish_chain
        else:
            return self.selfish_chain, self.honest_chain

    def _get_winning_block(self, winner: str) -> Block | None:
        """Get the winning block based on winner"""
        if winner == "honest":
            return self.honest_chain.blocks[-1] if self.honest_chain.blocks else None
        else:
            return self.selfish_chain.blocks[-1] if self.selfish_chain.blocks else None

    ####################
    # Race Resolution Detection
    # Private
    ####################

    def _check_if_race_continues(self) -> None:
        """Evaluate race conditions and trigger resolution if needed."""
        if not self.race_history_manager.current_race:
            return

        current_race = self.race_history_manager.current_race
        honest_blocks = current_race.final_honest_blocks
        selfish_blocks = current_race.final_selfish_blocks
        selfish_lead = selfish_blocks - honest_blocks

        # Define resolution strategies in priority order
        strategies = [
            lambda sl, hb: self._check_does_honest_win(sl),
            lambda sl, hb: self._check_if_tied(sl, hb),
            lambda sl, hb: self._check_if_honest_caught_up(sl),
        ]

        for strategy in strategies:
            if strategy(selfish_lead, honest_blocks):
                return  # Strategy handled the resolution

        # If no strategy triggered, race continues

    def _check_does_honest_win(self, selfish_lead: int) -> bool:
        if selfish_lead == -1:
            self._trigger_resolution("honest")
            return True
        return False

    def _check_if_tied(self, selfish_lead: int, honest_blocks: int) -> bool:
        if selfish_lead == 0 and honest_blocks > 0:
            self._reveal_selfish_chain_for_tie()
            winner = self._resolve_tiebreak()
            self._add_tiebreak_winning_block(winner)
            self.scene.wait(AnimationTimingConfig.WAIT_TIME)
            self._trigger_resolution(winner)
            return True
        return False

    def _check_if_honest_caught_up(self, selfish_lead: int) -> bool:
        if selfish_lead == 1 and self._had_selfish_lead_of_exactly_two():
            self._trigger_resolution("selfish")
            return True
        return False

    ####################
    # Race Resolution Execution
    # Private
    ####################

    def _trigger_resolution(self, winner: str):
        """Trigger resolution and update genesis reference"""

        # Use helper method instead of inline logic
        winning_block = self._get_winning_block(winner)

        # Run resolution animation
        self._animate_race_resolution(winner)

        # Update genesis reference to winning block
        if winning_block:
            winning_block.set_as_next_genesis()
            self._transition_to_next_race(winning_block)

            # Reset for next race
        self._finalize_race_and_start_next(winner)

    def _animate_race_resolution(self, winner: str):
        """Unified 4-step animation: move up, move left, fade out, fade in new label"""

        # Get winning and losing chains
        winning_chain, losing_chain = self._get_winning_and_losing_chains(winner)
        winning_block = winning_chain.blocks[-1] if winning_chain.blocks else None

        if not winning_block:
            return

        # Mark winning block as next genesis
        winning_block.set_as_next_genesis()

        # Step 1: Calculate vertical shift based on winning block's current position
        genesis_y = self.genesis_position[1]
        winning_block_current_y = winning_block.get_center()[1]
        vertical_shift = genesis_y - winning_block_current_y

        # Collect all mobjects from both chains
        all_mobjects = []
        all_mobjects.extend(winning_chain.get_all_mobjects())
        all_mobjects.extend(losing_chain.get_all_mobjects())

        # Collect FollowLine animations for vertical movement
        follow_line_animations = self._collect_follow_line_animations(
            [winning_chain, losing_chain],
            AnimationTimingConfig.VERTICAL_SHIFT_TIME
        )

        # Step 1: Move both chains vertically to genesis Y position
        self.scene.play(AnimationGroup(
            *[mob.animate.shift(UP * vertical_shift) for mob in all_mobjects],
            *follow_line_animations,
            run_time=AnimationTimingConfig.VERTICAL_SHIFT_TIME
        ))

        # Step 2: Calculate horizontal shift to move winning block to genesis X position
        winning_block_x = winning_block.get_center()[0]
        genesis_x = self.genesis_position[0]
        horizontal_shift = genesis_x - winning_block_x

        # Collect FollowLine animations for horizontal movement
        follow_line_animations = self._collect_follow_line_animations(
            [winning_chain, losing_chain],
            AnimationTimingConfig.SHIFT_TO_NEW_GENESIS_TIME
        )

        # Step 2: Move all mobjects horizontally to genesis X position
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
        fade_out_mobjects.append(winning_block.label)

        # All losing chain blocks
        for block in losing_chain.blocks:
            fade_out_mobjects.extend(block.get_mobjects())

        # All lines from both chains
        fade_out_mobjects.extend(winning_chain.lines)
        fade_out_mobjects.extend(losing_chain.lines)

        # Old genesis
        fade_out_mobjects.extend(self.genesis.get_mobjects())

        self.scene.play(AnimationGroup(
            *[self.animation_factory.fade_out_and_remove(mob) for mob in fade_out_mobjects]
        ))

        # Step 4: Create and fade in new "Gen" label for winning block
        new_label = Text("Gen", font_size=LayoutConfig.LABEL_FONT_SIZE, color=LayoutConfig.LABEL_COLOR)
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

            # Calculate target y-positions using config - now returns both positions as a tuple
        genesis_y = self.genesis_position[1]
        honest_target_y, selfish_target_y = LayoutConfig.get_tie_positions(genesis_y)

        # Calculate shifts based on actual current block positions
        honest_current_y = self.honest_chain.blocks[0].get_center()[1]
        selfish_current_y = self.selfish_chain.blocks[0].get_center()[1]

        honest_shift = honest_target_y - honest_current_y
        selfish_shift = selfish_target_y - selfish_current_y

        # Collect all mobjects from both chains
        honest_mobjects = self.honest_chain.get_all_mobjects()
        selfish_mobjects = self.selfish_chain.get_all_mobjects()

        # Collect FollowLine animations
        follow_line_animations = self._collect_follow_line_animations(
            [self.honest_chain, self.selfish_chain],
            AnimationTimingConfig.VERTICAL_SHIFT_TIME
        )

        # Animate vertical shift for both chains simultaneously
        self.scene.play(
            *[mob.animate.shift(UP * honest_shift) for mob in honest_mobjects],
            *[mob.animate.shift(UP * selfish_shift) for mob in selfish_mobjects],
            *follow_line_animations,
            run_time=AnimationTimingConfig.VERTICAL_SHIFT_TIME
        )

        # Wait to show the tie state
        self.scene.wait(AnimationTimingConfig.WAIT_TIME)

    @staticmethod
    def _resolve_tiebreak():
        """Simple 50/50 random tiebreak"""
        import random
        return "honest" if random.random() < 0.5 else "selfish"

    def _add_tiebreak_winning_block(self, winner: str):
        """Add the decisive block that breaks the tie"""
        if winner == "honest":
            self.advance_honest_chain()
        else:
            self.advance_selfish_chain()

    ####################
    # State Management
    # Private
    ####################

    def _had_selfish_lead_of_exactly_two(self) -> bool:
        """Check if previous selfish lead was 2"""
        return self.previous_selfish_lead == 2

    def _transition_to_next_race(self, winning_block: 'Block'):
        """Update genesis to point to the winning block and prepare for next race"""
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
        sm.advance_selfish_chain()
        sm.advance_selfish_chain()
        sm.advance_honest_chain()
        # too close, reveal
        self.wait(1)
