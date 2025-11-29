# blanim/examples/bitcoin_examples.py

from blanim import *
from blanim.blockDAGs.bitcoin import BitcoinConfig
from blanim.blockDAGs.kaspa import KaspaConfig
import random

from blanim.blockDAGs.kaspa.dag import KaspaDAG

# ============================================================================
# CUSTOM CONFIGURATIONS - Override ALL settings
# ============================================================================

# Custom Bitcoin configuration with all settings overridden
CUSTOM_BITCOIN_CONFIG = BitcoinConfig(
    # Visual styling
    block_color=PURPLE,
    fill_opacity=0.3,
    stroke_color=GOLD,
    stroke_width=4,
    side_length=0.9,

    # Label styling
    label_font_size=28,
    label_color=YELLOW,

    # Animation timing
    create_run_time=3.0,
    label_change_run_time=0.8,
    movement_run_time=1.5,

    # Line styling
    line_color=RED
)

# Custom Kaspa configuration with all settings overridden
CUSTOM_KASPA_CONFIG = KaspaConfig(
    # Visual styling
    block_color=GREEN,
    fill_opacity=0.4,
    stroke_color=TEAL,
    stroke_width=5,
    side_length=0.8,

    # Label styling
    label_font_size=26,
    label_color=ORANGE,

    # Animation timing
    create_run_time=2.5,
    label_change_run_time=0.7,
    movement_run_time=1.2,

    # Line styling (Kaspa-specific: multiple parents)
#    selected_parent_color=PINK,
#    other_parent_color=LIGHT_GRAY,
    line_stroke_width=6
)


# ============================================================================
# BITCOIN TEST SCENES
# ============================================================================

class BitcoinCustomConfigExample(HUD2DScene):
    """Demonstrate BitcoinVisualBlock with fully customized configuration.

    Shows:
    - Custom colors (PURPLE blocks, GOLD stroke, RED lines, YELLOW labels)
    - Custom sizing (0.9 side length, stroke width 4, font size 28)
    - Custom timing (3.0s create, 0.8s label change, 1.5s movement)
    - All config parameters overridden from defaults
    """

    def construct(self):
        self.narrate(r"Bitcoin Custom Config Demo")
        self.caption(r"All styling and timing overridden")

        # Create genesis block with custom config
        genesis = BitcoinVisualBlock(
            label_text="Gen",
            position=[-6, 0, 0],
            block_config=CUSTOM_BITCOIN_CONFIG
        )

        # Create chain of 4 more blocks with same custom config
        blocks = [genesis]
        for i in range(1, 5):
            block = BitcoinVisualBlock(
                label_text=str(i),
                position=[-6 + i * 3, 0, 0],
                parent=blocks[i - 1],
                block_config=CUSTOM_BITCOIN_CONFIG
            )
            blocks.append(block)

            # Animate creation - notice slower timing (3.0s)
        self.caption(r"Creating blocks (3.0s animation)")
        self.play(genesis.create_with_lines())
        for block in blocks[1:]:
            self.play(block.create_with_lines())
            self.wait(0.2)

        self.wait(1)

        # Label change - notice custom timing (0.8s)
        self.caption(r"Label change (0.8s animation)")
        self.play(blocks[1].change_label("A"))
        self.wait(0.5)

        # Movement with line update - notice custom timing (1.5s)
        self.caption(r"Movement with line update (1.5s)")
        random_shift = np.array([
            random.uniform(-1, 1),
            random.uniform(-2, 2),
            0
        ])
        self.play(blocks[1].create_movement_animation(
            blocks[1].animate.shift(random_shift)
        ))
        self.wait(0.5)

        # Sequential label change and movement
        self.caption(r"Sequential operations")
        self.play(blocks[2].change_label("B"))
        random_shift = np.array([
            random.uniform(-1, 1),
            random.uniform(-2, 2),
            0
        ])
        self.play(blocks[2].create_movement_animation(
            blocks[2].animate.shift(random_shift)
        ))
        self.wait(0.5)

        # Move genesis to show child line updates
        self.caption(r"Moving genesis with custom timing")
        random_shift = np.array([
            random.uniform(-1, 1),
            random.uniform(-2, 2),
            0
        ])
        self.play(genesis.create_movement_animation(
            genesis.animate.shift(random_shift)
        ))
        self.wait(2)

        self.clear_narrate()
        self.clear_caption()


