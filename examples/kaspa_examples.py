# blanim/examples/kaspa_examples.py

from blanim import *

####################
#Some examples NOT using anything but hud_2d_scene
####################

"""  
============================================================================  
PROJECT STATUS: Bitcoin vs Kaspa Block Comparison Animation  
============================================================================  

CURRENT STATE (as of last session):  
-----------------------------------  
Successfully implemented side-by-side block comparison with modular zoom  
animations. The scene creates two blocks (Bitcoin left, Kaspa right) with  
header and body sections, then supports zooming into bodies OR headers  
independently while keeping both blocks visible simultaneously.  

WHAT'S WORKING:  
---------------  
1. Block Creation (create_labeled_square, create_block_sections)  
   - Two labeled squares side by side (Bitcoin/Kaspa)  
   - Each square contains header and body rectangles with labels  
   - Proper spacing between header/body sections (section_buff = 0.3)  
   - All components use white strokes with fill_opacity=0 (transparent)  

2. Animation Timing Fix  
   - Separate animations for rectangles vs text labels  
   - Rectangles animate first, then labels (avoids lag_ratio issues)  
   - Each animation phase has dedicated run_time for consistent pacing  

3. Body Zoom System (zoom_to_bodies, zoom_out_from_bodies)  
   - Fades non-body elements using fade(0.95) for 5% opacity  
   - Transforms body rectangles to full block size (not just scaling)  
   - Creates transactions (tx0-txN) filling body top-to-bottom  
   - tx0 labeled as "coinbase" in both blocks  
   - Restores using Transform back to original + separate fade restoration  

4. Header Zoom System (zoom_to_headers, zoom_out_from_headers)  
   - Same pattern as body zoom but for headers  
   - Creates header fields (version, merkle root, timestamp, bits, nonce)  
   - Kaspa-specific fields in YELLOW (parents, accepted_id_merkle_root,   
     utxo_commitment, daa_score, blue_work, blue_score, pruning_point)  
   - Common fields in WHITE  
   - Fields centered vertically within zoomed header rectangles  

5. Opacity Restoration System  
   - Uses set_stroke(opacity=1.0) for rectangles (stroke-only mobjects)  
   - Uses set_fill(opacity=1.0) for text labels (fill-based mobjects)  
   - Critical: Cannot use set_opacity() or fade() for restoration due to  
     multiplicative behavior and fill_opacity=0 conflict  

CURRENT ARCHITECTURE:  
---------------------  
VGroup Structure:  
  bitcoin_square / kaspa_square  
  ├─ [0] Square (stroke-only, fill_opacity=0)  
  └─ [1] Text label ("Bitcoin Block" / "Kaspa Block")  

  bitcoin_sections / kaspa_sections (from create_block_sections)  
  ├─ [0] header_group  
  │  ├─ [0] header_rect (Rectangle)  
  │  └─ [1] header_label (Text "Header")  
  └─ [1] body_group  
     ├─ [0] body_rect (Rectangle)  
     └─ [1] body_label (Text "Body")  

Zoom Pattern:  
1. Store original state (copy() for Transform restoration)  
2. Fade non-target elements (fade(0.95) = 5% opacity)  
3. Transform target rectangles to full block size  
4. Create content (transactions or header fields)  
5. Wait for viewing  
6. FadeOut content  
7. Transform rectangles back (using stored originals)  
8. Restore opacity (set_stroke for rects, set_fill for text)  

KNOWN ISSUES & SOLUTIONS:  
-------------------------  
1. Opacity Restoration Problem  
   - WRONG: fade(0) after fade(0.95) - multiplicative, doesn't restore  
   - WRONG: set_opacity(1.0) - sets fill_opacity=1.0, makes rects solid white  
   - RIGHT: set_stroke(opacity=1.0) for rectangles  
   - RIGHT: set_fill(opacity=1.0) for text labels  

2. Animation Timing Issues  
   - Create() on VGroup with mixed complexity causes stagger  
   - Solution: Separate animations for each component type  
   - Pattern: self.play(Create(rect1), Create(rect2)), then   
              self.play(Create(label1), Create(label2))  

3. Transform vs Scale  
   - Scale maintains aspect ratio, doesn't change shape  
   - Transform allows both size AND shape changes  
   - Use Transform with target rectangles for zoom effect  

NEXT STEPS:  
-----------  
1. Add zoom_out_from_headers() method (currently missing)  
2. Test full animation flow: blocks → body zoom → headers zoom → restore  
3. Consider adding zoom_blocks() for outer square zoom  
4. Add more granular zoom levels (e.g., zoom into specific transaction)  

FUTURE IMPROVEMENTS:  
--------------------  
1. Encapsulate Zoom Behavior  
   - Create ZoomableSection class wrapping VGroup  
   - Methods: zoom_in(), zoom_out(), add_content(), clear_content()  
   - Eliminates need for external zoom_to_* methods  

2. Nested Zoom Support  
   - Allow zooming into zoomed content (e.g., body → specific tx)  
   - Maintain zoom stack for proper restoration  
   - Each zoom level tracks its own fade targets  

3. Animation State Machine  
   - Track current zoom state (OVERVIEW, BODY_ZOOM, HEADER_ZOOM)  
   - Validate transitions (can't zoom to headers while in body zoom)  
   - Enable smooth transitions between any two states  

4. Content Templates  
   - Define field/transaction templates separately  
   - Easy to swap Bitcoin/Kaspa content  
   - Support for other blockchain types  

5. Camera Integration Option  
   - Hybrid approach: mobject transform for dual-block view  
   - Camera zoom for single-block deep dives  
   - Best of both worlds  

DEBUGGING TIPS:  
---------------  
- If fade doesn't work: Check if using fade() vs set_stroke/set_fill  
- If colors wrong: Check WHITE vs YELLOW in field creation  
- If spacing off: Verify section_buff and field_spacing values  
- If animation skips: Add wait() calls and check run_time values  
- If Transform fails: Ensure original state is stored with copy()  

TECHNICAL NOTES:  
----------------  
- HUD2DScene provides fixed narration/caption during animations  
- All coordinates in Manim units (not pixels)  
- LEFT/RIGHT/UP/DOWN are unit vectors (magnitude 1)  
- VGroup indexing: [0] first child, [1] second child, etc.  
- Text uses fill, Rectangles use stroke (when fill_opacity=0)  

LAST MODIFIED: [Current Date]  
WORKING ON: Adding Kaspa-specific header fields with color coding  
============================================================================  
"""

