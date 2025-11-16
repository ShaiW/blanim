# blanim\tests\bitcoin_tests.py

from blanim import *
from blanim.blockDAGs.bitcoin.chain import BitcoinDAG


class TestAutomaticNaming(HUD2DScene):
    """Test automatic block naming with height-based convention."""

    def construct(self):
        dag = BitcoinDAG(scene=self)

        # Create blocks without names - should auto-generate
        genesis = dag.add_block()
        b1 = dag.add_block(parent=genesis)
        b2 = dag.add_block(parent=b1)
        b3 = dag.add_block(parent=b2)

        # Verify automatic names
        assert genesis.name == "Gen", f"Genesis name should be 'Gen', got {genesis.name}"
        assert b1.name == "B1", f"B1 name should be 'B1', got {b1.name}"
        assert b2.name == "B2", f"B2 name should be 'B2', got {b2.name}"
        assert b3.name == "B3", f"B3 name should be 'B3', got {b3.name}"

        # Verify weights match naming
        assert genesis.weight == 1, f"Genesis weight should be 1, got {genesis.weight}"
        assert b1.weight == 2, f"B1 weight should be 2, got {b1.weight}"
        assert b2.weight == 3, f"B2 weight should be 3, got {b2.weight}"
        assert b3.weight == 4, f"B3 weight should be 4, got {b3.weight}"

        # Visual confirmation
        text = Text("Automatic Naming Test Passed", color=GREEN).to_edge(UP)
        self.play(Write(text))
        self.wait(2)


class TestManualNaming(HUD2DScene):
    """Test that manual naming still works when specified."""

    def construct(self):
        dag = BitcoinDAG(scene=self)

        # Create blocks with custom names
        genesis = dag.add_block(name="CustomGenesis")
        b1 = dag.add_block(parent=genesis, name="MyBlock1")
        b2 = dag.add_block(parent=b1, name="MyBlock2")

        # Verify custom names
        assert genesis.name == "CustomGenesis", f"Expected 'CustomGenesis', got {genesis.name}"
        assert b1.name == "MyBlock1", f"Expected 'MyBlock1', got {b1.name}"
        assert b2.name == "MyBlock2", f"Expected 'MyBlock2', got {b2.name}"

        # Verify retrieval by custom names
        assert dag.get_block("CustomGenesis") == genesis
        assert dag.get_block("MyBlock1") == b1
        assert dag.get_block("MyBlock2") == b2

        # Visual confirmation
        text = Text("Manual Naming Test Passed", color=GREEN).to_edge(UP)
        self.play(Write(text))
        self.wait(2)

class TestParallelBlockNaming(HUD2DScene):
    """Test naming convention for parallel blocks (forks)."""

    def construct(self):
        dag = BitcoinDAG(scene=self)

        # Create chain with fork
        genesis = dag.add_block()
        b1 = dag.add_block(parent=genesis)

        # Create parallel blocks at height 2
        b2 = dag.add_block(parent=b1)
        b2_fork = dag.add_block(parent=b1)
        b2_fork2 = dag.add_block(parent=b1)

        # Verify naming convention for parallel blocks
        assert b2.name == "B2", f"First block at height 2 should be 'B2', got {b2.name}"
        assert b2_fork.name == "B2a", f"Second block at height 2 should be 'B2a', got {b2_fork.name}"
        assert b2_fork2.name == "B2b", f"Third block at height 2 should be 'B2b', got {b2_fork2.name}"

        # All should have same weight
        assert b2.weight == b2_fork.weight == b2_fork2.weight == 3

        # Visual confirmation
        text = Text("Parallel Block Naming Test Passed", color=GREEN).to_edge(UP)
        self.play(Write(text))
        self.wait(2)


