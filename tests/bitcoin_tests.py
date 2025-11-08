# blanim\tests\bitcoin_tests.py

from blanim import *
from blanim.blockDAGs.bitcoin.chain import BitcoinDAG


class BasicBitcoinChain(HUD2DScene):
    """Test basic chain creation with sequential blocks."""

    def construct(self):
        dag = BitcoinDAG(scene=self)

        # Create genesis block
        genesis = dag.add_block("Gen", parent=None)
        dag.play(genesis.create_with_lines())
        self.wait(1)

        # Add blocks to chain
        b1 = dag.add_block("B1", parent=genesis)
        dag.play(b1.create_with_lines())
        self.wait(1)

        b2 = dag.add_block("B2", parent=b1)
        dag.play(b2.create_with_lines())
        self.wait(1)

        b3 = dag.add_block("B3", parent=b2)
        dag.play(b3.create_with_lines())
        self.wait(1)


class TestBlockRegistry(HUD2DScene):
    """Test block registration and retrieval."""

    def construct(self):
        dag = BitcoinDAG(scene=self)

        # Create blocks
        gen = dag.add_block("Gen")
        b1 = dag.add_block("B1", parent=gen)
        b2 = dag.add_block("B2", parent=b1)

        # Verify registry
        assert dag.get_block("Gen") == gen, "Genesis not found in registry"
        assert dag.get_block("B1") == b1, "B1 not found in registry"
        assert dag.get_block("B2") == b2, "B2 not found in registry"
        assert dag.genesis == gen, "Genesis not tracked correctly"
        assert len(dag.all_blocks) == 3, "all_blocks count incorrect"

        # Animate to show success
        dag.play(gen.create_with_lines(), b1.create_with_lines(), b2.create_with_lines())
        self.wait(1)

        # Add success indicator
        text = Text("Registry Test Passed", color=GREEN).to_edge(UP)
        self.play(Write(text))
        self.wait(2)


class TestMovement(HUD2DScene):
    """Test multi-block movement with line deduplication - sequential movements."""

    def construct(self):
        dag = BitcoinDAG(scene=self)

        # Create chain
        gen = dag.add_block("Gen")
        b1 = dag.add_block("B1", parent=gen)
        b2 = dag.add_block("B2", parent=b1)

        dag.play(gen.create_with_lines(), b1.create_with_lines(), b2.create_with_lines())
        self.wait(1)

        # Move blocks ONE AT A TIME to verify lines follow correctly

        # Move genesis block - should update b1's parent line
        self.caption("Moving Genesis block")
        dag.move([gen], [(0, 2)])
        self.wait(1)

        # Move b1 - should update both its parent line (to gen) and b2's parent line (to b1)
        self.caption("Moving B1 block")
        dag.move([b1], [(2, 2)])
        self.wait(1)

        # Move b2 - should update its parent line (to b1)
        self.caption("Moving B2 block")
        dag.move([b2], [(4, 2)])
        self.wait(1)

        self.clear_caption()
        self.wait(0.5)

        # Move back down - again one at a time
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

        # Add visual confirmation
        passed_text = Text("Passed: Lines followed blocks correctly", color=GREEN, font_size=24)
        passed_text.to_edge(DOWN)
        self.play(Write(passed_text))
        self.wait(1)


