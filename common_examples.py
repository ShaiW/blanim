# blanim/common_examples.py

from common import *
#TODO run and verify these tests work as expected, if yes, organize for user demonstrations, then properly document common.py
"""      
Camera Animation Patterns - Common Mistakes      

This file demonstrates correct and incorrect ways to animate the camera in HUD2DScene.      
The behavior matches Manim's MovingCameraScene exactly.      

GOLDEN RULE: Use method chaining on a SINGLE .animate call      
    ✓ CORRECT: self.play(camera.frame.animate.move_to(pos).shift(vec).scale(factor))      
    ✗ WRONG:   self.play(camera.frame.animate.move_to(pos), camera.frame.animate.shift(vec))      

See TestSeparateVsChained for detailed examples and explanations.      
"""

class TestNarrateAndClear(HUD2DScene):
    """Demonstrate narrate_and_clear() convenience method."""

    def construct(self):
        square = Square(color=BLUE)
        self.add(square)

        # Shows narration for 2 seconds, then clears it automatically
        self.narrate_and_clear(r"This text will disappear", wait_time=2.0)

        # Continue with animation after narration is cleared
        self.caption(r"Narration cleared, caption remains")
        self.play(square.animate.scale(2))
        self.wait(1)

class TestClearMethods(HUD2DScene):
    """Demonstrate clearing narration and caption independently."""

    def construct(self):
        square = Square(color=BLUE)
        self.add(square)

        # Set both narration and caption
        self.narrate(r"Upper text")
        self.caption(r"Lower text")
        self.wait(2)

        # Clear only caption, narration remains
        self.clear_caption()
        self.wait(1)

        # Add new caption while narration still visible
        self.caption(r"New caption text")
        self.wait(1)

        # Clear narration, caption remains
        self.clear_narrate()
        self.wait(1)

        # Clear both
        self.clear_caption()
        self.wait(1)

class TestCustomFontSizes(HUD2DScene):
    """Demonstrate custom font sizes for narration and caption."""

    narration_font_size = 48  # Larger than default 32
    caption_font_size = 20  # Smaller than default 26

    def construct(self):
        square = Square(color=BLUE)
        self.add(square)

        self.narrate(r"Large narration text")
        self.caption(r"Small caption text")
        self.wait(2)

##########Transcript Usage##########

class TranscriptExample(HUD2DScene):
    """Example showing how to add a transcript (.txt) file alongside video output.

    The transcript provides verbose descriptions of scene events, separate from
    the visual narration/caption text shown on screen.
    """

    def construct(self):
        # Create objects
        square = Square(color=BLUE)
        circle = Circle(color=RED, radius=1.5)

        # Introduction
        self.narrate(r"Geometric Transformations")
        self.transcript.add_transcript("Scene opens with title 'Geometric Transformations'")
        self.wait(1)

        # Create square
        self.caption(r"Creating a square")
        self.transcript.add_transcript("A blue square appears at the origin using Create animation")
        self.play(Create(square))
        self.wait(0.5)

        # Rotate square
        self.caption(r"Rotating $90°$")
        self.transcript.add_transcript("The square rotates 90 degrees clockwise over 1.5 seconds")
        self.play(Rotate(square, angle=PI / 2), run_time=1.5)
        self.wait(0.5)

        # Scale square
        self.caption(r"Scaling by factor $1.5$")
        self.transcript.add_transcript("The square scales up by a factor of 1.5")
        self.play(square.animate.scale(1.5))
        self.wait(0.5)

        # Transform to circle
        self.caption(r"Morphing shape")
        self.transcript.add_transcript("The blue square transforms into a red circle using Transform animation")
        self.play(Transform(square, circle))
        self.wait(0.5)

        # Move circle
        self.caption(r"Moving $3$ units right")
        self.transcript.add_transcript("The circle shifts 3 units to the right")
        self.play(square.animate.shift(RIGHT * 3))
        self.wait(0.5)

        # Fade out
        self.clear_caption()
        self.transcript.add_transcript("The circle fades out and the scene ends")
        self.play(FadeOut(square))
        self.clear_narrate()
        self.wait(1)