class TestParallelBlockRepositioningWithChildren(HUD2DScene):
    """Test that parallel blocks don't reposition when one has children."""

    def construct(self):
        dag = BitcoinDAG(scene=self)

        # Create chain with fork
        genesis = dag.add_block()
        b1 = dag.add_block(parent=genesis)

        # Create first block at height 2 and extend it (give it a child)
        b2 = dag.add_block(parent=b1)
        b3 = dag.add_block(parent=b2)  # b2 now has a child

        # Store b2's position before adding parallel block
        b2_pos_before = b2._visual.square.get_center().copy()

        self.wait(1)

        # Add parallel block at height 2 - should NOT trigger repositioning
        # because b2 has a child
        b2_fork = dag.add_block(parent=b1)

        # Store positions after
        b2_pos_after = b2._visual.square.get_center()
        b2_fork_pos = b2_fork._visual.square.get_center()

        # Verify b2 did NOT move (stayed at genesis_y)
        assert abs(b2_pos_before[1] - b2_pos_after[1]) < 0.01, \
            f"b2 should not have moved, but y changed from {b2_pos_before[1]} to {b2_pos_after[1]}"

        # Verify b2 is at genesis_y (the longer chain stays centered)
        assert abs(b2_pos_after[1] - dag.config.genesis_y) < 0.01, \
            f"b2 should be at genesis_y ({dag.config.genesis_y}), but is at {b2_pos_after[1]}"

        # Verify b2_fork is below b2 (offset position maintained)
        assert b2_fork_pos[1] < b2_pos_after[1], \
            f"b2_fork should be below b2, but b2_fork.y={b2_fork_pos[1]}, b2.y={b2_pos_after[1]}"

        # Verify naming
        assert b2.name == "B2", f"Expected 'B2', got {b2.name}"
        assert b2_fork.name == "B2a", f"Expected 'B2a', got {b2_fork.name}"

        # Visual confirmation
        text = Text("No Repositioning With Children Test Passed", color=GREEN, font_size=24)
        text.to_edge(UP)
        self.play(Write(text))
        self.wait(2)


