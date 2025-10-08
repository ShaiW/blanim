from manim.typing import Point3DLike
from common import *
import random

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

# TODO implement an optional state text / narration, currently this is broken
class StateTextManager:
    def __init__(self):
        self.states = {}
        self.transitions = {}

        self.state_text_position = DOWN
        self.caption_text_position = UP

    def get_state(self, state_name: str):
        """Get or create state text dynamically based on state name"""
        if state_name not in self.states:
            # Parse the state name to generate appropriate text
            if state_name == "0":
                text = "State 0"
            elif state_name == "0prime":
                text = "State 0'"
            elif state_name.isdigit():
                # For any numeric state (1, 2, 3, ..., infinity)
                text = f"State {state_name}"
            else:
                # Fallback for any other state names
                text = state_name

            state = MathTex(rf"\text{{{text}}}", color=LayoutConfig.STATE_TEXT_COLOR)
            state.to_edge(self.state_text_position)
            self.states[state_name] = state
        return self.states[state_name]

    def get_transition(self, from_state: str, to_state: str):
        """Get or create transition text (e.g., '1→0'', '2→0')"""
        transition_key = f"{from_state}→{to_state}"
        if transition_key not in self.transitions:
            transition = MathTex(
                rf"\text{{{from_state}}} \rightarrow \text{{{to_state}}}",
                color=LayoutConfig.STATE_TEXT_COLOR
            )
            transition.to_edge(self.state_text_position)
            self.transitions[transition_key] = transition
        return self.transitions[transition_key]

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
    STATE_FONT_SIZE = 24
    CAPTION_FONT_SIZE = 24

    LABEL_COLOR = WHITE
    LINE_COLOR = WHITE
    SELFISH_CHAIN_COLOR = "#FF0000" # PURE_RED
    HONEST_CHAIN_COLOR = "#0000FF" # PURE_BLUE
    GENESIS_BLOCK_COLOR = "#0000FF" # PURE_BLUE
    STATE_TEXT_COLOR = WHITE
    CAPTION_TEXT_COLOR = WHITE

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
    def fade_in_and_create_block_body(mobject) -> Animation:
        mobject.is_visible = True
        return Create(mobject, run_time=AnimationTimingConfig.FADE_IN_TIME)

    @staticmethod
    def fade_out_and_remove_block_body(mobject) -> Animation:
        mobject.is_visible = False
        return FadeOut(mobject, run_time=AnimationTimingConfig.FADE_OUT_TIME)

    @staticmethod
    def fade_in_and_create_block_label(mobject) -> Animation:
        mobject.is_visible = True
        return Create(mobject, run_time=AnimationTimingConfig.FADE_IN_TIME)

    @staticmethod
    def fade_out_and_remove_block_label(mobject) -> Animation:
        mobject.is_visible = False
        return FadeOut(mobject, run_time=AnimationTimingConfig.FADE_OUT_TIME)

    @staticmethod
    def fade_in_and_create_line(mobject) -> Animation:
        mobject.is_visible = True
        return Create(mobject, run_time=AnimationTimingConfig.FADE_IN_TIME)

    @staticmethod
    def fade_out_and_remove_line(mobject) -> Animation:
        mobject.is_visible = False
        return FadeOut(mobject, run_time=AnimationTimingConfig.FADE_OUT_TIME)

    @staticmethod
    def add_state_text(mobject) -> Animation:
        """Fade in state text"""
        return Create(mobject, run_time=AnimationTimingConfig.FADE_IN_TIME)

    @staticmethod
    def transform_state_text(old_mobject, new_mobject) -> Animation:
        """Transform one state text to another"""
        return ReplacementTransform(old_mobject, new_mobject, run_time=AnimationTimingConfig.FADE_IN_TIME)

    @staticmethod
    def remove_state_text(mobject) -> Animation:
        """Fade out state text"""
        return FadeOut(mobject, run_time=AnimationTimingConfig.FADE_OUT_TIME)

