# blanim/tests/hud2dscene_tests.py

from blanim import *


# TODO check the video outputs and debug if required, add some docs to each test to explain expected result

class TestBasicNarration(HUD2DScene):
    """Test basic narration display and clearing."""

    def construct(self):
        # Display narration
        self.narrate(r"Test Narration")
        self.wait(1)

        # Clear narration
        self.clear_narrate()
        self.wait(1)

        # Visual confirmation
        text = Text("Basic Narration Test Passed", color=GREEN).to_edge(DOWN)
        self.play(Write(text))
        self.wait(2)


class TestBasicCaption(HUD2DScene):
    """Test basic caption display and clearing."""

    def construct(self):
        # Display caption
        self.caption(r"Test Caption")
        self.wait(1)

        # Clear caption
        self.clear_caption()
        self.wait(1)

        # Visual confirmation
        text = Text("Basic Caption Test Passed", color=GREEN).to_edge(UP)
        self.play(Write(text))
        self.wait(2)


class TestNarrationAndCaption(HUD2DScene):
    """Test displaying narration and caption simultaneously."""

    def construct(self):
        # Display both
        self.narrate(r"Upper Narration")
        self.caption(r"Lower Caption")
        self.wait(2)

        # Clear both
        self.clear_narrate()
        self.clear_caption()
        self.wait(1)

        # Visual confirmation
        text = Text("Simultaneous Display Test Passed", color=GREEN)
        self.play(Write(text))
        self.wait(2)


class TestNarrateAndClear(HUD2DScene):
    """Test auto-clearing narration with narrate_and_clear."""

    def construct(self):
        # Display for 2 seconds then auto-clear
        self.narrate_and_clear(r"This disappears after 2 seconds", display_time=2.0)
        self.wait(3)  # Wait to see it clear

        # Test caption auto-clear
        self.narrate_and_clear(r"Caption auto-clear", display_time=2.0, upper=False)
        self.wait(3)

        # Visual confirmation
        text = Text("Auto-Clear Test Passed", color=GREEN)
        self.play(Write(text))
        self.wait(2)


class TestRapidNarrationUpdates(HUD2DScene):
    """Test multiple rapid narration changes."""

    def construct(self):
        # Rapid updates
        self.narrate(r"First")
        self.wait(0.5)
        self.narrate(r"Second")
        self.wait(0.5)
        self.narrate(r"Third")
        self.wait(0.5)
        self.narrate(r"Fourth")
        self.wait(1)

        self.clear_narrate()

        # Visual confirmation
        text = Text("Rapid Updates Test Passed", color=GREEN).to_edge(DOWN)
        self.play(Write(text))
        self.wait(2)


class TestTextTypes(HUD2DScene):
    """Test different text types (Tex, MathTex, Text)."""
    narration_text_type = "Tex"  # Default

    def construct(self):
        # Test Tex (default)
        self.narrate(r"Tex: $x^2 + y^2 = r^2$")
        self.wait(1)
        self.clear_narrate()

        # Visual confirmation
        text = Text("Text Types Test Passed", color=GREEN).to_edge(DOWN)
        self.play(Write(text))
        self.wait(2)


class TestMathTexType(HUD2DScene):
    """Test MathTex text type."""
    narration_text_type = "MathTex"

    def construct(self):
        # Test MathTex
        self.narrate(r"\int_0^\infty e^{-x^2} dx = \frac{\sqrt{\pi}}{2}")
        self.wait(2)
        self.clear_narrate()

        # Visual confirmation
        text = Text("MathTex Type Test Passed", color=GREEN).to_edge(DOWN)
        self.play(Write(text))
        self.wait(2)


class TestPlainTextType(HUD2DScene):
    """Test plain Text type."""
    narration_text_type = "Text"

    def construct(self):
        # Test Text (no LaTeX processing)
        self.narrate("Plain text without LaTeX")
        self.caption("Another plain text caption")
        self.wait(2)

        self.clear_narrate()
        self.clear_caption()

        # Visual confirmation
        text = Text("Plain Text Type Test Passed", color=GREEN)
        self.play(Write(text))
        self.wait(2)