class TestCascadingChainRepositioning(HUD2DScene):
    """Test that adding children to parallel blocks causes cascading repositioning
    so the longest chain is always centered at genesis_y."""

    def construct(self):
        dag = BitcoinDAG(scene=self)

        # Create initial structure: Gen -> B1 -> (B2, B2a, B2b)
        genesis = dag.add_block()
        b1 = dag.add_block(parent=genesis)

        # Create 3 parallel blocks at height 2 (all childless, will be centered)
        b2 = dag.add_block(parent=b1)
        b2a = dag.add_block(parent=b1)
        b2b = dag.add_block(parent=b1)

        self.wait(1)

        # After centering, blocks should be:
        # b2: genesis_y + spacing (top)
        # b2a: genesis_y (middle)
        # b2b: genesis_y - spacing (bottom)

        # Store initial positions
        b2_pos_initial = b2._visual.square.get_center().copy()
        b2a_pos_initial = b2a._visual.square.get_center().copy()
        b2b_pos_initial = b2b._visual.square.get_center().copy()

        self.caption("Initial: 3 parallel childless blocks centered")
        self.wait(2)

        # === TEST 1: Add child to bottom block (b2b) ===
        self.caption("Test 1: Add child to bottom block")
        b3b = dag.add_block(parent=b2b)

        # Verify all blocks at height 2 shifted up so b2b is now at genesis_y
        b2_pos_after_test1 = b2._visual.square.get_center()
        b2a_pos_after_test1 = b2a._visual.square.get_center()
        b2b_pos_after_test1 = b2b._visual.square.get_center()

        # b2b should now be at genesis_y (longest chain)
        assert abs(b2b_pos_after_test1[1] - dag.config.genesis_y) < 0.01, \
            f"b2b should be at genesis_y after getting child, but is at {b2b_pos_after_test1[1]}"

        # All blocks should have shifted by the same amount
        shift_amount = b2b_pos_after_test1[1] - b2b_pos_initial[1]
        assert abs((b2_pos_after_test1[1] - b2_pos_initial[1]) - shift_amount) < 0.01, \
            "b2 should have shifted by same amount as b2b"
        assert abs((b2a_pos_after_test1[1] - b2a_pos_initial[1]) - shift_amount) < 0.01, \
            "b2a should have shifted by same amount as b2b"

        # b3b (child) should also have shifted
        b3b_pos = b3b._visual.square.get_center()

        self.wait(2)

        # === TEST 2: Add child to another block (b2) - creates tied chains ===
        self.caption("Test 2: Add child to top block (creates tie)")
        b3 = dag.add_block(parent=b2)

        # Now b2 and b2b both have 1 child (tied for longest)
        # They should be equidistant from genesis_y
        b2_pos_after_test2 = b2._visual.square.get_center()
        b2a_pos_after_test2 = b2a._visual.square.get_center()
        b2b_pos_after_test2 = b2b._visual.square.get_center()

        # Calculate middle of tied chains
        tied_middle = (b2_pos_after_test2[1] + b2b_pos_after_test2[1]) / 2.0
        assert abs(tied_middle - dag.config.genesis_y) < 0.01, \
            f"Tied chains should be centered around genesis_y, but middle is at {tied_middle}"

        # b2a (shorter chain) should maintain relative position
        # It should be between b2 and b2b
        assert b2b_pos_after_test2[1] < b2a_pos_after_test2[1] < b2_pos_after_test2[1], \
            "b2a should remain between the two tied chains"

        # Verify descendants also shifted
        b3_pos = b3._visual.square.get_center()
        b3b_pos_after_test2 = b3b._visual.square.get_center()

        self.wait(2)

        # === TEST 3: Extend one chain further (b2b wins) ===
        self.caption("Test 3: Extend bottom chain (breaks tie)")
        b4b = dag.add_block(parent=b3b)

        # Now b2b has longest chain (2 children), should be at genesis_y
        b2_pos_after_test3 = b2._visual.square.get_center()
        b2a_pos_after_test3 = b2a._visual.square.get_center()
        b2b_pos_after_test3 = b2b._visual.square.get_center()

        assert abs(b2b_pos_after_test3[1] - dag.config.genesis_y) < 0.01, \
            f"b2b (longest chain) should be at genesis_y, but is at {b2b_pos_after_test3[1]}"

        # b2 and b2a should be above genesis_y (offset from longest chain)
        assert b2_pos_after_test3[1] > dag.config.genesis_y, \
            "b2 should be above genesis_y"
        assert b2a_pos_after_test3[1] > dag.config.genesis_y, \
            "b2a should be above genesis_y"

        # Verify all descendants shifted with their parents
        b3_pos_final = b3._visual.square.get_center()
        b3b_pos_final = b3b._visual.square.get_center()
        b4b_pos_final = b4b._visual.square.get_center()

        # b3b and b4b should be aligned with b2b (same x, offset y)
        assert abs(b3b_pos_final[0] - b2b_pos_after_test3[0] - dag.config.horizontal_spacing) < 0.01, \
            "b3b should be horizontally aligned with b2b's chain"
        assert abs(b4b_pos_final[0] - b3b_pos_final[0] - dag.config.horizontal_spacing) < 0.01, \
            "b4b should be horizontally aligned with b3b's chain"

        self.wait(2)

        # Visual confirmation
        text = Text("Cascading Chain Repositioning Test Passed", color=GREEN, font_size=24)
        text.to_edge(UP)
        self.play(Write(text))
        self.wait(2)