class NoTranscriptExample(HUD2DScene):
    """Example showing that scenes without transcript calls don't create files."""

    def construct(self):
        # Visual elements only, no transcript documentation
        self.narrate(r"No Transcript")
        square = Square()
        self.play(Create(square))
        # No .txt file will be created since add_transcript() was never called


##########
# PART 1: INDIVIDUAL OPERATIONS (NO CHAINING) WITH TEX FOR NARRATION/CAPTION
##########

class TestIndividualOperations(HUD2DScene):
    """Test each camera operation independently with Tex narration.

    Demonstrates using Tex (text mode with $...$ for math) for HUD text.
    This is the default text type for HUD2DScene.
    """

    # narration_text_type = "Tex"  # This is the default, no need to specify

    def construct(self):
        square = Square(color=BLUE, side_length=2).shift(LEFT * 3)
        circle = Circle(color=RED, radius=1).shift(RIGHT * 3)
        grid = NumberPlane(x_range=[-7, 7], y_range=[-4, 4])

        self.add(grid, square, circle)

        # Test 1: move_to alone
        self.narrate(r"camera.frame.animate.move\_to(square)")
        self.caption(r"Camera smoothly moves to center on the blue square")
        self.play(self.camera.frame.animate.move_to(square), run_time=2.0)
        self.wait(1.0)

        # Test 2: shift alone - with math notation
        self.narrate(r"camera.frame.animate.shift(RIGHT $\times$ 2)")
        self.caption(r"Camera shifts $2$ units to the right")
        self.play(self.camera.frame.animate.shift(RIGHT * 2), run_time=2.0)
        self.wait(1.0)

        # Test 3: scale with mathematical notation
        self.narrate(r"camera.frame.animate.scale($0.5$)")
        self.caption(r"Camera zooms in (objects appear $2\times$ larger)")
        self.play(self.camera.frame.animate.scale(0.5), run_time=2.0)
        self.wait(1.0)

        # Test 4: scale alone (zoom out)
        self.narrate(r"camera.frame.animate.scale($2.0$)")
        self.caption(r"Camera zooms out (objects appear $2\times$ smaller)")
        self.play(self.camera.frame.animate.scale(2.0), run_time=2.0)
        self.wait(1.0)

        # Test 5: set width alone
        self.narrate(r"camera.frame.animate.set(width=$10$)")
        self.caption(r"Camera sets frame width to $10$ units")
        self.play(self.camera.frame.animate.set(width=10), run_time=2.0)
        self.wait(1.0)

        # Reset for next test
        self.narrate(r"Reset: move\_to(ORIGIN).set(width=$14$)")
        self.caption(r"Camera returns to origin with default width")
        self.play(self.camera.frame.animate.move_to(ORIGIN).set(width=14), run_time=2.0)
        self.wait(1.0)


class TestMathTexNarration(HUD2DScene):
    """Example using MathTex for math-heavy narration.

    Use MathTex when your narration is primarily mathematical expressions.
    Regular text requires \\text{} wrapping in MathTex mode.
    """
    narration_text_type = "MathTex"  # Override to use MathTex

    def construct(self):
        # Create mathematical objects
        equation = MathTex(r"f(x) = x^2 + 2x + 1")
        self.add(equation)

        # MathTex mode: math by default, use \text{} for regular text
        self.narrate(r"f(x) = x^2 + 2x + 1")
        self.caption(r"\text{A quadratic function}")
        self.wait(2)

        # Show factored form
        factored = MathTex(r"f(x) = (x + 1)^2")
        self.narrate(r"f(x) = (x + 1)^2")
        self.caption(r"\text{Factored form}")
        self.play(Transform(equation, factored))
        self.wait(2)

        # Show derivative
        derivative = MathTex(r"f'(x) = 2x + 2")
        self.narrate(r"f'(x) = 2x + 2")
        self.caption(r"\text{The derivative}")
        self.play(Transform(equation, derivative))
        self.wait(2)


