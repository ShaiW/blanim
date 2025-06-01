from random import random, choice, randint
from typing import Self, Dict, List
from manim import *
from itertools import chain
from numpy import array
from typing_extensions import runtime

from common import *
import string
import math

BLOCK_H = 0.4
BLOCK_W = 0.4
GENESIS_POSITION = [-5,0,0]
BLOCK_SPACING_H = 1.3
BLOCK_SPACING_W = 2
DAG_WIDTH = 5
NOISE_H = 0.3
NOISE_W = 0.5

DEF_RATE_FUNC = smooth
DEF_RUN_TIME = 0.5

PROMPT_DELAY = 2

def safe_play(scene, anims):
    if anims:
        scene.play(anims)

class Parent():
    def __init__(self, name, **kwargs):
        self.name = name
        self.kwargs = kwargs

class Block():

    parents: list[Self]
    children: list[Self]
    rect: Rectangle
    label: Tex
    
    def __init__(self, name, DAG, parents, pos, label = None, color  = BLUE, h = BLOCK_H, w = BLOCK_W):

        self.name = name
        self.w = w
        self.h = h
        self.DAG = DAG
        self.parents = [DAG.blocks[p.name] for p in parents]
        self.children = []
        self.rect = Rectangle(
            color      = color, 
            fill_opacity    = 1, 
            height          = h,
            width           = w,
        )
        self.rect.move_to(pos)
        if label:
            self.label = Tex(label if label else name).set_z_index(1).scale(0.7)
            self.label.add_updater(lambda l: l.move_to(self.rect.get_center()), call_updater=True)
        else:
            self.label = None

        for p in parents:
            DAG.blocks[p.name].children.append(self.name)


    def is_tip(self):
        return bool(self.children)
class BlockDAG():

    blocks: Dict[str, Block]
    history: List[str]
    block_color : ManimColor
    block_w: float
    block_h: float

    def __init__(self, history_size = 20, block_color = BLUE, block_w=BLOCK_W, block_h=BLOCK_H):
        self.blocks = {}
        self.history = []
        self.history_size = history_size
        self.block_color = block_color
        self.block_h = block_h
        self.block_w = block_w

    ## construction

    def add(self, name, pos, parents = [], **kwargs):
        #label = None, color=block_color, w=BLOCK_W, h=BLOCK_H
        kwargs.setdefault("label",None)
        kwargs.setdefault("color",self.block_color)
        kwargs.setdefault("w",self.block_w)
        kwargs.setdefault("h",self.block_h)

        anims = []
        pos = pos+[0]

        assert(not name in self.blocks)
        
        parents = list(map(lambda p: Parent(p) if type(p) is str else p, parents))

        B = Block(name, self, parents, pos, **kwargs)

        anims = [FadeIn(B.rect)] + \
                ([FadeIn(B.label)] if B.label else []) + \
                [self.add_arrow(B,self.blocks[p.name],**p.kwargs) for p in parents]
        
        self.blocks[name] = B

        self.history.insert(0,self._get_tips())
        if len(self.history)  > self.history_size:
            self.history.pop()

        return anims

    def random_block(self):
        return choice(list(self.blocks.keys()))

    def add_arrow(self, f :Block, t :Block, **kwargs):

        # For some reason ArrowUpdater gets crazy if you add it before initing the arrow
        # This hack solves it
        class GrowArrowUpdater(GrowArrow):

            def __init__(self, a, u, **kwargs):
                super().__init__(a, **kwargs)
                self.a = a
                self.u = u

            def __del__(self):
                self.a.add_updater(self.u)

        kwargs.setdefault("buff",0)
        kwargs.setdefault("stroke_width",2)
        kwargs.setdefault("tip_shape",StealthTip)
        kwargs.setdefault("max_tip_length_to_length_ratio",0.04)
        kwargs.setdefault("color",WHITE)
        a = Arrow(**kwargs)
        # if "z_index" in kwargs:
        #     a.set_z_index(kwargs["z_index"])
        
        def get_start_end():
            fl = f.rect.get_left()[0]
            fr = f.rect.get_right()[0]
            tl = t.rect.get_left()[0]
            tr = t.rect.get_right()[0]
            ft = f.rect.get_top()[1]
            fb = f.rect.get_bottom()[1]
            tt = t.rect.get_top()[1]
            tb = t.rect.get_bottom()[1]
            s = f.rect.get_left()
            e = t.rect.get_right()
            if tr - fl > 0:
                s = f.rect.get_right()
                e = t.rect.get_left()
            if max(tr-fl,fr-tl) < max(tb-ft,fb-tt):
                if tb-ft > fb-tt:
                    s = f.rect.get_top()
                    e = t.rect.get_bottom()
                else:
                    s = f.rect.get_bottom()
                    e = t.rect.get_top()
            return {"start":s, "end":e}

        a.put_start_and_end_on(**get_start_end())
        return GrowArrowUpdater(a,lambda a: a.put_start_and_end_on(**get_start_end()))
    
    ## combinatorics

    def get_future(self, B):
        f = []

        def _calc_future(A):
            if not (A in f):
                f.append(A)
                [_calc_future(C) for C in self.blocks[A].children]

        _calc_future(B)

        return f
        


    def get_tips(self, missed_blocks = 0):
        return self.history[min(missed_blocks,len(self.history)-1)]

    def _get_tips(self):
        tips = list(filter(lambda x: not self.blocks[x].is_tip(), self.blocks.keys()))
        return tips
    
    ## transformations

    def shift(self, name, offset, rate_func=DEF_RATE_FUNC, run_time=DEF_RUN_TIME):
        rects = self._name_to_rect(name)
        return Transform(rects, rects.copy().shift(offset + [0]), rate_func=rate_func, run_time=run_time)
    
    def change_color(self, blocks: str | list[str], color):
        if type(blocks) is str:
            blocks = [blocks]
        return [FadeToColor(rect, color=color) for rect in self._name_to_rect(blocks)]

    ## gestures
    def blink(self, B):
        if type(B) is str:    
            rect = self._name_to_rect(B)
            rect_color = rect.color
            return Succession(FadeToColor(rect, color=YELLOW, run_time=0.2),FadeToColor(rect, color=rect_color))
        return [self.blink(b) for b in B]

    
    ## utility
    
    def _name_to_rect(self, name : str | list[str]):
        return self.blocks[name].rect if type(name) is str else VGroup(*[self.blocks[b].rect for b in name])
    
    