class TestThreeWayTieResolution(HUD2DScene):
    """Test three parallel forks with equal length, then resolve the tie."""

    def construct(self):
        dag = BitcoinDAG(scene=self)

        # Create initial structure: Gen -> B1 -> (B2, B2a, B2b)
        genesis = dag.add_block()
        b1 = dag.add_block(parent=genesis)

        # Create 3 parallel blocks
        b2 = dag.add_block(parent=b1)
        b2a = dag.add_block(parent=b1)
        b2b = dag.add_block(parent=b1)

        # All should be centered around genesis_y
        b2_pos_1 = b2._visual.square.get_center()
        b2a_pos_1 = b2a._visual.square.get_center()
        b2b_pos_1 = b2b._visual.square.get_center()

        # Calculate middle position
        middle_y = (b2_pos_1[1] + b2a_pos_1[1] + b2b_pos_1[1]) / 3
        assert abs(middle_y - dag.config.genesis_y) < 0.01, \
            "Three childless blocks should be centered around genesis_y"

        self.wait(1)

        # Extend all three forks by one block each (maintain tie)
        b3 = dag.add_block(parent=b2)
        b3a = dag.add_block(parent=b2a)
        b3b = dag.add_block(parent=b2b)

        # All should still be centered around genesis_y
        b2_pos_2 = b2._visual.square.get_center()
        b2a_pos_2 = b2a._visual.square.get_center()
        b2b_pos_2 = b2b._visual.square.get_center()

        middle_y_2 = (b2_pos_2[1] + b2a_pos_2[1] + b2b_pos_2[1]) / 3
        assert abs(middle_y_2 - dag.config.genesis_y) < 0.01, \
            "Three tied chains should remain centered around genesis_y"

        self.wait(1)

        # Extend middle fork (b2a) to break the tie
        b4 = dag.add_block(parent=b3)

        # b2 should now be at genesis_y (longest chain with 4 blocks)
        b2_pos_3 = b2._visual.square.get_center()
        assert abs(b2_pos_3[1] - dag.config.genesis_y) < 0.01, \
            "b2 should be at genesis_y after breaking the tie (longest chain)"

        # b2a and b2b should be above and below genesis_y respectively
        b2a_pos_3 = b2a._visual.square.get_center()
        b2b_pos_3 = b2b._visual.square.get_center()
        assert b2a_pos_3[1] > dag.config.genesis_y or b2a_pos_3[1] < dag.config.genesis_y, \
            "b2a should be offset from genesis_y"
        assert b2b_pos_3[1] > dag.config.genesis_y or b2b_pos_3[1] < dag.config.genesis_y, \
            "b2b should be offset from genesis_y"

        # Verify descendants are properly aligned
        b4_pos = b4._visual.square.get_center()
        assert abs(b4_pos[0] - b3._visual.square.get_center()[0] - dag.config.horizontal_spacing) < 0.01, \
            "b4 should be horizontally aligned with b3"

        self.wait(2)

        text = Text("Three-Way Tie Resolution Test Passed", color=GREEN, font_size=24)
        text.to_edge(UP)
        self.play(Write(text))
        self.wait(2)