class TestTextNarration(HUD2DScene):
    """Example using Text for plain text narration (no LaTeX required).

    Use Text as a fallback when LaTeX is not available, or when you
    don't need mathematical notation at all.
    """
    narration_text_type = "Text"  # Override to use Text (no LaTeX)

    def construct(self):
        square = Square(color=BLUE)
        self.add(square)

        # Text mode: plain strings, no special syntax needed
        self.narrate("Simple Animation")
        self.caption("No LaTeX required for this example")
        self.wait(1)

        # Animate the square
        self.caption("Rotating the square")
        self.play(Rotate(square, angle=PI / 2))
        self.wait(1)

        # Note: Math symbols won't render in Text mode
        self.caption("Text mode doesn't support math like x^2")
        self.wait(2)


##########
# PART 2: PANNING CHAINS (move_to + shift combinations)
##########

class TestPanningChains(HUD2DScene):
    """Test all combinations of panning operations chained together.

    Expected: All should work smoothly with target-based approach.
    """

    def construct(self):
        square = Square(color=BLUE, side_length=2).shift(LEFT * 3)
        circle = Circle(color=RED, radius=1).shift(RIGHT * 3)
        grid = NumberPlane(x_range=[-7, 7], y_range=[-4, 4])

        self.add(grid, square, circle)

        # Test 1: move_to → shift
        self.narrate(r"camera.frame.animate.move\_to(square).shift(UP)")
        self.caption(r"Camera moves to square, then shifts up $1$ unit (chained)")
        self.play(
            self.camera.frame.animate
            .move_to(square)
            .shift(UP * 1),
            run_time=2.0
        )
        self.wait(1.0)

        # Test 2: shift → move_to
        self.narrate(r"camera.frame.animate.shift(RIGHT $\times$ 2).move\_to(circle)")
        self.caption(r"Camera shifts right $2$ units, then moves to circle (final position: circle)")
        self.play(
            self.camera.frame.animate
            .shift(RIGHT * 2)
            .move_to(circle),
            run_time=2.0
        )
        self.wait(1.0)

        # Test 3: move_to → shift → shift
        self.narrate(r"camera.frame.animate.move\_to(ORIGIN).shift(RIGHT).shift(DOWN)")
        self.caption(r"Camera moves to origin, shifts right, then down (cumulative)")
        self.play(
            self.camera.frame.animate
            .move_to(ORIGIN)
            .shift(RIGHT * 1)
            .shift(DOWN * 1),
            run_time=2.0
        )
        self.wait(1.0)

        # Test 4: shift → shift → move_to
        self.narrate(r"camera.frame.animate.shift(LEFT).shift(UP).move\_to(square)")
        self.caption(r"Camera shifts left, up, then moves to square (final position: square)")
        self.play(
            self.camera.frame.animate
            .shift(LEFT * 1)
            .shift(UP * 1)
            .move_to(square),
            run_time=2.0
        )
        self.wait(1.0)

        # Test 5: move_to → move_to (overwrite)
        self.narrate(r"camera.frame.animate.move\_to(circle).move\_to(ORIGIN)")
        self.caption(r"Camera moves to circle, then to origin (second move\_to overwrites first)")
        self.play(
            self.camera.frame.animate
            .move_to(circle)
            .move_to(ORIGIN),
            run_time=2.0
        )
        self.wait(1.0)

    ##########


# PART 3: ZOOM CHAINS (scale + set combinations)
##########