class LayerDAG(BlockDAG):

    layers : List[List[str]]

    ## Automagically orders DAGs into layers
    ##
    def __init__(self, layer_spacing = 1.5, chain_spacing = 1, gen_pos = [-6.5,0], width=4, block_spacing = 1, *args, **kwargs):
        super().__init__(*args,**kwargs)
        self.init_animation = super().add("Gen", gen_pos)[0]
        self.layers = [["Gen"]]
        self.layer_spacing = layer_spacing
        self.chain_spacing = chain_spacing
        self.gen_pos = gen_pos
        self.block_spacing = block_spacing
        self.width = width

    def add(self, name, parent_names, selected_parent=None, random_sp = False, *args, **kwargs):
        layer = 0
        top_parent_layer = 0
        if type(parent_names) is str:
            parent_names = [parent_names]
        for i in range(len(self.layers)):
            if any(b in self.layers[i] for b in parent_names):
                top_parent_layer = i
        for i in range(top_parent_layer+1,len(self.layers)):
            if len(self.layers[i]) < self.width - ((i+1)%2):
                layer = i
                break
        if layer <= top_parent_layer: #all layers above top parent are full
            layer = len(self.layers)
        layer_top = -self.chain_spacing
        if layer == len(self.layers):
            self.layers.append([name])
        else:
            layer_top = self.blocks[self.layers[layer][-1]].rect.get_center()[1]
            self.layers[layer].append(name)
        pos = [layer*self.layer_spacing+self.gen_pos[0],layer_top+self.chain_spacing]
        if random_sp:
            selected_parent = choice(parent_names)
        parents = [Parent(p,color=BLUE,stroke_width=3,z_index=-1) if p == selected_parent else Parent(p,z_index=-2) for p in parent_names]
        return super().add(name, pos, parents=parents, *args, **kwargs)
    
    def adjust_layer(self,layer):
        if layer >= len(self.layers): #empty layer
            return None
        top = self.blocks[self.layers[layer][-1]].rect.get_center()[1]
        bot = self.blocks[self.layers[layer][0]].rect.get_center()[1]
        shift = abs(top-bot)/2 - top
        if shift == 0:
            return None #layer already adjusted
        return [self.shift(b,[0,shift]) for b in self.layers[layer]]

    def adjust_layers(self, chained=True):
        shifts = list(filter(None,[self.adjust_layer(layer) for layer in range(len(self.layers))]))
        return list(chain(*shifts)) if chained else shifts