class TestCameraShift(HUD2DScene):
    """Test camera shift with HUD persistence.

    Expected Result:
    - NumberPlane grid and blue square should shift left as camera moves right
    - Narration "Camera Shift Test" should remain fixed at top of screen
    - Caption "HUD should stay fixed" should remain fixed at bottom of screen
    - After camera returns to origin, all elements should be back in original positions
    """

    def construct(self):
        # Add coordinate grid to visualize movement
        grid = NumberPlane(
            x_range=[-10, 10, 1],
            y_range=[-6, 6, 1],
            background_line_style={
                "stroke_color": BLUE_E,
                "stroke_width": 1,
                "stroke_opacity": 0.3,
            }
        )
        self.add(grid)

        # Add reference square at origin
        square = Square(color=BLUE).move_to(ORIGIN)
        self.add(square)

        # Add HUD text
        self.narrate(r"Camera Shift Test")
        self.caption(r"HUD should stay fixed")

        # Shift camera - grid and square move, HUD stays fixed
        self.play(self.camera.frame.animate.shift(RIGHT * 3))
        self.wait(1)

        # Shift back
        self.play(self.camera.frame.animate.shift(LEFT * 3))
        self.wait(1)

        self.clear_narrate()
        self.clear_caption()

        # Visual confirmation
        text = Text("Camera Shift Test Passed", color=GREEN).to_edge(DOWN)
        self.play(Write(text))
        self.wait(2)


class TestCameraScale(HUD2DScene):
    """Test camera zoom with HUD persistence."""

    def construct(self):
        # Add grid to visualize zoom
        grid = NumberPlane(
            x_range=[-10, 10, 1],
            y_range=[-6, 6, 1],
            background_line_style={
                "stroke_color": BLUE_E,
                "stroke_width": 1,
                "stroke_opacity": 0.3,
            }
        )
        self.add(grid)

        # Add reference circle at origin
        circle = Circle(color=RED).move_to(ORIGIN)
        self.add(circle)

        # Add HUD text
        self.narrate(r"Camera Zoom Test")

        # Zoom in
        self.play(self.camera.frame.animate.scale(0.5))
        self.wait(1)

        # Zoom out
        self.play(self.camera.frame.animate.scale(2))
        self.wait(1)

        self.clear_narrate()

        # Visual confirmation
        text = Text("Camera Zoom Test Passed", color=GREEN).to_edge(DOWN)
        self.play(Write(text))
        self.wait(2)


class TestCameraMoveTo(HUD2DScene):
    """Test camera move_to with HUD persistence."""

    def construct(self):
        # Add grid
        grid = NumberPlane(
            x_range=[-10, 10, 1],
            y_range=[-6, 6, 1],
            background_line_style={
                "stroke_color": BLUE_E,
                "stroke_width": 1,
                "stroke_opacity": 0.3,
            }
        )
        self.add(grid)

        # Add labeled squares at different positions
        square1 = VGroup(
            Square(color=BLUE).shift(LEFT * 3),
            Text("A", font_size=24).shift(LEFT * 3)
        )
        square2 = VGroup(
            Square(color=RED).shift(RIGHT * 3),
            Text("B", font_size=24).shift(RIGHT * 3)
        )
        self.add(square1, square2)

        # Add HUD text
        self.caption(r"Moving camera between squares")

        # Move to first square
        self.play(self.camera.frame.animate.move_to(square1))
        self.wait(1)

        # Move to second square
        self.play(self.camera.frame.animate.move_to(square2))
        self.wait(1)

        # Move back to origin
        self.play(self.camera.frame.animate.move_to(ORIGIN))
        self.wait(1)

        self.clear_caption()

        # Visual confirmation
        text = Text("Camera MoveTo Test Passed", color=GREEN).to_edge(UP)
        self.play(Write(text))
        self.wait(2)


