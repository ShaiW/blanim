from blanim import *

from numpy.random import poisson as poi

import random

#TODO everything using mobs in blanim is prohibitivly slow
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


class SelfishMiningExample(SequentialPlayScene):
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
                sm._fade_out_and_remove(sm.state4),
                sm._fade_out(sm.selfish_block2),
                sm._fade_out(sm.selfish_block2_label),
                sm._fade_out_and_remove(sm.selfish_line2),
                sm._fade_out(sm.selfish_block3),
                sm._fade_out(sm.selfish_block3_label),
                sm._fade_out_and_remove(sm.selfish_line3),
                sm._fade_out(sm.selfish_block4),
                sm._fade_out(sm.selfish_block4_label),
                sm._fade_out_and_remove(sm.selfish_line4),
            ),
            Wait(1),
            AnimationGroup(
                sm._fade_in_and_create(sm.state1),
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
                sm._fade_out(sm.state0prime),
                sm._fade_out(sm.honest_block1),
                sm._fade_out(sm.honest_block1_label),
                sm._fade_out_and_remove(sm.honest_line1),
                sm._fade_out(sm.selfish_block1),
                sm._fade_out(sm.selfish_block1_label),
                sm._fade_out_and_remove(sm.selfish_line1),
            ),
            Wait(1),
            AnimationGroup(
                sm._fade_in_and_create(sm.state0)
            )
        ))
        self.wait(2)

        # Show the zero_to_zero transition (honest miner finds a block in state 0)
        sm.zero_to_zero()

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

#TODO Remove and remove SelfishMining (runaway ram)
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