class TestZoomChains(HUD2DScene):
    """Test all combinations of zoom operations chained together.

    Expected: With target-based approach, these should work correctly.
    Last operation should determine final zoom level.
    """

    def construct(self):
        square = Square(color=BLUE, side_length=2)
        grid = NumberPlane(x_range=[-7, 7], y_range=[-4, 4])

        self.add(grid, square)

        # Test 1: scale → scale (zoom in then out)
        self.narrate(r"camera.frame.animate.scale($0.5$).scale($2.0$)")
        self.caption(r"Camera zooms in $2\times$, then out $2\times$ (net effect: back to original zoom)")
        self.play(
            self.camera.frame.animate
            .scale(0.5)
            .scale(2.0),
            run_time=2.0
        )
        self.wait(1.0)

        # Test 2: scale → set
        self.narrate(r"camera.frame.animate.scale($0.5$).set(width=$10$)")
        self.caption(r"Camera zooms in $2\times$, then sets width to $10$ (set overwrites scale)")
        self.play(
            self.camera.frame.animate
            .scale(0.5)
            .set(width=10),
            run_time=2.0
        )
        self.wait(1.0)

        # Test 3: set → scale
        self.narrate(r"camera.frame.animate.set(width=$8$).scale($0.5$)")
        self.caption(r"Camera sets width to $8$, then zooms in $2\times$ (cumulative: width=$4$)")
        self.play(
            self.camera.frame.animate
            .set(width=8)
            .scale(0.5),
            run_time=2.0
        )
        self.wait(1.0)

        # Test 4: set → set (overwrite)
        self.narrate(r"camera.frame.animate.set(width=$6$).set(width=$14$)")
        self.caption(r"Camera sets width to $6$, then to $14$ (second set overwrites first)")
        self.play(
            self.camera.frame.animate
            .set(width=6)
            .set(width=14),
            run_time=2.0
        )
        self.wait(1.0)

        # Test 5: Multiple scales
        self.narrate(r"camera.frame.animate.scale($0.5$).scale($2.0$).scale($0.5$)")
        self.caption(r"Camera zooms in $2\times$, out $2\times$, in $2\times$ (net effect: zoomed in $2\times$)")
        self.play(
            self.camera.frame.animate
            .scale(0.5)
            .scale(2.0)
            .scale(0.5),
            run_time=2.0
        )
        self.wait(1.0)


##########
# PART 4: MIXED CHAINS (panning + zoom in all orders)
##########

