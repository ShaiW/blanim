from blanim import *
from random import randint

class Test(Scene):
    def construct(self):
        BD = BlockDAG()
        self.play(BD.add("Gen", [0,0], label="G"),
                  BD.add("X", [1,0], label="G", parents=[Parent("Gen")]))
        self.play(
                BD.add("Y",[3,3],label=":)", parents=["Gen", Parent("X", color=WHITE)]),
                BD.add("Z",[3,2],parents=["Y"])
            )
        self.play(BD.shift("Y",[0,-6]))
        self.play(BD.shift("Y",[-6,0]))
        self.wait(1)

class TestLayer(Scene):
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
    BLOCKS = 30
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