class ScrollingBlocks(Scene):
    # Constants for better maintainability
    BLOCK_SIZE = 4
    MINI_BLOCK_SIZE = 0.3
    BLOCK_SPACING = 6
    MINI_BLOCK_SPACING = 0.4
    MAX_VISIBLE_BLOCKS = 3
    PRUNING_THRESHOLD = 16

    def __init__(self):
        super().__init__()
        self.visible_blocks = set()
        self.next_block_number = 1
        self.mini_visible_blocks = set()
        self.mini_blocks = []
        self.mini_labels = []
        self.total_blocks_created = 1
        self.blocks = []
        self.block_labels = []
        self.mini_chain_frame = None

    def construct(self):
        """Main scene construction method."""
        self._setup_scene_elements()
        self._create_initial_display()
        self._run_scrolling_animation()

    def _setup_scene_elements(self):
        """Create and position all scene elements."""
        narration = self._create_narration()
        self.mini_chain_frame = self._create_mini_chain_frame(narration)
        self._create_mini_blocks()
        self._create_main_blocks()

        # Display initial elements
        self.play(Write(narration))
        self.play(Create(self.mini_chain_frame))
        self.wait(1)

    def _create_narration(self) -> Text:
        """Create the title narration text."""
        narration = Text("Kaspa Pruning (k=0)", font_size=36, color=WHITE)
        narration.to_edge(UP)
        return narration

    def _create_mini_chain_frame(self, narration: Text) -> Rectangle:
        """Create the mini-chain container frame."""
        frame = Rectangle(
            width=1.0,
            height=0.6,
            color=YELLOW,
            stroke_width=2,
            fill_opacity=0
        )
        frame.next_to(narration, DOWN, buff=0.3)
        return frame

    def _create_mini_blocks(self):
        """Create all mini blocks for the chain visualization."""
        for i in range(50):  # Increased from 20 to handle larger block numbers
            mini_block = self._create_single_mini_block(i)
            mini_label = self._create_mini_label(i, mini_block)

            self.mini_blocks.append(mini_block)
            self.mini_labels.append(mini_label)

    def _create_single_mini_block(self, index: int) -> Square:
        """Create a single mini block at the specified index."""
        mini_block = Square(
            side_length=self.MINI_BLOCK_SIZE,
            color=WHITE,
            fill_opacity=0,
            stroke_width=1
        )
        position = self.mini_chain_frame.get_center() + RIGHT * index * self.MINI_BLOCK_SPACING
        mini_block.move_to(position)
        return mini_block

    def _create_mini_label(self, index: int, mini_block: Square) -> Text:
        """Create label for a mini block."""
        label_text = "G" if index == 0 else str(index)
        mini_label = Text(label_text, font_size=6, color=WHITE)
        mini_label.move_to(mini_block.get_center())
        return mini_label

    def _create_main_blocks(self):
        """Create all main block objects."""
        for i in range(4):
            block_group = self._create_single_main_block(i)
            label = self._create_main_block_label(i, block_group)

            self.blocks.append(block_group)
            self.block_labels.append(label)

    def _create_single_main_block(self, index: int) -> VGroup:
        """Create a single main block with header and body."""
        # Create main container
        block = Square(
            side_length=self.BLOCK_SIZE,
            color=WHITE,
            fill_opacity=0,
            stroke_width=3
        )

        # Position block based on index
        position = self._get_block_position(index)
        block.move_to(position)

        # Create header and body
        header = self._create_block_header(block)
        body = self._create_block_body(block)

        return VGroup(block, header, body)

    def _get_block_position(self, index: int) -> np.ndarray:
        """Calculate position for a block based on its index."""
        if index == 0:
            return np.array([-6, -0.75, 0])  # Left
        elif index == 1:
            return np.array([0, -0.75, 0])  # Center
        else:
            return np.array([6, -0.75, 0])  # Right

    def _create_block_header(self, block: Square) -> Rectangle:
        """Create header rectangle for a block."""
        header = Rectangle(
            width=3.5,
            height=0.8,
            color=WHITE,
            fill_opacity=0,
            stroke_width=2
        )
        header.move_to(block.get_center() + UP * 1.3)
        return header

    def _create_block_body(self, block: Square) -> Rectangle:
        """Create body rectangle for a block."""
        body = Rectangle(
            width=3.5,
            height=2.1,
            color=WHITE,
            fill_opacity=0,
            stroke_width=2
        )
        body.move_to(block.get_center() + DOWN * 0.6)
        return body

    def _create_main_block_label(self, index: int, block_group: VGroup) -> Text:
        """Create label for a main block."""
        label_text = "Genesis" if index == 1 else f"Block {index + 1}"
        label = Text(label_text, font_size=24)
        label.move_to(block_group.get_top() + UP * 0.3)
        return label

    def _create_initial_display(self):
        """Show the initial Genesis block and mini block."""
        self.play(
            Create(self.blocks[1]),
            Write(self.block_labels[1]),
            Create(self.mini_blocks[0]),
            Write(self.mini_labels[0])
        )
        self.visible_blocks.add(1)
        self.mini_visible_blocks.add(0)
        self.wait(1)  # Fixed: Removed Wait(1) from play() and added proper wait

    def _run_scrolling_animation(self):
        """Execute the main scrolling animation loop."""
        # Normal scrolling for first few blocks
        for _ in range(5):
            self._scroll_left()
            self.wait(1)

            # Fast scroll to block 50
        self.wait(1)
        self._fast_scroll_to_block(50, scroll_duration=1.0)
        self.wait(2)

        # Continue normal scrolling from there
        for _ in range(5):
            self._scroll_left()
            self.wait(1)

        self.wait(2)

    def _fast_scroll_to_block(self, target_block_number: int, scroll_duration: float = 0.5):
        """Perform fast scroll animation to target block number."""
        # Phase 1: Create streaming blocks effect (keep existing blocks visible)
        self._create_streaming_blocks_effect(scroll_duration * 0.7)

        # Phase 2: Stop 1 block away and settle to final position
        self._settle_blocks_to_final_position(target_block_number, scroll_duration * 0.3)

        # Update tracking variables
        self._update_tracking_for_target(target_block_number)

    def _animate_existing_blocks_fast_scroll(self, target_block_number: int, duration: float):
        """Move existing blocks very fast during scroll with intermediate frames."""
        if not self.visible_blocks:
            return

            # Instead of moving existing blocks off-screen, create streaming effect
        self._create_streaming_blocks_effect(duration)

    def _create_streaming_blocks_effect(self, duration: float):
        """Create streaming blocks effect during fast scroll."""
        num_streaming_frames = 8
        frame_duration = duration / num_streaming_frames

        # Ensure minimum frame duration
        min_frame_duration = 1 / config.frame_rate
        frame_duration = max(frame_duration, min_frame_duration)

        for frame in range(num_streaming_frames):
            # Create temporary streaming blocks
            streaming_blocks = []
            streaming_labels = []
            animations = []

            # Create 3-4 blocks that stream across the screen
            for i in range(4):
                # Create streaming block
                stream_block = Rectangle(
                    width=self.BLOCK_SIZE * 0.8,
                    height=self.BLOCK_SIZE * 0.8,
                    fill_opacity=0.3,
                    stroke_opacity=0.7,
                    color=BLUE
                )

                # Create streaming label
                block_num = self.next_block_number + frame * 4 + i
                stream_label = Text(f"Block {block_num}", font_size=18, color=WHITE)

                # Position blocks starting from right side
                start_x = 8 + i * 3  # Start off-screen right
                stream_block.move_to([start_x, -0.75, 0])
                stream_label.move_to([start_x, -0.75 + self.BLOCK_SIZE / 2 + 0.3, 0])

                # Add to scene
                self.add(stream_block, stream_label)
                streaming_blocks.append(stream_block)
                streaming_labels.append(stream_label)

                # Create animation to move left across screen
                animations.extend([
                    stream_block.animate.shift(LEFT * 16),  # Move across entire screen
                    stream_label.animate.shift(LEFT * 16)
                ])

                # Play streaming animation
            self.play(*animations, run_time=frame_duration, rate_func=linear)

            # Remove streaming blocks
            for block, label in zip(streaming_blocks, streaming_labels):
                self.remove(block, label)

    def _settle_blocks_to_final_position(self, target_block_number: int, duration: float):
        """Move blocks from 1 block away to their final positions."""
        # Clear current blocks and reposition to target
        self._clear_current_blocks()

        # Calculate which blocks should be visible around target
        center_block = target_block_number
        visible_range = range(
            max(0, center_block - 1),
            min(center_block + self.MAX_VISIBLE_BLOCKS - 1, target_block_number + 10)
        )

        # Position blocks 1 block away from final position
        settle_animations = []

        for i, block_num in enumerate(visible_range):
            if i < len(self.blocks):
                # Calculate final position
                final_x = (i - 1) * self.BLOCK_SPACING  # Center the target block

                # Start 1 block away (to the right)
                start_x = final_x + self.BLOCK_SPACING

                # Position block at start position
                self.blocks[i].move_to(np.array([start_x, -0.75, 0]))

                # Update label
                label_text = "Genesis" if block_num == 0 else f"Block {block_num}"
                self.block_labels[i].become(Text(label_text, font_size=24))
                self.block_labels[i].move_to(self.blocks[i].get_top() + UP * 0.3)

                # Add to scene
                self.add(self.blocks[i], self.block_labels[i])
                self.visible_blocks.add(i)

                # Create settling animation
                settle_animations.extend([
                    self.blocks[i].animate.move_to(np.array([final_x, -0.75, 0])),
                    self.block_labels[i].animate.move_to(
                        np.array([final_x, -0.75 + self.BLOCK_SIZE / 2 + 0.3, 0])
                    )
                ])

                # Reposition mini blocks similarly
        self._reposition_mini_blocks_for_target(target_block_number)

        # Play settling animation
        if settle_animations:
            self.play(*settle_animations, run_time=duration, rate_func=smooth)

    def _create_scroll_blur_effect(self, duration: float):
        """Create visual effect of fast scrolling with blocks moving."""
        # Calculate the vertical range based on large block positions
        block_top = -0.75 + self.BLOCK_SIZE / 2  # Top of blocks
        block_bottom = -0.75 - self.BLOCK_SIZE / 2  # Bottom of blocks

        # Create motion blur lines that span the full block height
        blur_lines = VGroup()
        num_lines = 15  # More lines for better coverage

        for i in range(num_lines):
            # Calculate y position for this line
            y_pos = block_bottom + (i / (num_lines - 1)) * (block_top - block_bottom)

            # Create lines that span the full vertical space of blocks
            line = Line(
                start=[-8, y_pos, 0],  # Use list instead of np.array with LEFT
                end=[8, y_pos, 0],  # Use list instead of np.array with RIGHT
                stroke_width=3,
                stroke_opacity=0.4,
                color=WHITE
            )
            blur_lines.add(line)

            # Create block silhouettes that move with the blur
        moving_blocks = VGroup()
        for i in range(3):  # Create 3 moving block silhouettes
            block_silhouette = Rectangle(
                width=self.BLOCK_SIZE * 0.8,
                height=self.BLOCK_SIZE * 0.8,
                fill_opacity=0.3,
                stroke_opacity=0.6,
                color=BLUE
            )
            # Position them at different x positions
            block_silhouette.move_to([i * 8 - 4, -0.75, 0])  # Use list instead of np.array
            moving_blocks.add(block_silhouette)

            # Animate the blur effect with moving blocks
        self.play(
            *[FadeIn(line) for line in blur_lines],
            *[FadeIn(block) for block in moving_blocks],
            run_time=duration * 0.2
        )

        # Move everything left together
        self.play(
            *[line.animate.shift(LEFT * 25) for line in blur_lines],
            *[block.animate.shift(LEFT * 25) for block in moving_blocks],
            run_time=duration * 0.6,
            rate_func=rush_into
        )

        # Fade out
        self.play(
            *[FadeOut(line) for line in blur_lines],
            *[FadeOut(block) for block in moving_blocks],
            run_time=duration * 0.2
        )

    def _reposition_to_target_block(self, target_block_number: int):
        """Instantly reposition blocks to show target block range."""
        # Clear current visible blocks
        self._clear_current_blocks()

        # Calculate which blocks should be visible around target
        center_block = target_block_number
        visible_range = range(
            max(0, center_block - 1),
            min(center_block + self.MAX_VISIBLE_BLOCKS - 1, target_block_number + 10)
        )

        # Position new blocks
        for i, block_num in enumerate(visible_range):
            if i < len(self.blocks):
                self._setup_block_for_position(i, block_num, i - 1)  # Center the target block
                self.visible_blocks.add(i)

                # Position mini blocks around target
        self._reposition_mini_blocks_for_target(target_block_number)

    def _clear_current_blocks(self):
        """Remove all currently visible blocks from scene."""
        for block_idx in list(self.visible_blocks):
            self.remove(self.blocks[block_idx], self.block_labels[block_idx])

        for mini_idx in list(self.mini_visible_blocks):
            self.remove(self.mini_blocks[mini_idx], self.mini_labels[mini_idx])

        self.visible_blocks.clear()
        self.mini_visible_blocks.clear()

    def _setup_block_for_position(self, block_idx: int, block_number: int, position_offset: int):
        """Setup a block at a specific position with correct numbering."""
        # Position block
        x_position = position_offset * self.BLOCK_SPACING
        self.blocks[block_idx].move_to(np.array([x_position, -0.75, 0]))

        # Update label
        label_text = "Genesis" if block_number == 0 else f"Block {block_number}"
        self.block_labels[block_idx].become(Text(label_text, font_size=24))
        self.block_labels[block_idx].move_to(
            self.blocks[block_idx].get_top() + UP * 0.3
        )

        # Add to scene
        self.add(self.blocks[block_idx], self.block_labels[block_idx])

    def _reposition_mini_blocks_for_target(self, target_block_number: int):
        """Reposition mini blocks to show range around target, maintaining visibility."""
        # Clear current mini block tracking but don't remove from scene yet
        old_visible = self.mini_visible_blocks.copy()
        self.mini_visible_blocks.clear()

        # Calculate the range of blocks to show (±15 around target)
        start_block = max(0, target_block_number - 15)
        end_block = min(target_block_number + 15, self.total_blocks_created)

        # Position mini blocks for the visible range
        for i, block_num in enumerate(range(start_block, end_block + 1)):
            if i < len(self.mini_blocks):
                # Position mini block relative to frame center
                x_offset = (block_num - target_block_number) * self.MINI_BLOCK_SPACING
                x_pos = self.mini_chain_frame.get_center()[0] + x_offset

                self.mini_blocks[i].move_to(np.array([
                    x_pos,
                    self.mini_chain_frame.get_center()[1],
                    0
                ]))

                # Update label based on block number
                if block_num == 0:
                    label_text = "G"  # Genesis
                else:
                    label_text = str(block_num)

                self.mini_labels[i].become(Text(label_text, font_size=6, color=WHITE))
                self.mini_labels[i].move_to(self.mini_blocks[i].get_center())

                # Add to scene and tracking
                self.add(self.mini_blocks[i], self.mini_labels[i])
                self.mini_visible_blocks.add(i)

                # Remove any old mini blocks that are no longer needed
        for old_idx in old_visible:
            if old_idx not in self.mini_visible_blocks and old_idx < len(self.mini_blocks):
                self.remove(self.mini_blocks[old_idx], self.mini_labels[old_idx])

    def _update_tracking_for_target(self, target_block_number: int):
        """Update tracking variables after fast scroll."""
        self.next_block_number = target_block_number + 1
        # Don't reset total_blocks_created - it should reflect the maximum reached
        self.total_blocks_created = max(self.total_blocks_created, target_block_number + 1)

    def _scroll_left(self):
        """Perform left scrolling animation."""
        # Find available indices
        rightmost_block_idx = self._find_next_available_block()
        rightmost_mini_idx = self._find_next_available_mini_block()

        if rightmost_block_idx is None or rightmost_mini_idx is None:
            return

            # Position new elements
        self._position_new_block(rightmost_block_idx)
        self._position_new_mini_block(rightmost_mini_idx)

        # Create and play animations
        create_animations = self._create_block_animations(rightmost_block_idx, rightmost_mini_idx)
        fade_animations = self._create_fade_animations()

        all_animations = create_animations + fade_animations
        self.play(*all_animations, run_time=1)

        # Update tracking
        self._update_tracking(rightmost_block_idx, rightmost_mini_idx)

        # Shift remaining blocks
        self._shift_all_blocks_left()

    def _find_next_available_block(self) -> int | None:
        """Find the next available block index."""
        for i in range(4):
            if i not in self.visible_blocks:
                return i
        return None

    def _find_next_available_mini_block(self) -> int | None:
        """Find the next available mini block index."""
        for i in range(len(self.mini_blocks)):  # Use actual length instead of hardcoded 20
            if i not in self.mini_visible_blocks:
                return i
        return None

    def _position_new_block(self, block_idx: int):
        """Position a new block next to the rightmost visible block."""
        if not self.visible_blocks:
            # If no blocks are visible, start from center
            rightmost_pos = 0
        else:
            rightmost_pos = max([self.blocks[i].get_center()[0] for i in self.visible_blocks])

        final_position = np.array([rightmost_pos + self.BLOCK_SPACING, -0.75, 0])

        self.blocks[block_idx].move_to(final_position)

        # Update label
        self.block_labels[block_idx].become(
            Text(f"Block {self.next_block_number}", font_size=24)
        )
        self.block_labels[block_idx].move_to(
            self.blocks[block_idx].get_top() + UP * 0.3
        )

    def _position_new_mini_block(self, mini_idx: int):
        """Position a new mini block next to the rightmost visible mini block."""
        if not self.mini_visible_blocks:
            # If no mini blocks are visible, start from the frame center
            rightmost_mini_pos = self.mini_chain_frame.get_center()[0]
        else:
            rightmost_mini_pos = max([
                self.mini_blocks[i].get_center()[0] for i in self.mini_visible_blocks
            ])

        final_position = np.array([
            rightmost_mini_pos + self.MINI_BLOCK_SPACING,
            self.mini_chain_frame.get_center()[1],
            0
        ])

        self.mini_blocks[mini_idx].move_to(final_position)

        # Update label
        self.mini_labels[mini_idx].become(
            Text(f"{self.next_block_number}", font_size=6)
        )
        self.mini_labels[mini_idx].move_to(self.mini_blocks[mini_idx].get_center())

    def _create_block_animations(self, block_idx: int, mini_idx: int) -> list:
        """Create animations for new blocks appearing."""
        self.add(self.blocks[block_idx], self.block_labels[block_idx])
        self.add(self.mini_blocks[mini_idx], self.mini_labels[mini_idx])

        return [
            Create(self.blocks[block_idx]),
            Write(self.block_labels[block_idx]),
            Create(self.mini_blocks[mini_idx]),
            Write(self.mini_labels[mini_idx])
        ]

    def _create_fade_animations(self) -> list:
        """Create fade animations for blocks that should disappear."""
        fade_animations = []

        # Fade main blocks if too many visible
        if len(self.visible_blocks) >= self.MAX_VISIBLE_BLOCKS:
            leftmost_idx = min(self.visible_blocks, key=lambda i: self.blocks[i].get_center()[0])
            fade_animations.extend([
                FadeOut(self.blocks[leftmost_idx]),
                FadeOut(self.block_labels[leftmost_idx])
            ])
            self.visible_blocks.remove(leftmost_idx)

            # Fade mini blocks based on pruning rule - WITH SAFETY CHECK
        if self.total_blocks_created >= self.PRUNING_THRESHOLD and self.mini_visible_blocks:
            leftmost_mini_idx = min(
                self.mini_visible_blocks,
                key=lambda i: self.mini_blocks[i].get_center()[0]
            )
            fade_animations.extend([
                FadeOut(self.mini_blocks[leftmost_mini_idx]),
                FadeOut(self.mini_labels[leftmost_mini_idx])
            ])
            self.mini_visible_blocks.remove(leftmost_mini_idx)

        return fade_animations

    def _update_tracking(self, block_idx: int, mini_idx: int):
        """Update tracking variables after adding new blocks."""
        self.visible_blocks.add(block_idx)
        self.mini_visible_blocks.add(mini_idx)
        self.next_block_number += 1
        self.total_blocks_created += 1

    def _shift_all_blocks_left(self):
        """Shift all visible blocks to the left."""
        shift_animations = []

        # Shift main blocks
        for i in self.visible_blocks:
            shift_animations.extend([
                self.blocks[i].animate.shift(LEFT * self.BLOCK_SPACING),
                self.block_labels[i].animate.shift(LEFT * self.BLOCK_SPACING)
            ])

            # Shift mini blocks
        for i in self.mini_visible_blocks:
            shift_animations.extend([
                self.mini_blocks[i].animate.shift(LEFT * self.MINI_BLOCK_SPACING),
                self.mini_labels[i].animate.shift(LEFT * self.MINI_BLOCK_SPACING)
            ])

        self.play(*shift_animations, run_time=1)

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


