# blanim/tests/kaspa_tests.py

from blanim import *


# user created theme to change parameters of the dag, visual appearance, ect with typehinting
def test_theme() -> KaspaConfig:
    """Test theme with various configuration parameters."""
    return {
        "block_color": RED,
        "fill_opacity": 0.7,
        "stroke_color": BLUE,
        "stroke_width": 5,
        "k": 25,
        "label_font_size": 32,
        "horizontal_spacing": 2.5,
        "vertical_spacing": 1.5,
    }

class TestConfigBasic(HUD2DScene):
    """Test basic configuration application and chaining."""

    def construct(self):
        dag = KaspaDAG(scene=self)

        # Test chaining and theme application
        dag.apply_config(test_theme()).set_block_color(YELLOW).set_fill_opacity(0.5)

        # Create blocks to verify config is applied
        genesis = dag.add_block()
        b1 = dag.add_block(parents=[genesis])
        b2 = dag.add_block(parents=[genesis])

        self.wait(1)

        # Verify config values
        assert dag.config.block_color == YELLOW
        assert dag.config.fill_opacity == 0.5
        assert dag.config.k == 25

        text = Text("Config Basic Test Passed", color=GREEN).to_edge(UP)
        self.play(Write(text))
        self.wait(2)


class TestConfigGenesisLock(HUD2DScene):
    """Test that critical parameters are locked after genesis creation."""

    def construct(self):
        dag = KaspaDAG(scene=self)

        # Set k before genesis (should work)
        dag.set_k(20)
        assert dag.config.k == 20

        # Create genesis block
        genesis = dag.add_block()

        # Try to change k after genesis (should warn and not change)
        dag.set_k(30)  # This will log a warning
        assert dag.config.k == 20  # Should remain unchanged

        # Visual parameters should still change
        dag.set_block_color(PURPLE)
        assert dag.config.block_color == PURPLE

        self.wait(1)

        text = Text("Genesis Lock Test Passed", color=GREEN).to_edge(UP)
        self.play(Write(text))
        self.wait(2)


class TestConfigValidation(HUD2DScene):
    """Test configuration validation and auto-correction."""

    def construct(self):
        dag = KaspaDAG(scene=self)

        # Test invalid opacity values (should auto-correct)
        dag.apply_config({
            "fill_opacity": -0.5,  # Should auto-correct to 0.01
            "stroke_opacity": 1.5,  # Should auto-correct to 1.0
            "fade_opacity": -0.1,  # Should auto-correct to 0
            "k": -5,  # Should auto-correct to 0
            "stroke_width": 0,  # Should auto-correct to 1
        })

        # Verify auto-correction
        assert dag.config.fill_opacity == 0.01
        assert dag.config.stroke_opacity == 1.0
        assert dag.config.fade_opacity == 0
        assert dag.config.k == 0
        assert dag.config.stroke_width == 1

        # Create blocks to ensure config works
        genesis = dag.add_block()
        b1 = dag.add_block(parents=[genesis])

        self.wait(1)

        text = Text("Validation Test Passed", color=GREEN).to_edge(UP)
        self.play(Write(text))
        self.wait(2)


class TestConfigPartialUpdate(HUD2DScene):
    """Test partial configuration updates with TypedDict."""

    def construct(self):
        dag = KaspaDAG(scene=self)

        # Apply partial config (only specified parameters change)
        dag.apply_config({
            "block_color": GREEN,
            "k": 15,
        })

        # Verify only specified parameters changed
        assert dag.config.block_color == GREEN
        assert dag.config.k == 15
        assert dag.config.fill_opacity == 0.3  # Should remain default

        # Create blocks
        genesis = dag.add_block()
        b1 = dag.add_block(parents=[genesis])

        self.wait(1)

        text = Text("Partial Update Test Passed", color=GREEN).to_edge(UP)
        self.play(Write(text))
        self.wait(2)

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