class SelfishMiningSquares:
    def __init__(self, scene, alpha=0.3, gamma=0.5, enable_narration=False):
        # Scene to bypass manim and use play in SelfishMiningSquares
        self.scene = scene

        # Adversary % and Connectedness
        self.alpha = alpha
        self.gamma = gamma

        # Narration control
        self.enable_narration = enable_narration

        self.current_race_number = 0
        self.race_history = []  # List of dicts with race results

        self.genesis_position = (LayoutConfig.GENESIS_X, LayoutConfig.GENESIS_Y, 0)

        self.selfish_miner_block_opacity = LayoutConfig.SELFISH_BLOCK_OPACITY

        self.selfish_blocks_created = 0
        self.honest_blocks_created = 0
        self.previous_selfish_lead = 0

        # Initialize managers
        self.state_manager = StateTextManager()
        self.animation_factory = AnimationFactory()

        self.current_state_text = None
        self.current_caption_text = None

        # Create blockchains
        self.selfish_chain = ChainBranch("selfish")
        self.honest_chain = ChainBranch("honest")

        # Create Genesis block
        self.genesis = Block("Gen", self.genesis_position, LayoutConfig.GENESIS_BLOCK_COLOR)

        self.scene.wait(AnimationTimingConfig.INITIAL_SCENE_WAIT_TIME)

        # Add genesis block to scene
        genesis_animations = [
            self.animation_factory.fade_in_and_create_block_body(self.genesis.square),
            self.animation_factory.fade_in_and_create_block_label(self.genesis.label)
        ]
        self.scene.play(*genesis_animations)
        self.scene.wait(AnimationTimingConfig.WAIT_TIME)

    ####################
    # Probabilistic Block Generation
    # Public API
    ####################

    def generate_next_block_probabilistic(self):
        """Generate next block based on alpha and gamma probabilities"""
        honest_blocks, selfish_blocks, selfish_lead, is_tied = self._get_race_state()

        if is_tied:
            decision = self._decide_next_block_in_tie()

            if decision == "selfish_on_selfish":
                self.advance_selfish_chain()
            elif decision == "honest_on_honest":
                self.advance_honest_chain()
            else:  # "honest_on_selfish"
                self._advance_honest_on_selfish_chain()
        else:
            decision = self._decide_next_block_normal()

            if decision == "selfish":
                self.advance_selfish_chain()
            else:
                self.advance_honest_chain()

    ####################
    # Probabilistic Decision Helpers
    # Private
    ####################

    def _get_race_state(self) -> tuple[int, int, int, bool]:
        """Get current race state from chain lengths"""
        honest_len = len(self.honest_chain.blocks)
        selfish_len = len(self.selfish_chain.blocks)
        selfish_lead = selfish_len - honest_len
        is_tied = (selfish_lead == 0 and honest_len > 0)
        return honest_len, selfish_len, selfish_lead, is_tied

    def _decide_next_block_in_tie(self) -> str:
        """Decide which type of block to create during tie state

        Returns:
            str: One of "selfish_on_selfish", "honest_on_honest", "honest_on_selfish"
        """
        rand = random.random()
        h = 1 - self.alpha

        if rand < self.alpha:
            return "selfish_on_selfish"
        elif rand < self.alpha + h * (1 - self.gamma):
            return "honest_on_honest"
        else:
            return "honest_on_selfish"

    def _decide_next_block_normal(self) -> str:
        """Decide which type of block to create during normal (non-tie) state

        Returns:
            str: Either "selfish" or "honest"
        """
        return "selfish" if random.random() < self.alpha else "honest"

    ####################
    # Advance Race / Block Creation
    # Public API
    ####################

    def advance_selfish_chain(self, caption: str = None) -> None:
        """Create next selfish block with animated fade-in"""
        self._store_previous_lead()

        self.selfish_blocks_created += 1
        label = f"S{self.selfish_blocks_created}"

        parent = self._get_parent_block("selfish")
        position = self._calculate_block_position(parent, "selfish")

        block = self.selfish_chain.add_block(label, position, parent_block=parent)
        line = self.selfish_chain.create_line_to_target(block, parent)

        self._animate_block_and_line(block, line, caption)

        self._check_if_race_continues()

    def advance_honest_chain(self, caption: str = None) -> None:
        """Create next honest block with animated fade-in"""
        self._store_previous_lead()

        self.honest_blocks_created += 1
        label = f"H{self.honest_blocks_created}"

        parent = self._get_parent_block("honest")
        position = self._calculate_block_position(parent, "honest")

        block = self.honest_chain.add_block(label, position, parent_block=parent)
        line = self.honest_chain.create_line_to_target(block, parent)

        self._animate_block_and_line(block, line, caption)

        self._check_if_race_continues()

    def _advance_honest_on_selfish_chain(self, caption: str = None) -> None:
        """Create honest block on selfish chain (honest miner builds on selfish parent)"""
        self._store_previous_lead()

        self.honest_blocks_created += 1
        label = f"H{self.honest_blocks_created}"

        parent = self.selfish_chain.blocks[-1] if self.selfish_chain.blocks else self.genesis
        position = self._calculate_block_position(parent, "selfish")

        block_color = LayoutConfig.HONEST_CHAIN_COLOR
        block = Block(label, position, block_color, parent_block=parent)
        self.selfish_chain.blocks.append(block)

        line = self.selfish_chain.create_line_to_target(block, parent)

        self._animate_block_and_line(block, line, caption)

        self._check_if_race_continues()

    ####################
    # Block Race Tracking
    # Private
    ####################

    def _get_current_chain_lengths(self) -> tuple[int, int, int]:
        """Get current chain lengths directly from the chain objects"""
        honest_len = len(self.honest_chain.blocks)
        selfish_len = len(self.selfish_chain.blocks)
        selfish_lead = selfish_len - honest_len
        return honest_len, selfish_len, selfish_lead

    def _record_race_result(self, winner: str):
        """Record race result in simple dict format"""
        honest_len, selfish_len, _ = self._get_current_chain_lengths()
        self.race_history.append({
            'race_number': self.current_race_number,
            'winner': winner,
            'honest_blocks': honest_len,
            'selfish_blocks': selfish_len
        })
        self.current_race_number += 1

    ####################
    # Helper Methods
    # Private
    ####################

    def _store_previous_lead(self) -> None:
        """Store the previous selfish lead before making changes"""
        _, _, self.previous_selfish_lead = self._get_current_chain_lengths()

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

    def _animate_block_and_line(self, block: Block, line: Line | FollowLine, caption: str = None) -> None:
        """Animate block and line creation"""
        animations = [
            self.animation_factory.fade_in_and_create_block_body(block.square),
            self.animation_factory.fade_in_and_create_block_label(block.label),
        ]

        # Add line animation if present
        if line:
            animations.append(self.animation_factory.fade_in_and_create_line(line))

        # Add caption animation if present
        if caption:
            caption_text = Text(
                caption,
                font_size=LayoutConfig.CAPTION_FONT_SIZE,
                color=LayoutConfig.CAPTION_TEXT_COLOR
            )
            caption_text.to_edge(self.state_manager.caption_text_position)

            if self.current_caption_text:
                animations.append(self.animation_factory.transform_state_text(self.current_caption_text, caption_text))
                self.current_caption_text = caption_text
            else:
                animations.append(self.animation_factory.add_state_text(caption_text))
                self.current_caption_text = caption_text

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

        honest_len, selfish_len, selfish_lead = self._get_current_chain_lengths()

        # Define resolution strategies in priority order
        strategies = [
            lambda sl, hb: self._check_does_honest_win(sl),
            lambda sl, hb: self._check_if_tied(sl, hb),
            lambda sl, hb: self._check_if_honest_caught_up(sl),
        ]

        for strategy in strategies:
            if strategy(selfish_lead, honest_len):
                return

    def _check_does_honest_win(self, selfish_lead: int) -> bool:
        if selfish_lead == -1:
            self._trigger_resolution("honest")
            return True
        return False

    def _check_if_tied(self, selfish_lead: int, honest_blocks: int) -> bool:
        if selfish_lead == 0 and honest_blocks > 0:
            self._reveal_selfish_chain_for_tie()
            self.scene.wait(AnimationTimingConfig.WAIT_TIME)

            decision = self._decide_next_block_in_tie()

            if decision == "selfish_on_selfish":
                self.advance_selfish_chain()
            elif decision == "honest_on_honest":
                self.advance_honest_chain()
            else:
                self._advance_honest_on_selfish_chain()

            self.scene.wait(AnimationTimingConfig.WAIT_TIME)

            _, _, new_lead = self._get_current_chain_lengths()

            if new_lead > 0:
                self._trigger_resolution("selfish")
            elif new_lead < 0:
                self._trigger_resolution("honest")

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

        # Step 3: Fade out everything except winning block square using AnimationFactory
        fade_out_animations = []

        # All winning chain blocks except winner - fade out both body and label
        for block in winning_chain.blocks[:-1]:
            fade_out_animations.append(self.animation_factory.fade_out_and_remove_block_body(block.square))
            fade_out_animations.append(self.animation_factory.fade_out_and_remove_block_label(block.label))

            # Fade out winning block's old label (keep square)
        fade_out_animations.append(self.animation_factory.fade_out_and_remove_block_label(winning_block.label))

        # All losing chain blocks - fade out both body and label
        for block in losing_chain.blocks:
            fade_out_animations.append(self.animation_factory.fade_out_and_remove_block_body(block.square))
            fade_out_animations.append(self.animation_factory.fade_out_and_remove_block_label(block.label))

            # All lines from both chains
        for line in winning_chain.lines:
            fade_out_animations.append(self.animation_factory.fade_out_and_remove_line(line))
        for line in losing_chain.lines:
            fade_out_animations.append(self.animation_factory.fade_out_and_remove_line(line))

            # Old genesis - fade out both body and label
        fade_out_animations.append(self.animation_factory.fade_out_and_remove_block_body(self.genesis.square))
        fade_out_animations.append(self.animation_factory.fade_out_and_remove_block_label(self.genesis.label))

        self.scene.play(AnimationGroup(*fade_out_animations))

        # Step 4: Create and fade in new "Gen" label for winning block
        new_label = Text("Gen", font_size=LayoutConfig.LABEL_FONT_SIZE, color=LayoutConfig.LABEL_COLOR)
        new_label.move_to(winning_block.square.get_center())

        self.scene.play(self.animation_factory.fade_in_and_create_block_label(new_label))

        # Update the winning block's label reference
        winning_block.label = new_label

        # Add wait after genesis label is created
        self.scene.wait(AnimationTimingConfig.WAIT_TIME)

    def _finalize_race_and_start_next(self, winner: str):
        """Record result and reset for next race"""
        self._record_race_result(winner)

        # Reset counters
        self.honest_blocks_created = 0
        self.selfish_blocks_created = 0
        self.previous_selfish_lead = 0

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

    ####################
    # State Management
    # Private
    ####################
    # unused atm
    def _calculate_current_state(self) -> str:
        """Calculate current state name based on selfish lead

        Returns:
            State name as string: "0", "0prime", "1", "2", etc.
        """
        _, _, selfish_lead = self._get_current_chain_lengths()

        if selfish_lead == 0:
            # Check if we're in a tie situation (both chains have blocks)
            honest_len, selfish_len, _ = self._get_current_chain_lengths()
            if honest_len > 0 and selfish_len > 0:
                return "0prime"  # Tied state
            return "0"  # Initial state
        elif selfish_lead > 0:
            # Return the lead as a string - supports infinite states
            return str(selfish_lead)
        else:
            # Honest is ahead, back to state 0
            return "0"
    # unused atm
    def _show_state(self, state_name: str):
        """Display state text at top of scene"""
        if not self.enable_narration:
            return  # Skip state text if narration is disabled

        new_state = self.state_manager.get_state(state_name)

        if self.current_state_text:
            self.scene.play(
                self.animation_factory.transform_state_text(self.current_state_text, new_state)
            )
        else:
            self.scene.play(
                self.animation_factory.add_state_text(new_state)
            )
            self.current_state_text = new_state
    # unused atm
    def _hide_current_state(self):
        """Remove current state text"""
        if not self.enable_narration:
            return  # Skip state text if narration is disabled

        if self.current_state_text:
            self.scene.play(
                self.animation_factory.remove_state_text(self.current_state_text)
            )
            self.current_state_text = None

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