class Miner():
    def __init__(self, scene, x=0 , y=0, attempts = 20):
        self.scene = scene
        self.x = x
        self.y = y
        self.attempts = attempts
        self.nonce = randint(10000,99000)
        self.parts = {}
        self.rect = Rectangle(
            color=RED,
            fill_opacity=1,
            height = 2,
            width = 3
        )
        self.rect.move_to([x,y,0])
        self.lpar = Tex(r"(",font_size = 220)
        self.lpar.move_to([x-1.8,y,0])
        self.rpar = Tex(r")",font_size = 220)
        self.rpar.move_to([x+1.8,y,0])
        self.eq = Tex(r"=",font_size = 100)
        self.eq.move_to([x+2.7,y,0])
        self.H = Tex(r"\textsf{H}", font_size = 100)
        self.H.move_to([x-2.6,y,0])
        self.header = Rectangle(
            color=BLACK,
            fill_opacity=1,
            height = 0.5,
            width = 2.8
        )
        self.header.move_to([x,y+0.6,0])
        self.nonce_label = Text("Nonce: " + str(self.nonce), font_size = 30)
        self.nonce_label.move_to([x,y+0.6,0])
        self.hash = self._nexthash()
        self.hash.move_to([x+7,y,0])
        scene.add(self.rect, self.H, self.lpar, self.rpar, self.eq, self.header, self.nonce_label, self.hash)
        scene.wait(0.5)

    def _nexthash(self, win=False, color=RED):
        nhash = Text(("0"*10 if win else fake_sha(10)) + "..." + fake_sha(), font_size = 50, color=color, font="Monospace")
        nhash.move_to([self.x+7,self.y,0])
        return nhash

    def update(self):
        self.nonce += 1
        self.attempts -= 1
        newnonce = Text("Nonce: " + str(self.nonce), font_size = 30)
        newnonce.move_to([self.x,self.y+0.6,0])
        self.scene.play(Unwrite(self.hash),run_time = 0.3)
        self.scene.play(Transform(self.nonce_label, newnonce))
        self.hash = self._nexthash(win = not bool(self.attempts),color=WHITE)
        self.scene.play(Write(self.hash),run_time = 0.3)
        self.scene.play(FadeToColor(self.hash, RED if self.attempts else BLUE))

    def mining(self):
        return self.attempts > 0

def fake_sha(n=6):
    return ''.join(choice(string.ascii_lowercase[:6]+string.digits[1:]) for _ in range(n))

class Node(Square):
    def __init__(self, peers:list = []):
        super().__init__()
        # Create a Node with a list of peers

        self.side_length = 0.8
        self.set_fill("#0000FF", opacity=1)

        if peers:
            self.peers_list = peers

    def set_blue(self):
        self.set_fill("0000FF", opacity=1, family=False)

    def set_red(self):
        self.set_fill("#FF0000", opacity=1, family=False)

# TODO Create BlockChain and DAG classes for BlockMob

# TODO add lines from this block to all blocks in mergeset
# TODO color past, future, and leave anticone for visulizing add functions within BlockMob

# Create a chain of blocks that can follow parent
# TODO incomplete, will add pointers soon, begin creating animations within BlockChainMob