class BitcoinDefaultVsCustomExample(HUD2DScene):
    """Compare default config vs custom config side-by-side.

    Shows:
    - Left side: Default configuration (BLUE, standard timing)
    - Right side: Custom configuration (PURPLE, slower timing)
    - Visual comparison of all styling differences
    """

    def construct(self):
        self.narrate(r"Default vs Custom Config")
        self.caption(r"Side-by-side comparison")

        # Left side: Default config chain
        default_genesis = BitcoinVisualBlock(
            label_text="D0",
            position=[-6, 2, 0]
        )

        default_blocks = [default_genesis]
        for i in range(1, 3):
            block = BitcoinVisualBlock(
                label_text=f"D{i}",
                position=[-6 + i * 2.5, 2, 0],
                parent=default_blocks[i - 1]
            )
            default_blocks.append(block)

            # Right side: Custom config chain
        custom_genesis = BitcoinVisualBlock(
            label_text="C0",
            position=[-6, -2, 0],
            block_config=CUSTOM_BITCOIN_CONFIG
        )

        custom_blocks = [custom_genesis]
        for i in range(1, 3):
            block = BitcoinVisualBlock(
                label_text=f"C{i}",
                position=[-6 + i * 2.5, -2, 0],
                parent=custom_blocks[i - 1],
                block_config=CUSTOM_BITCOIN_CONFIG
            )
            custom_blocks.append(block)

            # Create both chains simultaneously
        self.caption(r"Creating both chains")
        self.play(
            default_genesis.create_with_lines(),
            custom_genesis.create_with_lines()
        )

        for i in range(1, 3):
            self.play(
                default_blocks[i].create_with_lines(),
                custom_blocks[i].create_with_lines()
            )
            self.wait(0.2)

        self.wait(1)

        # Compare label changes
        self.caption(r"Label changes: default (0.5s) vs custom (0.8s)")
        self.play(
            default_blocks[1].change_label("DA"),
            custom_blocks[1].change_label("CA")
        )
        self.wait(1)

        # Compare movements
        self.caption(r"Movements: default (1.0s) vs custom (1.5s)")
        self.play(
            default_blocks[1].create_movement_animation(
                default_blocks[1].animate.shift(UP * 0.5)
            ),
            custom_blocks[1].create_movement_animation(
                custom_blocks[1].animate.shift(DOWN * 0.5)
            )
        )
        self.wait(2)

        self.clear_narrate()
        self.clear_caption()

    # ============================================================================


# KASPA TEST SCENES
# ============================================================================