class BlockComparisonScene(HUD2DScene):
    def __init__(self):
        super().__init__()
        self.kaspa_header_fields = None
        self.btc_header_fields = None
        self.kaspa_header_rect_original = None
        self.btc_header_rect_original = None
        self.kaspa_body_rect_original = None
        self.btc_body_rect_original = None
        self.kaspa_txs = None
        self.btc_txs = None
        self.kaspa_sections = None
        self.bitcoin_sections = None
        self.kaspa_square = None
        self.bitcoin_square = None
        self.btc_body_original_scale = None
        self.kaspa_body_original_pos = None
        self.btc_body_original_pos = None

    def construct(self):
        # Add narration and caption
        self.narrate(r"Bitcoin vs Kaspa", run_time=1)

        # Create two labeled squares with adjusted spacing and size
        bitcoin_square = self.create_labeled_square("Bitcoin Block", LEFT * 3.75)
        kaspa_square = self.create_labeled_square("Kaspa Block", RIGHT * 3.75)

        self.caption(r"Let us compare Bitcoin and Kaspa Blocks.", run_time=1)

        # Animate squares first (index [0] is the square)
        self.play(
            Create(bitcoin_square[0]),
            Create(kaspa_square[0]),
            run_time=1
        )

        # Then animate labels (index [1] is the label)
        self.play(
            Create(bitcoin_square[1]),
            Create(kaspa_square[1]),
            run_time=1
        )

        # Create header and body rectangles for both blocks
        bitcoin_sections = self.create_block_sections(bitcoin_square[0])
        kaspa_sections = self.create_block_sections(kaspa_square[0])

        # Animate header RECTANGLES first (index [0][0] is header rect)
        self.play(
            Create(bitcoin_sections[0][0]),  # Bitcoin header rectangle
            Create(kaspa_sections[0][0]),  # Kaspa header rectangle
            run_time=1
        )

        # Then animate header LABELS (index [0][1] is header label)
        self.play(
            Create(bitcoin_sections[0][1]),  # Bitcoin header label
            Create(kaspa_sections[0][1]),  # Kaspa header label
            run_time=1
        )

        # Animate body RECTANGLES (index [1][0] is body rect)
        self.play(
            Create(bitcoin_sections[1][0]),  # Bitcoin body rectangle
            Create(kaspa_sections[1][0]),  # Kaspa body rectangle
            run_time=1
        )

        # Then animate body LABELS (index [1][1] is body label)
        self.play(
            Create(bitcoin_sections[1][1]),  # Bitcoin body label
            Create(kaspa_sections[1][1]),  # Kaspa body label
            run_time=1
        )

        self.wait(3)

        # Store references for zoom operations
        self.bitcoin_square = bitcoin_square
        self.kaspa_square = kaspa_square
        self.bitcoin_sections = bitcoin_sections
        self.kaspa_sections = kaspa_sections

        self.caption(r"First we examine the body.", run_time=1)

        # Perform zoom sequence
        self.zoom_to_bodies()
        self.caption(r"Here we can see the body contains transactions...", run_time=1)

        self.wait(2)

        self.caption(r"the first transaction is always a coinbase transaction...", run_time=1)

        self.wait(2)

        self.caption(r"this is where block rewards are paid...", run_time=1)

        self.wait(2)

        self.caption(r"every other transaction is a user transaction...", run_time=1)

        self.wait(2)
        self.clear_caption()

        self.zoom_out_from_bodies()

        self.caption(r"Next we examine the headers.", run_time=1)

        # Now zoom to headers
        self.zoom_to_headers()
        self.wait(2)
        self.caption(r"The header contains the version...", run_time=1)
        self.wait(2)
        self.caption(r"then the hash of the previous block/s...", run_time=1)
        self.wait(2)
        self.caption(r"this blocks 'parent' or 'parents'...", run_time=1)
        self.wait(2)
        self.caption(r"next is the merkle root of the transactions in this block...", run_time=1)
        self.wait(2)
        self.caption(r"timestamp is another shared field...", run_time=1)
        self.wait(2)
        self.caption(r"followed by target difficulty bits...", run_time=1)
        self.wait(2)
        self.caption(r"and a nonce to reproduce a valid PoW hash...", run_time=1)
        self.wait(2)
        self.clear_caption()
        self.zoom_out_from_headers()
        self.wait(3)

    @staticmethod
    def create_labeled_square(label_text, position):
        """Create a white rounded square with a label"""
        from manim import Square, Text, VGroup, WHITE, UP

        # Create square with white stroke and rounded corners
        square = Square(
            side_length=4.75,
            stroke_color=WHITE,
            stroke_width=3,
            fill_opacity=0
        )
        square.round_corners(radius=0.3)

        # Create label
        label = Text(label_text, font_size=28, color=WHITE)
        label.next_to(square, UP, buff=0.3)

        # Group square and label together
        group = VGroup(square, label)
        group.move_to(position)

        return group

    @staticmethod
    def create_block_sections(parent_square):
        """Create header and body rectangles inside a square with spacing"""
        from manim import Rectangle, Text, VGroup, WHITE, UP, DOWN

        # Get parent square dimensions and position
        square_width = parent_square.width * 0.85
        square_height = parent_square.height * 0.85
        square_center = parent_square.get_center()

        # Add buffer between sections
        section_buff = 0.15  # Space between header and body

        # Calculate section heights (header is 1/3, body is 2/3)
        # Subtract half the buffer from each section
        header_height = (square_height * 0.33) - (section_buff / 2)
        body_height = (square_height * 0.67) - (section_buff / 2)

        # Create header rectangle at top
        header_rect = Rectangle(
            width=square_width,
            height=header_height,
            stroke_color=WHITE,
            stroke_width=2,
            fill_opacity=0
        )
        header_rect.round_corners(radius=0.2)

        # Position header at top - ADD buffer to push it up
        header_y_offset = (square_height - header_height) / 2 + (section_buff / 2)
        header_rect.move_to(square_center + UP * header_y_offset)

        # Create header label
        header_label = Text("Header", font_size=20, color=WHITE)
        header_label.move_to(header_rect.get_center())

        # Group header rect and label
        header_group = VGroup(header_rect, header_label)

        # Create body rectangle at bottom
        body_rect = Rectangle(
            width=square_width,
            height=body_height,
            stroke_color=WHITE,
            stroke_width=2,
            fill_opacity=0
        )
        body_rect.round_corners(radius=0.2)

        # Position body at bottom - ADD buffer to push it down
        body_y_offset = (square_height - body_height) / 2 + (section_buff / 2)
        body_rect.move_to(square_center + DOWN * body_y_offset)

        # Create body label
        body_label = Text("Body", font_size=20, color=WHITE)
        body_label.move_to(body_rect.get_center())

        # Group body rect and label
        body_group = VGroup(body_rect, body_label)

        return VGroup(header_group, body_group)

    def zoom_to_bodies(self):
        """Zoom into body sections by transforming body rectangles to block size"""

        # Get body sections
        btc_body = self.bitcoin_sections[1]  # VGroup(body_rect, body_label)
        kaspa_body = self.kaspa_sections[1]

        # Get just the body rectangles (index [0] within each body section)
        btc_body_rect = btc_body[0]
        kaspa_body_rect = kaspa_body[0]

        # Store original states for zoom out
        self.btc_body_rect_original = btc_body_rect.copy()
        self.kaspa_body_rect_original = kaspa_body_rect.copy()

        # Fade out everything except body sections
        fade_targets = [
            self.bitcoin_square[0],  # Bitcoin outer square box
            self.bitcoin_square[1],  # Bitcoin label
            self.kaspa_square[0],  # Kaspa outer square box
            self.kaspa_square[1],  # Kaspa label
            self.bitcoin_sections[0],  # Bitcoin header
            self.kaspa_sections[0],  # Kaspa header
            btc_body[1],  # Body label (fade this too)
            kaspa_body[1],  # Body label (fade this too)
        ]

        self.play(
            *[mob.animate.fade(0.9) for mob in fade_targets],
            run_time=1
        )

        # Create target rectangles with block-like dimensions
        # Make them similar size to original blocks (4.75 side length)
        target_width = 4.5
        target_height = 5.5

        btc_target_rect = Rectangle(
            width=target_width,
            height=target_height,
            stroke_color=WHITE,
            stroke_width=2,
            fill_opacity=0
        )
        btc_target_rect.round_corners(radius=0.2)
        btc_target_rect.move_to(LEFT * 3.75)

        kaspa_target_rect = Rectangle(
            width=target_width,
            height=target_height,
            stroke_color=WHITE,
            stroke_width=2,
            fill_opacity=0
        )
        kaspa_target_rect.round_corners(radius=0.2)
        kaspa_target_rect.move_to(RIGHT * 3.75)

        # Transform body rectangles to target size/shape
        self.play(
            Transform(btc_body_rect, btc_target_rect),
            Transform(kaspa_body_rect, kaspa_target_rect),
            run_time=2
        )

        # Create transactions one by one
        self.btc_txs = VGroup()
        self.kaspa_txs = VGroup()

        # Calculate how many transactions fit in the body
        body_height = btc_body_rect.height
        tx_font_size = 18
        tx_spacing = 0.35  # Reduced spacing to fit more

        # Estimate number of transactions that fit (accounting for text height)
        num_txs = int((body_height - 1.0) / tx_spacing)  # Leave margin at top/bottom

        tx_start_y = btc_body_rect.get_top()[1] - 0.5

        for i in range(num_txs):
            btc_tx = Text(f"tx{i}", font_size=tx_font_size, color=WHITE)
            btc_tx.move_to(
                btc_body_rect.get_center() + UP * (tx_start_y - i * tx_spacing - btc_body_rect.get_center()[1])
            )
            btc_tx.shift(LEFT * 1.5)

            kaspa_tx = Text(f"tx{i}", font_size=tx_font_size, color=WHITE)
            kaspa_tx.move_to(
                kaspa_body_rect.get_center() + UP * (tx_start_y - i * tx_spacing - kaspa_body_rect.get_center()[1])
            )
            kaspa_tx.shift(LEFT * 1.5)

            if i == 0:
                btc_coinbase = Text("coinbase", font_size=16, color=YELLOW)
                btc_coinbase.next_to(btc_tx, RIGHT, buff=0.3)

                kaspa_coinbase = Text("coinbase", font_size=16, color=YELLOW)
                kaspa_coinbase.next_to(kaspa_tx, RIGHT, buff=0.3)

                self.play(
                    Create(btc_tx),
                    Create(kaspa_tx),
                    Create(btc_coinbase),
                    Create(kaspa_coinbase),
                    run_time=0.8
                )

                self.btc_txs.add(btc_tx, btc_coinbase)
                self.kaspa_txs.add(kaspa_tx, kaspa_coinbase)
            else:
                self.play(
                    Create(btc_tx),
                    Create(kaspa_tx),
                    run_time=0.4  # Faster for subsequent transactions
                )

                self.btc_txs.add(btc_tx)
                self.kaspa_txs.add(kaspa_tx)

    def zoom_out_from_bodies(self):
        """Zoom out from bodies back to full block view"""

        # Fade out transactions
        self.play(
            FadeOut(self.btc_txs),
            FadeOut(self.kaspa_txs),
            run_time=1
        )

        # Get body rectangles
        btc_body = self.bitcoin_sections[1]
        kaspa_body = self.kaspa_sections[1]
        btc_body_rect = btc_body[0]
        kaspa_body_rect = kaspa_body[0]

        # Transform bodies back to original size and position
        self.play(
            Transform(btc_body_rect, self.btc_body_rect_original),
            Transform(kaspa_body_rect, self.kaspa_body_rect_original),
            run_time=2
        )

        # Separate rectangles (stroke-only) from text labels (fill-based)
        rect_targets = [
            self.bitcoin_square[0],  # Bitcoin outer square box
            self.kaspa_square[0],  # Kaspa outer square box
            self.bitcoin_sections[0][0],  # Bitcoin header rectangle
            self.kaspa_sections[0][0],  # Kaspa header rectangle
            btc_body[0],  # Bitcoin body rectangle
            kaspa_body[0],  # Kaspa body rectangle
        ]

        text_targets = [
            self.bitcoin_square[1],  # Bitcoin block label
            self.kaspa_square[1],  # Kaspa block label
            self.bitcoin_sections[0][1],  # Bitcoin header label
            self.kaspa_sections[0][1],  # Kaspa header label
            btc_body[1],  # Bitcoin body label
            kaspa_body[1],  # Kaspa body label
        ]

        # Restore stroke opacity for rectangles and fill opacity for text
        self.play(
            *[mob.animate.set_stroke(opacity=1.0) for mob in rect_targets],
            *[mob.animate.set_fill(opacity=1.0) for mob in text_targets],
            run_time=1
        )

        self.wait(3)

    def zoom_to_headers(self):
        """Zoom into header sections by transforming header rectangles to block size"""

        # Get header sections
        btc_header = self.bitcoin_sections[0]
        kaspa_header = self.kaspa_sections[0]

        # Get just the header rectangles
        btc_header_rect = btc_header[0]
        kaspa_header_rect = kaspa_header[0]

        # Store original states for zoom out
        self.btc_header_rect_original = btc_header_rect.copy()
        self.kaspa_header_rect_original = kaspa_header_rect.copy()

        # Fade out everything except header sections
        fade_targets = [
            self.bitcoin_square[0],
            self.bitcoin_square[1],
            self.kaspa_square[0],
            self.kaspa_square[1],
            self.bitcoin_sections[1],  # Bitcoin body
            self.kaspa_sections[1],  # Kaspa body
            btc_header[1],  # Header label
            kaspa_header[1],  # Header label
        ]

        self.play(
            *[mob.animate.fade(0.9) for mob in fade_targets],
            run_time=1
        )

        # Create target rectangles with specific dimensions
        target_width = 6.0
        target_height = 5.5

        btc_target_rect = Rectangle(
            width=target_width,
            height=target_height,
            stroke_color=WHITE,
            stroke_width=2,
            fill_opacity=0
        )
        btc_target_rect.round_corners(radius=0.2)
        btc_target_rect.move_to(LEFT * 3.75)

        kaspa_target_rect = Rectangle(
            width=target_width,
            height=target_height,
            stroke_color=WHITE,
            stroke_width=2,
            fill_opacity=0
        )
        kaspa_target_rect.round_corners(radius=0.2)
        kaspa_target_rect.move_to(RIGHT * 3.75)

        # Transform header rectangles
        self.play(
            Transform(btc_header_rect, btc_target_rect),
            Transform(kaspa_header_rect, kaspa_target_rect),
            run_time=2
        )

        # Define header fields - Bitcoin (all white)
        btc_fields = [
            "version:",
            "hashPrevBlock:",
            "hashMerkleRoot:",
            "Time:",
            "Bits:",
            "Nonce:"
        ]

        # Define header fields - Kaspa (white for common, yellow for unique)
        # Format: (field_text, color)
        kaspa_fields = [
            ("version:", WHITE),  # Common
            ("parents_by_level:", WHITE),  # Kaspa-hashchain
            ("hash_merkle_root:", WHITE),  # Common
            ("accepted_id_merkle_root:", YELLOW),  # Kaspa-specific
            ("utxo_commitment:", YELLOW),  # Kaspa-specific
            ("timestamp:", WHITE),  # Common
            ("bits:", WHITE),  # Common
            ("nonce:", WHITE),  # Common
            ("daa_score:", YELLOW),  # Kaspa-specific
            ("blue_work:", YELLOW),  # Kaspa-specific
            ("blue_score:", YELLOW),  # Kaspa-specific
            ("pruning_point:", YELLOW),  # Kaspa-specific
        ]

        field_font_size = 16
        field_spacing = 0.35

        # Calculate centering for Bitcoin fields
        btc_num_fields = len(btc_fields)
        btc_total_height = (btc_num_fields - 1) * field_spacing
        btc_field_start_y = btc_total_height / 2

        # Calculate centering for Kaspa fields
        kaspa_num_fields = len(kaspa_fields)
        kaspa_total_height = (kaspa_num_fields - 1) * field_spacing
        kaspa_field_start_y = kaspa_total_height / 2

        self.btc_header_fields = VGroup()
        self.kaspa_header_fields = VGroup()

        # Create Bitcoin fields (all white)
        for i, btc_field_text in enumerate(btc_fields):
            btc_field = Text(btc_field_text, font_size=field_font_size, color=WHITE)
            btc_field.move_to(
                btc_header_rect.get_center() + UP * (btc_field_start_y - i * field_spacing)
            )

            # Create corresponding Kaspa field with appropriate color
            kaspa_field_text, kaspa_color = kaspa_fields[i] if i < len(kaspa_fields) else ("", WHITE)
            kaspa_field = Text(kaspa_field_text, font_size=field_font_size, color=kaspa_color)
            kaspa_field.move_to(
                kaspa_header_rect.get_center() + UP * (kaspa_field_start_y - i * field_spacing)
            )

            self.play(
                Create(btc_field),
                Create(kaspa_field),
                run_time=0.4
            )

            self.btc_header_fields.add(btc_field)
            self.kaspa_header_fields.add(kaspa_field)

            # Create remaining Kaspa-only fields (all yellow)
        for i in range(len(btc_fields), len(kaspa_fields)):
            kaspa_field_text, kaspa_color = kaspa_fields[i]
            kaspa_field = Text(kaspa_field_text, font_size=field_font_size, color=kaspa_color)
            kaspa_field.move_to(
                kaspa_header_rect.get_center() + UP * (kaspa_field_start_y - i * field_spacing)
            )

            self.play(
                Create(kaspa_field),
                run_time=0.4
            )

            self.kaspa_header_fields.add(kaspa_field)

        self.wait(2)


    def zoom_out_from_headers(self):
        """Zoom out from headers back to full block view"""

        # Fade out header fields
        self.play(
            FadeOut(self.btc_header_fields),
            FadeOut(self.kaspa_header_fields),
            run_time=1
        )

        # Get header rectangles
        btc_header = self.bitcoin_sections[0]
        kaspa_header = self.kaspa_sections[0]
        btc_header_rect = btc_header[0]
        kaspa_header_rect = kaspa_header[0]

        # Transform headers back to original size and position
        self.play(
            Transform(btc_header_rect, self.btc_header_rect_original),
            Transform(kaspa_header_rect, self.kaspa_header_rect_original),
            run_time=2
        )

        # Separate rectangles (stroke-only) from text labels (fill-based)
        rect_targets = [
            self.bitcoin_square[0],
            self.kaspa_square[0],
            self.bitcoin_sections[1][0],  # Body rectangle
            self.kaspa_sections[1][0],  # Body rectangle
            btc_header[0],  # Header rectangle
            kaspa_header[0],  # Header rectangle
        ]

        text_targets = [
            self.bitcoin_square[1],
            self.kaspa_square[1],
            self.bitcoin_sections[1][1],  # Body label
            self.kaspa_sections[1][1],  # Body label
            btc_header[1],  # Header label
            kaspa_header[1],  # Header label
        ]

        # Restore stroke opacity for rectangles and fill opacity for text
        self.play(
            *[mob.animate.set_stroke(opacity=1.0) for mob in rect_targets],
            *[mob.animate.set_fill(opacity=1.0) for mob in text_targets],
            run_time=1
        )

        self.wait(3)