class BlockMobBitcoin:
    def __init__(self, blocks:int = 0):
        self.blocks_to_create = blocks
        self.chain = [] #all blocks added to the chain
        self.pointers = []

        # Create Genesis
        block = BlockMob("Gen", None)
        self.chain.append(block)

        # Create chain of BlockMob
        i = 1

        while i < self.blocks_to_create:
            parent = self.chain[-1]

            block = BlockMob(str(i), parent)
            self.chain.append(block)

            pointer = Pointer(block, parent)
            self.pointers.append(pointer)
            block.attach_pointer(pointer)

            i += 1

    def add_chain(self, scene):
        add_chain_one_by_one_with_fade_in = []

        for each in self.chain:

            add_chain_one_by_one_with_fade_in.append(
                AnimationGroup(
                    scene.camera.frame.animate.move_to(each.get_center()),
                    FadeIn(each)
                )
            )

            for pointer in each.pointers:
                add_chain_one_by_one_with_fade_in.append(
                    AnimationGroup(
                        FadeIn(pointer)
                    )
            )

            add_chain_one_by_one_with_fade_in.extend(
                [Wait(0.5)],
            )

        add_chain_one_by_one_with_fade_in.append(
            AnimationGroup(
                scene.camera.auto_zoom(self.chain, margin=1)
            )
        )

        add_chain_one_by_one_with_fade_in.append(Wait(run_time=0))
        return Succession(*add_chain_one_by_one_with_fade_in)

    def blink_past(self, block:int):
        blink_past_animations = []
        current = self.chain[block].parent

        while current is not None:
            blink_past_animations.append(
                current.blink()
                )
            current = current.parent

        return AnimationGroup(*blink_past_animations)

    ####################
    # Testing animation
    ####################

    # Snaps position up when called in scene, updaters do not complete
    def shift_genesis(self):
        self.chain[0].shift(UP*2)
        return Wait(run_time=1)
    # Gradually moves when called in scene, moving slowly enough allows updaters to keep up
    def smooth_genesis(self):
        animations = []

        animations.append(
            self.chain[0].animate.shift(UP*1)
        )

        return AnimationGroup(animations)

    ####################
    # Functions
    ####################

# Succession returns animations to be played one by one
# AnimationGroup plays all animations together

# Not for use, saving in case snippets are useful later
class BlockMobChain:
    def __init__(self, blocks:int = 0):
        self.blocks_to_create = blocks
        self.chain = [] #all blocks added to the chain
        self.pointers = []
        self.forks = [] # list of lists [[original chain],[forked chain]]
        self.blocks_with_forks = [] #list of blocks with multiple childen

        block = BlockMob("Gen", None)
        self.chain.append(block)

        i = 1
        while i < self.blocks_to_create:
            parent = self.chain[-1]

            block = BlockMob(str(i), parent)
            self.chain.append(block)

            pointer = Pointer(block, parent)
            self.pointers.append(pointer)

            i += 1

    def add_chain(self):
        add_chain_one_by_one_with_fade_in = []

        for each in chain(self.chain):
            add_chain_one_by_one_with_fade_in.append(
                [FadeIn(each)],
            )

            add_chain_one_by_one_with_fade_in.append(
                Wait(0.5)
            )

        add_chain_one_by_one_with_fade_in.append(Wait(run_time=0))
        return Succession(*add_chain_one_by_one_with_fade_in)

    ####################
    # Testing animation
    ####################

    # Snaps position up when called in scene, updaters do not complete
    def shift_genesis(self):
        self.chain[0].shift(UP*2)
        return Wait(run_time=1)
    # Gradually moves when called in scene, moving slowly enough allows updaters to keep up
    def smooth_genesis(self):
        animations = []

        animations.append(
            self.chain[0].animate.shift(UP*1)
        )

        return AnimationGroup(animations)

    ####################
    # Functions
    ####################
    def create_fork(self, fork_block:int = 0):
        original_chain = []
        forked_chain = []

        block = BlockMob(str(self.chain[fork_block - 1].name), self.chain[fork_block - 1])

        forked_chain.append(block)
        original_chain.append(self.chain[fork_block - 1])

        original_chain[0].safe_remove_current_position_updater()
        forked_chain[0].safe_remove_current_position_updater()
        print(original_chain[0].get_center())
        print(forked_chain[0].get_center())
        forked_chain[0].shift(DOWN)

        i = 1
        while i < len(self.chain) - fork_block:
            block = BlockMob(str(int(forked_chain[-1].name) + 1), forked_chain[-1])
            forked_chain.append(block)
            original_chain.append(self.chain[fork_block + i])