class KaspaCustomConfigExample(HUD2DScene):
    """Demonstrate KaspaVisualBlock with fully customized configuration.

    Shows:
    - Custom colors (GREEN blocks, TEAL stroke, PINK/GRAY lines, ORANGE labels)
    - Custom sizing (0.8 side length, stroke width 5, font size 26)
    - Custom timing (2.5s create, 0.7s label change, 1.2s movement)
    - Multiple parent lines with different colors
    """

    def construct(self):
        self.narrate(r"Kaspa Custom Config Demo")
        self.caption(r"All styling and timing overridden")

        # Create genesis block with custom config
        genesis = KaspaVisualBlock(
            label_text="Gen",
            position=[-6, 0, 0],
            block_config=CUSTOM_KASPA_CONFIG
        )

        # Create two parallel blocks at layer 1
        block1 = KaspaVisualBlock(
            label_text="1",
            position=[-3, 1.5, 0],
            parents=[genesis],
            block_config=CUSTOM_KASPA_CONFIG
        )

        block2 = KaspaVisualBlock(
            label_text="2",
            position=[-3, -1.5, 0],
            parents=[genesis],
            block_config=CUSTOM_KASPA_CONFIG
        )

        # Create merge block with multiple parents
        # First parent line will be PINK, second will be LIGHT_GRAY
        block3 = KaspaVisualBlock(
            label_text="3",
            position=[0, 0, 0],
            parents=[block1, block2],
            block_config=CUSTOM_KASPA_CONFIG
        )

        # Create final block
        block4 = KaspaVisualBlock(
            label_text="4",
            position=[3, 0, 0],
            parents=[block3],
            block_config=CUSTOM_KASPA_CONFIG
        )

        blocks = [genesis, block1, block2, block3, block4]

        # Animate creation - notice slower timing (2.5s)
        self.caption(r"Creating DAG (2.5s animation)")
        self.play(genesis.create_with_lines())
        self.wait(0.3)

        self.play(block1.create_with_lines())
        self.wait(0.3)

        self.play(block2.create_with_lines())
        self.wait(0.3)

        self.caption(r"Block 3: PINK (selected) + GRAY (other) lines")
        self.play(block3.create_with_lines())
        self.wait(0.5)

        self.play(block4.create_with_lines())
        self.wait(1)

        # Label change - notice custom timing (0.7s)
        self.caption(r"Label change (0.7s animation)")
        self.play(block1.change_label("A"))
        self.wait(0.5)

        # Movement with line updates - notice custom timing (1.2s)
        self.caption(r"Movement with line updates (1.2s)")
        random_shift = np.array([
            random.uniform(-1, 1),
            random.uniform(-1, 1),
            0
        ])
        self.play(block1.create_movement_animation(
            block1.animate.shift(random_shift)
        ))
        self.wait(0.5)

        # Sequential label change and movement
        self.caption(r"Sequential operations")
        self.play(block3.change_label("C"))
        random_shift = np.array([
            random.uniform(-1, 1),
            random.uniform(-1, 1),
            0
        ])
        self.play(block3.create_movement_animation(
            block3.animate.shift(random_shift)
        ))
        self.wait(0.5)

        # Move genesis to show all descendant line updates
        self.caption(r"Moving genesis affects all descendants")
        random_shift = np.array([
            random.uniform(-1, 1),
            random.uniform(-1, 1),
            0
        ])
        self.play(genesis.create_movement_animation(
            genesis.animate.shift(random_shift)
        ))
        self.wait(2)

        self.clear_narrate()
        self.clear_caption()


