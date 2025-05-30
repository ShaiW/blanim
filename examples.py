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
        block = BlockMob("Gen", label="label test")
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
        block = BlockMob("Gen", label="label test")
        self.add(block)
        self.wait(1)
        self.play(block.animate(runtime = 1).shift(UP * 2))
        block.set_label("success")
        self.wait(1)
        self.play(block.animate(runtime = 1).shift(DOWN * 2))
        block.set_blue()
        self.wait(1)

class TestBlockMobChain(Scene):
    def construct(self):
        BMC = BlockMobChain(4)
        self.play(BMC.draw_chain())
        self.play(BMC.create_fork(2))
        self.play(BMC.shift_forks())
        self.wait(1)