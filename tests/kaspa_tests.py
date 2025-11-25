# blanim/tests/kaspa_tests.py

from blanim import *
from blanim.blockDAGs.kaspa.dag import KaspaDAG

#TODO look at changing animation sequence from create(), move_camera(), vertical_shift()
class TestAutomaticNaming(HUD2DScene):
    """Test automatic block naming with DAG structure."""

    def construct(self):
        dag = KaspaDAG(scene=self)

        # Create genesis
        genesis = dag.add_block()

        # Create blocks with single parent
        b1 = dag.add_block(parents=[genesis])
        b2 = dag.add_block(parents=[genesis])

        # Create block with multiple parents (DAG merge)
        b3 = dag.add_block(parents=[b1, b2])

        # Verify automatic names
        assert genesis.name == "Gen", f"Genesis name should be 'Gen', got {genesis.name}"
        assert b1.name == "B1", f"B1 name should be 'B1', got {b1.name}"
        assert b2.name == "B1a", f"B2 name should be 'B1a', got {b2.name}"
        assert b3.name == "B2", f"B3 name should be 'B2', got {b3.name}"

        # Visual confirmation
        text = Text("Automatic Naming Test Passed", color=GREEN).to_edge(UP)
        self.play(Write(text))
        self.wait(2)


class TestManualNaming(HUD2DScene):
    """Test manual naming with DAG structure."""

    def construct(self):
        dag = KaspaDAG(scene=self)

        # Create blocks with custom names
        genesis = dag.add_block(name="CustomGenesis")
        b1 = dag.add_block(parents=[genesis], name="MyBlock1")
        b2 = dag.add_block(parents=[genesis], name="MyBlock2")
        b3 = dag.add_block(parents=[b1, b2], name="MergeBlock")

        # Verify custom names
        assert genesis.name == "CustomGenesis"
        assert b1.name == "MyBlock1"
        assert b2.name == "MyBlock2"
        assert b3.name == "MergeBlock"

        # Verify retrieval
        assert dag.get_block("CustomGenesis") == genesis
        assert dag.get_block("MergeBlock") == b3

        text = Text("Manual Naming Test Passed", color=GREEN).to_edge(UP)
        self.play(Write(text))
        self.wait(2)


class TestCreateBlockWorkflow(HUD2DScene):
    """Test step-by-step workflow with create_block() and next_step()."""

    def construct(self):
        dag = KaspaDAG(scene=self)

        # Create blocks without animation
        genesis = dag.queue_block()
        self.caption("Genesis created (not animated yet)")
        self.wait(1)

        b1 = dag.queue_block(parents=[genesis])
        b2 = dag.queue_block(parents=[genesis])
        self.caption("B1 and B2 created (not animated yet)")
        self.wait(1)

        # Animate genesis
        self.caption("Animating genesis...")
        dag.next_step()
#        dag.next_step()
        self.wait(1)

        # Animate b1
        self.caption("Animating B1...")
        dag.next_step()
#        dag.next_step()
        self.wait(1)

        # Animate b2
        self.caption("Animating B2...")
        dag.next_step()
        self.wait(1)

        # Auto-queue and execute repositioning
        self.caption("Auto-repositioning...")
        dag.next_step()
        self.wait(1)

        self.clear_caption()
        text = Text("Step-by-step Workflow Test Passed", color=GREEN).to_edge(UP)
        self.play(Write(text))
        self.wait(2)


class TestCatchUpWorkflow(HUD2DScene):
    """Test batch creation with catch_up()."""

    def construct(self):
        dag = KaspaDAG(scene=self)

        # Create multiple blocks without animation
        genesis = dag.queue_block()
        b1 = dag.queue_block(parents=[genesis])
        b2 = dag.queue_block(parents=[genesis])
        b3 = dag.queue_block(parents=[b1, b2])

        self.caption("4 blocks created, none animated yet")
        self.wait(2)

        # Animate everything at once
        self.caption("Catching up - animating all blocks...")
        dag.catch_up()

        self.clear_caption()
        text = Text("Catch-up Workflow Test Passed", color=GREEN).to_edge(UP)
        self.play(Write(text))
        self.wait(2)


