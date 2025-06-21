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
    GD_K = 1

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