#            block.lock_to_parent()

            i += 1

        new_forks = [original_chain, forked_chain]
        self.forks.append(new_forks)

        fork_positioning_animations = []
        fork_positioning_animations.append(
            forked_chain[0].animate.shift(DOWN)
        )
#        forked_chain[0].shift(DOWN)

        draw_fork_anims = []

        for each in forked_chain:
            draw_fork_anims.append(
                [FadeIn(each)],
            )
            draw_fork_anims.append(
                Wait(0.5),
            )

        draw_fork_anims.append(Wait(run_time=0))

#        return AnimationGroup(*draw_fork_anims)
        return Succession(*fork_positioning_animations), AnimationGroup(*draw_fork_anims)

    def create_fork_old(self, fork_depth:int = 0):
        original_chain = []
        forked_chain = []

        block = BlockMob(str(self.chain[-fork_depth].name), self.chain[-fork_depth - 1])
        forked_chain.append(block)
        original_chain.append(self.chain[-fork_depth])
        block.lock_fork_to_parent()

        i = 1
        while i < fork_depth:
            block = BlockMob(str(int(forked_chain[-1].name) + 1), forked_chain[-1])
            forked_chain.append(block)
            original_chain.append(self.chain[-fork_depth + i])
            block.lock_to_parent()

            i += 1

        original_chain.append(self.chain[-1])
        new_forks = [original_chain, forked_chain]
        self.forks.append(new_forks)

        draw_fork_anims = []

        for each in forked_chain:
            draw_fork_anims.append(
                [FadeIn(each)],
            )
            draw_fork_anims.append(
                Wait(0.5),
            )

        draw_fork_anims.append(Wait(run_time=0))

        return AnimationGroup(*draw_fork_anims)

    def blink(self):
        #blinks only additional forked blocks
        forks_list = self.forks[0]
        blink_anims = [Wait(run_time=4),]

        blink_these_blocks = forks_list[1]

        for each in blink_these_blocks:
            blink_anims.append(each.blink(),)

        blink_anims.append(Wait(run_time=0))
        return AnimationGroup(*blink_anims)

# Succession returns animations to be played one by one
# AnimationGroup plays all animations together

# TODO track both forks and shift together, try as a function within BlockMob using position updaters
    def shift_forks(self):
        shift_forks_anims = []
        list_of_fork_to_shift = self.blocks_with_forks[0]
        list_of_original_blocks_to_shift = list_of_fork_to_shift[0]
        list_of_forked_blocks_to_shift = list_of_fork_to_shift[1]

        for each in list_of_original_blocks_to_shift:
            shift_forks_anims.append(
                each.animate.shift(UP * 0.8),

            )

        for each in list_of_forked_blocks_to_shift:
            shift_forks_anims.append(
                each.animate.shift(UP * 0.8),

            )



        shift_forks_anims.append(Wait(run_time=5))
        return AnimationGroup(*shift_forks_anims)


    def shift_forks_not_used(self):
        shift_forks_anims = []
        list_of_fork_to_shift = self.forks[0]
        list_of_original_blocks_to_shift = list_of_fork_to_shift[0]
        list_of_forked_blocks_to_shift = list_of_fork_to_shift[1]

        for each in list_of_original_blocks_to_shift:
            shift_forks_anims.append(
                each.animate.shift(UP * 0.8),

            )

        for each in list_of_forked_blocks_to_shift:
            shift_forks_anims.append(
                each.animate.shift(UP * 0.8),

            )



        shift_forks_anims.append(Wait(run_time=0))
        return AnimationGroup(*shift_forks_anims)