class TestAddBlocksMethod(HUD2DScene):
    """Test add_blocks() convenience method."""

    def construct(self):
        dag = KaspaDAG(scene=self)

        genesis = dag.add_block()

        # Batch add multiple blocks
        blocks = dag.add_blocks([
            ([genesis], "B1"),
            ([genesis], "B2"),
            ([genesis], "B3"),
        ])

        # Verify all created
        assert len(blocks) == 3
        assert blocks[0].name == "B1"
        assert blocks[1].name == "B2"
        assert blocks[2].name == "B3"

        # Add merge block
        merge = dag.add_block(parents=blocks, name="Merge")
        assert len(merge.parents) == 3

        text = Text("add_blocks() Test Passed", color=GREEN).to_edge(UP)
        self.play(Write(text))
        self.wait(2)


class TestDAGPositioning(HUD2DScene):
    """Test DAG positioning with multiple parents."""

    def construct(self):
        dag = KaspaDAG(scene=self)

        # Create diamond structure
        genesis = dag.add_block()
        b1 = dag.add_block(parents=[genesis])
        b2 = dag.add_block(parents=[genesis])
        merge = dag.add_block(parents=[b1, b2])

        # Verify positioning
        gen_pos = genesis.visual_block.square.get_center()
        b1_pos = b1.visual_block.square.get_center()
        b2_pos = b2.visual_block.square.get_center()
        merge_pos = merge.visual_block.square.get_center()

        # Merge should be right of rightmost parent (b2)
        assert merge_pos[0] > b2_pos[0], "Merge should be right of b2"

        # b1 and b2 should be at same x (parallel)
        assert abs(b1_pos[0] - b2_pos[0]) < 0.01, "b1 and b2 should be at same x"

        text = Text("DAG Positioning Test Passed", color=GREEN).to_edge(UP)
        self.play(Write(text))
        self.wait(2)


class TestGenerateDAG(HUD2DScene):
    """Test generate_dag() with various parameters."""

    def construct(self):
        dag = KaspaDAG(scene=self)

        genesis = dag.add_block()

        self.caption("Generating DAG with 5 rounds...")
        dag.generate_dag(
            num_rounds=5,
            lambda_parallel=1.5,
            chain_prob=0.6,
            old_tip_prob=0.2
        )

        # Verify structure
        assert len(dag.all_blocks) > 5, "Should have more than 5 blocks"

        # Check for parallel blocks
        has_parallel = any(
            len([b for b in dag.all_blocks if b.weight == block.weight]) > 1
            for block in dag.all_blocks
        )
        assert has_parallel, "Should have some parallel blocks"

        self.clear_caption()
        text = Text("generate_dag() Test Passed", color=GREEN).to_edge(UP)
        self.play(Write(text))
        self.wait(2)


class TestFuzzyBlockRetrieval(HUD2DScene):
    """Test fuzzy matching in get_block()."""

    def construct(self):
        dag = KaspaDAG(scene=self)

        genesis = dag.add_block()
        b1 = dag.add_block(parents=[genesis])
        b2 = dag.add_block(parents=[genesis])
        b3 = dag.add_block(parents=[b1, b2])

        # Test exact matches
        assert dag.get_block("Gen").name == "Gen"
        assert dag.get_block("B1").name == "B1"

        # Test fuzzy matching
        result = dag.get_block("1")
        assert result is not None, "Fuzzy matching should work"

        result = dag.get_block("B10")  # Non-existent
        assert result is not None, "Should return closest match"

        text = Text("Fuzzy Retrieval Test Passed", color=GREEN).to_edge(UP)
        self.play(Write(text))
        self.wait(2)