class TestMixedChains(HUD2DScene):
    """Test all combinations of panning and zoom operations chained together.

    Expected: With target-based approach, ALL combinations should work!
    This is the key improvement over the previous implementation.
    """

    def construct(self):
        square = Square(color=BLUE, side_length=2).shift(LEFT * 3)
        circle = Circle(color=RED, radius=1).shift(RIGHT * 3)
        grid = NumberPlane(x_range=[-7, 7], y_range=[-4, 4])

        self.add(grid, square, circle)

        # Test 1: move_to → scale
        self.narrate(r"camera.frame.animate.move\_to(square).scale($0.5$)")
        self.caption(r"Camera moves to square AND zooms in $2\times$ simultaneously")
        self.play(
            self.camera.frame.animate
            .move_to(square)
            .scale(0.5),
            run_time=2.0
        )
        self.wait(1.0)

        # Test 2: scale → move_to
        self.narrate(r"camera.frame.animate.scale($2.0$).move\_to(circle)")
        self.caption(r"Camera zooms out $2\times$ AND moves to circle simultaneously")
        self.play(
            self.camera.frame.animate
            .scale(2.0)
            .move_to(circle),
            run_time=2.0
        )
        self.wait(1.0)

        # Test 3: shift → scale
        self.narrate(r"camera.frame.animate.shift(LEFT $\times$ 2).scale($0.5$)")
        self.caption(r"Camera shifts left 2 units AND zooms in $2\times$ simultaneously")
        self.play(
            self.camera.frame.animate
            .shift(LEFT * 2)
            .scale(0.5),
            run_time=2.0
        )
        self.wait(1.0)

        # Test 4: scale → shift
        self.narrate(r"camera.frame.animate.scale($2.0$).shift(RIGHT $\times$ 2)")
        self.caption(r"Camera zooms out $2\times$ AND shifts right 2 units simultaneously")
        self.play(
            self.camera.frame.animate
            .scale(2.0)
            .shift(RIGHT * 2),
            run_time=2.0
        )
        self.wait(1.0)

        # Test 5: move_to → shift → scale
        self.narrate(r"camera.frame.animate.move\_to(ORIGIN).shift(UP).scale($0.5$)")
        self.caption(r"Camera moves to origin, shifts up, AND zooms in $2\times$ (all combined)")
        self.play(
            self.camera.frame.animate
            .move_to(ORIGIN)
            .shift(UP * 1)
            .scale(0.5),
            run_time=2.0
        )
        self.wait(1.0)

        # Test 6: scale → move_to → shift
        self.narrate(r"camera.frame.animate.scale($2.0$).move\_to(square).shift(DOWN)")
        self.caption(r"Camera zooms out $2\times$, moves to square, AND shifts down (all combined)")
        self.play(
            self.camera.frame.animate
            .scale(2.0)
            .move_to(square)
            .shift(DOWN * 1),
            run_time=2.0
        )
        self.wait(1.0)

        # Test 7: move_to → scale → shift
        self.narrate(r"camera.frame.animate.move\_to(circle).scale($0.5$).shift(RIGHT)")
        self.caption(r"Camera moves to circle, zooms in $2\times$, AND shifts right (all combined)")
        self.play(
            self.camera.frame.animate
            .move_to(circle)
            .scale(0.5)
            .shift(RIGHT * 1),
            run_time=2.0
        )
        self.wait(1.0)

        # Test 8: shift → scale → move_to
        self.narrate(r"camera.frame.animate.shift(LEFT).scale($2.0$).move\_to(ORIGIN)")
        self.caption(r"Camera shifts left, zooms out $2\times$, AND moves to origin (final: origin)")
        self.play(
            self.camera.frame.animate
            .shift(LEFT * 1)
            .scale(2.0)
            .move_to(ORIGIN),
            run_time=2.0
        )
        self.wait(1.0)

        # Test 9: scale → shift → scale
        self.narrate(r"camera.frame.animate.scale($0.5$).shift(UP).scale($2.0$)")
        self.caption(r"Camera zooms in $2\times$, shifts up, AND zooms out $2\times$ (net zoom: original)")
        self.play(
            self.camera.frame.animate
            .scale(0.5)
            .shift(UP * 1)
            .scale(2.0),
            run_time=2.0
        )
        self.wait(1.0)

        # Test 10: move_to → set → shift
        self.narrate(r"camera.frame.animate.move\_to(square).set(width=$8$).shift(DOWN)")
        self.caption(r"Camera moves to square, sets width to $8$, AND shifts down (all combined)")
        self.play(
            self.camera.frame.animate
            .move_to(square)
            .set(width=8)
            .shift(DOWN * 1),
            run_time=2.0
        )
        self.wait(1.0)

        # Test 11: Complex chain with all operations
        self.narrate(r"camera.frame.animate.move\_to(ORIGIN).shift(RIGHT).scale($0.5$).shift(UP).scale($2.0$)")
        self.caption(r"Complex: moves to origin, shifts right, zooms in, shifts up, zooms out")
        self.play(
            self.camera.frame.animate
            .move_to(ORIGIN)
            .shift(RIGHT * 1)
            .scale(0.5)
            .shift(UP * 1)
            .scale(2.0),
            run_time=2.0
        )
        self.wait(1.0)

    ##########


# PART 5: DIRECT (NON-ANIMATED) OPERATIONS
##########

class TestDirectOperations(HUD2DScene):
    """Test direct (non-animated) camera operations.

    These operations execute instantly without animation.
    """

    def construct(self):
        square = Square(color=BLUE, side_length=2).shift(LEFT * 3)
        circle = Circle(color=RED, radius=1).shift(RIGHT * 3)
        grid = NumberPlane(x_range=[-7, 7], y_range=[-4, 4])

        self.add(grid, square, circle)

        # Test 1: Direct move_to
        self.narrate(r"camera.frame.move\_to(square)")
        self.caption(r"Camera instantly jumps to square (no animation)")

        self.camera.frame.move_to(square)
        self.wait(1.0)

        # Test 2: Direct shift
        self.narrate(r"camera.frame.shift(RIGHT $\times$ 3)")
        self.caption(r"Camera instantly shifts right (no animation)")

        self.camera.frame.shift(RIGHT * 3)
        self.wait(1.0)

        # Test 3: Direct scale
        self.narrate(r"camera.frame.scale($0.5$)")
        self.caption(r"Camera instantly zooms in (no animation)")

        self.camera.frame.scale(0.5)
        self.wait(1.0)

        # Test 4: Direct set
        self.narrate(r"camera.frame.set(width=$14$)")
        self.caption(r"Camera instantly sets width to $14$ (no animation)")

        self.camera.frame.set(width=14)
        self.wait(1.0)

        # Test 5: Chained direct operations
        self.narrate(r"camera.frame.move\_to(ORIGIN).shift(UP).scale($1.5$)")
        self.caption(r"Camera instantly moves to origin, shifts up, and zooms out (all chained, no animation)")

        self.camera.frame.move_to(ORIGIN).shift(UP * 1).scale(1.5)
        self.wait(1.0)