class TransactionSelection(Scene):
    def construct(self):
        # Create narration text at the top
        narration = Text("Kaspa Transaction Selection", font_size=36, color=WHITE)
        narration.to_edge(UP)

        # Create Round container (left side)
        round_container = Square(
            side_length=4,
            color=WHITE,
            fill_opacity=0,
            stroke_width=3
        )
        round_container.shift(LEFT * 3 + DOWN * 0.75)

        # Create Transaction Pool container (right side)
        tx_pool_container = Square(
            side_length=4,
            color=WHITE,
            fill_opacity=0,
            stroke_width=3
        )
        tx_pool_container.shift(RIGHT * 3 + DOWN * 0.75)

        # Create individual transaction containers inside the pool
        tx1_container = Rectangle(
            width=3.0,
            height=1.2,
            color="#B6B6B6",
            fill_opacity=0.1,
            stroke_width=2
        )
        tx1_container.move_to(tx_pool_container.get_center() + UP * 0.8)

        tx2_container = Rectangle(
            width=3.0,
            height=1.2,
            color="#70C7BA",
            fill_opacity=0.1,
            stroke_width=2
        )
        tx2_container.move_to(tx_pool_container.get_center() + DOWN * 0.8)

        # Create labels
        round_label = Text("Round", font_size=24).move_to(round_container.get_top() + UP * 0.3)
        tx_pool_label = Text("Transaction Pool", font_size=24).move_to(tx_pool_container.get_top() + UP * 0.3)

        tx1_label = Text("tx1 1 KAS", font_size=18, color=WHITE).move_to(tx1_container.get_center())
        tx2_label = Text("tx2 1.1 KAS", font_size=18, color=WHITE).move_to(tx2_container.get_center())

        self.wait(3)
        # Start with narration
        self.play(Write(narration))
        self.wait(1)

        # Animate creation of containers
        self.play(
            Create(round_container),
            Create(tx_pool_container)
        )
        self.play(
            Write(round_label),
            Write(tx_pool_label)
        )

        # Animate transaction containers appearing
        self.play(
            Create(tx1_container),
            Create(tx2_container)
        )
        self.play(
            Write(tx1_label),
            Write(tx2_label)
        )
        self.wait(2)

        # Create sub-narration text - positioned below the main title
        sub_narration = Text("When selecting highest paying", font_size=24, color=WHITE)
        sub_narration.next_to(narration, DOWN, buff=0.5)

        # Show sub-narration and highlight tx2 container
        self.play(Write(sub_narration))
        self.play(Indicate(tx2_container))
        self.wait(0.5)

        # Create two square blocks in the round container
        block1 = Square(
            side_length=1.5,
            color="#70C7BA",
            fill_opacity=0.2,
            stroke_width=2
        )
        block1.move_to(round_container.get_center() + UP * 0.90)

        block2 = Square(
            side_length=1.5,
            color="#70C7BA",
            fill_opacity=0.2,
            stroke_width=2
        )
        block2.move_to(round_container.get_center() + DOWN * 0.90)

        # Add tx2 labels to both blocks
        block1_label = Text("tx2", font_size=16, color=WHITE).move_to(block1.get_center())
        block2_label = Text("tx2", font_size=16, color=WHITE).move_to(block2.get_center())

        # Animate creation of blocks
        self.play(
            Create(block1),
            Create(block2)
        )
        self.play(
            Write(block1_label),
            Write(block2_label)
        )
        self.wait(1)

        # Transform sub-narration to "only 1 miner is paid"
        new_sub_narration = Text("only 1 miner is paid", font_size=24, color=WHITE)
        new_sub_narration.next_to(narration, DOWN, buff=0.5)
        self.play(Transform(sub_narration, new_sub_narration))
        self.wait(1)

        # Fade out everything in the round container and sub-narration
        self.play(
            FadeOut(block1),
            FadeOut(block2),
            FadeOut(block1_label),
            FadeOut(block2_label),
            FadeOut(sub_narration)
        )
        self.wait(0.5)

        # Create new sub-narration for random selection
        random_sub_narration = Text("When random selecting", font_size=24, color=WHITE)
        random_sub_narration.next_to(narration, DOWN, buff=0.5)

        # Create new squares with tx1 and tx2 - equally spaced
        new_block1 = Square(
            side_length=1.5,
            color="#B6B6B6",
            fill_opacity=0.2,
            stroke_width=2
        )
        new_block1.move_to(round_container.get_center() + UP * 0.90)

        new_block2 = Square(
            side_length=1.5,
            color="#70C7BA",
            fill_opacity=0.2,
            stroke_width=2
        )
        new_block2.move_to(round_container.get_center() + DOWN * 0.90)

        new_block1_label = Text("tx1", font_size=16, color=WHITE).move_to(new_block1.get_center())
        new_block2_label = Text("tx2", font_size=16, color=WHITE).move_to(new_block2.get_center())

        # Show random selection sub-narration and animate creation of new blocks
        self.play(Write(random_sub_narration))
        self.play(
            Create(new_block1),
            Create(new_block2)
        )
        self.play(
            Write(new_block1_label),
            Write(new_block2_label)
        )
        self.wait(1)

        # Transform to final sub-narration
        final_sub_narration = Text("50% chance of both miners getting paid", font_size=24, color=WHITE)
        final_sub_narration.next_to(narration, DOWN, buff=0.5)
        self.play(Transform(random_sub_narration, final_sub_narration))
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