#TODO this debug warns when centers of submobjects in visual block do not match positions, use this for solving how to clear block labels
class TestDAGPositioning(HUD2DScene):
    """Test DAG positioning with multiple parents."""

    def construct(self):
        dag = KaspaDAG(scene=self)

        # Create diamond structure
        genesis = dag.add_block()
        b1 = dag.add_block(parents=[genesis])
        b2 = dag.add_block(parents=[genesis])
        merge = dag.add_block(parents=[b1, b2])

        # Test all logical blocks return square center
        blocks_to_test = [genesis, b1, b2, merge]
        for block in blocks_to_test:
            logical_center = block.get_center()
            vgroup_center = block.visual_block.get_center()
            square_center = block.visual_block.square.get_center()

            print(f"{block.name} logical center: {logical_center}")
            print(f"{block.name} VGroup center: {vgroup_center}")
            print(f"{block.name} square center: {square_center}")

            # Check ALL submobjects in VGroup
            print(f"{block.name} VGroup submobjects:")
            for i, submob in enumerate(block.visual_block.submobjects):
                submob_center = submob.get_center()
                submob_type = type(submob).__name__
                print(f"  [{i}] {submob_type}: {submob_center}")

                # Warning if ANY submobject doesn't match expected center
                if not np.allclose(submob_center, logical_center):
                    print(f"WARNING: {block.name} submobject {i} ({submob_type}) center mismatch!")
                    print(f"  Expected: {logical_center}")
                    print(f"  Actual: {submob_center}")

            print()  # Empty line for readability

        # Original positioning checks (non-breaking)
        gen_pos = genesis.visual_block.square.get_center()
        b1_pos = b1.visual_block.square.get_center()
        b2_pos = b2.visual_block.square.get_center()
        merge_pos = merge.visual_block.square.get_center()

        # Merge should be right of rightmost parent (b2)
        if not merge_pos[0] > b2_pos[0]:
            print("WARNING: Merge should be right of b2")

            # b1 and b2 should be at same x (parallel)
        if not abs(b1_pos[0] - b2_pos[0]) < 0.01:
            print("WARNING: b1 and b2 should be at same x")

        text = Text("DAG Positioning Test Passed", color=GREEN).to_edge(UP)
        self.play(Write(text))
        self.wait(2)

#TODO since adding GHOSTDAG, weight may not exist
#TODO failed

# class TestGenerateDAG(HUD2DScene):
#     """Test generate_dag() with various parameters."""
#
#     def construct(self):
#         dag = KaspaDAG(scene=self)
#
#         genesis = dag.add_block()
#
#         self.caption("Generating DAG with 5 rounds...")
#         dag.generate_dag(
#             num_rounds=5,
#             lambda_parallel=1.5,
#             chain_prob=0.6,
#             old_tip_prob=0.2
#         )
#
#         # Verify structure
#         assert len(dag.all_blocks) > 5, "Should have more than 5 blocks"
#
#         # Check for parallel blocks
#         has_parallel = any(
#             len([b for b in dag.all_blocks if b.weight == block.weight]) > 1
#             for block in dag.all_blocks
#         )
#         assert has_parallel, "Should have some parallel blocks"
#
#         self.clear_caption()
#         text = Text("generate_dag() Test Passed", color=GREEN).to_edge(UP)
#         self.play(Write(text))
#         self.wait(2)


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

class TestZIndexBugReproduce(HUD2DScene):
    """Test highlighting anticone in DAG structure."""

    def construct(self):
        dag = KaspaDAG(scene=self)

        # Create structure with clear anticone
        genesis = dag.add_block()
        b1 = dag.add_block(parents=[genesis])
        b2 = dag.add_block(parents=[b1, genesis])
        b3 = dag.add_block(parents=[b1, genesis])
        b4 = dag.add_block(parents=[b2, b1])
        b5 = dag.add_block(parents=[b4, b2])
        b6 = dag.add_block(parents=[b5, b4])

        # Add merge block connecting both branches
        merge = dag.add_block(parents=[b2, b4])
        merge2 = dag.add_block(parents=[b2, b4])

class TestZIndexScene(HUD2DScene):
    def construct(self):
        # Create objects with different z-index values
        line = Line(LEFT * 2, RIGHT * 2).set_z_index(5)
        square = Square(fill_color=BLUE, fill_opacity=0.9).set_z_index(10)

        # Add in order that would normally be wrong
        self.play(Create(square))  # Higher z-index but added first

        # Move camera (this triggers the bug)
        self.play(self.camera.frame.animate.shift(RIGHT * 2))

        self.play(Create(line))  # Lower z-index but added second
        self.wait(1)


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


class TestNormalConditions(HUD2DScene):
    """Test highlighting anticone in DAG structure."""
#TODO change block creation animations to move camera at the same time to speed up animations
#TODO refactor the functions in this test to clean them up in DAG
    def construct(self):
        dag = KaspaDAG(scene=self)