class BlockMob(Square):
    def __init__(self,
                 name:str = "",
                 selected_parent:'BlockMob' = None,
                 side_length:float=0.8):
        super().__init__(
            color="#0000FF",
            fill_opacity=1,
            side_length=side_length,
            background_stroke_color=WHITE,
            background_stroke_width=10,
            background_stroke_opacity=1.0
        )
        self.set_blue()

        # set instance variables
        self.name = name
        self.parent = selected_parent
        self.weight = 1

        self.mergeset = [] # parent inclusive mergeset  NOT yet used
        self.children = []
        self.pointers = []

        if selected_parent:
            self.weight = selected_parent.weight + 1
            self.parent.add_self_as_child(self)
            self.shift_position_to_parent()

        # changed label to text mobject, will attempt to create a latex mobject at a later date
        if self.name:
            self.label = Text(name, font_size=24, color=WHITE, weight=BOLD)
            self.label.move_to(self.get_center())
            self.add(self.label)

        # Initialize time tracking
        self.fade_time = 0

    # Setters and getters

    def add_self_as_child(self, mobject):
        self.children.append(mobject)

    def is_tip(self):
        return bool(self.children)

    def set_label(self, to_label:str = ""):
        if self.label:
            self.remove(self.label)
        self.label = Text(to_label, font_size=24, color=WHITE, weight=BOLD)
        self.label.move_to(self.get_center())
        self.add(self.label)

    ####################
    # Color Setters
    ####################
    # TODO test if adding run_time to setters will make them change color slowly
    def set_blue(self):
        self.set_color("#0000FF", family=False)

    def set_red(self):
        self.set_color("#FF0000", family=False)

    def set_to_color(self, to_color):
        self.set_color(to_color, family=False)

    def fade_blue(self):
        return self.animate.fade_to(color=PURE_BLUE, alpha=1.0, family=False)

    def fade_red(self):
        return self.animate.fade_to(color=PURE_RED, alpha=1.0, family=False)

    # fade_to_color ONLY works with ManimColor, does not work with hex format str
    def fade_to_color(self, to_color:ManimColor = WHITE):
        return self.animate.fade_to(color=to_color, alpha=1.0, family=False)

    ####################
    # Unused, transitioning to using updaters instead of calling from scene
    # might reuse code for shifting position within chain/dag and adding updater to maintain set position
    ####################
    def shift_to_parent(self):
        to_position: array = ([])
        parent_right = self.parent.get_right()
        to_position = [parent_right[0] + (self.side_length * 1.75), parent_right[1], 0]
        self.move_to(to_position)

    def shift_fork_to_parent(self):
        to_position: array = ([])
        parent_right = self.parent.get_right()
        to_position = [parent_right[0] + (self.side_length * 1.75), parent_right[1] - (self.side_length * 1.75), 0]
        self.move_to(to_position)

    ####################
    # Pointers Handling
    ####################

    def attach_pointer(self, pointer):
        self.pointers.append(pointer)

    ####################
    # Position Handling (Updaters leave position at [0,0,0])
    ####################

    def shift_position_to_parent(self):
        self.next_to(self.parent, RIGHT * 4)

    ####################
    # Blink Animations
    ####################
    def blink(self):
        return Succession(
            ApplyMethod(self.set_color, YELLOW, False, run_time=0.8),
            ApplyMethod(self.set_color, self.color, False, run_time=0.8),
        )
        # Using ApplyMethod directly bypasses limitations of Manim FadeToColor

class Pointer(Line):
    def __init__(self, this_block:'BlockMob', parent_block: 'BlockMob'):
        # Initialize with proper start/end points
        super().__init__(
            start=this_block.get_left(),
            end=parent_block.get_right(),
            buff=0.1,
            color=BLUE,
            stroke_width=5,  # Set stroke width directly
            cap_style = CapStyleType.ROUND
        )

        self.this_block = this_block
        self.parent_block = parent_block

        # Store fixed stroke width (no tip needed for Line)
        self._fixed_stroke_width = 5

        # Add updater for continuous tracking
        self.add_updater(self._update_position_and_size)

    def _update_position_and_size(self, mobject):
        # Get the raw endpoints from the blocks
        new_start = self.this_block.get_left()
        new_end = self.parent_block.get_right()

        # Maintain fixed stroke width
        self.set_stroke(width=self._fixed_stroke_width)

        # Use set_points_by_ends which respects buff
        self.set_points_by_ends(new_start, new_end, buff=self.buff)

# TODO
#  This is rough notes from discussion
#  priorities labels misbehaving, blockchain class - location updates based on parent, BlockDAG(get_past, get future, get_anticone),
#  parallel chains like kadena, ect, ghostdag, function that computes k cluster and blueset for each block, output a transcript that has each step eg.
#  eg. added to blue set, appended children,

# TODO please list priorities here