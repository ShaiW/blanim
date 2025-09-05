from blanim import *
from random import randint
from numpy.random import poisson as poi

class BlockDAGDemo(Scene):
    ##terrible demo
    def construct(self):
        BD = BlockDAG()
        self.play(BD.add("Gen", [-3,0], label="G"))
        self.play(BD.add("X", [-1,0], label="G", parents=["Gen"]))
        self.play(
                BD.add("Y",[0,3],label=":)", parents=["Gen", Parent("X", color=WHITE)]),
                BD.add("Z",[2,2],parents=["Y"])
            )
        self.play(BD.shift("Y",[1,-6],run_time=2),BD.shift("Z",[1,0],run_time=2))
        self.wait(1)

# Broken since refactoring
class LayerDAGDemo(Scene):
    def construct(self):
        LD = LayerDAG()
        self.play(LD.init_animation)
        self.play(*[LD.add("U%d"%i,["Gen"],"X",label=str(i)) for i in range(3)])
        t = LD.get_tips()
        self.play(*[LD.add("W%d"%i,t) for i in range(5)])
        safe_play(self, LD.adjust_layers())
        self.play(LD.change_color(t, GREEN))
        self.play(LD.change_color(LD.get_tips(), RED))
        self.wait(1)

class RandomDAG(Scene):
    AVG_AC = 4
    BLOCKS = 20
    DAG_WIDTH = 5
    MAX_BLOCKS_PER_BATCH = 2 #doesn't affect resulting DAG, just the animation

    def construct(self):
        blocks = self.BLOCKS

        LD = LayerDAG(width=self.DAG_WIDTH, block_w = BLOCK_W*0.75, block_h = BLOCK_H*0.75)

        self.play(LD.init_animation)

        safe_play(self, LD.adjust_layers())

        i = 0
        while blocks > 0:
            i += 1

            batch_size = randint(1,min(self.MAX_BLOCKS_PER_BATCH,blocks))

            blocks -= batch_size

            self.play(
                *[LD.add("V%d%d"%(i,j),LD.get_tips(missed_blocks=poi(lam=self.AVG_AC)),random_sp=True) for j in range(batch_size)]
                      )
            safe_play(self, LD.adjust_layers())

        self.wait(3)

class GHOSTDAGScene(Scene):
    AVG_AC = 4
    BLOCKS = 20
    DAG_WIDTH = 4
    MAX_BLOCKS_PER_BATCH = 1
    GD_K = 2

    def construct(self):
        blocks = self.BLOCKS

        GD = GHOSTDAG(self.GD_K, width=self.DAG_WIDTH, block_w=BLOCK_W * 0.75, block_h=BLOCK_H * 0.75)

        self.play(GD.init_animation)
        safe_play(self, GD.adjust_layers())

        i = 0
        while blocks > 0:
            i += 1
            batch_size = randint(1, min(self.MAX_BLOCKS_PER_BATCH, blocks))
            blocks -= batch_size

            # Use GHOSTDAG's blue_score-based parent selection
            # GHOSTDAG automagically names each block, based on position in the DAG,
            # L3_1 will be 3rd layer, first block,
            # L6_2 will be 6th layer, second block.
            # Gen will be Genesis.
            # TODO add return limits for requesting out of bound names so referencing a block that does not exist, returns a nearby block
            self.play(
                *[GD.add(GD.get_tips(missed_blocks=poi(lam=self.AVG_AC)))
                  for each in range(batch_size)]
            )
            safe_play(self, GD.adjust_layers())

#        self.play(GD.highlight_random_block_and_past(self))
#        self.wait(2)

        # Reset to normal
#        self.play(GD.reset_all_opacity(self))
#        self.wait(1)
        print("b4 create tree animations")
        tree_animations = GD.create_tree_animation_fast()
        print("b4 play tree animations")
        self.play(tree_animations, run_time=5.0)
        print("after play tree animations")
        self.wait(3)

class BlinkTest(Scene):
    AVG_AC = 5
    BLOCKS = 40
    DAG_WIDTH = 7
    def construct(self):
        LD = LayerDAG(width=self.DAG_WIDTH, block_w = BLOCK_W*0.75, block_h = BLOCK_H*0.75)
        self.play(LD.init_animation, *[LD.add("V%d"%i,LD.get_tips(missed_blocks=poi(lam=self.AVG_AC)), random_sp=True) for i in range(self.BLOCKS)])
        self.play(LD.adjust_layers())
        for _ in range(5):
            self.play(LD.blink(LD.random_block()))
        for _ in range(5):
            self.play(LD.blink(LD.get_future(LD.random_block())))

class MinerDemo(Scene):
    def construct(self):
        m = Miner(self, x=-3.5, y=0, attempts = 5)
        while m.mining():
            m.update()

class Blink(Scene):
    def construct(self):
        LD = LayerDAG()
        self.play(LD.init_animation)
        self.play(LD.blink("Gen"))

class BlockMobAndColors(MovingCameraScene):
    def construct(self):
        block = BlockMob(None, "Gen")
        self.add(block)
        self.wait(1)
        self.play(block.animate(runtime = 1).shift(UP * 2))
        block.set_red()
        self.wait(1)
        self.play(block.animate(runtime = 1).shift(DOWN * 2))
        block.set_blue()
        self.wait(1)
        self.play(block.animate(runtime = 1).shift(UP * 2))
        block.set_to_color("#70C7BA")
        self.wait(1)
        self.play(block.animate(runtime = 1).shift(DOWN * 2))
        self.play(block.fade_red())
        self.wait(1)
        self.play(block.animate(runtime = 1).shift(UP * 2))
        self.play(block.fade_blue())
        self.wait(1)
        self.play(block.animate(runtime = 1).shift(DOWN * 2))
        self.play(block.fade_to_color(PURE_GREEN))
        self.wait(1)

class ChangingLabel(Scene):
    def construct(self):
        block = BlockMob(None, "Gen")
        self.add(block)
        self.wait(1)
        self.play(block.animate(runtime = 1).shift(UP * 2))
        block.set_label("success")
        self.wait(1)
        self.play(block.animate(runtime = 1).shift(DOWN * 2))
        block.set_blue()
        self.wait(1)