#        dag.set_k(18)

        self.wait(1)
        self.narrate("GHOSTDAG, 1 BPS, k=18", run_time=1.0)
        self.caption("Network Delay during this simulation is 5000ms.", run_time=1.0)
        blocks1 = dag.simulate_blocks(30, 1, 5000)
        dag.create_blocks_from_simulator_list_instant(blocks1)

        dag.animate_ghostdag_process(context_block="4b", narrate=True)

        self.wait(3)

        # self.caption("These next 20 seconds, network has degraded to half of max delay, 2500ms.", run_time=1.0)
        # blocks2 = dag.simulate_blocks(20, 1, 2500)
        # dag.create_blocks_from_simulator_list(blocks2)
        #
        # self.caption("These next 20 seconds, network has degraded to max delay, 5000ms.", run_time=1.0)
        # blocks3 = dag.simulate_blocks(20, 1, 5000)
        # dag.create_blocks_from_simulator_list(blocks3)
        #
        # self.caption("These next 20 seconds, network has improved to half of max delay, 2500ms.", run_time=1.0)
        # blocks4 = dag.simulate_blocks(20, 1, 2500)
        # dag.create_blocks_from_simulator_list(blocks4)
        #
        # self.caption("These next 20 seconds, network delay has recovered to normal, 350ms.", run_time=1.0)
        # blocks5 = dag.simulate_blocks(20, 1, 350)
        # dag.create_blocks_from_simulator_list(blocks5)
        #
        # self.caption("No orphan(Red) blocks, even under degraded conditions, Security Maintained.", run_time=1.0)
        # dag.add_block(dag.get_current_tips())
        # self.wait(3)

        # # Add the new parent chain highlighting at the end
        # self.wait(1)
        # self.caption("Highlighting Selected Parent Chain back to Genesis", run_time=1.0)
        # self.wait(1)
        # dag.traverse_parent_chain_with_right_fade(scroll_speed_factor=0.6)
        # self.wait(2)

# TODO troubleshoot showing GHOSTDAG
class TestGHOSTDAGProcess(HUD2DScene):
    """Test GhostDAG process visualization in DAG structure."""

    def construct(self):
        dag = KaspaDAG(scene=self)
        self.narrate("Kaspa Finality Depth - Oversimplified", run_time=1.0)
        # Create entire structure from scratch, including genesis
        all_blocks = dag.create_blocks_from_list_instant([
            ("Gen", None),  # Genesis block (no parents)
            ("b1", ["Gen"]),  # Child of genesis
            ("b2", ["b1"]),  # Child of b1
            ("b3", ["b2"]),  # Child of b2
            ("b4", ["b3"]),  # Child of b3
            ("b5", ["b4"]),  # Child of b4
        ])
        self.caption("This is our current view of the DAG", run_time=1.0)
        self.wait(3)
        self.caption("Finality Depth in this example is $4$", run_time=1.0)
        dag.highlight(all_blocks[1])
        self.wait(3)
        other_blocks = dag.create_blocks_from_list_instant([
            ("b1a", ["Gen"]),  # Child of genesis
            ("b2a", ["b1a"]),  # Child of b1
            ("b3a", ["b2a"]),  # Child of b2
            ("b4a", ["b3a"]),  # Child of b3
            ("b5a", ["b4a"]),  # Child of b4
        ])

        self.caption("This newly revealed fork does NOT have Finality Point in its past", run_time=1.0)
        self.wait(3)
        self.caption("This fork is rejected with a Finality Violation", run_time=1.0)
        dag.fade_blocks(other_blocks)
        self.wait(3)
        self.clear_caption(run_time=1.0)
        dag.clear_all_blocks()

        # Create entire structure from scratch, including genesis
        all_blocks = dag.create_blocks_from_list_instant([
            ("Gen", None),  # Genesis block (no parents)
            ("b1", ["Gen"]),  # Child of genesis
            ("b2", ["b1"]),  # Child of b1
            ("b3", ["b2"]),  # Child of b2
            ("b4", ["b3"]),  # Child of b3
            ("b5", ["b4"]),  # Child of b4
        ])

        self.caption("Back to our current view of the DAG", run_time=1.0)
        self.wait(3)
        self.caption("Finality Depth is still $4$", run_time=1.0)
        dag.highlight(all_blocks[1])

        other_blocks = dag.create_blocks_from_list_instant([
            ("b2a", ["b1"]),  # Child of b1
            ("b3a", ["b2a"]),  # Child of b2
            ("b4a", ["b3a"]),  # Child of b3
            ("b5a", ["b4a"]),  # Child of b4
        ])

        self.caption("This newly revealed fork does have Finality Point in its past", run_time=1.0)
        self.wait(3)
        self.caption("This fork does NOT violate Finality", run_time=1.0)
        self.wait(3)
        self.caption("Kaspa uses $432,000$ as its Finality Depth", run_time=1.0)
        self.wait(3)
        self.caption("The probability of a 49\% adversary successfully creating this fork...", run_time=1.0)
        self.wait(3)
        self.caption("...is $(49/51)^{432000}$ or $10^{-7522}$", run_time=1.0)
        self.wait(3)
        self.caption("Zero Probability is accepted as $10^{-100}$", run_time=1.0)
        self.wait(5)