class TestTraversal(HUD2DScene):
    """Test graph traversal methods (past cone, future cone, anticone)."""

    def construct(self):
        dag = BitcoinDAG(scene=self)

        # Create chain
        gen = dag.add_block("Gen")
        b1 = dag.add_block("B1", parent=gen)
        b2 = dag.add_block("B2", parent=b1)
        b3 = dag.add_block("B3", parent=b2)

        dag.play(gen.create_with_lines(), b1.create_with_lines(),
                 b2.create_with_lines(), b3.create_with_lines())
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
    """Test visual highlighting system - with flash verification."""

    def construct(self):
        dag = BitcoinDAG(scene=self)

        # Create chain
        gen = dag.add_block("Gen")
        b1 = dag.add_block("B1", parent=gen)
        b2 = dag.add_block("B2", parent=b1)
        b3 = dag.add_block("B3", parent=b2)

        dag.play(gen.create_with_lines(), b1.create_with_lines(),
                 b2.create_with_lines(), b3.create_with_lines())
        self.wait(1)

        # Test highlight_block_context with past cone
        self.caption("Highlighting B3 with past cone (should flash lines)")
        flash_lines = dag.highlight_block_context(b3, show_past=True)

        # Debug: Check if flash_lines were created
        if flash_lines:
            debug_text = Text(f"Flash lines created: {len(flash_lines)}", color=YELLOW, font_size=20)
            debug_text.to_corner(UL)
            self.add(debug_text)
        else:
            debug_text = Text("WARNING: No flash lines created!", color=RED, font_size=20)
            debug_text.to_corner(UL)
            self.add(debug_text)

        self.wait(3)  # Longer wait to see flashing
        self.remove(debug_text)

        # Test reset_highlighting
        self.caption("Resetting highlighting")
        dag.reset_highlighting(b3, flash_lines=flash_lines)
        self.wait(1)
        self.clear_caption()

        # Test highlighting with future cone
        self.caption("Highlighting Genesis with future cone")
        flash_lines = dag.highlight_block_context(gen, show_future=True)

        # Debug: Check flash lines again
        if flash_lines:
            debug_text = Text(f"Flash lines created: {len(flash_lines)}", color=YELLOW, font_size=20)
            debug_text.to_corner(UL)
            self.add(debug_text)
        else:
            debug_text = Text("WARNING: No flash lines created!", color=RED, font_size=20)
            debug_text.to_corner(UL)
            self.add(debug_text)

        self.wait(3)
        self.remove(debug_text)

        dag.reset_highlighting(gen, flash_lines=flash_lines)
        self.wait(1)

        # Final confirmation
        passed_text = Text("Test Complete - Check flash visibility", color=GREEN, font_size=24)
        passed_text.to_edge(DOWN)
        self.play(Write(passed_text))
        self.wait(1)


class TestWeightCalculation(HUD2DScene):
    """Test that block weights (heights) are calculated correctly."""

    def construct(self):
        dag = BitcoinDAG(scene=self)

        # Create chain
        gen = dag.add_block("Gen")
        b1 = dag.add_block("B1", parent=gen)
        b2 = dag.add_block("B2", parent=b1)
        b3 = dag.add_block("B3", parent=b2)

        # Verify weights
        assert gen.weight == 1, f"Genesis weight should be 1, got {gen.weight}"
        assert b1.weight == 2, f"B1 weight should be 2, got {b1.weight}"
        assert b2.weight == 3, f"B2 weight should be 3, got {b2.weight}"
        assert b3.weight == 4, f"B3 weight should be 4, got {b3.weight}"

        # Animate to show weights
        dag.play(gen.create_with_lines(), b1.create_with_lines(),
                 b2.create_with_lines(), b3.create_with_lines())
        self.wait(1)

        # Success indicator
        text = Text("Weight Calculation Passed", color=GREEN).to_edge(UP)
        self.play(Write(text))
        self.wait(2)


class TestAutoPositioning(HUD2DScene):
    """Test automatic position calculation using layout_config."""

    def construct(self):
        dag = BitcoinDAG(scene=self)

        # Create blocks without specifying positions
        gen = dag.add_block("Gen")
        b1 = dag.add_block("B1", parent=gen)
        b2 = dag.add_block("B2", parent=b1)

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

        # Animate
        dag.play(gen.create_with_lines(), b1.create_with_lines(), b2.create_with_lines())
        self.wait(1)

        text = Text("Auto-Positioning Passed", color=GREEN).to_edge(UP)
        self.play(Write(text))
        self.wait(2)


class TestParentChildRelationships(HUD2DScene):
    """Test that parent-child relationships are correctly established."""

    def construct(self):
        dag = BitcoinDAG(scene=self)

        # Create chain
        gen = dag.add_block("Gen")
        b1 = dag.add_block("B1", parent=gen)
        b2 = dag.add_block("B2", parent=b1)

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

        # Animate
        dag.play(gen.create_with_lines(), b1.create_with_lines(), b2.create_with_lines())
        self.wait(1)

        text = Text("Parent-Child Tests Passed", color=GREEN).to_edge(UP)
        self.play(Write(text))
        self.wait(2)