class BitcoinExample(MovingCameraFixedLayerScene):
    def construct(self):
        BTC = Bitcoin(self)
        self.play(BTC.genesis())
        self.play(BTC.add_block_to_chain())
        self.play(BTC.add_block_to_chain())
        self.play(BTC.add_block_to_chain())
        self.play(BTC.add_block_to_chain())
        self.play(BTC.add_first_fork_block(1))
        self.play(BTC.move_camera_to(4))
        self.play(BTC.add_block_to_chain())
        self.play(BTC.add_block_to_chain())
        self.play(BTC.add_block_to_fork())
        self.play(BTC.add_block_to_fork())
        self.play(BTC.move_camera_to(5))
        self.play(BTC.adjust_block_color_by_longest_chain())
        self.play(BTC.blink_these_blocks(BTC.get_tips()))
        self.play(BTC.blink_these_blocks(BTC.get_longest_chain_tips()))
        self.play(BTC.blink_past_of_random_block())
#        self.wait(1)
        self.play(BTC.blink_future_of_random_block())
#        self.wait(1)
        self.play(BTC.blink_anticone_of_random_block())
        self.wait(3)

#Selfish Mining in Bitcoin, simulator must use blockanimator
class SMBitcoin(MovingCameraFixedLayerScene):
    def construct(self):
        # Create narration text using pure Manim MathTex
        selfishmining = MathTex(r"\text{Selfish Mining in Bitcoin}", color=WHITE)
        selfishmining.to_edge(UP)

        state0 = MathTex(r"\text{State 0}", color=WHITE)
        state0.to_edge(UP)
        state0prime = MathTex(r"\text{State 0'}", color=WHITE)
        state0prime.to_edge(UP)
        state1 = MathTex(r"\text{State 1}", color=WHITE)
        state1.to_edge(UP)
        state2 = MathTex(r"\text{State 2}", color=WHITE)
        state2.to_edge(UP)
        state3 = MathTex(r"\text{State 3}", color=WHITE)
        state3.to_edge(UP)
        state4 = MathTex(r"\text{State 4}", color=WHITE)
        state4.to_edge(UP)
        state5 = MathTex(r"\text{State ...}", color=WHITE)
        state5.to_edge(UP)

        # Create genesis block directly
        genesis = BlockMob(None, "Gen")
        genesis.move_to([-4, 0, 0])
        genesis.set_label("0")

        # Create blocks with pointers - start in lower position
        offset_amount = DOWN * 1.2  # More than block height (0.8)

        block1 = BlockMob(genesis, "0")
        block1.set_label("1")
        block1.shift(offset_amount)  # Start in lower position
        block1.set_red()  # Make red
        block1.set_opacity(0.5)  # Set to 50% opacity
        pointer1 = Pointer(block1, genesis)

        block2 = BlockMob(block1, "1")
        block2.set_label("2")
        block2.set_red()  # Make red
        block2.set_opacity(0.5)  # Set to 50% opacity
        pointer2 = Pointer(block2, block1)

        block3 = BlockMob(block2, "2")
        block3.set_label("3")
        block3.set_red()  # Make red
        block3.set_opacity(0.5)  # Set to 50% opacity
        pointer3 = Pointer(block3, block2)

        block4 = BlockMob(block3, "3")
        block4.set_label("4")
        block4.set_red()  # Make red
        block4.set_opacity(0.5)  # Set to 50% opacity
        pointer4 = Pointer(block4, block3)

        # Create branch from genesis - same horizontal plane as genesis, same vertical plane as block1
        honest_block = BlockMob(genesis, "branch")
        honest_block.set_label("1")
        honest_pointer = Pointer(honest_block, genesis)
        # Position at same y as genesis, same x as block1
        honest_block.move_to([block1.get_center()[0], genesis.get_center()[1], 0])

        # Start transitions
        self.wait(1)
        self.play(
            AnimationGroup(
                FadeIn(selfishmining, run_time=1.0),
                FadeIn(genesis, run_time=1.0),
                FadeIn(block1, run_time=1.0),
                FadeIn(pointer1, run_time=1.0),
                FadeIn(block2, run_time=1.0),
                FadeIn(pointer2, run_time=1.0),
                FadeIn(block3, run_time=1.0),
                FadeIn(pointer3, run_time=1.0),
                FadeIn(block4, run_time=1.0),
                FadeIn(pointer4, run_time=1.0),
                FadeIn(honest_block, run_time=1.0),
                FadeIn(honest_pointer, run_time=1.0)
            )
        )

        self.wait(1)

        self.play(
            AnimationGroup(
                FadeOut(selfishmining, run_time=1.0),
                FadeOut(genesis, run_time=1.0),
                FadeOut(block1, run_time=1.0),
                FadeOut(pointer1, run_time=1.0),
                FadeOut(block2, run_time=1.0),
                FadeOut(pointer2, run_time=1.0),
                FadeOut(block3, run_time=1.0),
                FadeOut(pointer3, run_time=1.0),
                FadeOut(block4, run_time=1.0),
                FadeOut(pointer4, run_time=1.0),
                FadeOut(honest_block, run_time=1.0),
                FadeOut(honest_pointer, run_time=1.0)
            )
        )

        self.wait(1)

        self.play(
            AnimationGroup(
                FadeIn(state0, run_time=1),
                FadeIn(genesis, run_time=1)
            )
        )

        self.wait(1)

        self.play(
                FadeOut(state0, run_time=1)
        )

        self.wait(1)

        self.play(
            AnimationGroup(
                FadeIn(state1, run_time=1),
                FadeIn(pointer1, run_time=1),
                FadeIn(block1, run_time=1)
            )
        )

        self.wait(1)

        self.play(
                FadeOut(state1, run_time=1)
        )

        self.wait(1)

        self.play(
            AnimationGroup(
                FadeIn(state2, run_time=1),
                FadeIn(pointer2, run_time=1),
                FadeIn(block2, run_time=1)
            )
        )

        self.wait(1)

        self.play(
                FadeOut(state2, run_time=1)
        )

        self.wait(1)

        self.play(
            AnimationGroup(
                FadeIn(state3, run_time=1),
                FadeIn(pointer3, run_time=1),
                FadeIn(block3, run_time=1)
            )
        )

        self.wait(1)

        self.play(
                FadeOut(state3, run_time=1)
        )

        self.wait(1)

        self.play(
            AnimationGroup(
                FadeIn(state4, run_time=1),
                FadeIn(pointer4, run_time=1),
                FadeIn(block4, run_time=1)
            )
        )

        self.wait(1)

        self.play(
            AnimationGroup(
                FadeOut(state4, run_time=1.0),
                FadeOut(block2, run_time=1.0),
                FadeOut(pointer2, run_time=1.0),
                FadeOut(block3, run_time=1.0),
                FadeOut(pointer3, run_time=1.0),
                FadeOut(block4, run_time=1.0),
                FadeOut(pointer4, run_time=1.0)
            )
        )

        self.wait(1)

        self.play(
            AnimationGroup(
                FadeIn(state0prime, run_time=1),
                FadeIn(honest_block, run_time=1),
                FadeIn(honest_pointer, run_time=1)
            )
        )

        self.wait(1)

        self.play(
            AnimationGroup(
                FadeOut(state0prime, run_time=1.0),
                FadeOut(block1, run_time=1.0),
                FadeOut(pointer1, run_time=1.0),
                FadeOut(honest_block, run_time=1.0),
                FadeOut(honest_pointer, run_time=1.0),
                FadeOut(genesis, run_time=1.0),
            )
        )

        self.wait(1)