class TestMoveBlocks(HUD2DScene):
    """Test moving multiple blocks with move()."""

    def construct(self):
        dag = KaspaDAG(scene=self)

        # Step 1: Create blocks at default positions (likely origin)
        genesis = dag.add_block(name="Genesis")
        b1 = dag.add_block(name="B1", parents=[genesis])
        b2 = dag.add_block(name="B2", parents=[genesis])
        b3 = dag.add_block(name="B3", parents=[b1, b2])

        self.wait(1)

        # Step 2: Move blocks to starting positions
        self.caption("Positioning blocks...")
        dag.move(
            [genesis, b1, b2, b3],
            [(0, -2), (-2, 0), (2, 0), (0, 2)]
        )
        self.wait(1)

        # Step 3: Test movements
        self.caption("Moving blocks...")
        dag.move([genesis, b1, b2], [(0, 2), (2, 2), (4, 2)])
        self.wait(1)

        # Move back
        self.caption("Moving back...")
        dag.move([genesis, b1, b2], [(0, -2), (-2, 0), (2, 0)])
        self.wait(1)

        self.clear_caption()
        text = Text("Move Test Passed", color=GREEN).to_edge(UP)
        self.play(Write(text))
        self.wait(2)


class TestMoveBlocksWithBGRectVerify(HUD2DScene):
    """Test moving multiple blocks with move()."""

    def construct(self):
        dag = KaspaDAG(scene=self)

        # Step 1: Create blocks at default positions (likely origin)
        genesis = dag.add_block(name="Genesis")
        b1 = dag.add_block(name="B1", parents=[genesis])
        b2 = dag.add_block(name="B2", parents=[genesis])
        b3 = dag.add_block(name="B3", parents=[b1, b2])

        # Set b2's background rectangle opacity to 0 to verify line rendering
        b2.visual_block.background_rect.set_opacity(0)
        self.wait(1)

        # Step 2: Move blocks to starting positions
        self.caption("Positioning blocks...")
        dag.move(
            [genesis, b1, b2, b3],
            [(0, -2), (-2, 0), (2, 0), (0, 2)]
        )
        self.wait(1)

        # Step 3: Test movements
        self.caption("Moving blocks...")
        dag.move([genesis, b1, b2], [(0, 2), (2, 2), (4, 2)])
        self.wait(1)

        # Move back
        self.caption("Moving back...")
        dag.move([genesis, b1, b2], [(0, -2), (-2, 0), (2, 0)])
        self.wait(1)

        self.clear_caption()
        text = Text("Move Test Passed", color=GREEN).to_edge(UP)
        self.play(Write(text))
        self.wait(2)


class TestPastCone(HUD2DScene):
    """Test get_past_cone() with DAG structure."""

    def construct(self):
        dag = KaspaDAG(scene=self)

        # Create diamond
        genesis = dag.add_block()
        b1 = dag.add_block(parents=[genesis])
        b2 = dag.add_block(parents=[genesis])
        merge = dag.add_block(parents=[b1, b2])
        self.wait(1)

        # Test past cone of merge
        past = dag.get_past_cone(merge)
        assert set(past) == {genesis, b1, b2}, f"Past cone incorrect: {[b.name for b in past]}"

        # Test with string name
        past_str = dag.get_past_cone("B2")
        assert merge in past_str or len(past_str) > 0, "String lookup should work"

        text = Text("Past Cone Test Passed", color=GREEN).to_edge(UP)
        self.play(Write(text))
        self.wait(2)


class TestFutureCone(HUD2DScene):
    """Test get_future_cone() with DAG structure."""

    def construct(self):
        dag = KaspaDAG(scene=self)

        # Create structure
        genesis = dag.add_block()
        b1 = dag.add_block(parents=[genesis])
        b2 = dag.add_block(parents=[genesis])
        merge = dag.add_block(parents=[b1, b2])
        b3 = dag.add_block(parents=[merge])
        self.wait(1)

        # Test future cone of genesis
        future = dag.get_future_cone(genesis)
        assert set(future) == {b1, b2, merge, b3}, f"Future cone incorrect: {[b.name for b in future]}"

        # Test future cone of b1
        future_b1 = dag.get_future_cone(b1)
        assert merge in future_b1 and b3 in future_b1, "b1 future should include merge and b3"

        text = Text("Future Cone Test Passed", color=GREEN).to_edge(UP)
        self.play(Write(text))
        self.wait(2)