##########
# PART 6: COMPARISON WITH SEPARATE ANIMATIONS
# This example demonstrates CORRECT vs INCORRECT camera animation patterns.
# Tests 2-4 show common mistakes that produce unexpected results.
##########

class TestSeparateVsChained(HUD2DScene):
    """Compare chained operations vs separate animations in same play().

    IMPORTANT: This example demonstrates both correct and incorrect usage patterns.

    **Correct Usage (Test 1):**
    - Chain multiple operations on a single .animate call
    - Example: `camera.frame.animate.move_to(pos).shift(vec).scale(factor)`

    **Incorrect Usage (Tests 2-4):**
    - Multiple separate .animate calls for the same mobject in one play()
    - Example: `play(obj.animate.move(), obj.animate.scale())`  # DON'T DO THIS

    **Why It Fails:**
    Manim's .animate system creates separate Animation objects for each .animate call.
    When multiple animations target the same mobject in a single play() call, only
    the LAST animation executes - all previous animations are discarded.

    This matches MovingCameraScene behavior and is documented in Manim's warning:
    "Passing multiple animations for the same Mobject in one call to Scene.play
    is discouraged and will most likely not work properly."

    See: manim/mobject/mobject.py:313-324 for the official warning.
    """

    def construct(self):
        square = Square(color=BLUE, side_length=2).shift(LEFT * 3)
        circle = Circle(color=RED, radius=1).shift(RIGHT * 3)
        grid = NumberPlane(x_range=[-7, 7], y_range=[-4, 4])

        self.add(grid, square, circle)

        # ========== TEST 1: CORRECT USAGE ==========
        self.narrate(r"camera.frame.animate.move\_to(square).shift(RIGHT $\times$ 2)")
        self.caption(r"$\checkmark$ CORRECT: Chained operations create single animation")

        self.play(
            self.camera.frame.animate.move_to(square).shift(RIGHT * 2),
            run_time=2.0
        )
        self.wait(1.0)

        # Reset camera
        self.play(
            self.camera.frame.animate.move_to(ORIGIN),
            run_time=2.0
        )
        self.wait(1.0)

        # ========== TEST 2: INCORRECT USAGE - Multiple Position Animations ==========
        self.narrate(r"camera.frame.animate.move\_to(square), camera.frame.animate.shift(RIGHT $\times$ 2)")
        self.caption(r"$\times$ WRONG: Only shift executes, move\_to is ignored (last animation wins)")

        # ANTI-PATTERN: Two separate .animate calls for same mobject
        # Expected: Camera moves to square THEN shifts right
        # Actual: Only the shift(RIGHT * 2) executes, move_to(square) is discarded
        self.play(
            self.camera.frame.animate.move_to(square),  # ← This is IGNORED
            self.camera.frame.animate.shift(RIGHT * 2),  # ← Only this executes
            run_time=2.0
        )
        self.wait(1.0)

        # Reset camera
        self.play(
            self.camera.frame.animate.move_to(ORIGIN),
            run_time=2.0
        )
        self.wait(1.0)

        # ========== TEST 3: INCORRECT USAGE - Position + Scale Animations ==========
        self.narrate(r"camera.frame.animate.move\_to(circle).shift(UP), camera.frame.animate.scale($0.5$)")
        self.caption(r"$\times$ WRONG: Only scale executes, chained position ops are ignored")
        # ANTI-PATTERN: Chained position ops + separate scale animation
        # Expected: Camera moves to circle+up AND zooms in
        # Actual: Only scale(0.5) executes, move_to().shift() is discarded
        # Note: Even though move_to/shift are chained, they're still part of the
        # FIRST .animate call, which gets overridden by the SECOND .animate call
        self.play(
            self.camera.frame.animate.move_to(circle).shift(UP * 1),  # ← IGNORED
            self.camera.frame.animate.scale(0.5),  # ← Only this executes
            run_time=2.0
        )
        self.wait(1.0)

        # Reset camera
        # NOTE: This reset also demonstrates the problem - move_to(ORIGIN) is ignored!
        # The camera stays at ORIGIN only because Test 3's position change was ignored,
        # so we're accidentally already at ORIGIN. This is NOT reliable behavior.
        self.play(
            self.camera.frame.animate.move_to(ORIGIN),  # ← IGNORED
            self.camera.frame.animate.scale(2.0),  # ← Only this executes
            run_time=2.0
        )
        self.wait(1.0)

        # ========== TEST 4: INCORRECT USAGE - Three Separate Animations ==========
        self.narrate(
            r"camera.frame.animate.move\_to(circle), camera.frame.animate.shift(UP), camera.frame.animate.scale($0.5$)")
        self.caption(r"$\times$ WRONG: Only scale executes, all position anims ignored")
        # ANTI-PATTERN: Three separate .animate calls
        # Expected: Camera moves to circle, shifts up, AND zooms in
        # Actual: Only scale(0.5) executes, both position animations are discarded
        self.play(
            self.camera.frame.animate.move_to(circle),  # ← IGNORED
            self.camera.frame.animate.shift(UP * 1),  # ← IGNORED
            self.camera.frame.animate.scale(0.5),  # ← Only this executes
            run_time=2.0
        )
        self.wait(1.0)

        self.narrate(r"Comparison complete!")
        self.caption(r"Remember: Chain operations on ONE .animate call, not multiple separate calls")
        self.wait(1.0)
    # Compare to movingcamerascene