class SelfishMiningExample(MovingCameraFixedLayerScene):
    def construct(self):
        # Create the SelfishMining instance
        sm = SelfishMiningSquares()

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
        self.play(
            AnimationGroup(
                sm._fade_out(sm.state4),
                sm._fade_out(sm.selfish_block2),
                sm._fade_out(sm.selfish_block2_label),
                sm._fade_out(sm.selfish_line2),
                sm._fade_out(sm.selfish_block3),
                sm._fade_out(sm.selfish_block3_label),
                sm._fade_out(sm.selfish_line3),
                sm._fade_out(sm.selfish_block4),
                sm._fade_out(sm.selfish_block4_label),
                sm._fade_out(sm.selfish_line4),
                sm._fade_in(sm.state1)
            )
        )
        self.wait(1)

        # Show transition from state 1 to state 0' (honest miner finds a block)
        self.play(sm.one_to_zero_prime())
        self.wait(1)

        # Finally, demonstrate the zero_to_zero transition
        # First fade out state 0' elements and show state 0
        self.play(
            AnimationGroup(
                sm._fade_out(sm.state0prime),
                sm._fade_out(sm.honest_block1),
                sm._fade_out(sm.honest_block1_label),
                sm._fade_out(sm.honest_line1),
                sm._fade_out(sm.selfish_block1),
                sm._fade_out(sm.selfish_block1_label),
                sm._fade_out(sm.selfish_line1),
                sm._fade_in(sm.state0)
            )
        )
        self.wait(1)

        # Show the zero_to_zero transition (honest miner finds a block in state 0)
        self.play(sm.zero_to_zero())
        self.wait(2)

