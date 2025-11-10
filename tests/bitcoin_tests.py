# blanim\tests\bitcoin_tests.py

from blanim import *
from blanim.blockDAGs.bitcoin.chain import BitcoinDAG

#TODO verify the problems in the outputs and debug

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
        assert genesis.name == "Genesis", f"Genesis name should be 'Genesis', got {genesis.name}"
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
        assert blocks[0].name == "Genesis"
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
        text = Text("Generate Chain Test Passed", color=GREEN).to_edge(UP)
        self.play(Write(text))
        self.wait(2)


class TestFuzzyBlockRetrieval(HUD2DScene):
    """Test fuzzy matching in get_block()."""

    def construct(self):
        dag = BitcoinDAG(scene=self)

        # Generate 5-block chain
        dag.generate_chain(5)

        # Test exact matches
        assert dag.get_block("Genesis").name == "Genesis"
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
        assert genesis.name == "Genesis"
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
        assert dag.get_block("Genesis") == gen, "Genesis not found in registry"
        assert dag.get_block("B1") == b1, "B1 not found in registry"
        assert dag.get_block("B2") == b2, "B2 not found in registry"
        assert dag.genesis == gen, "Genesis not tracked correctly"
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
        spacing = dag.layout_config.horizontal_spacing
        assert abs(b1_pos[0] - gen_pos[0] - spacing) < 0.01, "B1 horizontal spacing incorrect"
        assert abs(b2_pos[0] - b1_pos[0] - spacing) < 0.01, "B2 horizontal spacing incorrect"

        # Check vertical alignment (should be at genesis_y)
        assert abs(gen_pos[1] - dag.layout_config.genesis_y) < 0.01, "Genesis y position incorrect"
        assert abs(b1_pos[1] - dag.layout_config.genesis_y) < 0.01, "B1 y position incorrect"
        assert abs(b2_pos[1] - dag.layout_config.genesis_y) < 0.01, "B2 y position incorrect"

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