class TestAlternatingForkExtensions(HUD2DScene):
    """Test alternating extensions between two competing forks."""

    def construct(self):
        dag = BitcoinDAG(scene=self)

        # Create initial structure: Gen -> B1 -> (B2, B2a)
        genesis = dag.add_block()
        b1 = dag.add_block(parent=genesis)

        # Create 2 parallel blocks
        b2 = dag.add_block(parent=b1)
        b2a = dag.add_block(parent=b1)

        self.wait(1)

        # Extend b2 (top fork)
        b3 = dag.add_block(parent=b2)
        b2_pos_1 = b2._visual.square.get_center()
        assert abs(b2_pos_1[1] - dag.config.genesis_y) < 0.01, \
            "b2 should be at genesis_y after first extension"

        self.wait(0.5)

        # Extend b2a (bottom fork) to tie
        b3a = dag.add_block(parent=b2a)
        b2_pos_2 = b2._visual.square.get_center()
        b2a_pos_2 = b2a._visual.square.get_center()
        # Both should be equidistant from genesis_y
        assert abs(abs(b2_pos_2[1] - dag.config.genesis_y) - abs(b2a_pos_2[1] - dag.config.genesis_y)) < 0.01, \
            "Tied chains should be equidistant from genesis_y"

        self.wait(0.5)

        # Extend b2 again (top fork takes lead)
        b4 = dag.add_block(parent=b3)
        b2_pos_3 = b2._visual.square.get_center()
        assert abs(b2_pos_3[1] - dag.config.genesis_y) < 0.01, \
            "b2 should be at genesis_y after taking lead"

        self.wait(0.5)

        # Extend b2a twice (bottom fork overtakes)
        b4a = dag.add_block(parent=b3a)
        b5a = dag.add_block(parent=b4a)
        b2a_pos_4 = b2a._visual.square.get_center()
        assert abs(b2a_pos_4[1] - dag.config.genesis_y) < 0.01, \
            "b2a should be at genesis_y after overtaking"

        # Verify b2 is now above genesis_y
        b2_pos_4 = b2._visual.square.get_center()
        assert b2_pos_4[1] > dag.config.genesis_y, \
            "b2 should be above genesis_y after being overtaken"

        self.wait(2)

        text = Text("Alternating Fork Extensions Test Passed", color=GREEN, font_size=24)
        text.to_edge(UP)
        self.play(Write(text))
        self.wait(2)


class TestMultipleCompetingForksWithDifferentDepths(HUD2DScene):
    """Test multiple parallel forks growing to different depths."""

    def construct(self):
        dag = BitcoinDAG(scene=self)

        # Create initial structure: Gen -> B1 -> (B2, B2a, B2b)
        genesis = dag.add_block()
        b1 = dag.add_block(parent=genesis)

        # Create 3 parallel blocks at height 2
        b2 = dag.add_block(parent=b1)
        b2a = dag.add_block(parent=b1)
        b2b = dag.add_block(parent=b1)

        self.wait(1)

        # Extend b2 chain (middle fork) by 2 blocks
        b3 = dag.add_block(parent=b2)
        b4 = dag.add_block(parent=b3)

        # Verify b2 is at genesis_y (longest chain)
        b2_pos = b2._visual.square.get_center()
        assert abs(b2_pos[1] - dag.config.genesis_y) < 0.01, \
            f"b2 should be at genesis_y after extending its chain"

        self.wait(1)

        # Extend b2b chain (bottom fork) by 3 blocks to overtake
        b3b = dag.add_block(parent=b2b)
        b4b = dag.add_block(parent=b3b)
        b5b = dag.add_block(parent=b4b)

        # Verify b2b is now at genesis_y (new longest chain)
        b2b_pos = b2b._visual.square.get_center()
        assert abs(b2b_pos[1] - dag.config.genesis_y) < 0.01, \
            f"b2b should be at genesis_y after becoming longest chain"

        # Verify b2 and b2a are above genesis_y
        b2_pos_final = b2._visual.square.get_center()
        b2a_pos_final = b2a._visual.square.get_center()
        assert b2_pos_final[1] > dag.config.genesis_y, \
            "b2 should be above genesis_y"
        assert b2a_pos_final[1] > dag.config.genesis_y, \
            "b2a should be above genesis_y"

        # Verify all descendants are properly aligned
        b4_pos = b4._visual.square.get_center()
        b5b_pos = b5b._visual.square.get_center()
        assert abs(b4_pos[0] - b3._visual.square.get_center()[0] - dag.config.horizontal_spacing) < 0.01, \
            "b4 should be horizontally aligned with b3"
        assert abs(b5b_pos[0] - b4b._visual.square.get_center()[0] - dag.config.horizontal_spacing) < 0.01, \
            "b5b should be horizontally aligned with b4b"

        self.wait(2)

        text = Text("Multiple Competing Forks Test Passed", color=GREEN, font_size=24)
        text.to_edge(UP)
        self.play(Write(text))
        self.wait(2)