class KaspaDefaultVsCustomExample(HUD2DScene):
    """Side-by-side comparison of default vs custom Kaspa block styling.

    Shows:
    - Two parallel DAGs with different configurations
    - Default config on left, custom config on right
    - All timing and styling differences visible
    - Multiple parent lines with different colors
    """

    def construct(self):
        self.narrate(r"Kaspa: Default vs Custom Config")
        self.caption(r"Creating two DAGs side-by-side")

        # Create default DAG (left side)
        default_gen = KaspaVisualBlock(
            label_text="G",
            position=[-3, 2, 0],
            parents=[]
        )

        default_b1 = KaspaVisualBlock(
            label_text="1",
            position=[-3, 0.5, 0],
            parents=[default_gen]
        )

        default_b2 = KaspaVisualBlock(
            label_text="2",
            position=[-2, 0.5, 0],
            parents=[default_gen]
        )

        default_b3 = KaspaVisualBlock(
            label_text="3",
            position=[-2.5, -1, 0],
            parents=[default_b1, default_b2]
        )

        # Create custom DAG (right side)
        custom_gen = KaspaVisualBlock(
            label_text="G",
            position=[3, 2, 0],
            parents=[],
            block_config=CUSTOM_KASPA_CONFIG
        )

        custom_b1 = KaspaVisualBlock(
            label_text="1",
            position=[3, 0.5, 0],
            parents=[custom_gen],
            block_config=CUSTOM_KASPA_CONFIG
        )

        custom_b2 = KaspaVisualBlock(
            label_text="2",
            position=[4, 0.5, 0],
            parents=[custom_gen],
            block_config=CUSTOM_KASPA_CONFIG
        )

        custom_b3 = KaspaVisualBlock(
            label_text="3",
            position=[3.5, -1, 0],
            parents=[custom_b1, custom_b2],
            block_config=CUSTOM_KASPA_CONFIG
        )

        # Create both genesis blocks
        self.play(
            default_gen.create_with_lines(),
            custom_gen.create_with_lines()
        )
        self.wait(0.5)

        # Create first layer (notice timing difference)
        self.caption(r"Notice the different animation speeds")
        self.play(
            default_b1.create_with_lines(),
            custom_b1.create_with_lines()
        )
        self.wait(0.3)

        self.play(
            default_b2.create_with_lines(),
            custom_b2.create_with_lines()
        )
        self.wait(0.5)

        # Create blocks with multiple parents
        self.caption(r"Multiple parent lines with different colors")
        self.play(
            default_b3.create_with_lines(),
            custom_b3.create_with_lines()
        )
        self.wait(1)

        # Label changes (sequential, not during movement)
        self.caption(r"Label changes with different timing")
        self.play(
            default_b1.change_label("A"),
            custom_b1.change_label("A")
        )
        self.wait(0.5)

        # Movement with line updates
        self.caption(r"Movement with automatic line updates")
        self.play(
            default_b2.create_movement_animation(
                default_b2.animate.shift(LEFT * 0.5)
            ),
            custom_b2.create_movement_animation(
                custom_b2.animate.shift(RIGHT * 0.5)
            )
        )
        self.wait(1)

        # Move genesis to show all descendant lines update
        self.caption(r"Moving genesis affects all descendants")
        self.play(
            default_gen.create_movement_animation(
                default_gen.animate.shift(DOWN * 0.5)
            ),
            custom_gen.create_movement_animation(
                custom_gen.animate.shift(UP * 0.5)
            )
        )
        self.wait(2)

        self.clear_narrate()
        self.clear_caption()

    # ============================================================================


# SIMPLE EXAMPLE SCENES - Using default configs
# ============================================================================

class SimpleBitcoinExample(HUD2DScene):
    """Simple Bitcoin chain with default styling."""

    def construct(self):
        self.narrate(r"Simple Bitcoin Chain")

        # Create a simple 3-block chain
        genesis = BitcoinVisualBlock("G", [-2, 0, 0])
        block1 = BitcoinVisualBlock("1", [0, 0, 0], parent=genesis)
        block2 = BitcoinVisualBlock("2", [2, 0, 0], parent=block1)

        # Animate creation
        self.play(genesis.create_with_lines())
        self.play(block1.create_with_lines())
        self.play(block2.create_with_lines())
        self.wait(1)

        # Change labels
        self.caption(r"Updating labels")
        self.play(block1.change_label("A"))
        self.play(block2.change_label("B"))
        self.wait(1)

        # Move the chain
        self.caption(r"Moving the entire chain")
        self.play(
            AnimationGroup(
            genesis.create_movement_animation(genesis.animate.shift(UP)),
            block1.create_movement_animation(block1.animate.shift(UP)),
            block2.create_movement_animation(block2.animate.shift(UP))
            )
        )
        self.wait(2)

        self.clear_narrate()
        self.clear_caption()