class TestAnticone(HUD2DScene):
    """Test get_anticone() with DAG structure."""

    def construct(self):
        dag = KaspaDAG(scene=self)

        # Create structure with anticone
        genesis = dag.add_block()
        b1 = dag.add_block(parents=[genesis])
        b2 = dag.add_block(parents=[genesis])
        b3 = dag.add_block(parents=[b1])
        b4 = dag.add_block(parents=[b2])
        self.wait(1)

        # b3 and b4 are in each other's anticone
        anticone_b3 = dag.get_anticone(b3)
        assert b4 in anticone_b3, "b4 should be in b3's anticone"

        anticone_b4 = dag.get_anticone(b4)
        assert b3 in anticone_b4, "b3 should be in b4's anticone"

        # Genesis should not be in anticone
        assert genesis not in anticone_b3, "Genesis should not be in anticone"

        text = Text("Anticone Test Passed", color=GREEN).to_edge(UP)
        self.play(Write(text))
        self.wait(2)


class TestCameraFollowing(HUD2DScene):
    """Test camera following as DAG grows."""

    def construct(self):
        dag = KaspaDAG(scene=self)

        genesis = dag.add_block()

        # Create long chain to trigger camera movement
        current = genesis
        for i in range(8):
            current = dag.add_block(parents=[current])
            self.wait(0.3)

        text = Text("Camera Following Test Passed", color=GREEN).to_edge(UP)
        self.play(Write(text))
        self.wait(2)


class TestComplexDAGStructure(HUD2DScene):
    """Test complex DAG with multiple merges."""

    def construct(self):
        dag = KaspaDAG(scene=self)

        # Create complex structure
        genesis = dag.add_block()

        # Layer 1: 3 parallel blocks
        b1 = dag.add_block(parents=[genesis])
        b2 = dag.add_block(parents=[genesis])
        b3 = dag.add_block(parents=[genesis])
        self.wait(1)

        # Layer 2: Partial merges
        m1 = dag.add_block(parents=[b1, b2])
        m2 = dag.add_block(parents=[b2, b3])
        self.wait(1)

        # Layer 3: Final merge
        final = dag.add_block(parents=[m1, m2])
        self.wait(1)

        # Verify structure
        assert len(final.parents) == 2
        assert len(dag.get_past_cone(final)) == 6  # All previous blocks

        text = Text("Complex DAG Test Passed", color=GREEN).to_edge(UP)
        self.play(Write(text))
        self.wait(2)


class TestHighlightingPast(HUD2DScene):
    """Test highlighting past cone in DAG structure."""

    def construct(self):
        dag = KaspaDAG(scene=self)

        # Create diamond structure
        genesis = dag.add_block()
        b1 = dag.add_block(parents=[genesis])
        b2 = dag.add_block(parents=[genesis])
        merge = dag.add_block(parents=[b1, b2])
        b3 = dag.add_block(parents=[merge])
        self.wait(1)

        # Highlight past cone of merge block
        self.caption("Highlighting past cone of merge block")
        dag.highlight_past(merge)
        self.wait(5)

        # Reset
        dag.reset_highlighting()
        self.wait(1)
        self.clear_caption()

        text = Text("Past Highlighting Test Passed", color=GREEN).to_edge(UP)
        self.play(Write(text))
        self.wait(2)


