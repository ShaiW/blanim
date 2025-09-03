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


class SMBTC_testing(MovingCameraFixedLayerScene):
    def construct(self):
        sm = SelfishMining()

        self.wait(1)

        self.play(sm.intro_anim())

        self.wait(1.0)

        self.play(sm.zero_to_zero())

        self.wait(2)


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