class MovingCameraComparison(MovingCameraScene):
    """Compare with standard MovingCameraScene behavior."""

    def construct(self):
        square = Square(color=BLUE, side_length=2).shift(LEFT * 3)
        circle = Circle(color=RED, radius=1).shift(RIGHT * 3)
        grid = NumberPlane(x_range=[-7, 7], y_range=[-4, 4])

        self.add(grid, square, circle)

        # Test 1: Chained panning operations
        self.play(
            self.camera.frame.animate.move_to(square).shift(RIGHT * 2),
            run_time=2.0
        )
        self.wait(1.0)

        # Reset camera
        self.play(
            self.camera.frame.animate.move_to(ORIGIN),
            run_time=2.0
        )
        self.wait(1.0)

        # Test 2: Same operations as separate animations
        self.play(
            self.camera.frame.animate.move_to(square),
            self.camera.frame.animate.shift(RIGHT * 2),
            run_time=2.0
        )
        self.wait(1.0)

        # Reset camera
        self.play(
            self.camera.frame.animate.move_to(ORIGIN),
            run_time=2.0
        )
        self.wait(1.0)

        # Test 3: Chained panning + separate zoom
        self.play(
            self.camera.frame.animate.move_to(circle).shift(UP * 1),
            self.camera.frame.animate.scale(0.5),
            run_time=2.0
        )
        self.wait(1.0)

        # Reset camera
        self.play(
            self.camera.frame.animate.move_to(ORIGIN),
            self.camera.frame.animate.scale(2.0),
            run_time=2.0
        )
        self.wait(1.0)

        # Test 4: All separate animations
        self.play(
            self.camera.frame.animate.move_to(circle),
            self.camera.frame.animate.shift(UP * 1),
            self.camera.frame.animate.scale(0.5),
            run_time=2.0
        )
        self.wait(1.0)


class TestHeightParameter(HUD2DScene):
    """Test height parameter in set() method."""

    def construct(self):
        grid = NumberPlane(x_range=[-7, 7], y_range=[-4, 4])
        self.add(grid)

        # Test height alone
        self.narrate(r"camera.frame.animate.set(height=$6$)")
        self.play(self.camera.frame.animate.set(height=6), run_time=2.0)
        self.wait(1.0)

        # Test width and height (width takes precedence)
        self.narrate(r"camera.frame.animate.set(width=$10$, height=$6$)")
        self.caption(r"Width takes precedence when both specified")
        self.play(self.camera.frame.animate.set(width=10, height=6), run_time=2.0)
        self.wait(1.0)