class TestCameraChaining(HUD2DScene):
    """Test chained camera transformations."""

    def construct(self):
        # Add grid to visualize movement
        grid = NumberPlane(
            x_range=[-10, 10, 1],
            y_range=[-6, 6, 1],
            background_line_style={
                "stroke_color": BLUE_E,
                "stroke_width": 1,
                "stroke_opacity": 0.3,
            }
        )
        self.add(grid)

        # Add reference triangle at origin
        triangle = Triangle(color=YELLOW).move_to(ORIGIN)
        self.add(triangle)

        # Add HUD text
        self.narrate(r"Chained Transformations")

        # Chain multiple transformations
        self.play(
            self.camera.frame.animate
            .shift(RIGHT * 2)
            .scale(0.5)
        )
        self.wait(1)

        # Chain back
        self.play(
            self.camera.frame.animate
            .shift(LEFT * 2)
            .scale(2)
        )
        self.wait(1)

        self.clear_narrate()

        # Visual confirmation
        text = Text("Camera Chaining Test Passed", color=GREEN).to_edge(DOWN)
        self.play(Write(text))
        self.wait(2)


class TestCameraSet(HUD2DScene):
    """Test camera set width/height."""

    def construct(self):
        # Add grid to visualize zoom changes
        grid = NumberPlane(
            x_range=[-10, 10, 1],
            y_range=[-6, 6, 1],
            background_line_style={
                "stroke_color": BLUE_E,
                "stroke_width": 1,
                "stroke_opacity": 0.3,
            }
        )

        # Add scene content
        rect = Rectangle(width=4, height=2, color=PURPLE)
        self.add(grid, rect)

        # Add HUD text
        self.caption(r"Testing set width/height")

        # Set width
        self.play(self.camera.frame.animate.set(width=6))
        self.wait(1)

        # Set height
        self.play(self.camera.frame.animate.set(height=4))
        self.wait(1)

        # Reset to default
        self.play(self.camera.frame.animate.set(width=14))
        self.wait(1)

        self.clear_caption()

        # Visual confirmation
        text = Text("Camera Set Test Passed", color=GREEN).to_edge(UP)
        self.play(Write(text))
        self.wait(2)


class TestTranscriptBasic(HUD2DScene):
    """Test basic transcript functionality."""

    def construct(self):
        # Add transcript entries
        self.transcript.add_transcript("Scene begins with a blue square")

        square = Square(color=BLUE)
        self.play(Create(square))

        self.transcript.add_transcript("Square is created using Create animation")
        self.wait(1)

        self.transcript.add_transcript("Square fades out")
        self.play(FadeOut(square))

        # Visual confirmation
        text = Text("Transcript Test Passed", color=GREEN)
        self.play(Write(text))
        self.wait(2)


class TestTranscriptWithNarration(HUD2DScene):
    """Test transcript alongside narration."""

    def construct(self):
        # Visual narration
        self.narrate(r"Creating Circle")

        # Detailed transcript
        self.transcript.add_transcript(
            "Title 'Creating Circle' appears at top of screen in white text"
        )

        circle = Circle(color=RED)
        self.transcript.add_transcript(
            "A red circle with radius 1 unit appears at origin using Create animation"
        )
        self.play(Create(circle))
        self.wait(1)

        self.clear_narrate()

        # Visual confirmation
        text = Text("Transcript + Narration Test Passed", color=GREEN).to_edge(DOWN)
        self.play(Write(text))
        self.wait(2)


class TestLongNarration(HUD2DScene):
    """Test narration with text approaching primer capacity."""

    def construct(self):
        # Test with long text (but under 100 chars)
        long_text = r"This is a longer narration text to test the primer pattern capacity limits"
        self.narrate(long_text)
        self.wait(2)

        # Verify length
        assert len(long_text.replace(" ", "")) < 100, "Text exceeds primer capacity"

        self.clear_narrate()

        # Visual confirmation
        text = Text("Long Narration Test Passed", color=GREEN).to_edge(DOWN)
        self.play(Write(text))
        self.wait(2)