####################
#Kaspa Specific Examples
####################

class FinalityDepth(HUD2DScene):
    """Explainer animation for Finality Depth."""

    def construct(self):
        dag = KaspaDAG(scene=self)
        self.wait(1)
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
        self.wait(5)
        self.caption("Finality Depth in this example is $4$", run_time=1.0)
        dag.highlight(all_blocks[1])
        self.wait(5)

        other_blocks = dag.create_blocks_from_list_instant([
            ("b1a", ["Gen"]),  # Child of genesis
            ("b2a", ["b1a"]),  # Child of b1
            ("b3a", ["b2a"]),  # Child of b2
            ("b4a", ["b3a"]),  # Child of b3
            ("b5a", ["b4a"]),  # Child of b4
        ])

        self.caption("This newly revealed fork is NOT in the future of Finality Point", run_time=1.0)
        self.wait(5)
        self.caption("This fork is rejected with a Finality Violation", run_time=1.0)
        dag.fade_blocks(other_blocks)
        self.wait(5)
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
        self.wait(5)
        self.caption("Finality Depth is still $4$", run_time=1.0)
        dag.highlight(all_blocks[1])
        self.wait(5)

        other_blocks = dag.create_blocks_from_list_instant([
            ("b2a", ["b1"]),  # Child of b1
            ("b3a", ["b2a"]),  # Child of b2
            ("b4a", ["b3a"]),  # Child of b3
            ("b5a", ["b4a"]),  # Child of b4
        ])

        self.caption("This newly revealed fork is in the future of Finality Point", run_time=1.0)
        self.wait(5)
        self.caption("This fork does NOT violate Finality", run_time=1.0)
        self.wait(5)
        self.caption("Kaspa uses $432,000$ as its Finality Depth", run_time=1.0)
        self.wait(5)
        self.caption("The probability of a 49\% adversary successfully creating this fork...", run_time=1.0)
        self.wait(5)
        self.caption("...is $(49/51)^{432000}$ or $10^{-7522}$", run_time=1.0)
        self.wait(5)
        self.caption("In cryptography, $10^{-100}$ is already accepted as 'Effectively Zero'.", run_time=1.0)
        self.wait(5)
        self.caption("At $10^{-7522}$, this event is physically impossible in our universe.", run_time=1.0)
        self.wait(8)

