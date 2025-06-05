from codecs import namereplace_errors
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
        self.width = w
        self.height = h
        self.DAG = DAG
        self.parents = [DAG.blocks[p.name] for p in parents]
        self.children = []
#        self.rect = Rectangle(
#            color      = color,
#            fill_opacity    = 1,
#            height          = h,
#            width           = w,
#        )
        # currently breaks Block has no attribute "weight"
#        self.selected_parent = None
#        if len(self.parents) != 0:
#            self.selected_parent = self.parents[0]

        # currently works, but does not take advantage of anything built into BlockMob
        self.rect = BlockMob(
            None
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

# Create a chain of blocks that can follow parent
# TODO incomplete, begin adding text explanation of each step

class BlockMobBitcoin:
    def __init__(self, blocks:int = 0):
        self.blocks_to_create = blocks
        self.all_blocks = [] #all blocks added to the chain
        self.narration_text_mobject = NarrationMathTex()

        # Create Genesis
        block = BlockMob(None, "Gen")
        self.all_blocks.append(block)

        self.create_blocks_and_pointers(self.blocks_to_create - 1)

    def create_blocks_and_pointers(self, number_of_blocks_to_create:int = 0):
        # Create chain of BlockMob
        i = 0

        while i < number_of_blocks_to_create:
            parent = self.all_blocks[-1]

            block = BlockMob(parent)
            self.all_blocks.append(block)

            pointer = Pointer(block, parent)
            block.pointers.append(pointer)

            i += 1

    # returns animations for adding all blocks and pointers
    def add_chain(self, scene):
        add_chain_one_by_one_with_fade_in = []

        for each in self.all_blocks:

            add_chain_one_by_one_with_fade_in.append(
                AnimationGroup(
                    scene.camera.frame.animate.move_to(each.get_center()),
                    FadeIn(each),
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
                scene.camera.auto_zoom(self.all_blocks, margin= 1.0),
            )
        )

        add_chain_one_by_one_with_fade_in.append(Wait(run_time=0))
        return Succession(*add_chain_one_by_one_with_fade_in)

    def add_blocks(self, scene, how_many_blocks_to_add:int = 1):
        add_blocks_one_by_one_with_fade_in = []

        # Create blocks to add
        self.create_blocks_and_pointers(how_many_blocks_to_add)

        for each in self.all_blocks[-how_many_blocks_to_add:]:

            add_blocks_one_by_one_with_fade_in.append(
                AnimationGroup(
                    scene.camera.frame.animate.move_to(each.get_center()),
                    FadeIn(each),
                )
            )

            for pointer in each.pointers:
                add_blocks_one_by_one_with_fade_in.append(
                    AnimationGroup(
                        FadeIn(pointer)
                    )
            )

            add_blocks_one_by_one_with_fade_in.extend(
                [Wait(0.5)],
            )

        add_blocks_one_by_one_with_fade_in.append(
            AnimationGroup(
                scene.camera.auto_zoom(self.all_blocks, margin= 1.0),
            )
        )

        add_blocks_one_by_one_with_fade_in.append(Wait(run_time=0))
        return Succession(*add_blocks_one_by_one_with_fade_in)

    def create_fork(self, scene, how_many_blocks_to_add:int = 1, from_depth:int = 1):
        add_blocks_one_by_one_with_fade_in = []

        # Create forked blocks to add
        fork = [self.all_blocks[-from_depth -1]]

        i = 0
        while i < how_many_blocks_to_add:
            parent = fork[-1]

            block = BlockMob(parent)
            fork.append(block)

            pointer = Pointer(block, parent)
            block.pointers.append(pointer)

            i += 1

        self.all_blocks = list(set(self.all_blocks + fork))

        fork[1].shift_fork()

        for each in fork[1:]:

            add_blocks_one_by_one_with_fade_in.append(
                AnimationGroup(
                    scene.camera.frame.animate.move_to(each.get_center()),
                    FadeIn(each),
                )
            )

            for pointer in each.pointers:
                add_blocks_one_by_one_with_fade_in.append(
                    AnimationGroup(
                        FadeIn(pointer)
                    )
            )

            add_blocks_one_by_one_with_fade_in.extend(
                [Wait(0.5)],
            )

        add_blocks_one_by_one_with_fade_in.append(
            AnimationGroup(
                scene.camera.auto_zoom(self.all_blocks, margin= 1.0),
            )
        )

        add_blocks_one_by_one_with_fade_in.append(Wait(run_time=0))
        return Succession(*add_blocks_one_by_one_with_fade_in)

    ####################
    # Get past/future/anticone and blink
    ####################

    # returns group of blink animations on past of block at selected round
    def blink_past_of_random_block(self):
        random_block: 'Mobject' = choice(self.all_blocks)
        blink_past_animations = []
        current_list_to_blink = random_block.get_past()
        blink_past_animations.append(random_block.highlight_self())

        for each in current_list_to_blink:
            blink_past_animations.append(each.blink())

        blink_past_animations.append(Wait(run_time=0.1)) # added to prevent random block not having past and breaking animation with no runtime
        return AnimationGroup(*blink_past_animations)

    # returns group of blink animations on future of block at selected round
    def blink_future_of_random_block(self):
        random_block: 'Mobject' = choice(self.all_blocks)
        blink_future_animations = []
        current_list_to_blink = random_block.get_future()
        blink_future_animations.append(random_block.highlight_self())

        for each in current_list_to_blink:
            blink_future_animations.append(each.blink())

        blink_future_animations.append(Wait(run_time=0.1)) # added to prevent random block not having future and breaking animation with no runtime
        return AnimationGroup(*blink_future_animations)

    # returns group of blink animations on anticone of block at selected round
    def blink_anticone_of_random_block(self):
        random_block: 'Mobject' = choice(self.all_blocks)
        blink_anticone_animations = []

        # need to get past and get future, need to get all blocks from all_blocks, and compare
#        list_of_blocks_not_in_past = list(set(self.all_blocks) - set(random_block.get_past()))
#        list_of_blocks_not_in_past_or_future = list(set(list_of_blocks_not_in_past) - set(random_block.get_future()))
#        anticone = list(set(list_of_blocks_not_in_past_or_future) - set(random_block))
        list_of_blocks_reachable = list(set(self.all_blocks) - set(random_block.get_reachable()))
        anticone = list(set(list_of_blocks_reachable) - set(random_block))

        blink_anticone_animations.append(random_block.highlight_self())

        for each in anticone:
            blink_anticone_animations.append(each.blink())

        blink_anticone_animations.append(Wait(run_time=0.1)) # added to prevent random block not having future and breaking animation with no runtime
        return AnimationGroup(*blink_anticone_animations)

    ####################
    # Testing animation
    ####################

    # Gradually moves when called in scene, moving slowly enough allows updaters to keep up
    def smooth_genesis(self):
        animations = []

        animations.append(
            self.all_blocks[0].animate.shift(UP*1)
        )

        return AnimationGroup(animations)

    ####################
    # Functions
    ####################

# Succession returns animations to be played one by one
# AnimationGroup plays all animations together

class BlockMob(Square):
    def __init__(self,
                 selected_parent:'BlockMob' = None,
                 name:str = ""
                 ):
        super().__init__(
            color="#0000FF",
            fill_opacity=1,
            side_length=0.8,
            background_stroke_color=WHITE,
            background_stroke_width=10,
            background_stroke_opacity=1.0
        )
        self.set_blue()

        # set instance variables
        self.name = name
        self.parent = selected_parent
        self.weight = 1

        self.mergeset = []
        self.children = []
        self.pointers = []

        if self.parent:
            self.mergeset.append(self.parent)
            self.weight = selected_parent.weight + 1
#            self.parent.add_self_to_children(self)
            self.shift_position_to_parent()

        if self.mergeset:
            for each in self.mergeset:
                each.add_self_to_children(self)

        # name instead displays weight of the block
        if self.name != "Gen":
            self.name = self.weight

        # changed label to text mobject, will attempt to create a latex mobject at a later date
        if self.name:
            self.label = Text(str(self.name), font_size=24, color=WHITE, weight=BOLD)
            self.label.move_to(self.get_center())
            self.add(self.label)


    # Setters and getters

    def fade_in(self):
        return AnimationGroup(
            self.animate(runtime=0.5).set_opacity(1)
        )

    def add_self_to_children(self, mobject):
        self.children.append(mobject)

    def is_tip(self):
        return bool(self.children)

    def set_label(self, to_label:str = ""):
        if self.label:
            self.remove(self.label)
        self.label = Text(to_label, font_size=24, color=WHITE, weight=BOLD)
        self.label.move_to(self.get_center())
        self.add(self.label)

    # TODO test this
    def fade_to_next_label(self, to_label: str = ""):
        animations = []

        # Fade out existing label if it exists
        if self.label:
            animations.append(FadeOut(self.label))

            # Create new label
        new_label = Text(to_label, font_size=24, color=WHITE, weight=BOLD)
        new_label.move_to(self.get_center())

        # Fade in new label
        animations.append(FadeIn(new_label))

        # Update the label reference
        self.label = new_label

        # Return animation sequence
        return Succession(*animations) if len(animations) > 1 else animations[0]

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
    # Pointers Handling
    ####################

    def attach_pointer(self, pointer):
        self.pointers.append(pointer)

    ####################
    # Position Handling (Updaters leave position at [0,0,0])
    ####################

    # immediately changes position relative to self.parent, no animation, for setting initial position
    def shift_position_to_parent(self):
        self.next_to(self.parent, RIGHT * 4)
        if self.children:
            self.children[0].shift_position_to_parent()

    def shift_fork(self):
        self.next_to(self.parent, RIGHT * 4 + DOWN * 4)
        if self.children:
            self.children[0].shift_position_to_parent()

    ####################
    # Blink Animations
    ####################

    def blink(self):
        return Succession(
            ApplyMethod(self.set_color, YELLOW, False, run_time=0.8),
            ApplyMethod(self.set_color, self.color, False, run_time=0.8),
        )
        # Using ApplyMethod directly bypasses limitations of Manim FadeToColor

    def highlight_self(self):
        return Succession(
            ApplyMethod(self.set_color, GREEN, False, run_time=0.8),
            ApplyMethod(self.set_color, self.color, False, run_time=0.8),
        )

    ####################
    # Determine past/future/anticone
    ####################

    def get_future(self):
        future_of_this_block = []
        future_of_this_block.extend(self.children)

        for each in self.children:
            future_of_this_block.extend(each.get_future())

        duplicates_removed = list(set(future_of_this_block))
        return duplicates_removed

    def get_past(self):
        past_of_this_block = []
        past_of_this_block.extend(self.mergeset)

        for each in self.mergeset:
            past_of_this_block.extend(each.get_past())

        duplicates_removed = list(set(past_of_this_block))
        return duplicates_removed

    def get_reachable(self):
        reachable = []

        reachable.extend(self.get_past())
        reachable.extend(self.get_future())

        return reachable

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

# TODO check if useful using MovingCameraFixedLayerScene, if not destroy this
class Narration(Text):
    def __init__(self):
        super().__init__(
            text="empty narration Text",
            color=WHITE
        )

    def fade_to_next_narration(self, to_text: str = ""):
        # Store current properties
        current_pos = self.get_center()
        current_color = self.color

        # Create new text object
        new_text_obj = Text(to_text, color=current_color)
        new_text_obj.move_to(current_pos)

        # Update this object to become the new text
        self.become(new_text_obj)

        return Succession(
            self.animate.set_opacity(0),
            self.animate.set_opacity(1)
        )

class NarrationText(Text):
    def __init__(self):
        super().__init__(
            "created on init text",
            color=WHITE
        )

        self.fixedLayer= True
        self.to_edge(UP)

    def fade_to_next_narration(self, to_text: str = ""):
        # Store current properties
        current_pos = self.get_center()
        current_color = self.color

        # Create new text object
        new_text_obj = Text(to_text, color=current_color)
        new_text_obj.move_to(current_pos)

        # Update this object to become the new text
        self.become(new_text_obj)

        return Succession(
            self.animate(runtime = 1).set_opacity(0),
            self.animate(runtime = 1).set_opacity(1)
        )

class NarrationTex(Tex):
    def __init__(self):
        super().__init__(
            r"\text{created on init text and math: } \int_0^\infty e^{-x^2} dx",
            color=WHITE
        )

        self.fixedLayer= True
        self.to_edge(UP)

    def fade_to_next_narration(self, to_text: str = ""):
        # Store current properties
        current_pos = self.get_center()
        current_color = self.color

        # Create new text object
        new_text_obj = Tex(to_text, color=current_color)
        new_text_obj.move_to(current_pos)

        # Update this object to become the new text
        self.become(new_text_obj)

        return Succession(
            self.animate(runtime = 1).set_opacity(0),
            self.animate(runtime = 1).set_opacity(1)
        )

class NarrationMathTex(MathTex):
    def __init__(self):
        super().__init__(
            r"\text{created on init text and math: } \int_0^\infty e^{-x^2} dx",
            color=WHITE
        )

        self.fixedLayer= True
        self.to_edge(UP)

    def fade_to_next_narration(self, to_text: str = ""):
        # Store current properties
        current_pos = self.get_center()
        current_color = self.color

        # Create new text object
        new_text_obj = MathTex(to_text, color=current_color)
        new_text_obj.move_to(current_pos)

        # Update this object to become the new text
        self.become(new_text_obj)

        return Succession(
            self.animate(runtime = 1).set_opacity(0),
            self.animate(runtime = 1).set_opacity(1)
        )
# TODO
#  This is rough notes from discussion
#  priorities
#               labels misbehaving,
#               blockchain class - location updates based on parent,
#  COMPLETE     for BlockMobBitcoin(BlockDAG(blink(get_past, get future, get_anticone)) #method works for Kaspa),
#               parallel chains like kadena, ect,
#               ghostdag, function that computes k cluster and blueset for each block,
#               output a transcript that has each step eg. added to blue set, appended children,

# TODO please list priorities here