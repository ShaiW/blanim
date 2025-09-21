from common import *

class Block:
    def __init__(self, label: str, position: tuple, color: str, side_length: float = 0.8):
        self.square = Square(side_length=side_length, color=color, fill_opacity=0)
        self.square.move_to(position)
        self.label = Text(label, font_size=24, color=WHITE)
        self.label.move_to(self.square.get_center())

    def get_mobjects(self):
        return [self.square, self.label]

    def move_to(self, position):
        self.square.move_to(position)
        self.label.move_to(self.square.get_center())

    def get_center(self):
        return self.square.get_center()

    def get_left(self):
        return self.square.get_left()

    def get_right(self):
        return self.square.get_right()


class Blockchain:
    def __init__(self, chain_type: str, color: str, y_offset: float = 0):
        self.chain_type = chain_type
        self.color = color
        self.y_offset = y_offset
        self.blocks = []
        self.lines = []

    def add_block(self, label: str, x_position: float):
        position = (x_position, self.y_offset, 0)
        block = Block(label, position, self.color)
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


class SelfishMiningSquares:
    def __init__(self, scene):
        self.scene = scene
        self.genesis_position = (-4, 0, 0)
        self.wait_time = 1.0
        self.fade_in_time = 1.0
        self.fade_out_time = 1.0
        self.selfish_miner_block_opacity = 0.5
        self.current_state = "init"

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

    def _setup_blocks(self):
        # Create selfish blocks
        for i in range(1, 5):
            self.selfish_chain.add_block(f"s{i}", -2 + (i - 1) * 2)

            # Create honest blocks
        for i in range(1, 5):
            self.honest_chain.add_block(f"h{i}", -2 + (i - 1) * 2)

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

        # Now demonstrate some transitions

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