class WeightedLotteryBlocks(Scene):
    def construct(self):
        # Define fee rates and total blocks
        feerate_a = 4.1
        feerate_b = 3.1
        total_blocks = 20

        # Calculate weights by cubing the fee rates
        weight_a_raw = feerate_a ** 3
        weight_b_raw = feerate_b ** 3
        total_weight = weight_a_raw + weight_b_raw

        # Normalize to get proportions
        weight_a = weight_a_raw / total_weight
        weight_b = weight_b_raw / total_weight

        # Calculate number of each type
        num_a = int(total_blocks * weight_a)
        num_b = total_blocks - num_a

        # Create individual blocks with their labels stored together
        block_data = []
        blocks = VGroup()

        # Create A blocks
        for i in range(num_a):
            block = Square(side_length=0.5, fill_opacity=0.8, color=BLUE)
            label = Text("A", font_size=24, color=WHITE)
            labeled_block = VGroup(block, label)
            blocks.add(labeled_block)
            block_data.append("A")

            # Create B blocks
        for i in range(num_b):
            block = Square(side_length=0.5, fill_opacity=0.8, color=RED)
            label = Text("B", font_size=24, color=WHITE)
            labeled_block = VGroup(block, label)
            blocks.add(labeled_block)
            block_data.append("B")

            # Shuffle blocks and their corresponding labels together
        combined = list(zip(blocks.submobjects, block_data))
        random.shuffle(combined)
        shuffled_blocks, shuffled_labels = zip(*combined)

        # Recreate the VGroup with shuffled blocks
        blocks = VGroup(*shuffled_blocks)
        block_labels = list(shuffled_labels)

        # Arrange blocks in a grid with more spacing
        blocks.arrange_in_grid(rows=4, cols=5, buff=0.3)

        # Move the blocks lower in the scene
        blocks.shift(DOWN * 0.5)

        # Create larger container
        container_width = blocks.width + 2
        container_height = blocks.height + 1.5
        container = Rectangle(
            width=container_width,
            height=container_height,
            color=WHITE,
            stroke_width=4,
            fill_opacity=0.1,
            fill_color=GRAY
        )
        container.move_to(blocks.get_center())

        # Add title
        title = Text("Kaspa Transaction Selection", font_size=40)
        title.to_edge(UP, buff=0.3)

        # Add weight information showing fee rates and resulting percentages
        weight_info = Text(
            f"A: feerate {feerate_a}\n"
            f"B: feerate {feerate_b}",
            font_size=24
        )
        weight_info.next_to(title, DOWN, buff=0.2)

        # Show the setup
        self.play(Write(title))
        self.play(Write(weight_info))
        self.play(Create(container))
        self.play(LaggedStart(*[FadeIn(block) for block in blocks], lag_ratio=0.1))
        self.wait(2)