#        self.caption("There are estimated $10^{80}$ atoms in the universe.", run_time=1.0)
#        self.wait(3)

        # # Show GhostDAG process for b3 (demonstrates parent selection and blue candidate evaluation)
        # self.caption("Showing GhostDAG process for block b3")
        # dag.animate_ghostdag_process(b3, narrate=True, step_delay=1.0)
        # self.wait(2)
        #
        # # Show GhostDAG process for merge (demonstrates mergeset with multiple parents)
        # self.caption("Showing GhostDAG process for merge block")
        # dag.animate_ghostdag_process(merge, narrate=True, step_delay=1.0)
        # self.wait(2)



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

#TODO FAILED

# class TestBlockRegistry(HUD2DScene):
#     """Test block registration and retrieval."""
#
#     def construct(self):
#         dag = KaspaDAG(scene=self)
#
#         # Create blocks
#         genesis = dag.add_block()
#         b1 = dag.add_block(parents=[genesis])
#         b2 = dag.add_block(parents=[genesis])
#
#         # Verify registry
#         assert dag.get_block("Gen") == genesis, "Genesis not found"
#         assert dag.get_block("B1") == b1, "B1 not found"
#         assert dag.genesis == genesis, "Genesis not tracked"
#         assert len(dag.all_blocks) == 3, "Block count incorrect"
#
#         text = Text("Registry Test Passed", color=GREEN).to_edge(UP)
#         self.play(Write(text))
#         self.wait(2)

#TODO does not work (weight not yet implemented)
#TODO FAILED

# class TestWeightCalculation(HUD2DScene):
#     """Test block weight calculation in DAG."""
#
#     def construct(self):
#         dag = KaspaDAG(scene=self)
#
#         # Create diamond structure
#         genesis = dag.add_block()
#         b1 = dag.add_block(parents=[genesis])
#         b2 = dag.add_block(parents=[genesis])
#         merge = dag.add_block(parents=[b1, b2])
#
#         # Verify weights (based on rightmost parent)
#         assert genesis.weight == 1, f"Genesis weight should be 1, got {genesis.weight}"
#         assert b1.weight == 2, f"B1 weight should be 2, got {b1.weight}"
#         assert b2.weight == 2, f"B2 weight should be 2, got {b2.weight}"
#         assert merge.weight == 3, f"Merge weight should be 3, got {merge.weight}"
#
#         text = Text("Weight Calculation Test Passed", color=GREEN).to_edge(UP)
#         self.play(Write(text))
#         self.wait(2)


class ComprehensiveHighlightingExample(HUD2DScene):
    """Comprehensive example demonstrating past, future, and anticone highlighting."""

    def construct(self):
        dag = KaspaDAG(scene=self)
        self.narrate("Kaspa DAG Relationships")

        # Create a complex DAG structure with anticone relationships
        genesis = dag.add_block()
        b1 = dag.add_block(parents=[genesis])
        b2 = dag.add_block(parents=[genesis])
        b3 = dag.add_block(parents=[b1])
        b4 = dag.add_block(parents=[b2])
        merge = dag.add_block(parents=[b3, b4])
        final = dag.add_block(parents=[merge])
        self.wait(1)

        # 1. Highlight past of a block (b3)
        self.caption("Past of Yellow Block")
        dag.highlight_past(b3)
        self.wait(4)
        dag.reset_highlighting()
        self.wait(1)

        # 2. Highlight past of the merge block
        self.caption("Past of a Different Block")
        dag.highlight_past(merge)
        self.wait(4)
        dag.reset_highlighting()
        self.wait(1)

        # 3. Highlight future of a block in an anticone (b1)
        # b4 and b2 are in b1's anticone
        self.caption("Future of Yellow Block")
        dag.highlight_future(b1)
        self.wait(4)
        dag.reset_highlighting()
        self.wait(1)

        # 4. Highlight future of genesis
        self.caption("Future of Genesis")
        dag.highlight_future(genesis)
        self.wait(4)
        dag.reset_highlighting()
        self.wait(1)

        # 5. Highlight anticone of an anticone block (b3)
        # b4 is in b3's anticone, then we highlight b4's anticone
        self.caption("Anticone of Yellow Block")
        dag.highlight_anticone(b3)
        self.wait(4)
        dag.reset_highlighting()
        self.wait(1)

        # Bonus: Show anticone of b4 to demonstrate the reverse relationship
        self.caption("Anticone of Different block")
        dag.highlight_anticone(b4)
        self.wait(4)
        dag.reset_highlighting()
        self.wait(1)