class SimpleKaspaExample(HUD2DScene):
    """Simple Kaspa DAG with default styling."""

    def construct(self):
        self.narrate(r"Simple Kaspa DAG")

        # Create a simple DAG
        genesis = KaspaVisualBlock("G", [0, 2, 0], parents=[])
        block1 = KaspaVisualBlock("1", [-1, 0, 0], parents=[genesis])
        block2 = KaspaVisualBlock("2", [1, 0, 0], parents=[genesis])
        block3 = KaspaVisualBlock("3", [0, -2, 0], parents=[block1, block2])

        # Animate creation
        self.play(genesis.create_with_lines())
        self.play(
            block1.create_with_lines(),
            block2.create_with_lines()
        )
        self.play(block3.create_with_lines())
        self.wait(1)

        # Change labels
        self.caption(r"Updating labels")
        self.play(block1.change_label("A"))
        self.play(block2.change_label("B"))
        self.wait(1)

        # Move blocks
        self.caption(r"Moving blocks updates all connected lines")
        self.play(
            block1.create_movement_animation(block1.animate.shift(LEFT * 0.5)),
            block2.create_movement_animation(block2.animate.shift(RIGHT * 0.5))
        )
        self.wait(2)

        self.clear_narrate()
        self.clear_caption()

######################
#TODO figure out how to show a chain, explain the limitations of bitcoin, then continue on as a dag making a wide DAG
class BlockchainToDAGNarration(HUD2DScene):
    """Demonstrate blockchain chain transitioning to DAG with narration."""

    def construct(self):
        # Initialize DAG with invisible labels
        dag = KaspaDAG(scene=self)
        dag.config.label_opacity = 0

        # Phase 1: Build initial chain to block height 5
#        self.caption("Starting with genesis block")
        self.narrate(r"Kaspa is Inclusive Bitcoin")
        genesis = dag.queue_block()
        dag.next_step()
        dag.next_step()
        self.wait(1)

#        self.caption("Adding blocks to form a chain")
        self.caption(r"Bitcoin blocks point to a Parent")
        b1 = dag.queue_block(parents=[genesis])
        dag.next_step()
        dag.next_step()
        self.wait(0.5)

        self.caption(r"The result is a Chain")
        b2 = dag.queue_block(parents=[b1])
        dag.next_step()
        dag.next_step()
        self.wait(0.5)

        self.caption(r"This limits how many blocks can be produced")
        b3 = dag.queue_block(parents=[b2])
        dag.next_step()
        dag.next_step()
        self.wait(0.5)

        self.caption(r"Only a single block per round can be accepted")
        b4 = dag.queue_block(parents=[b3])
        dag.next_step()
        dag.next_step()
        self.wait(0.5)

        self.caption(r"If multiple blocks are produced in a single round")
        b5 = dag.queue_block(parents=[b4])
        dag.next_step()
        dag.next_step()
        self.wait(1)

        # Phase 2: Fork happens at block height 5
#        self.caption("A competing block appears - creating a fork")
        self.caption(r"Bitcoin Security is harmed")
        fork_block = dag.queue_block(parents=[b4], name="Fork")
        dag.next_step()
        dag.next_step()
        self.wait(1)

#        self.caption("Main chain continues - fork block abandoned")
        self.caption(r"Wasted Work = Lower Security")
        b6 = dag.queue_block(parents=[b5])
        dag.next_step()
        dag.next_step()
        self.wait(1)

        # 4 more chain blocks (total 5 after fork)
        self.caption(r"So we must avoid forks in Bitcoin")
        b7 = dag.queue_block(parents=[b6])
        dag.next_step()
        dag.next_step()
        self.wait(1)

        self.caption(r"Kaspa fixes this")
        b8 = dag.queue_block(parents=[b7])
        dag.next_step()
        dag.next_step()
        self.wait(1)

        self.caption(r"Kaspa allows blocks to point to multiple parents")
        b9 = dag.queue_block(parents=[b8])
        dag.next_step()
        dag.next_step()
        self.wait(1)

        self.caption(r"Kaspa remains Secure when multiple blocks are created")
        b10 = dag.queue_block(parents=[b9])
        dag.next_step()
        dag.next_step()
        self.wait(1)

        # Phase 3: Transition to inclusive DAG structure