class MergeDepthBound(HUD2DScene):
    """Explainer for Merge Depth."""

    def construct(self):
        dag = KaspaDAG(scene=self)
        dag.set_k(2)

        self.wait(1)
        self.narrate("Kaspa Merge Depth Bound - Oversimplified", run_time=1.0)
        # Create entire structure from scratch, including genesis
        all_blocks = dag.create_blocks_from_list_instant([
            ("Gen", None),
            ("b1", ["Gen"]),
            ("b2", ["b1"]),
            ("b3", ["b2"]),
            ("b4", ["b3"]),
            ("b5", ["b4"]),
        ])
        self.caption("This demonstration uses k=2", run_time=1.0)
        self.wait(5)
        self.caption("Merge Depth Bound in this example is $4$", run_time=1.0)
        dag.highlight(all_blocks[1])
        self.wait(5)

        other_blocks = dag.create_blocks_from_list_instant([
            ("b1a", ["Gen"]),
            ("b5a", ["b1a","b4"]),
        ])

        self.caption("This fork attempts to Merge a block NOT in the future of Merge Depth Root.", run_time=1.0)
        self.wait(5)
        self.caption("This block is rejected with a Bounded Merge Depth Violation.", run_time=1.0)
        self.play(other_blocks[1].highlight_stroke_red())
        self.wait(3)
        dag.fade_blocks(other_blocks)
        self.wait(3)
        self.clear_caption(run_time=1.0)
        dag.clear_all_blocks()

        all_blocks = dag.create_blocks_from_list_instant([
            ("Gen", None),
            ("b1", ["Gen"]),
            ("b2", ["b1"]),
            ("b3", ["b2"]),
            ("b4", ["b3"]),
            ("b5", ["b4"]),
        ])

        self.caption("Back to our current view of the DAG", run_time=1.0)
        self.wait(5)

        other_blocks = dag.create_blocks_from_list_instant([
            ("b1a", ["Gen"]),
            ("b4a", ["b1a","b3"]),
        ])

        self.caption("This fork merges a block that does not violate Merge Depth Bound", run_time=1.0)
        self.wait(5)
        self.caption("The Merge Depth Bound is still 4", run_time=1.0)
        self.wait(5)
        self.caption("The Merge Depth Root from this tip, is here", run_time=1.0)
        dag.highlight(all_blocks[0])
        self.wait(5)
        dag.reset_highlighting()

        final_block = dag.create_blocks_from_list_instant([
            ("b6", ["b4a","b5"]),
        ])

        self.caption("As a new block is added to merge these tips...", run_time=1.0)
        self.wait(5)
        self.caption("Merge Depth Root is here", run_time=1.0)
        dag.highlight(all_blocks[2])
        self.wait(5)
        self.caption("Even though there is a red block that violates the Merge Depth Bound", run_time=1.0)
        self.play(other_blocks[0].square.animate.set_fill(color=RED, opacity=0.7))
        self.wait(5)
        self.caption("This block is \"Kosherized\" by the Blue block in the Mergeset", run_time=1.0)
        self.play(other_blocks[1].square.animate.set_fill(color=BLUE, opacity=0.7))
        self.wait(5)
        self.caption("This is the only exception to the Merge Depth Bound", run_time=1.0)
        self.wait(8)