"""    
VALIDATION TESTING    
  
NOTE: The validation system checks for common Python string issues (missing raw string prefix)  
that lead to LaTeX compilation errors. It may produce false positives for valid LaTeX commands  
containing character sequences like \t or \n (e.g., \textbf, \newcommand). The validation does  
NOT catch all possible LaTeX errors - only Python escape sequence issues.  
  
The TestLoggerValidation scene demonstrates the LaTeX string validation system.    
It includes both correct and incorrect usage patterns.    
  
**Tests that succeed (no warnings, no crashes):**    
- Test 1: Raw string with math notation    
- Test 5: Raw string with escaped backslash    
- Test 7: Raw string with math and escaped characters    
  
**Tests that are EXPECTED TO CRASH:**    
- Test 2: Missing r prefix with \n (newline) - demonstrates validation warning before crash    
- Test 3: Missing r prefix with \t (tab) - demonstrates validation warning before crash    
- Test 4: Missing r prefix with \r (carriage return) - demonstrates validation warning before crash    
- Test 6: Multiple escape sequences - demonstrates validation warning before crash    
  
The crashes are intentional and demonstrate that:    
1. The validation system correctly detects Python escape sequence issues    
2. Warnings appear in the console BEFORE the LaTeX compilation error    
3. Users receive helpful guidance about the likely cause    
  
To run only successful tests, comment out tests 2-6 in the construct() method.    
"""

class TestLoggerValidation(HUD2DScene):
    """Test scene to trigger logger warnings for LaTeX string validation.

    This scene demonstrates various mistakes that trigger validation warnings
    in the UniversalNarrationManager._validate_latex_string() method.

    **IMPORTANT**: Tests 2-4 and 6 are EXPECTED TO CRASH with LaTeX compilation
    errors. They demonstrate incorrect usage patterns that the validation system
    warns about. The warnings appear in the console before the crash occurs.

    To run only the successful tests, comment out tests 2-6.
    """

    def construct(self):
        square = Square(color=BLUE)
        self.add(square)

        # Test 1: Correct usage (no warning, no crash)
        self.narrate(r"Correct: Using raw string with $x^2$")
        self.caption(r"This should not trigger any warnings")
        self.wait(2)

        # Test 2: Missing r prefix with \n (newline escape sequence)
        # EXPECTED TO CRASH: This will trigger a warning, then crash with LaTeX error
        # The warning demonstrates that validation caught the issue before compilation
        self.narrate("Missing r prefix\nThis has a newline")
        self.caption("Check console for warning about \\n escape sequence")
        self.wait(2)

        # Test 3: Missing r prefix with \t (tab escape sequence)
        # EXPECTED TO CRASH: Similar to test 2
        self.narrate("Missing r prefix\tThis has a tab")
        self.caption("Check console for warning about \\t escape sequence")
        self.wait(2)

        # Test 4: Missing r prefix with \r (carriage return)
        # EXPECTED TO CRASH: Similar to tests 2-3
        self.narrate("Missing r prefix\rThis has carriage return")
        self.caption("Check console for warning about \\r escape sequence")
        self.wait(2)

        # Test 5: Correct usage with escaped backslash (no warning, no crash)
        self.narrate(r"Correct: Using \\backslash properly")
        self.caption(r"This should not trigger warnings")
        self.wait(2)

        # Test 6: Multiple escape sequences
        # EXPECTED TO CRASH: Demonstrates multiple issues in one string
        self.narrate("Multiple issues\n\there")
        self.caption("Check console for warning about multiple escape sequences")
        self.wait(2)

        # Test 7: Correct usage with math and escaped characters (no warning, no crash)
        self.narrate(r"Correct: $x^2$ with escaped \% percent")
        self.caption(r"This should not trigger warnings")
        self.wait(2)