class TestEmptyText(HUD2DScene):
    """Test clearing with empty strings."""

    def construct(self):
        # Display text
        self.narrate(r"Test Text")
        self.caption(r"Test Caption")
        self.wait(1)

        # Clear using the clear methods (which use empty text internally)
        self.clear_narrate()
        self.clear_caption()
        self.wait(1)

        # Visual confirmation
        text = Text("Empty Text Test Passed", color=GREEN)
        self.play(Write(text))
        self.wait(2)


class TestNarrationDuringAnimation(HUD2DScene):
    """Test narration changes during other animations."""

    def construct(self):
        square = Square(color=BLUE)
        self.add(square)

        # Change narration while animating square
        self.narrate(r"Square moves right")
        self.play(square.animate.shift(RIGHT * 2))

        self.narrate(r"Square moves left")
        self.play(square.animate.shift(LEFT * 2))

        self.clear_narrate()

        # Visual confirmation
        text = Text("Narration During Animation Test Passed", color=GREEN).to_edge(DOWN)
        self.play(Write(text))
        self.wait(2)


class TestCameraAndNarrationTogether(HUD2DScene):
    """Test camera movement and narration changes simultaneously."""

    def construct(self):
        square = Square(color=YELLOW)
        self.add(square)

        # Simultaneous camera and narration
        self.narrate(r"Camera and narration change together")
        self.play(
            self.camera.frame.animate.shift(RIGHT * 2),
            run_time=2
        )

        self.narrate(r"Moving back")
        self.play(
            self.camera.frame.animate.shift(LEFT * 2),
            run_time=2
        )

        self.clear_narrate()

        # Visual confirmation
        text = Text("Combined Test Passed", color=GREEN).to_edge(DOWN)
        self.play(Write(text))
        self.wait(2)


class TestCustomPrimerConfig(HUD2DScene):
    """Test custom primer configuration."""

    def setup(self):
        super().setup()
        # Customize after initialization
        self.narration.set_narration_font_size(48)
        self.narration.set_caption_font_size(32)
        self.narration.set_narration_color(YELLOW)
        self.narration.set_caption_color(GREEN)

    def construct(self):
        self.narrate(r"Large Yellow Narration")
        self.caption(r"Large Green Caption")
        self.wait(2)

        self.clear_narrate()
        self.clear_caption()

        text = Text("Custom Config Test Passed", color=GREEN)
        self.play(Write(text))
        self.wait(2)


class TestDirectCameraSnap(HUD2DScene):
    """Test direct camera methods (instant snap, no animation)."""

    def construct(self):
        grid = NumberPlane()
        self.add(grid)

        self.narrate(r"Testing instant camera snap")

        # Direct call - instant snap (no animation)
        self.camera.frame.shift(RIGHT * 3)
        self.wait(1)

        self.camera.frame.move_to(ORIGIN)
        self.wait(1)

        self.camera.frame.scale(0.5)
        self.wait(1)

        self.clear_narrate()

        text = Text("Direct Snap Test Passed", color=GREEN).to_edge(DOWN)
        self.play(Write(text))
        self.wait(2)


class TestLaTeXValidationWarning(HUD2DScene):
    """Test that LaTeX validation warns about escape sequences."""

    def construct(self):
        # This should trigger a warning (but still work)
        # Using \t without raw string
        self.narrate("Text with \t tab")  # Should warn
        self.wait(1)

        # Correct usage with raw string
        self.narrate(r"Text with $\tau$ symbol")  # No warning
        self.wait(1)

        self.clear_narrate()

        text = Text("LaTeX Validation Test Passed", color=GREEN).to_edge(DOWN)
        self.play(Write(text))
        self.wait(2)