#TODO refine camera following blocks and determine timing
class TestGenerateChain(HUD2DScene):
    """Test bulk chain generation with generate_chain()."""

    def construct(self):
        dag = BitcoinDAG(scene=self)

        # Generate 10-block chain
        blocks = dag.generate_chain(10)

        # Verify correct number of blocks
        assert len(blocks) == 10, f"Expected 10 blocks, got {len(blocks)}"
        assert len(dag.all_blocks) == 10, f"DAG should track 10 blocks, got {len(dag.all_blocks)}"

        # Verify naming sequence
        assert blocks[0].name == "Gen"
        assert blocks[1].name == "B1"
        assert blocks[5].name == "B5"
        assert blocks[9].name == "B9"

        # Verify weights
        for i, block in enumerate(blocks):
            expected_weight = i + 1
            assert block.weight == expected_weight, f"Block {i} weight should be {expected_weight}, got {block.weight}"

            # Verify parent-child relationships
        for i in range(1, len(blocks)):
            assert blocks[i].parent == blocks[i - 1], f"Block {i} parent incorrect"

            # Visual confirmation
#        text = Text("Generate Chain Test Passed", color=GREEN).to_edge(UP)# this places text at world coords instead of camera coords
#        self.play(Write(text))
        self.narrate("Generate Chain Test Passed")
        self.wait(2)


class TestFuzzyBlockRetrieval(HUD2DScene):
    """Test fuzzy matching in get_block()."""

    def construct(self):
        dag = BitcoinDAG(scene=self)

        # Generate 5-block chain
        dag.generate_chain(5)

        # Test exact matches
        assert dag.get_block("Gen").name == "Gen"
        assert dag.get_block("B2").name == "B2"
        assert dag.get_block("B4").name == "B4"

        # Test fuzzy matching - requesting non-existent block
        # Should return closest block by height
        result = dag.get_block("B10")  # Doesn't exist, should return B4 (closest)
        assert result is not None, "Fuzzy matching should return a block"
        assert result.name == "B4", f"B10 should fuzzy match to B4, got {result.name}"

        # Test fuzzy matching with lower height
        result = dag.get_block("B3")
        assert result.name == "B3", f"B3 should match exactly, got {result.name}"

        # Visual confirmation
        text = Text("Fuzzy Retrieval Test Passed", color=GREEN).to_edge(UP)
        self.play(Write(text))
        self.wait(2)


class BasicBitcoinChain(HUD2DScene):
    """Test basic chain creation with automatic naming."""

    def construct(self):
        dag = BitcoinDAG(scene=self)

        # Create genesis block (automatic naming)
        genesis = dag.add_block()
        self.wait(1)

        # Add blocks to chain (automatic naming)
        b1 = dag.add_block(parent=genesis)
        self.wait(1)

        b2 = dag.add_block(parent=b1)
        self.wait(1)

        b3 = dag.add_block(parent=b2)
        self.wait(1)

        # Verify automatic names
        assert genesis.name == "Gen"
        assert b1.name == "B1"
        assert b2.name == "B2"
        assert b3.name == "B3"


class TestBlockRegistry(HUD2DScene):
    """Test block registration and retrieval with automatic naming."""

    def construct(self):
        dag = BitcoinDAG(scene=self)

        # Create blocks with automatic naming
        gen = dag.add_block()
        b1 = dag.add_block(parent=gen)
        b2 = dag.add_block(parent=b1)

        # Verify registry with automatic names
        assert dag.get_block("Gen") == gen, "Gen not found in registry"
        assert dag.get_block("B1") == b1, "B1 not found in registry"
        assert dag.get_block("B2") == b2, "B2 not found in registry"
        assert dag.genesis == gen, "Gen not tracked correctly"
        assert len(dag.all_blocks) == 3, "all_blocks count incorrect"

        # Add success indicator
        text = Text("Registry Test Passed", color=GREEN).to_edge(UP)
        self.play(Write(text))
        self.wait(2)