class SMBitcoinWithoutBlock(MovingCameraFixedLayerScene):
    def construct(self):
        # Create narration text using pure Manim MathTex
        selfishmining = MathTex(r"\text{Selfish Mining in Bitcoin}", color=WHITE)
        selfishmining.to_edge(UP)

        state0 = MathTex(r"\text{State 0}", color=WHITE)
        state0.to_edge(UP)
        state0prime = MathTex(r"\text{State 0'}", color=WHITE)
        state0prime.to_edge(UP)
        state1 = MathTex(r"\text{State 1}", color=WHITE)
        state1.to_edge(UP)
        state2 = MathTex(r"\text{State 2}", color=WHITE)
        state2.to_edge(UP)
        state3 = MathTex(r"\text{State 3}", color=WHITE)
        state3.to_edge(UP)
        state4 = MathTex(r"\text{State 4}", color=WHITE)
        state4.to_edge(UP)
        state5 = MathTex(r"\text{State ...}", color=WHITE)
        state5.to_edge(UP)

        # Create genesis block using pure Manim Square
        genesis = Square(side_length=0.8, color="#0000FF", fill_opacity=0)
        genesis.move_to([-4, 0, 0])
        genesis_label = Text("0", font_size=24, color=WHITE)
        genesis_label.move_to(genesis.get_center())

        # Create blocks with lines - start in lower position
        offset_amount = DOWN * 1.2  # More than block height (0.8)

        block1 = Square(side_length=0.8, color=PURE_RED, fill_opacity=0.5)
        block1.move_to([-2, -1.2, 0])  # Manual positioning instead of automatic
        block1_label = Text("1", font_size=24, color=WHITE)
        block1_label.move_to(block1.get_center())
        line1 = Line(start=block1.get_left(), end=genesis.get_right(),
                     buff=0.1, color=WHITE, stroke_width=2)

        block2 = Square(side_length=0.8, color=PURE_RED, fill_opacity=0.5)
        block2.move_to([0, -1.2, 0])
        block2_label = Text("2", font_size=24, color=WHITE)
        block2_label.move_to(block2.get_center())
        line2 = Line(start=block2.get_left(), end=block1.get_right(),
                     buff=0.1, color=WHITE, stroke_width=2)

        block3 = Square(side_length=0.8, color=PURE_RED, fill_opacity=0.5)
        block3.move_to([2, -1.2, 0])
        block3_label = Text("3", font_size=24, color=WHITE)
        block3_label.move_to(block3.get_center())
        line3 = Line(start=block3.get_left(), end=block2.get_right(),
                     buff=0.1, color=WHITE, stroke_width=2)

        block4 = Square(side_length=0.8, color=PURE_RED, fill_opacity=0.5)
        block4.move_to([4, -1.2, 0])
        block4_label = Text("4", font_size=24, color=WHITE)
        block4_label.move_to(block4.get_center())
        line4 = Line(start=block4.get_left(), end=block3.get_right(),
                     buff=0.1, color=WHITE, stroke_width=2)

        # Create branch from genesis - same horizontal plane as genesis, same vertical plane as block1
        honest_block = Square(side_length=0.8, color="#0000FF", fill_opacity=0)
        honest_block.move_to([-2, 0, 0])  # Same y as genesis, same x as block1
        honest_block_label = Text("1", font_size=24, color=WHITE)
        honest_block_label.move_to(honest_block.get_center())
        honest_line = Line(start=honest_block.get_left(), end=genesis.get_right(),
                           buff=0.1, color=WHITE, stroke_width=2)

        # Start transitions
        self.wait(1)
        self.play(
            AnimationGroup(
                FadeIn(selfishmining, run_time=1.0),
                FadeIn(genesis, run_time=1.0),
                FadeIn(genesis_label, run_time=1.0),
                FadeIn(block1, run_time=1.0),
                FadeIn(block1_label, run_time=1.0),
                Create(line1, run_time=1.0),
                FadeIn(block2, run_time=1.0),
                FadeIn(block2_label, run_time=1.0),
                Create(line2, run_time=1.0),
                FadeIn(block3, run_time=1.0),
                FadeIn(block3_label, run_time=1.0),
                Create(line3, run_time=1.0),
                FadeIn(block4, run_time=1.0),
                FadeIn(block4_label, run_time=1.0),
                Create(line4, run_time=1.0),
                FadeIn(honest_block, run_time=1.0),
                FadeIn(honest_block_label, run_time=1.0),
                Create(honest_line, run_time=1.0)
            )
        )

        self.wait(1)

        self.play(
            AnimationGroup(
                FadeOut(selfishmining, run_time=1.0),
                FadeOut(genesis, run_time=1.0),
                FadeOut(genesis_label, run_time=1.0),
                FadeOut(block1, run_time=1.0),
                FadeOut(block1_label, run_time=1.0),
                FadeOut(line1, run_time=1.0),
                FadeOut(block2, run_time=1.0),
                FadeOut(block2_label, run_time=1.0),
                FadeOut(line2, run_time=1.0),
                FadeOut(block3, run_time=1.0),
                FadeOut(block3_label, run_time=1.0),
                FadeOut(line3, run_time=1.0),
                FadeOut(block4, run_time=1.0),
                FadeOut(block4_label, run_time=1.0),
                FadeOut(line4, run_time=1.0),
                FadeOut(honest_block, run_time=1.0),
                FadeOut(honest_block_label, run_time=1.0),
                FadeOut(honest_line, run_time=1.0)
            )
        )

        self.wait(1)

        self.play(
            AnimationGroup(
                FadeIn(state0, run_time=1),
                FadeIn(genesis, run_time=1),
                FadeIn(genesis_label, run_time=1)
            )
        )

        self.wait(1)

        self.play(
            FadeOut(state0, run_time=1)
        )

        self.wait(1)

        self.play(
            AnimationGroup(
                FadeIn(state1, run_time=1),
                Create(line1, run_time=1),
                FadeIn(block1, run_time=1),
                FadeIn(block1_label, run_time=1)
            )
        )

        self.wait(1)

        self.play(
            FadeOut(state1, run_time=1)
        )

        self.wait(1)

        self.play(
            AnimationGroup(
                FadeIn(state2, run_time=1),
                Create(line2, run_time=1),
                FadeIn(block2, run_time=1),
                FadeIn(block2_label, run_time=1)
            )
        )

        self.wait(1)

        self.play(
            FadeOut(state2, run_time=1)
        )

        self.wait(1)

        self.play(
            AnimationGroup(
                FadeIn(state3, run_time=1),
                Create(line3, run_time=1),
                FadeIn(block3, run_time=1),
                FadeIn(block3_label, run_time=1)
            )
        )

        self.wait(1)

        self.play(
            FadeOut(state3, run_time=1)
        )

        self.wait(1)

        self.play(
            AnimationGroup(
                FadeIn(state4, run_time=1),
                Create(line4, run_time=1),
                FadeIn(block4, run_time=1),
                FadeIn(block4_label, run_time=1)
            )
        )

        self.wait(1)

        self.play(
            AnimationGroup(
                FadeOut(state4, run_time=1.0),
                FadeOut(block2, run_time=1.0),
                FadeOut(block2_label, run_time=1.0),
                FadeOut(line2, run_time=1.0),
                FadeOut(block3, run_time=1.0),
                FadeOut(block3_label, run_time=1.0),
                FadeOut(line3, run_time=1.0),
                FadeOut(block4, run_time=1.0),
                FadeOut(block4_label, run_time=1.0),
                FadeOut(line4, run_time=1.0)
            )
        )

        self.wait(1)

        self.play(
            AnimationGroup(
                FadeIn(state0prime, run_time=1),
                FadeIn(honest_block, run_time=1),
                FadeIn(honest_block_label, run_time=1),
                Create(honest_line, run_time=1)
            )
        )

        self.wait(1)

        self.play(
            AnimationGroup(
                FadeOut(state0prime, run_time=1.0),
                FadeOut(block1, run_time=1.0),
                FadeOut(block1_label, run_time=1.0),
                FadeOut(line1, run_time=1.0),
                FadeOut(honest_block, run_time=1.0),
                FadeOut(honest_block_label, run_time=1.0),
                FadeOut(honest_line, run_time=1.0),
                # Keep genesis and genesis_label visible
            )
        )

        self.wait(1)

        # NEW: State 0 to 0 transition animation
        # Create new state label
        state0_transition = MathTex(r"\text{State 0 to 0 Transition}", color=WHITE)
        state0_transition.to_edge(UP)

        # Show transition label
        self.play(FadeIn(state0_transition, run_time=1))
        self.wait(1)

        # Add new blue block on same horizontal plane as genesis
        new_honest_block = Square(side_length=0.8, color="#0000FF", fill_opacity=0)
        new_honest_block.move_to([-2, 0, 0])  # Same y as genesis, to the right
        new_honest_block_label = Text("1", font_size=24, color=WHITE)
        new_honest_block_label.move_to(new_honest_block.get_center())

        # Create line connecting the blocks
        transition_line = Line(start=new_honest_block.get_left(), end=genesis.get_right(),
                               buff=0.1, color=WHITE, stroke_width=2)

        # Add the new block and line
        self.play(
            AnimationGroup(
                FadeIn(new_honest_block, run_time=1),
                FadeIn(new_honest_block_label, run_time=1),
                Create(transition_line, run_time=1)
            )
        )
        self.wait(1)

        # Shift both blocks and line left AND fade them out simultaneously
        shift_amount = LEFT * 2

        self.play(
            AnimationGroup(
                # Combined shift and fade animations
                genesis.animate.shift(shift_amount).set_opacity(0),
                genesis_label.animate.shift(shift_amount).set_opacity(0),
                new_honest_block.animate.shift(shift_amount),
                new_honest_block_label.animate.shift(shift_amount).set_opacity(0),
                transition_line.animate.shift(shift_amount).set_opacity(0),
                run_time=1.5
            )
        )
        self.wait(1)

        # Clean up transition label
        self.play(FadeOut(state0_transition, run_time=1))
        self.wait(1)

        # Replace the honest block with the original genesis block
        # Move original genesis to the honest block's current position
        genesis.move_to(new_honest_block.get_center())
        genesis_label.move_to(new_honest_block.get_center())

        self.play(
            AnimationGroup(
                new_honest_block.animate.set_opacity(0),
                genesis.animate.set_opacity(1).set_fill(opacity=0),
                genesis_label.animate.set_opacity(1),
                run_time=1
            )
        )
        self.wait(0.5)

        original_honest_pos = [-2, 0, 0]

        # Reuse the new_honest_block instead of creating a new one
        new_honest_block.move_to(original_honest_pos)
        new_honest_block_label.move_to(original_honest_pos)

        # Reuse the transition_line instead of creating a new one
        # Update the line's endpoints to connect the blocks at their new positions
        transition_line.set_points_by_ends(
            new_honest_block.get_left(),
            genesis.get_right(),
            buff=0.1
        )

        new_honest_block.set_opacity(1)  # for debug
        transition_line.set_opacity(1)  # for debug

        self.wait(3)