class SelfishMiningAutomaticExample(Scene):
    def construct(self):
        # Initialize the mining system
        sm = SelfishMiningSquares(self, alpha=0.40, gamma=0.15)
        for _ in range(20):  # Generate 30 blocks
            sm.generate_next_block_probabilistic()

class SelfishMiningManualExample(Scene):
    def construct(self):
        # Initialize the mining system
        sm = SelfishMiningSquares(self, 0.30, 0.1)

        # TODO previous version limited to +4 from Gen, can change but any time selfish is +4 from gen and +1 added,
        #       need to shift chains left 1 position after filling the screen
        sm.advance_selfish_chain("Selfish Mines a Block")
        sm.advance_selfish_chain("Selfish Mines another Block")
        sm.advance_selfish_chain("Selfish Mines yet another Block")
        sm.advance_honest_chain("Honest Mines a Block")
        sm.advance_selfish_chain("Selfish Mines a Block again")
        sm.advance_honest_chain("Honest Mines another Block")
        sm.advance_honest_chain("Honest Mines yet another Block")
        # TODO after caption added, never removed
        # TODO add a way to caption without advancing chain
        # TODO add a way to manually tiebreak
        # first block race over
        sm.advance_honest_chain()
        # next race over
        sm.advance_honest_chain()
        # next race over
        sm.advance_selfish_chain()
        sm.advance_honest_chain()
        # tiebreak handled automatically
        sm.advance_selfish_chain()
        sm.advance_selfish_chain()
        sm.advance_honest_chain()
        # too close, reveal
        self.wait(1)

class SelfishMiningManualTiesExample(Scene):
    def construct(self):
        # Ties handled automatically
        sm = SelfishMiningSquares(self, 0.33, 0.5) # gives 1/3 chance to each outcome
        sm.advance_selfish_chain()
        sm.advance_honest_chain()

        sm.advance_selfish_chain()
        sm.advance_honest_chain()

        sm.advance_selfish_chain()
        sm.advance_honest_chain()

        sm.advance_selfish_chain()
        sm.advance_honest_chain()

        sm.advance_selfish_chain()
        sm.advance_honest_chain()

        sm.advance_selfish_chain()
        sm.advance_honest_chain()

        sm.advance_selfish_chain()
        sm.advance_honest_chain()

        sm.advance_selfish_chain()
        sm.advance_honest_chain()

        sm.advance_selfish_chain()
        sm.advance_honest_chain()