class TestPrimerCapacityOverflow(HUD2DScene):
    """Test behavior when text exceeds primer capacity."""

    def construct(self):
        # Create text that exceeds 100 chars (excluding spaces)
        # This should either fail gracefully or truncate
        very_long_text = r"A" * 120  # 120 characters

        try:
            self.narrate(very_long_text)
            self.wait(2)
            self.clear_narrate()

            text = Text("Overflow handled gracefully", color=GREEN).to_edge(DOWN)
        except Exception as e:
            text = Text(f"Overflow failed: {type(e).__name__}", color=RED).to_edge(DOWN)

        self.play(Write(text))
        self.wait(2)


class TestCameraGetCenter(HUD2DScene):
    """Test camera.frame.get_center() method."""

    def construct(self):
        grid = NumberPlane()
        self.add(grid)

        # Get initial center
        initial_center = self.camera.frame.get_center()
        self.narrate(f"Initial center: {initial_center}")
        self.wait(1)

        # Move camera
        self.play(self.camera.frame.animate.shift(RIGHT * 3 + UP * 2))

        # Get new center
        new_center = self.camera.frame.get_center()
        self.narrate(f"New center: {new_center}")
        self.wait(1)

        # Verify movement
        import numpy as np
        expected_shift = np.array([3, 2, 0])
        actual_shift = new_center - initial_center
        assert np.allclose(actual_shift, expected_shift, atol=0.01), \
            f"Expected shift {expected_shift}, got {actual_shift}"

        self.clear_narrate()

        text = Text("Get Center Test Passed", color=GREEN).to_edge(DOWN)
        self.play(Write(text))
        self.wait(2)


class TestTranscriptFileOutput(HUD2DScene):
    """Test that transcript file is written with correct content."""

    def construct(self):
        # Add multiple transcript entries
        self.transcript.add_transcript("Line 1: Scene starts")
        self.transcript.add_transcript("Line 2: Square appears")

        square = Square(color=BLUE)
        self.play(Create(square))

        self.transcript.add_transcript("Line 3: Square fades out")
        self.play(FadeOut(square))

        # Note: File verification must happen after render completes
        # This test just ensures no errors during transcript writing

        text = Text("Transcript File Test Passed", color=GREEN)
        self.play(Write(text))
        self.wait(2)


class TestMultipleUpdatesBeforePlay(HUD2DScene):
    """Test multiple narration updates before play()."""

    def construct(self):
        # Multiple updates without play() in between
        self.narrate(r"First")
        self.narrate(r"Second")  # Should replace first
        self.narrate(r"Third")  # Should replace second

        # Only "Third" should be visible
        self.wait(2)

        self.clear_narrate()

        text = Text("Multiple Updates Test Passed", color=GREEN).to_edge(DOWN)
        self.play(Write(text))
        self.wait(2)


class TestCameraSetBothDimensions(HUD2DScene):
    """Test camera.frame.set() with both width and height."""

    def construct(self):
        grid = NumberPlane()
        rect = Rectangle(width=4, height=2, color=PURPLE)
        self.add(grid, rect)

        self.caption(r"Testing width precedence")

        # Set both - width should take precedence
        self.play(self.camera.frame.animate.set(width=8, height=4))
        self.wait(1)

        # Verify width was used (visual check)
        self.clear_caption()

        text = Text("Set Both Dimensions Test Passed", color=GREEN).to_edge(UP)
        self.play(Write(text))
        self.wait(2)


class TestCaptionTextTypes(HUD2DScene):
    """Test caption with different text types."""
    caption_text_type = "MathTex"

    def construct(self):
        self.caption(r"\sum_{i=1}^n i = \frac{n(n+1)}{2}")
        self.wait(2)
        self.clear_caption()

        text = Text("Caption Text Types Test Passed", color=GREEN).to_edge(UP)
        self.play(Write(text))
        self.wait(2)