class StaticWeightedLotteryBlocks(Scene):
    def show_fee_rate_scenario(self, feerate_a, feerate_b, title_suffix=""):
        """Create and display blocks for given fee rates"""
        total_blocks = 20

        # Calculate weights by cubing the fee rates
        weight_a_raw = feerate_a ** 3
        weight_b_raw = feerate_b ** 3
        total_weight = weight_a_raw + weight_b_raw

        # Normalize to get proportions
        weight_a = weight_a_raw / total_weight
        weight_b = weight_b_raw / total_weight

        # Calculate number of each type
        num_a = int(total_blocks * weight_a)
        num_b = total_blocks - num_a

        # Create individual blocks
        blocks = VGroup()

        # Create A blocks
        for i in range(num_a):
            block = Square(side_length=0.5, fill_opacity=0.8, color=BLUE)
            label = Text("A", font_size=24, color=WHITE)
            labeled_block = VGroup(block, label)
            blocks.add(labeled_block)

            # Create B blocks
        for i in range(num_b):
            block = Square(side_length=0.5, fill_opacity=0.8, color=RED)
            label = Text("B", font_size=24, color=WHITE)
            labeled_block = VGroup(block, label)
            blocks.add(labeled_block)

            # Shuffle blocks for random arrangement
        random.shuffle(blocks.submobjects)

        # Arrange blocks in a grid
        blocks.arrange_in_grid(rows=4, cols=5, buff=0.3)
        blocks.shift(DOWN * 0.5)

        # Create container
        container_width = blocks.width + 2
        container_height = blocks.height + 1.5
        container = Rectangle(
            width=container_width,
            height=container_height,
            color=WHITE,
            stroke_width=4,
            fill_opacity=0.1,
            fill_color=GRAY
        )
        container.move_to(blocks.get_center())

        # Create title and info
        title = Text(f"Fee Rate Scenario{title_suffix}", font_size=40)
        title.to_edge(UP, buff=0.3)

        weight_info = Text(
            f"A: feerate {feerate_a} → weight {weight_a_raw:.1f} → {num_a} blocks ({weight_a * 100:.0f}%)\n"
            f"B: feerate {feerate_b} → weight {weight_b_raw:.1f} → {num_b} blocks ({weight_b * 100:.0f}%)",
            font_size=24
        )
        weight_info.next_to(title, DOWN, buff=0.2)

        return VGroup(title, weight_info, container, blocks)

    def construct(self):
        # Show first scenario
        scenario1 = self.show_fee_rate_scenario(4.1, 3.1, " 1")
        self.play(FadeIn(scenario1))
        self.wait(2)

        # Clear and show second scenario
        self.play(FadeOut(scenario1))
        scenario2 = self.show_fee_rate_scenario(5.0, 2.5, " 2")
        self.play(FadeIn(scenario2))
        self.wait(2)

        # Clear and show third scenario
        self.play(FadeOut(scenario2))
        scenario3 = self.show_fee_rate_scenario(3.5, 4.0, " 3")
        self.play(FadeIn(scenario3))
        self.wait(2)