class TestHighlightingFuture(HUD2DScene):
    """Test highlighting future cone in DAG structure."""

    def construct(self):
        dag = KaspaDAG(scene=self)

        # Create structure
        genesis = dag.add_block()
        b1 = dag.add_block(parents=[genesis])
        b2 = dag.add_block(parents=[genesis])
        merge = dag.add_block(parents=[b1, b2])
        b3 = dag.add_block(parents=[merge])
        self.wait(1)

        # Highlight future cone of genesis
        self.caption("Highlighting future cone of genesis")
        dag.highlight_future(genesis)
        self.wait(5)

        # Reset
        dag.reset_highlighting()
        self.wait(1)
        self.clear_caption()

        text = Text("Future Highlighting Test Passed", color=GREEN).to_edge(UP)
        self.play(Write(text))
        self.wait(2)


class TestHighlightingAnticone(HUD2DScene):
    """Test highlighting anticone in DAG structure."""

    def construct(self):
        dag = KaspaDAG(scene=self)

        # Create structure with clear anticone
        genesis = dag.add_block()
        b1 = dag.add_block(parents=[genesis])
        b2 = dag.add_block(parents=[genesis])
        b3 = dag.add_block(parents=[b1])
        b4 = dag.add_block(parents=[b2])

        # Add merge block connecting both branches
        merge = dag.add_block(parents=[b3, b4])

        # Add one more block after merge
        final = dag.add_block(parents=[merge])

        self.wait(1)

        # Highlight anticone of b3 (should now show b4 only, not merge or final)
        self.caption("Highlighting anticone of b3 (should show b4)")
        dag.highlight_anticone(b3)
        self.wait(5)

        # Reset
        dag.reset_highlighting()
        self.wait(1)
        self.clear_caption()

        text = Text("Anticone Highlighting Test Passed", color=GREEN).to_edge(UP)
        self.play(Write(text))
        self.wait(2)


class TestHighlightingFutureWithAnticone(HUD2DScene):
    """Test highlighting future cone when focused block has anticone relationships."""

    def construct(self):
        dag = KaspaDAG(scene=self)

        # Create structure with clear anticone (same as TestHighlightingAnticone)
        genesis = dag.add_block()
        b1 = dag.add_block(parents=[genesis])
        b2 = dag.add_block(parents=[genesis])
        b3 = dag.add_block(parents=[b1])
        b4 = dag.add_block(parents=[b2])

        # Add merge block connecting both branches
        merge = dag.add_block(parents=[b3, b4])

        # Add one more block after merge
        final = dag.add_block(parents=[merge])

        self.wait(1)

        # Highlight future cone of b1 (should show b3, merge, final)
        # b4 and b2 are in b1's anticone
        self.caption("Highlighting future cone of b1 (should show b3, merge, final)")
        dag.highlight_future(b1)
        self.wait(5)

        # Reset
        dag.reset_highlighting()
        self.wait(1)
        self.clear_caption()

        # Highlight future cone of b4 (should show merge, final)
        # b3 and b1 are in b4's anticone
        self.caption("Highlighting future cone of b4 (should show merge, final)")
        dag.highlight_future(b4)
        self.wait(5)

        # Reset
        dag.reset_highlighting()
        self.wait(1)
        self.clear_caption()

        text = Text("Future Highlighting with Anticone Test Passed", color=GREEN).to_edge(UP)
        self.play(Write(text))
        self.wait(2)


class TestHighlightingPastWithAnticone(HUD2DScene):
    """Test highlighting past cone when focused block has anticone relationships."""

    def construct(self):
        dag = KaspaDAG(scene=self)

        # Create structure with clear anticone (same as TestHighlightingAnticone)
        genesis = dag.add_block()
        b1 = dag.add_block(parents=[genesis])
        b2 = dag.add_block(parents=[genesis])
        b3 = dag.add_block(parents=[b1])
        b4 = dag.add_block(parents=[b2])

        # Add merge block connecting both branches
        merge = dag.add_block(parents=[b3, b4])

        # Add one more block after merge
        final = dag.add_block(parents=[merge])

        self.wait(1)

        # Highlight past cone of b1 (should show genesis only)
        # b4 and b2 are in b1's anticone
        self.caption("Highlighting past cone of b1 (should show genesis)")
        dag.highlight_past(b1)
        self.wait(5)

        # Reset
        dag.reset_highlighting()
        self.wait(1)
        self.clear_caption()

        # Highlight past cone of b4 (should show b2, genesis)
        # b3 and b1 are in b4's anticone
        self.caption("Highlighting past cone of b4 (should show b2, genesis)")
        dag.highlight_past(b4)
        self.wait(5)

        # Reset
        dag.reset_highlighting()
        self.wait(1)
        self.clear_caption()

        text = Text("Past Highlighting with Anticone Test Passed", color=GREEN).to_edge(UP)
        self.play(Write(text))
        self.wait(2)