class SMBTC_testing(MovingCameraFixedLayerScene):
    def construct(self):
        sm = SelfishMining()

        self.wait(1)

        self.play(sm.intro_anim())

        self.wait(1.0)

        self.play(sm.zero_to_zero())

        self.wait(2)


class SMBTC_testing_without_block(MovingCameraFixedLayerScene):
    def construct(self):
        # Replace SelfishMining() with direct Square/Line implementation
        # following your BitcoinBlockchainWithSquares pattern

        # Create title
        title = Text("Selfish Mining in Bitcoin", font_size=36, color=WHITE)
        title.to_edge(UP)

        # Create squares with no fill (like your example)
        genesis = Square(side_length=0.8, color="#f7931a", fill_opacity=0)
        genesis.move_to([-4, 0, 0])
        genesis_label = Text("Gen", font_size=24, color=WHITE)
        genesis_label.move_to(genesis.get_center())

        # Create additional blocks following your pattern
        block1 = Square(side_length=0.8, color=PURE_RED, fill_opacity=0)
        block1.move_to([-2, -1.2, 0])  # Offset down like your example
        block1_label = Text("1", font_size=24, color=WHITE)
        block1_label.move_to(block1.get_center())

        # Create lines without tips (like your example)
        line1 = Line(start=block1.get_left(), end=genesis.get_right(),
                     buff=0.1, color=WHITE, stroke_width=2)

        self.wait(1)

        # Intro animation
        self.play(
            AnimationGroup(
                FadeIn(title),
                FadeIn(genesis),
                FadeIn(genesis_label),
                FadeIn(block1),
                FadeIn(block1_label),
                Create(line1)
            )
        )

        self.wait(1.0)

        # Zero to zero transition (fade out and back to genesis only)
        self.play(
            AnimationGroup(
                FadeOut(block1),
                FadeOut(block1_label),
                FadeOut(line1)
            )
        )

        self.wait(2)

class SingleBlock(Scene):
    def construct(self):
        # Create Kaspa Block
        kaspa_container = Square(
            side_length=4,
            color=WHITE,
            fill_opacity=0,
            stroke_width=3
        )

        kaspa_header = Rectangle(
            width=3.5,
            height=0.8,
            color=WHITE,
            fill_opacity=0,
            stroke_width=2
        )
        kaspa_header.move_to(kaspa_container.get_center() + UP * 1.3)

        kaspa_body = Rectangle(
            width=3.5,
            height=2.1,
            color=WHITE,
            fill_opacity=0,
            stroke_width=2
        )
        kaspa_body.move_to(kaspa_container.get_center() + DOWN * 0.6)

        # Add label
        kaspa_label = Text("Kaspa Block", font_size=24).move_to(kaspa_container.get_top() + UP * 0.3)
        kaspa_header_label = Text("Header", font_size=20).move_to(kaspa_header.get_center())
        kaspa_body_label = Text("Body", font_size=20).move_to(kaspa_body.get_center())

        # Animate
        self.wait(2.0)
        self.play(
            Create(kaspa_container)
        )
        self.play(
            Write(kaspa_label)
        )
        self.play(
            Create(kaspa_header)
        )
        self.play(
            Write(kaspa_header_label)
        )
        self.play(
            Create(kaspa_body)
        )
        self.play(
            Write(kaspa_body_label)
        )
        self.wait(8)

class WideHeaderBodyBoxes(Scene):
    def construct(self):
        # Create Bitcoin Block (left side)
        bitcoin_container = Square(
            side_length=4,
            color=WHITE,
            fill_opacity=0,
            stroke_width=3
        )
        bitcoin_container.shift(LEFT * 3)

        bitcoin_header = Rectangle(
            width=3.5,
            height=0.8,
            color=WHITE,
            fill_opacity=0,
            stroke_width=2
        )
        bitcoin_header.move_to(bitcoin_container.get_center() + UP * 1.3)

        bitcoin_body = Rectangle(
            width=3.5,
            height=2.1,
            color=WHITE,
            fill_opacity=0,
            stroke_width=2
        )
        bitcoin_body.move_to(bitcoin_container.get_center() + DOWN * 0.6)

        # Create Kaspa Block (right side) - identical structure
        kaspa_container = Square(
            side_length=4,
            color=WHITE,
            fill_opacity=0,
            stroke_width=3
        )
        kaspa_container.shift(RIGHT * 3)

        kaspa_header = Rectangle(
            width=3.5,
            height=0.8,
            color=WHITE,
            fill_opacity=0,
            stroke_width=2
        )
        kaspa_header.move_to(kaspa_container.get_center() + UP * 1.3)

        kaspa_body = Rectangle(
            width=3.5,
            height=2.1,
            color=WHITE,
            fill_opacity=0,
            stroke_width=2
        )
        kaspa_body.move_to(kaspa_container.get_center() + DOWN * 0.6)

        # Add labels
        bitcoin_label = Text("Bitcoin Block", font_size=24).move_to(bitcoin_container.get_top() + UP * 0.3)
        kaspa_label = Text("Kaspa Block", font_size=24).move_to(kaspa_container.get_top() + UP * 0.3)

        bitcoin_header_label = Text("Header", font_size=20).move_to(bitcoin_header.get_center())
        bitcoin_body_label = Text("Body", font_size=20).move_to(bitcoin_body.get_center())

        kaspa_header_label = Text("Header", font_size=20).move_to(kaspa_header.get_center())
        kaspa_body_label = Text("Body", font_size=20).move_to(kaspa_body.get_center())

        # Animate creation - both blocks simultaneously
        self.play(
            Create(bitcoin_container),
            Create(kaspa_container)
        )
        self.play(
            Write(bitcoin_label),
            Write(kaspa_label)
        )
        self.play(
            Create(bitcoin_header), Create(bitcoin_body),
            Create(kaspa_header), Create(kaspa_body)
        )
        self.play(
            Write(bitcoin_header_label), Write(bitcoin_body_label),
            Write(kaspa_header_label), Write(kaspa_body_label)
        )

        self.wait(8)