# TODO save this one and reuse for showing sliding comparison of feerates
class DynamicWeightedLotteryBlocks(Scene):
    def construct(self):
        # Create ValueTrackers for fee rates
        feerate_a_tracker = ValueTracker(4.1)
        feerate_b_tracker = ValueTracker(3.1)
        total_blocks = 20

        # Function to create blocks based on current fee rates
        def create_blocks():
            feerate_a = feerate_a_tracker.get_value()
            feerate_b = feerate_b_tracker.get_value()

            # Calculate weights by cubing the fee rates
            weight_a_raw = feerate_a ** 3
            weight_b_raw = feerate_b ** 3
            total_weight = weight_a_raw + weight_b_raw

            # Normalize to get proportions
            weight_a = weight_a_raw / total_weight
            weight_b = weight_b_raw / total_weight

            # Calculate number of each type
            num_a = int(total_blocks * weight_a)
            num_b = total_blocks - num_a

            # Create individual blocks
            block_data = []
            blocks = VGroup()

            # Create A blocks
            for i in range(num_a):
                block = Square(side_length=0.5, fill_opacity=0.8, color=BLUE)
                label = Text("A", font_size=24, color=WHITE)
                labeled_block = VGroup(block, label)
                blocks.add(labeled_block)
                block_data.append("A")

                # Create B blocks
            for i in range(num_b):
                block = Square(side_length=0.5, fill_opacity=0.8, color=RED)
                label = Text("B", font_size=24, color=WHITE)
                labeled_block = VGroup(block, label)
                blocks.add(labeled_block)
                block_data.append("B")

                # Shuffle blocks for random arrangement
            combined = list(zip(blocks.submobjects, block_data))
            random.shuffle(combined)
            shuffled_blocks, shuffled_labels = zip(*combined)

            # Recreate the VGroup with shuffled blocks
            blocks = VGroup(*shuffled_blocks)

            # Arrange blocks in a grid with spacing
            blocks.arrange_in_grid(rows=4, cols=5, buff=0.3)
            blocks.shift(DOWN * 0.5)

            return blocks, weight_a, weight_b, weight_a_raw, weight_b_raw, num_a, num_b

            # Create dynamic blocks using always_redraw

        dynamic_blocks = always_redraw(lambda: create_blocks()[0])

        # Create dynamic container
        def create_container():
            blocks, _, _, _, _, _, _ = create_blocks()
            container_width = blocks.width + 2
            container_height = blocks.height + 1.5
            container = Rectangle(
                width=container_width,
                height=container_height,
                color=WHITE,
                stroke_width=4,
                fill_opacity=0.1,
                fill_color=GRAY
            )
            container.move_to(blocks.get_center())
            return container

        dynamic_container = always_redraw(create_container)

        # Create dynamic weight information
        def create_weight_info():
            feerate_a = feerate_a_tracker.get_value()
            feerate_b = feerate_b_tracker.get_value()
            _, weight_a, weight_b, weight_a_raw, weight_b_raw, num_a, num_b = create_blocks()

            weight_info = Text(
                f"A: feerate {feerate_a:.1f} → weight {weight_a_raw:.1f} → {num_a} blocks ({weight_a * 100:.0f}%)\n"
                f"B: feerate {feerate_b:.1f} → weight {weight_b_raw:.1f} → {num_b} blocks ({weight_b * 100:.0f}%)",
                font_size=24
            )
            weight_info.to_edge(UP, buff=1.0)
            return weight_info

        dynamic_weight_info = always_redraw(create_weight_info)

        # Add title
        title = Text("Dynamic Kaspa Transaction Selection", font_size=40)
        title.to_edge(UP, buff=0.3)

        # Add everything to scene
        self.add(feerate_a_tracker, feerate_b_tracker)  # Add trackers to scene
        self.play(Write(title))
        self.play(Write(dynamic_weight_info))
        self.play(Create(dynamic_container))
        self.play(FadeIn(dynamic_blocks))
        self.wait(1)

        # Demonstrate dynamic changes
        self.play(feerate_a_tracker.animate.set_value(5.0), run_time=2)
        self.wait(1)
        self.play(feerate_b_tracker.animate.set_value(2.5), run_time=2)
        self.wait(1)
        self.play(
            feerate_a_tracker.animate.set_value(3.5),
            feerate_b_tracker.animate.set_value(4.0),
            run_time=3
        )
        self.wait(2)