class TestMovement(HUD2DScene):
    """Test multi-block movement with automatic naming."""

    def construct(self):
        dag = BitcoinDAG(scene=self)

        # Create chain with automatic naming
        gen = dag.add_block()
        b1 = dag.add_block(parent=gen)
        b2 = dag.add_block(parent=b1)
        self.wait(1)

        # Move blocks ONE AT A TIME
        self.caption("Moving Genesis block")
        dag.move([gen], [(0, 2)])
        self.wait(1)

        self.caption("Moving B1 block")
        dag.move([b1], [(2, 2)])
        self.wait(1)

        self.caption("Moving B2 block")
        dag.move([b2], [(4, 2)])
        self.wait(1)

        self.clear_caption()
        self.wait(0.5)

        # Move back down
        self.caption("Moving back: Genesis")
        dag.move([gen], [(0, -2)])
        self.wait(1)

        self.caption("Moving back: B1")
        dag.move([b1], [(2, -2)])
        self.wait(1)

        self.caption("Moving back: B2")
        dag.move([b2], [(4, -2)])
        self.wait(1)

        self.clear_caption()

        # Visual confirmation
        passed_text = Text("Passed: Lines followed blocks correctly", color=GREEN, font_size=24)
        passed_text.to_edge(DOWN)
        self.play(Write(passed_text))
        self.wait(1)


class TestTraversal(HUD2DScene):
    """Test graph traversal methods with automatic naming."""

    def construct(self):
        dag = BitcoinDAG(scene=self)

        # Create chain using generate_chain
        blocks = dag.generate_chain(4)
        gen, b1, b2, b3 = blocks
        self.wait(1)

        # Test get_past_cone
        past = dag.get_past_cone(b3)
        assert set(past) == {gen, b1, b2}, f"Past cone incorrect: {[b.name for b in past]}"

        # Test get_future_cone
        future = dag.get_future_cone(gen)
        assert set(future) == {b1, b2, b3}, f"Future cone incorrect: {[b.name for b in future]}"

        # Test get_anticone (should be empty for linear chain)
        anticone = dag.get_anticone(b2)
        assert len(anticone) == 0, f"Anticone should be empty for linear chain: {[b.name for b in anticone]}"

        # Visual confirmation
        text = Text("Traversal Tests Passed", color=GREEN).to_edge(UP)
        self.play(Write(text))
        self.wait(2)

class TestHighlighting(HUD2DScene):
    """Test visual highlighting system with automatic naming."""

    def construct(self):
        dag = BitcoinDAG(scene=self)

        # Create chain using generate_chain
        blocks = dag.generate_chain(5)
        gen, b1, b2, b3, b4 = blocks
        self.wait(1)

        # Test 1: Genesis past (edge case - should be empty)
        self.caption("Test 1: Genesis past cone (empty)")
        dag.highlight_past(gen)
        self.wait(2)
        dag.reset_highlighting()
        self.wait(1)
        self.clear_caption()

        # Test 2: Genesis future (should highlight all blocks)
        self.caption("Test 2: Genesis future cone (all blocks)")
        dag.highlight_future(gen)
        self.wait(2)
        dag.reset_highlighting()
        self.wait(1)
        self.clear_caption()

        # Test 3: B2 past
        self.caption("Test 3: B2 past cone")
        dag.highlight_past(b2)
        self.wait(2)
        dag.reset_highlighting()
        self.wait(1)
        self.clear_caption()

        # Test 4: B2 future
        self.caption("Test 4: B2 future cone")
        dag.highlight_future(b2)
        self.wait(2)
        dag.reset_highlighting()
        self.wait(1)
        self.clear_caption()

        # Test 5: B4 past (should highlight all blocks)
        self.caption("Test 5: B4 past cone (all blocks)")
        dag.highlight_past(b4)
        self.wait(2)
        dag.reset_highlighting()
        self.wait(1)
        self.clear_caption()

        # Test 6: B4 future (edge case - should be empty)
        self.caption("Test 6: B4 future cone (empty)")
        dag.highlight_future(b4)
        self.wait(2)
        dag.reset_highlighting()
        self.wait(1)
        self.clear_caption()

        # Test 7: Anticone test (should be empty for linear chain)
        self.caption("Test 7: B2 anticone (empty for linear chain)")
        dag.highlight_anticone(b2)
        self.wait(2)
        dag.reset_highlighting()
        self.wait(1)
        self.clear_caption()

        # Final confirmation
        passed_text = Text("All edge cases tested!", color=GREEN, font_size=24)
        passed_text.to_edge(DOWN)
        self.play(Write(passed_text))
        self.wait(1)