class UTXOCommitment(Scene):
    def construct(self):
        # Create narration text at the top
        narration = Text("Kaspa UTXO Set Commitment", font_size=36, color=WHITE)
        narration.to_edge(UP)

        # Create Kaspa Block (left side) - shifted down less
        kaspa_container = Square(
            side_length=4,
            color=WHITE,
            fill_opacity=0,
            stroke_width=3
        )
        kaspa_container.shift(LEFT * 3 + DOWN * 0.75)

        kaspa_header = Rectangle(
            width=3.5,
            height=0.8,
            color=WHITE,
            fill_opacity=0,
            stroke_width=2
        )
        kaspa_header.move_to(kaspa_container.get_center() + UP * 1.3)

        kaspa_body = Rectangle(
            width=3.5,
            height=2.1,
            color=WHITE,
            fill_opacity=0,
            stroke_width=2
        )
        kaspa_body.move_to(kaspa_container.get_center() + DOWN * 0.6)

        # Create UTXO set (right side) - shifted down less
        utxo_container = Square(
            side_length=4,
            color=WHITE,
            fill_opacity=0,
            stroke_width=3
        )
        utxo_container.shift(RIGHT * 3 + DOWN * 0.75)

        # Create many small UTXO boxes inside the container
        utxo_boxes = []
        utxo_labels = []

        # Grid of 4x5 small boxes (20 total UTXOs)
        for row in range(4):
            for col in range(5):
                # Small box size
                box = Rectangle(
                    width=0.5,
                    height=0.3,
                    color=WHITE,
                    fill_opacity=0,
                    stroke_width=2
                )

                # Position within the container
                x_offset = (col - 2) * 0.6  # Center around 0
                y_offset = (1.5 - row) * 0.4  # Top to bottom
                box.move_to(utxo_container.get_center() + RIGHT * x_offset + UP * y_offset)

                # Label for each UTXO
                label = Text("UTXO", font_size=10, color=WHITE)
                label.move_to(box.get_center())

                utxo_boxes.append(box)
                utxo_labels.append(label)

                # Create lock logo - keep original size for better visibility
        lock_body = Rectangle(
            width=1.5,
            height=1.0,
            color=YELLOW,
            fill_opacity=0.8,
            stroke_width=3
        )
        lock_body.move_to(utxo_container.get_center())

        lock_shackle = Arc(
            radius=0.5,
            start_angle=0,
            angle=PI,
            color=YELLOW,
            stroke_width=6
        )
        lock_shackle.move_to(lock_body.get_center() + UP * 0.75)

        # Group lock components together
        lock_group = VGroup(lock_body, lock_shackle)

        # Create clone of UTXO container for transformation
        utxo_clone = utxo_container.copy()
        utxo_clone_boxes = [box.copy() for box in utxo_boxes]
        utxo_clone_labels = [label.copy() for label in utxo_labels]
        lock_group_clone = lock_group.copy()

        # Add main labels - automatically positioned relative to shifted containers
        kaspa_label = Text("Kaspa Block", font_size=24).move_to(kaspa_container.get_top() + UP * 0.3)
        utxo_label = Text("UTXO set", font_size=24).move_to(utxo_container.get_top() + UP * 0.3)

        kaspa_header_label = Text("Header", font_size=20).move_to(kaspa_header.get_center())
        kaspa_body_label = Text("Body", font_size=20).move_to(kaspa_body.get_center())

        # Start with narration
        self.play(Write(narration))
        self.wait(1)

        # Animate creation - both blocks simultaneously
        self.play(
            Create(kaspa_container),
            Create(utxo_container)
        )
        self.play(
            Write(kaspa_label),
            Write(utxo_label)
        )
        self.play(
            Create(kaspa_header), Create(kaspa_body)
        )
        self.play(
            Write(kaspa_header_label), Write(kaspa_body_label)
        )

        # Animate UTXO boxes appearing
        self.play(
            *[Create(box) for box in utxo_boxes]
        )
        self.play(
            *[Write(label) for label in utxo_labels]
        )

        # Fade in lock logo over UTXO set
        self.play(
            FadeIn(lock_group)
        )

        # Create and transform clone to header
        self.play(
            FadeIn(utxo_clone),
            *[FadeIn(box) for box in utxo_clone_boxes],
            *[FadeIn(label) for label in utxo_clone_labels],
            FadeIn(lock_group_clone)
        )

        # Transform and shift clone to kaspa header with scaling during animation
        self.play(
            Transform(utxo_clone, kaspa_header),
            *[FadeOut(box) for box in utxo_clone_boxes],
            *[FadeOut(label) for label in utxo_clone_labels],
            lock_group_clone.animate.scale(0.4).move_to(kaspa_header.get_center())
        )

        self.wait(8)