class PersistentWeightedLotteryBlocks(Scene):
    def show_scenario_blocks_only(self, feerate_a, feerate_b):
        """Create only the blocks for given fee rates"""
        total_blocks = 20

        # Calculate weights by cubing the fee rates
        weight_a_raw = feerate_a ** 3
        weight_b_raw = feerate_b ** 3
        total_weight = weight_a_raw + weight_b_raw

        # Normalize to get proportions
        weight_a = weight_a_raw / total_weight
        weight_b = weight_b_raw / total_weight

        # Calculate number of each type
        num_a = int(total_blocks * weight_a)
        num_b = total_blocks - num_a

        # Create individual blocks
        blocks = VGroup()

        # Create A blocks
        for i in range(num_a):
            block = Square(side_length=0.5, fill_opacity=0.5, color="#70C7BA", stroke_color=WHITE, stroke_width=2)
            label = Text("A", font_size=24, color=WHITE)
            labeled_block = VGroup(block, label)
            blocks.add(labeled_block)

            # Create B blocks
        for i in range(num_b):
            block = Square(side_length=0.5, fill_opacity=0.5, color="#B6B6B6", stroke_color=WHITE, stroke_width=2)
            label = Text("B", font_size=24, color=WHITE)
            labeled_block = VGroup(block, label)
            blocks.add(labeled_block)

            # Shuffle blocks for random arrangement
        random.shuffle(blocks.submobjects)

        # Arrange blocks in a grid with spacing
        blocks.arrange_in_grid(rows=4, cols=5, buff=0.3)
        blocks.shift(DOWN * 0.5)

        return blocks, num_a, num_b, weight_a, weight_b

    def construct(self):
        # Create persistent elements once
        title = Text("Kaspa Transaction Selection", font_size=40)
        title.to_edge(UP, buff=0.3)

        # Create persistent container (sized for the grid)
        container_width = 6  # Fixed size based on typical grid
        container_height = 4
        container = Rectangle(
            width=container_width,
            height=container_height,
            color=WHITE,
            stroke_width=4,
            fill_opacity=0.1,
            fill_color=GRAY
        )
        container.shift(DOWN * 0.5)

        # Show persistent elements
        self.wait(3)
        self.play(Write(title))
        self.play(Create(container))
        self.wait(1)

        # Scenario 1: Fee rates 4.1 and 3.1
        feerate_a, feerate_b = 1, 1
        blocks1, num_a1, num_b1, weight_a1, weight_b1 = self.show_scenario_blocks_only(feerate_a, feerate_b)

        # Create weight info for scenario 1
        weight_info = Text(
            f"A: feerate {feerate_a} → {num_a1} blocks ({weight_a1 * 100:.0f}%)\n"
            f"B: feerate {feerate_b} → {num_b1} blocks ({weight_b1 * 100:.0f}%)",
            font_size=24
        )
        weight_info.next_to(title, DOWN, buff=0.2)

        self.play(Write(weight_info, run_time=3.0))
        self.play(LaggedStart(*[FadeIn(block) for block in blocks1], lag_ratio=0.1))
        self.wait(2)

        # Scenario 2: Fee rates 5.0 and 2.5
        feerate_a, feerate_b = 1, 2
        blocks2, num_a2, num_b2, weight_a2, weight_b2 = self.show_scenario_blocks_only(feerate_a, feerate_b)

        # Update weight info for scenario 2
        new_weight_info = Text(
            f"A: feerate {feerate_a} → {num_a2} blocks ({weight_a2 * 100:.0f}%)\n"
            f"B: feerate {feerate_b} → {num_b2} blocks ({weight_b2 * 100:.0f}%)",
            font_size=24
        )
        new_weight_info.next_to(title, DOWN, buff=0.2)

        # Transition: remove old blocks and weight info, add new ones
        self.play(
            FadeOut(blocks1),
            Transform(weight_info, new_weight_info, run_time=3.0)
        )
        self.play(LaggedStart(*[FadeIn(block) for block in blocks2], lag_ratio=0.1))
        self.wait(2)

        # Scenario 3: Fee rates 3.5 and 4.0
        feerate_a, feerate_b = 1, 0.5
        blocks3, num_a3, num_b3, weight_a3, weight_b3 = self.show_scenario_blocks_only(feerate_a, feerate_b)

        # Update weight info for scenario 3
        new_weight_info2 = Text(
            f"A: feerate {feerate_a} → {num_a3} blocks ({weight_a3 * 100:.0f}%)\n"
            f"B: feerate {feerate_b} → {num_b3} blocks ({weight_b3 * 100:.0f}%)",
            font_size=24
        )
        new_weight_info2.next_to(title, DOWN, buff=0.2)

        # Transition: remove old blocks and update weight info
        self.play(
            FadeOut(blocks2),
            Transform(weight_info, new_weight_info2, run_time=3.0)
        )
        self.play(LaggedStart(*[FadeIn(block) for block in blocks3], lag_ratio=0.1))
        self.wait(8)