class TestWeightCalculation(HUD2DScene):
    """Test that block weights (heights) are calculated correctly with automatic naming."""

    def construct(self):
        dag = BitcoinDAG(scene=self)

        # Create chain using generate_chain
        blocks = dag.generate_chain(4)
        gen, b1, b2, b3 = blocks

        # Verify weights
        assert gen.weight == 1, f"Genesis weight should be 1, got {gen.weight}"
        assert b1.weight == 2, f"B1 weight should be 2, got {b1.weight}"
        assert b2.weight == 3, f"B2 weight should be 3, got {b2.weight}"
        assert b3.weight == 4, f"B3 weight should be 4, got {b3.weight}"

        # Success indicator
        text = Text("Weight Calculation Passed", color=GREEN).to_edge(UP)
        self.play(Write(text))
        self.wait(2)


class TestAutoPositioning(HUD2DScene):
    """Test automatic position calculation using layout_config."""

    def construct(self):
        dag = BitcoinDAG(scene=self)

        # Create blocks without specifying positions
        gen = dag.add_block()
        b1 = dag.add_block(parent=gen)
        b2 = dag.add_block(parent=b1)

        # Verify positions are auto-calculated
        gen_pos = gen._visual.square.get_center()
        b1_pos = b1._visual.square.get_center()
        b2_pos = b2._visual.square.get_center()

        # Check horizontal spacing
        spacing = dag.config.horizontal_spacing
        assert abs(b1_pos[0] - gen_pos[0] - spacing) < 0.01, "B1 horizontal spacing incorrect"
        assert abs(b2_pos[0] - b1_pos[0] - spacing) < 0.01, "B2 horizontal spacing incorrect"

        # Check vertical alignment (should be at genesis_y)
        assert abs(gen_pos[1] - dag.config.genesis_y) < 0.01, "Genesis y position incorrect"
        assert abs(b1_pos[1] - dag.config.genesis_y) < 0.01, "B1 y position incorrect"
        assert abs(b2_pos[1] - dag.config.genesis_y) < 0.01, "B2 y position incorrect"

        text = Text("Auto-Positioning Passed", color=GREEN).to_edge(UP)
        self.play(Write(text))
        self.wait(2)


class TestParentChildRelationships(HUD2DScene):
    """Test that parent-child relationships are correctly established."""

    def construct(self):
        dag = BitcoinDAG(scene=self)

        # Create chain with automatic naming
        gen = dag.add_block()
        b1 = dag.add_block(parent=gen)
        b2 = dag.add_block(parent=b1)

        # Verify parent relationships
        assert b1.parent == gen, "B1 parent should be genesis"
        assert b2.parent == b1, "B2 parent should be B1"
        assert gen.parent is None, "Genesis should have no parent"

        # Verify children relationships
        assert b1 in gen.children, "B1 should be in genesis children"
        assert b2 in b1.children, "B2 should be in B1 children"
        assert len(gen.children) == 1, "Genesis should have 1 child"
        assert len(b1.children) == 1, "B1 should have 1 child"
        assert len(b2.children) == 0, "B2 should have no children"

        text = Text("Parent-Child Tests Passed", color=GREEN).to_edge(UP)
        self.play(Write(text))
        self.wait(2)