class Transaction(Scene):
    def construct(self):
        # ========================================
        # OBJECT CREATION SECTION
        # ========================================

        # Narration text
        narration = Text("Kaspa UTXO Set Commitment", font_size=36, color=WHITE)
        narration.to_edge(UP)

        # Initial transaction square (block-sized)
        tx_square = Square(
            side_length=4,
            color=WHITE,
            fill_opacity=0,
            stroke_width=3
        )
        tx_square.shift(LEFT * 3 + DOWN * 0.75)

        tx_label = Text("Transaction", font_size=24, color=WHITE)
        tx_label.move_to(tx_square.get_center())

        # Transaction lock components - fixed positioning
        tx_lock_body = Rectangle(
            width=0.6,
            height=0.4,
            color=YELLOW,
            fill_opacity=0.8,
            stroke_width=2
        )

        tx_lock_shackle = Arc(
            radius=0.2,
            start_angle=0,
            angle=PI,
            color=YELLOW,
            stroke_width=3
        )
        tx_lock_shackle.move_to(tx_lock_body.get_center() + UP * 0.3)

        tx_lock_group = VGroup(tx_lock_body, tx_lock_shackle)

        # Outer block container
        block_body = Square(
            side_length=4,
            color=WHITE,
            fill_opacity=0,
            stroke_width=3
        )
        block_body.shift(LEFT * 3 + DOWN * 0.75)

        # Final kaspa body rectangle
        kaspa_body = Rectangle(
            width=3.5,
            height=2.1,
            color=WHITE,
            fill_opacity=0,
            stroke_width=2
        )
        kaspa_body.move_to(block_body.get_center() + DOWN * 0.6)

        # Kaspa header
        kaspa_header = Rectangle(
            width=3.5,
            height=0.8,
            color=WHITE,
            fill_opacity=0,
            stroke_width=2
        )
        kaspa_header.move_to(kaspa_body.get_center() + UP * 1.9)

        # Kaspa container (for UTXO animation)
        kaspa_container = Square(
            side_length=4,
            color=WHITE,
            fill_opacity=0,
            stroke_width=3
        )
        kaspa_container.shift(LEFT * 3 + DOWN * 0.75)

        # UTXO container
        utxo_container = Square(
            side_length=4,
            color=WHITE,
            fill_opacity=0,
            stroke_width=3
        )
        utxo_container.shift(RIGHT * 3 + DOWN * 0.75)

        # UTXO boxes and labels (19 instead of 20)
        utxo_boxes = []
        utxo_labels = []
        skip_position = (1, 2)  # Skip row 1, col 2 for transaction

        for row in range(4):
            for col in range(5):
                if (row, col) == skip_position:
                    continue  # Skip this position for transaction

                box = Rectangle(
                    width=0.5,
                    height=0.3,
                    color=WHITE,
                    fill_opacity=0,
                    stroke_width=2
                )
                x_offset = (col - 2) * 0.6
                y_offset = (1.5 - row) * 0.4
                box.move_to(utxo_container.get_center() + RIGHT * x_offset + UP * y_offset)

                label = Text("UTXO", font_size=10, color=WHITE)
                label.move_to(box.get_center())

                utxo_boxes.append(box)
                utxo_labels.append(label)

                # Target position for transaction transformation
        target_utxo_pos = utxo_container.get_center() + RIGHT * ((skip_position[1] - 2) * 0.6) + UP * (
                    (1.5 - skip_position[0]) * 0.4)

        # Lock components for UTXO set
        lock_body = Rectangle(
            width=1.5,
            height=1.0,
            color=YELLOW,
            fill_opacity=0.8,
            stroke_width=3
        )
        lock_body.move_to(utxo_container.get_center())

        lock_shackle = Arc(
            radius=0.5,
            start_angle=0,
            angle=PI,
            color=YELLOW,
            stroke_width=6
        )
        lock_shackle.move_to(lock_body.get_center() + UP * 0.75)

        lock_group = VGroup(lock_body, lock_shackle)

        # Clone objects for transformation (created at object creation time)
        utxo_clone = utxo_container.copy()
        lock_group_clone = lock_group.copy()

        # Target UTXO transformation objects
        new_utxo_box = Rectangle(
            width=0.5,
            height=0.3,
            color=WHITE,
            fill_opacity=0,
            stroke_width=2
        )
        new_utxo_box.move_to(target_utxo_pos)

        new_utxo_label = Text("UTXO", font_size=10, color=WHITE)
        new_utxo_label.move_to(target_utxo_pos)

        # Labels
        kaspa_label = Text("Kaspa Block", font_size=24)
        kaspa_label.move_to(kaspa_container.get_top() + UP * 0.3)

        utxo_label = Text("UTXO set", font_size=24)
        utxo_label.move_to(utxo_container.get_top() + UP * 0.3)

        kaspa_header_label = Text("Header", font_size=20)
        kaspa_header_label.move_to(kaspa_header.get_center())

        kaspa_body_label = Text("Body", font_size=20)
        kaspa_body_label.move_to(kaspa_body.get_center())

        # ========================================
        # ANIMATION SECTION
        # ========================================

        self.wait(2)
        # Start with narration
        self.play(Write(narration))
        self.wait(1)

        # Transaction appearance
        self.play(
            Write(tx_label)
        )
        self.play(
            Create(tx_square),
        )
        self.wait(2)

        # Scale transaction down
        self.play(
            tx_square.animate.scale(0.5),
            tx_label.animate.scale(0.5)
        )

        # Show container around scaled transaction
        self.play(Create(block_body))
        self.wait(2)

        # Transform container to body and move transaction
        self.play(
            Transform(block_body, kaspa_body),
            tx_square.animate.scale(0.5).move_to(kaspa_body.get_center() + LEFT * 1),
            tx_label.animate.scale(0.5).move_to(kaspa_body.get_center() + LEFT * 1)
        )

        # Create header
        self.play(Create(kaspa_header))

        # Show the complete Kaspa block container
        self.play(Create(kaspa_container))

        # Add block labels
        self.play(Write(kaspa_body_label))
        self.wait(1)
        self.play(Write(kaspa_header_label))
        self.wait(1)
        self.play(Write(kaspa_label))
        self.wait(1)

        # Lock the transaction
        tx_lock_group.move_to(tx_square.get_center())
        self.play(FadeIn(tx_lock_group))
        self.wait(2)

        # Create transaction clone for header transformation - clone the CURRENT transaction state
        tx_clone = tx_square.copy()
        tx_label_clone = tx_label.copy()
        tx_lock_group_clone = tx_lock_group.copy()

        # Position the clone lock at the transaction's current position
        tx_lock_group_clone.move_to(tx_square.get_center())

        self.play(
            FadeIn(tx_clone),
            FadeIn(tx_label_clone),
            FadeIn(tx_lock_group_clone)
        )

        # Transform transaction clone to header with LEFT offset
        self.play(
            Transform(tx_clone, kaspa_header),
            FadeOut(tx_label_clone),
            tx_lock_group_clone.animate.scale(0.4).move_to(kaspa_header.get_center() + LEFT * 1),
            run_time=3
        )
        self.wait(2)

        # Create UTXO container
        self.play(Create(utxo_container))
        self.play(Write(utxo_label))

        # Animate UTXO boxes appearing (19 instead of 20)
        self.play(*[Create(box) for box in utxo_boxes])
        self.play(*[Write(label) for label in utxo_labels])

        # Clone transaction for UTXO transformation (leaving original in place)
        tx_utxo_clone = tx_square.copy()
        tx_utxo_label_clone = tx_label.copy()
        tx_utxo_lock_clone = tx_lock_group.copy()

        # Position the UTXO clone at the transaction's current position
        tx_utxo_lock_clone.move_to(tx_square.get_center())

        self.play(
            FadeIn(tx_utxo_clone),
            FadeIn(tx_utxo_label_clone),
            FadeIn(tx_utxo_lock_clone)
        )
        self.wait(2)
        # Transform cloned transaction to missing UTXO position
        self.play(
            Transform(tx_utxo_clone, new_utxo_box),
            Transform(tx_utxo_label_clone, new_utxo_label),
            tx_utxo_lock_clone.animate.scale(0.3).move_to(target_utxo_pos),
            run_time=3
        )
        self.wait(2)
        # Add the new UTXO to the lists for the cloning animation
        utxo_boxes.append(tx_utxo_clone)  # tx_utxo_clone is now transformed to UTXO
        utxo_labels.append(tx_utxo_label_clone)  # tx_utxo_label_clone is now transformed to UTXO

        self.wait(2)

        # Fade in lock logo over UTXO set
        self.play(FadeIn(lock_group))

        self.wait(2)

        # Simplified UTXO set cloning - just container and lock
        self.play(
            FadeIn(utxo_clone),
            FadeIn(lock_group_clone)
        )
        # Final transformation with RIGHT offset and matching scale
        self.play(
            Transform(utxo_clone, kaspa_header),
            lock_group_clone.animate.scale(0.16).move_to(kaspa_header.get_center() + RIGHT * 1),
            run_time=3
        )

        self.wait(8)