class TestQueueRepositioning(HUD2DScene):
    """Test manual repositioning queue control."""

    def construct(self):
        dag = KaspaDAG(scene=self)

        # Create blocks without repositioning
        genesis = dag.queue_block()
        self.caption(r"after create gen, before dag.next\_step")
        dag.next_step()  # Animate genesis create

        b1 = dag.queue_block(parents=[genesis])
        b2 = dag.queue_block(parents=[genesis])
        dag.next_step()  # Animate b1 create
        dag.next_step()  # Animate b2 create

        self.wait(2)

        dag.next_step()  # Animate b2 movement

        self.clear_caption()
        text = Text("Manual Repositioning Test Passed", color=GREEN).to_edge(UP)
        self.play(Write(text))
        self.wait(2)


class TestMultipleParentLines(HUD2DScene):
    """Test that blocks with multiple parents show all parent lines."""

    def construct(self):
        dag = KaspaDAG(scene=self)

        # Create diamond with merge
        genesis = dag.add_block()
        b1 = dag.add_block(parents=[genesis])
        b2 = dag.add_block(parents=[genesis])
        merge = dag.add_block(parents=[b1, b2])
        self.wait(1)

        # Verify merge has 2 parent lines
        assert len(merge.visual_block.parent_lines) == 2, \
            f"Merge should have 2 parent lines, got {len(merge.visual_block.parent_lines)}"

        # Verify lines connect to correct parents
        self.caption("Merge block has 2 parent lines")
        self.wait(2)

        text = Text("Multiple Parent Lines Test Passed", color=GREEN).to_edge(UP)
        self.play(Write(text))
        self.wait(2)


class TestBlockRegistry(HUD2DScene):
    """Test block registration and retrieval."""

    def construct(self):
        dag = KaspaDAG(scene=self)

        # Create blocks
        genesis = dag.add_block()
        b1 = dag.add_block(parents=[genesis])
        b2 = dag.add_block(parents=[genesis])

        # Verify registry
        assert dag.get_block("Gen") == genesis, "Genesis not found"
        assert dag.get_block("B1") == b1, "B1 not found"
        assert dag.genesis == genesis, "Genesis not tracked"
        assert len(dag.all_blocks) == 3, "Block count incorrect"

        text = Text("Registry Test Passed", color=GREEN).to_edge(UP)
        self.play(Write(text))
        self.wait(2)

#TODO does not work (weight not yet implemented)
class TestWeightCalculation(HUD2DScene):
    """Test block weight calculation in DAG."""

    def construct(self):
        dag = KaspaDAG(scene=self)

        # Create diamond structure
        genesis = dag.add_block()
        b1 = dag.add_block(parents=[genesis])
        b2 = dag.add_block(parents=[genesis])
        merge = dag.add_block(parents=[b1, b2])

        # Verify weights (based on rightmost parent)
        assert genesis.weight == 1, f"Genesis weight should be 1, got {genesis.weight}"
        assert b1.weight == 2, f"B1 weight should be 2, got {b1.weight}"
        assert b2.weight == 2, f"B2 weight should be 2, got {b2.weight}"
        assert merge.weight == 3, f"Merge weight should be 3, got {merge.weight}"

        text = Text("Weight Calculation Test Passed", color=GREEN).to_edge(UP)
        self.play(Write(text))
        self.wait(2)