#        self.caption("Network now creates parallel blocks")

        # Round 1: 2 parallel blocks (both reference b10)
        self.caption(r"We could look at Kaspa as Inclusive Bitcoin")
        parallel_1_1 = dag.queue_block(parents=[b10])
        parallel_1_2 = dag.queue_block(parents=[b10])
        dag.next_step()
        dag.next_step()
        dag.next_step()
        dag.next_step()
#        self.wait(1)

#        self.caption("Blocks can now reference multiple parents")

        # Round 2: 2 parallel blocks (both reference both parents from round 1)
        self.caption(r"Instead of wasting work")
        parallel_2_1 = dag.queue_block(parents=[parallel_1_1, parallel_1_2])
        parallel_2_2 = dag.queue_block(parents=[parallel_1_1, parallel_1_2])
        dag.next_step()
        dag.next_step()
        dag.next_step()
        dag.next_step()
#        self.wait(1)

        # Round 3: 3 parallel blocks (all reference both parents from round 2)
        self.caption(r"Work is included")
        parallel_3_1 = dag.queue_block(parents=[parallel_2_1, parallel_2_2])
        parallel_3_2 = dag.queue_block(parents=[parallel_2_1, parallel_2_2])
        parallel_3_3 = dag.queue_block(parents=[parallel_2_1, parallel_2_2])
        dag.next_step()
        dag.next_step()
        dag.next_step()
        dag.next_step()
        dag.next_step()
        dag.next_step()
#        self.wait(1)

#        self.caption("DAG structure continues to expand")

        # Round 4: 3 parallel blocks (all reference all 3 parents from round 3)
        self.caption(r"Solving the Security-Scalability Tradeoff")
        parallel_4_1 = dag.queue_block(parents=[parallel_3_1, parallel_3_2, parallel_3_3])
        parallel_4_2 = dag.queue_block(parents=[parallel_3_1, parallel_3_2, parallel_3_3])
        parallel_4_3 = dag.queue_block(parents=[parallel_3_1, parallel_3_2, parallel_3_3])
        dag.next_step()
        dag.next_step()
        dag.next_step()
        dag.next_step()
        dag.next_step()
        dag.next_step()
#        self.wait(1)

        # Round 5: 4 parallel blocks (all reference all 3 parents from round 4)
        self.caption(r"While maintaining Decentralization")
        parallel_5_1 = dag.queue_block(parents=[parallel_4_1, parallel_4_2, parallel_4_3])
        parallel_5_2 = dag.queue_block(parents=[parallel_4_1, parallel_4_2, parallel_4_3])
        parallel_5_3 = dag.queue_block(parents=[parallel_4_1, parallel_4_2, parallel_4_3])
        parallel_5_4 = dag.queue_block(parents=[parallel_4_1, parallel_4_2, parallel_4_3])
        dag.next_step()
        dag.next_step()
        dag.next_step()
        dag.next_step()
        dag.next_step()
        dag.next_step()
        dag.next_step()
        dag.next_step()
#        self.wait(1)

#        self.caption("Final merge combines all parallel branches")

        # Final: 4 blocks (all reference all 4 parents from round 5)
        self.caption(r"Security-Scalability-Decentralization, Kaspa solved the Trilemma")
        final_1 = dag.queue_block(parents=[parallel_5_1, parallel_5_2, parallel_5_3, parallel_5_4])
        final_2 = dag.queue_block(parents=[parallel_5_1, parallel_5_2, parallel_5_3, parallel_5_4])
        final_3 = dag.queue_block(parents=[parallel_5_1, parallel_5_2, parallel_5_3, parallel_5_4])
        final_4 = dag.queue_block(parents=[parallel_5_1, parallel_5_2, parallel_5_3, parallel_5_4])
        dag.next_step()
        dag.next_step()
        dag.next_step()
        dag.next_step()
        dag.next_step()
        dag.next_step()
        dag.next_step()
        dag.next_step()
        self.wait(5)

        self.clear_caption()