class BitcoinBlockchainWithSquares(Scene):
    def construct(self):
        # First animation - Bitcoin Orphaning
        title1 = Text("Bitcoin Orphaning Blocks", font_size=36, color=WHITE)
        title1.to_edge(UP)

        btc_block_color = "#f7931a"
        kas_block_color = "#70C7BA"

        # Create squares for each block with no fill
        genesis = Square(side_length=0.8, color=btc_block_color, fill_opacity=0)
        genesis.move_to([-4, -1, 0])
        genesis_label = Text("Gen", font_size=24, color=WHITE)
        genesis_label.move_to(genesis.get_center())

        block1 = Square(side_length=0.8, color=btc_block_color, fill_opacity=0)
        block1.move_to([-2, -1, 0])
        block1_label = Text("1", font_size=24, color=WHITE)
        block1_label.move_to(block1.get_center())

        block2 = Square(side_length=0.8, color=btc_block_color, fill_opacity=0)
        block2.move_to([0, -1, 0])
        block2_label = Text("2", font_size=24, color=WHITE)
        block2_label.move_to(block2.get_center())

        orphan = Square(side_length=0.8, color=PURE_RED, fill_opacity=0)
        orphan.move_to([0, 0.5, 0])
        orphan_label = Text("2", font_size=24, color=WHITE)
        orphan_label.move_to(orphan.get_center())

        block3 = Square(side_length=0.8, color=btc_block_color, fill_opacity=0)
        block3.move_to([2, -1, 0])
        block3_label = Text("3", font_size=24, color=WHITE)
        block3_label.move_to(block3.get_center())

        block4 = Square(side_length=0.8, color=btc_block_color, fill_opacity=0)
        block4.move_to([4, -1, 0])
        block4_label = Text("4", font_size=24, color=WHITE)
        block4_label.move_to(block4.get_center())

        # Create lines without tips for consistent appearance
        line1 = Line(start=block1.get_left(), end=genesis.get_right(),
                     buff=0.1, color=WHITE, stroke_width=2)
        line2 = Line(start=block2.get_left(), end=block1.get_right(),
                     buff=0.1, color=WHITE, stroke_width=2)
        line3 = Line(start=block3.get_left(), end=block2.get_right(),
                     buff=0.1, color=WHITE, stroke_width=2)
        line4 = Line(start=block4.get_left(), end=block3.get_right(),
                     buff=0.1, color=WHITE, stroke_width=2)
        orphanLine = Line(start=orphan.get_left(), end=block1.get_right(),
                          buff=0.1, color=WHITE, stroke_width=2)

        # First animation sequence
        self.play(Write(title1))
        self.wait(1)
        self.play(FadeIn(genesis), FadeIn(genesis_label))
        self.play(FadeIn(block1), FadeIn(block1_label), Create(line1))
        self.play(FadeIn(block2, orphan), FadeIn(block2_label, orphan_label),
                  Create(line2), Create(orphanLine))
        self.play(FadeIn(block3), FadeIn(block3_label), Create(line3))
        self.play(FadeIn(block4), FadeIn(block4_label), Create(line4))
        self.wait(3)

        # Clear the screen
        self.play(FadeOut(*self.mobjects))
        self.wait(1)

        # Second animation - Kaspa including blocks
        title2 = Text("Kaspa Including Blocks", font_size=36, color=WHITE)
        title2.to_edge(UP)

        # Recreate all blocks (same positions and styling)
        genesis2 = Square(side_length=0.8, color=kas_block_color, fill_opacity=0)
        genesis2.move_to([-4, -1, 0])
        genesis2_label = Text("Gen", font_size=24, color=WHITE)
        genesis2_label.move_to(genesis2.get_center())

        block1_2 = Square(side_length=0.8, color=kas_block_color, fill_opacity=0)
        block1_2.move_to([-2, -1, 0])
        block1_2_label = Text("1", font_size=24, color=WHITE)
        block1_2_label.move_to(block1_2.get_center())

        block2_2 = Square(side_length=0.8, color=kas_block_color, fill_opacity=0)
        block2_2.move_to([0, -1, 0])
        block2_2_label = Text("2", font_size=24, color=WHITE)
        block2_2_label.move_to(block2_2.get_center())

        orphan2 = Square(side_length=0.8, color=PURE_RED, fill_opacity=0)
        orphan2.move_to([0, 0.5, 0])
        orphan2_label = Text("2", font_size=24, color=WHITE)
        orphan2_label.move_to(orphan2.get_center())

        block3_2 = Square(side_length=0.8, color=kas_block_color, fill_opacity=0)
        block3_2.move_to([2, -1, 0])
        block3_2_label = Text("3", font_size=24, color=WHITE)
        block3_2_label.move_to(block3_2.get_center())

        block4_2 = Square(side_length=0.8, color=kas_block_color, fill_opacity=0)
        block4_2.move_to([4, -1, 0])
        block4_2_label = Text("4", font_size=24, color=WHITE)
        block4_2_label.move_to(block4_2.get_center())

        # Recreate lines plus additional line from block3 to orphan
        line1_2 = Line(start=block1_2.get_left(), end=genesis2.get_right(),
                       buff=0.1, color=WHITE, stroke_width=2)
        line2_2 = Line(start=block2_2.get_left(), end=block1_2.get_right(),
                       buff=0.1, color=WHITE, stroke_width=2)
        line3_2 = Line(start=block3_2.get_left(), end=block2_2.get_right(),
                       buff=0.1, color=WHITE, stroke_width=2)
        line4_2 = Line(start=block4_2.get_left(), end=block3_2.get_right(),
                       buff=0.1, color=WHITE, stroke_width=2)
        orphanLine2 = Line(start=orphan2.get_left(), end=block1_2.get_right(),
                           buff=0.1, color=WHITE, stroke_width=2)
        # NEW: Additional line from block3 to orphan
        block3ToOrphanLine = Line(start=block3_2.get_left(), end=orphan2.get_right(),
                                  buff=0.1, color=WHITE, stroke_width=2)

        # Second animation sequence (same timing)
        self.play(Write(title2))
        self.wait(1)
        self.play(FadeIn(genesis2), FadeIn(genesis2_label))
        self.play(FadeIn(block1_2), FadeIn(block1_2_label), Create(line1_2))
        self.play(FadeIn(block2_2, orphan2), FadeIn(block2_2_label, orphan2_label),
                  Create(line2_2), Create(orphanLine2))
        self.play(FadeIn(block3_2), FadeIn(block3_2_label), Create(line3_2),
                  Create(block3ToOrphanLine))  # Added the new line here
        self.play(FadeIn(block4_2), FadeIn(block4_2_label), Create(line4_2))
        self.wait(8)